from datetime import datetime
import hashlib
import logging
from pathlib import Path
import secrets
from uuid import uuid4

from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import AliasChoices, BaseModel, ConfigDict, EmailStr, Field, model_validator
from sqlalchemy.exc import IntegrityError, OperationalError

from app.config import settings
from app.db import (
    check_database_connection,
    create_client,
    create_technician,
    create_vehicle,
    create_workshop_registration,
    delete_client,
    delete_vehicle,
    delete_workshop_registration,
    delete_technician,
    delete_technician_for_workshop,
    get_client_by_email,
    get_client_by_id,
    get_vehicle_by_id,
    get_workshop_by_id,
    get_workshop_by_email,
    init_database,
    list_clients,
    list_technicians,
    list_technicians_by_workshop,
    list_vehicles,
    list_workshop_registrations,
    update_client,
    update_client_status,
    update_technician,
    update_technician_for_workshop,
    update_vehicle,
    update_workshop_approval_status_with_password,
    update_workshop_password,
    update_workshop_registration,
)


UPLOADS_ROOT = Path(settings.uploads_dir)
VEHICLE_UPLOADS_DIR = UPLOADS_ROOT / "vehicles"
UPLOADS_ROOT.mkdir(parents=True, exist_ok=True)
VEHICLE_UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
logger = logging.getLogger(__name__)
PROTECTED_ADMIN_EMAIL = settings.protected_admin_email.lower().strip()
PROTECTED_ADMIN_ROLE = "admin"
PROTECTED_ADMIN_ID = 0
WORKSHOP_ROLE = "workshop"


class WorkshopRegistrationCreate(BaseModel):
    workshop_name: str = Field(min_length=3, max_length=160)
    contact_name: str = Field(min_length=3, max_length=160)
    phone: str = Field(min_length=7, max_length=40)
    email: EmailStr
    zone: str = Field(min_length=2, max_length=120)
    specialty: str = Field(min_length=2, max_length=120)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    timezone: str | None = Field(default=None, min_length=2, max_length=120)
    utc_offset_minutes: int | None = Field(default=None, ge=-840, le=840)


class WorkshopRegistrationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    workshop_name: str
    contact_name: str
    phone: str
    email: EmailStr
    zone: str
    specialty: str
    approval_status: str
    latitude: float | None = None
    longitude: float | None = None
    timezone: str | None = None
    utc_offset_minutes: int | None = None
    created_at: datetime


class WorkshopApprovalStatusUpdate(BaseModel):
    approval_status: str = Field(pattern="^(pendiente|activo|rechazado)$")


class TechnicianBase(BaseModel):
    full_name: str = Field(min_length=3, max_length=160)
    phone: str = Field(min_length=7, max_length=40)
    email: EmailStr
    specialty: str = Field(min_length=2, max_length=120)
    status: str = Field(pattern="^(disponible|ocupado|fuera_de_servicio)$")


class TechnicianCreate(TechnicianBase):
    workshop_id: int | None = Field(default=None, ge=1)


class TechnicianResponse(TechnicianBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    workshop_id: int | None = None
    created_at: datetime
    updated_at: datetime


class ClientRegistrationCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    identity_card: str = Field(
        min_length=5,
        max_length=40,
        validation_alias=AliasChoices("identity_card", "identityCard", "ci"),
    )
    full_name: str = Field(
        min_length=3,
        max_length=160,
        validation_alias=AliasChoices("full_name", "fullName", "name"),
    )
    email: EmailStr
    phone: str = Field(
        min_length=7,
        max_length=40,
        validation_alias=AliasChoices("phone", "telefono"),
    )
    password: str = Field(min_length=6, max_length=255)
    confirm_password: str | None = Field(
        default=None,
        min_length=6,
        max_length=255,
        validation_alias=AliasChoices("confirm_password", "confirmPassword"),
    )
    role: str = Field(default="client", min_length=2, max_length=40)
    accepted_terms: bool = Field(
        default=False,
        validation_alias=AliasChoices("accepted_terms", "acceptedTerms", "termsAccepted"),
    )

    @model_validator(mode="after")
    def validate_registration(self) -> "ClientRegistrationCreate":
        if self.confirm_password is not None and self.password != self.confirm_password:
            raise ValueError("Las contraseñas no coinciden")

        if not self.accepted_terms:
            raise ValueError("Debes aceptar los terminos y condiciones")

        return self


class ClientRegistrationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    identity_card: str
    full_name: str
    email: EmailStr
    phone: str
    role: str
    status: str
    accepted_terms: bool
    created_at: datetime
    updated_at: datetime


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=255)


class LoginResponse(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    phone: str
    role: str
    status: str
    access_token: str | None = None
    token_type: str | None = None


class WorkshopPasswordChangeRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    email: EmailStr
    new_password: str = Field(
        min_length=6,
        max_length=255,
        validation_alias=AliasChoices("new_password", "newPassword", "password"),
    )
    confirm_password: str = Field(
        min_length=6,
        max_length=255,
        validation_alias=AliasChoices("confirm_password", "confirmPassword"),
    )

    @model_validator(mode="after")
    def validate_passwords(self) -> "WorkshopPasswordChangeRequest":
        if self.new_password != self.confirm_password:
            raise ValueError("Las contraseñas no coinciden")

        return self


class ClientStatusUpdate(BaseModel):
    status: str = Field(pattern="^(active|suspended)$")


class ClientUpdate(BaseModel):
    identity_card: str = Field(min_length=5, max_length=40)
    full_name: str = Field(min_length=3, max_length=160)
    email: EmailStr
    phone: str = Field(min_length=7, max_length=40)
    password: str | None = Field(default=None, min_length=6, max_length=255)
    role: str = Field(min_length=2, max_length=40)
    status: str = Field(pattern="^(active|suspended)$")
    accepted_terms: bool = True


class VehicleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    client_id: int
    brand: str
    model: str
    year: int
    plate: str
    color: str
    is_primary: bool
    photo_path: str | None = None
    photo_url: str | None = None
    created_at: datetime


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000)
    return f"{salt}${digest.hex()}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        salt, expected_digest = password_hash.split("$", 1)
    except ValueError:
        return False

    candidate_digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        100_000,
    ).hex()
    return secrets.compare_digest(candidate_digest, expected_digest)


def normalize_plate(plate: str) -> str:
    return plate.strip().upper()


def is_protected_admin_email(email: str) -> bool:
    return email.lower().strip() == PROTECTED_ADMIN_EMAIL


def is_protected_admin_role(role: str) -> bool:
    return role.lower().strip() == PROTECTED_ADMIN_ROLE


def ensure_client_exists(client_id: int) -> None:
    try:
        client = get_client_by_id(client_id)
    except OperationalError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Base de datos no disponible",
        ) from exc

    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente no encontrado")


def save_vehicle_photo(photo: UploadFile | None) -> tuple[str | None, str | None]:
    if photo is None or not photo.filename:
        return None, None

    suffix = Path(photo.filename).suffix.lower()
    allowed_suffixes = {".jpg", ".jpeg", ".png", ".webp"}

    if suffix not in allowed_suffixes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La foto debe ser JPG, JPEG, PNG o WEBP",
        )

    filename = f"{uuid4().hex}{suffix}"
    relative_path = f"vehicles/{filename}"
    absolute_path = VEHICLE_UPLOADS_DIR / filename

    with absolute_path.open("wb") as buffer:
        while chunk := photo.file.read(1024 * 1024):
            buffer.write(chunk)

    return relative_path, f"/uploads/{relative_path}"


def remove_vehicle_photo(photo_path: str | None) -> None:
    if not photo_path:
        return

    candidate = (UPLOADS_ROOT / photo_path).resolve()

    try:
        candidate.relative_to(UPLOADS_ROOT.resolve())
    except ValueError:
        return

    if candidate.is_file():
        candidate.unlink()


app = FastAPI(
    title=settings.app_name,
    debug=settings.app_debug,
    version="0.1.0",
)
app.mount("/uploads", StaticFiles(directory=str(UPLOADS_ROOT)), name="uploads")

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=(
        r"^https?://("
        r"localhost|"
        r"127\.0\.0\.1|"
        r"10\.\d+\.\d+\.\d+|"
        r"172\.(1[6-9]|2\d|3[0-1])\.\d+\.\d+|"
        r"192\.168\.\d+\.\d+|"
        r"\d+\.\d+\.\d+\.\d+"
        r")(:\d+)?$"
    ),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    try:
        init_database()
    except OperationalError:
        logger.exception("No se pudo inicializar la base de datos en startup")


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "Backend running"}


@app.get(f"{settings.api_prefix}/health")
def healthcheck() -> dict[str, object]:
    database_ok = False

    try:
        database_ok = check_database_connection()
    except Exception:
        database_ok = False

    return {
        "status": "ok",
        "environment": settings.app_env,
        "database": "connected" if database_ok else "unavailable",
    }


@app.post(
    f"{settings.api_prefix}/workshops",
    response_model=WorkshopRegistrationResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_workshop(payload: WorkshopRegistrationCreate) -> WorkshopRegistrationResponse:
    created = create_workshop_registration(
        {
            **payload.model_dump(),
            "approval_status": "pendiente",
            "password_hash": None,
        }
    )
    return WorkshopRegistrationResponse.model_validate(created)


@app.post(
    f"{settings.api_prefix}/vehiculos",
    response_model=VehicleResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_vehicle(
    client_id: int = Form(ge=1),
    brand: str = Form(min_length=1, max_length=120),
    model: str = Form(min_length=1, max_length=120),
    year: int = Form(ge=1900, le=2100),
    plate: str = Form(min_length=3, max_length=40),
    color: str = Form(min_length=2, max_length=80),
    is_primary: bool = Form(default=False),
    photo: UploadFile | None = File(default=None),
) -> VehicleResponse:
    ensure_client_exists(client_id)
    photo_path, photo_url = save_vehicle_photo(photo)
    vehicle_payload = {
        "client_id": client_id,
        "brand": brand.strip(),
        "model": model.strip(),
        "year": year,
        "plate": normalize_plate(plate),
        "color": color.strip(),
        "is_primary": is_primary,
        "photo_path": photo_path,
        "photo_url": photo_url,
    }

    try:
        created = create_vehicle(vehicle_payload)
    except OperationalError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Base de datos no disponible",
        ) from exc
    except IntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un vehiculo con esa placa",
        ) from exc

    return VehicleResponse.model_validate(created)


@app.get(
    f"{settings.api_prefix}/vehiculos",
    response_model=list[VehicleResponse],
)
def get_vehicles(client_id: int = Query(ge=1)) -> list[VehicleResponse]:
    ensure_client_exists(client_id)
    try:
        rows = list_vehicles(client_id)
    except OperationalError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Base de datos no disponible",
        ) from exc

    return [VehicleResponse.model_validate(row) for row in rows]


@app.put(
    f"{settings.api_prefix}/vehiculos/{{vehicle_id}}",
    response_model=VehicleResponse,
)
def edit_vehicle(
    vehicle_id: int,
    client_id: int = Form(ge=1),
    brand: str = Form(min_length=1, max_length=120),
    model: str = Form(min_length=1, max_length=120),
    year: int = Form(ge=1900, le=2100),
    plate: str = Form(min_length=3, max_length=40),
    color: str = Form(min_length=2, max_length=80),
    is_primary: bool = Form(default=False),
    photo: UploadFile | None = File(default=None),
) -> VehicleResponse:
    ensure_client_exists(client_id)
    try:
        current_vehicle = get_vehicle_by_id(vehicle_id, client_id)
    except OperationalError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Base de datos no disponible",
        ) from exc

    if not current_vehicle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehiculo no encontrado")

    new_photo_path, new_photo_url = save_vehicle_photo(photo)
    photo_path = new_photo_path if new_photo_path is not None else current_vehicle.get("photo_path")
    photo_url = new_photo_url if new_photo_url is not None else current_vehicle.get("photo_url")

    vehicle_payload = {
        "client_id": client_id,
        "brand": brand.strip(),
        "model": model.strip(),
        "year": year,
        "plate": normalize_plate(plate),
        "color": color.strip(),
        "is_primary": is_primary,
        "photo_path": photo_path,
        "photo_url": photo_url,
    }

    try:
        updated = update_vehicle(vehicle_id, vehicle_payload)
    except OperationalError as exc:
        if new_photo_path is not None:
            remove_vehicle_photo(new_photo_path)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Base de datos no disponible",
        ) from exc
    except IntegrityError as exc:
        if new_photo_path is not None:
            remove_vehicle_photo(new_photo_path)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un vehiculo con esa placa",
        ) from exc

    if not updated:
        if new_photo_path is not None:
            remove_vehicle_photo(new_photo_path)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehiculo no encontrado")

    if new_photo_path is not None:
        remove_vehicle_photo(str(current_vehicle.get("photo_path")) if current_vehicle.get("photo_path") else None)

    return VehicleResponse.model_validate(updated)


@app.delete(
    f"{settings.api_prefix}/vehiculos/{{vehicle_id}}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_vehicle(vehicle_id: int, client_id: int = Query(ge=1)) -> None:
    ensure_client_exists(client_id)
    try:
        deleted = delete_vehicle(vehicle_id, client_id)
    except OperationalError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Base de datos no disponible",
        ) from exc

    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehiculo no encontrado")

    remove_vehicle_photo(str(deleted.get("photo_path")) if deleted.get("photo_path") else None)


@app.get(
    f"{settings.api_prefix}/workshops",
    response_model=list[WorkshopRegistrationResponse],
)
def get_workshops() -> list[WorkshopRegistrationResponse]:
    rows = list_workshop_registrations()
    return [WorkshopRegistrationResponse.model_validate(row) for row in rows]


@app.put(
    f"{settings.api_prefix}/workshops/{{workshop_id}}",
    response_model=WorkshopRegistrationResponse,
)
def edit_workshop(workshop_id: int, payload: WorkshopRegistrationCreate) -> WorkshopRegistrationResponse:
    updated = update_workshop_registration(
        workshop_id,
        {
            **payload.model_dump(),
            "approval_status": None,
            "password_hash": None,
        },
    )

    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Taller no encontrado")

    return WorkshopRegistrationResponse.model_validate(updated)


@app.put(
    f"{settings.api_prefix}/workshops/{{workshop_id}}/approval-status",
    response_model=WorkshopRegistrationResponse,
)
def edit_workshop_approval_status(
    workshop_id: int,
    payload: WorkshopApprovalStatusUpdate,
) -> WorkshopRegistrationResponse:
    current_workshop = get_workshop_by_id(workshop_id)

    if not current_workshop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Taller no encontrado")

    current_status = str(current_workshop["approval_status"])
    next_status = payload.approval_status

    if current_status == "activo" and next_status == "pendiente":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Un taller activo ya no puede volver a pendiente; solo puede pasar a rechazado",
        )

    password_hash = hash_password(settings.workshop_initial_password) if next_status == "activo" else None
    updated = update_workshop_approval_status_with_password(
        workshop_id,
        next_status,
        password_hash,
    )

    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Taller no encontrado")

    return WorkshopRegistrationResponse.model_validate(updated)


@app.delete(
    f"{settings.api_prefix}/workshops/{{workshop_id}}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_workshop(workshop_id: int) -> None:
    deleted = delete_workshop_registration(workshop_id)

    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Taller no encontrado")


@app.post(
    f"{settings.api_prefix}/clientes",
    response_model=ClientRegistrationResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_client(payload: ClientRegistrationCreate) -> ClientRegistrationResponse:
    normalized_email = payload.email.lower().strip()

    if is_protected_admin_email(normalized_email):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ese correo está reservado para el administrador del sistema",
        )

    if is_protected_admin_role(payload.role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No se permite registrar clientes con rol administrador",
        )

    client_payload = {
        "identity_card": payload.identity_card,
        "full_name": payload.full_name,
        "email": normalized_email,
        "phone": payload.phone,
        "password_hash": hash_password(payload.password),
        "role": payload.role,
        "status": "active",
        "accepted_terms": payload.accepted_terms,
    }

    try:
        created = create_client(client_payload)
    except IntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un cliente con ese carnet o correo",
        ) from exc

    return ClientRegistrationResponse.model_validate(created)


@app.get(
    f"{settings.api_prefix}/clientes",
    response_model=list[ClientRegistrationResponse],
)
def get_clients() -> list[ClientRegistrationResponse]:
    rows = list_clients()
    return [ClientRegistrationResponse.model_validate(row) for row in rows]


@app.put(
    f"{settings.api_prefix}/clientes/{{client_id}}/status",
    response_model=ClientRegistrationResponse,
)
def edit_client_status(client_id: int, payload: ClientStatusUpdate) -> ClientRegistrationResponse:
    updated = update_client_status(client_id, payload.status)

    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente no encontrado")

    return ClientRegistrationResponse.model_validate(updated)


@app.put(
    f"{settings.api_prefix}/clientes/{{client_id}}",
    response_model=ClientRegistrationResponse,
)
def edit_client(client_id: int, payload: ClientUpdate) -> ClientRegistrationResponse:
    normalized_email = payload.email.lower().strip()

    if is_protected_admin_email(normalized_email):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ese correo está reservado para el administrador del sistema",
        )

    if is_protected_admin_role(payload.role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No se permite asignar el rol administrador desde este módulo",
        )

    client_payload = {
        "identity_card": payload.identity_card,
        "full_name": payload.full_name,
        "email": normalized_email,
        "phone": payload.phone,
        "password_hash": hash_password(payload.password) if payload.password else None,
        "role": payload.role,
        "status": payload.status,
        "accepted_terms": payload.accepted_terms,
    }

    try:
        updated = update_client(client_id, client_payload)
    except IntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un cliente con ese carnet o correo",
        ) from exc

    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente no encontrado")

    return ClientRegistrationResponse.model_validate(updated)


@app.delete(
    f"{settings.api_prefix}/clientes/{{client_id}}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_client(client_id: int) -> None:
    deleted = delete_client(client_id)

    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente no encontrado")


@app.post(
    f"{settings.api_prefix}/auth/login",
    response_model=LoginResponse,
)
def login(payload: LoginRequest) -> LoginResponse:
    normalized_email = payload.email.lower().strip()

    if is_protected_admin_email(normalized_email):
        if payload.password != settings.protected_admin_password:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Correo o contraseña incorrectos",
            )

        return LoginResponse(
            id=PROTECTED_ADMIN_ID,
            email=PROTECTED_ADMIN_EMAIL,
            full_name=settings.protected_admin_full_name,
            phone=settings.protected_admin_phone,
            role=PROTECTED_ADMIN_ROLE,
            status="active",
            access_token=secrets.token_urlsafe(32),
            token_type="bearer",
        )

    workshop = get_workshop_by_email(normalized_email)

    if workshop:
        if workshop["approval_status"] != "activo":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="El taller todavía no fue habilitado por el administrador",
            )

        password_hash = workshop.get("password_hash")
        if not isinstance(password_hash, str) or not verify_password(payload.password, password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Correo o contraseña incorrectos",
            )

        if verify_password(settings.workshop_initial_password, password_hash):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "WORKSHOP_PASSWORD_CHANGE_REQUIRED",
                    "message": "Debes cambiar la contraseña temporal antes de acceder al dashboard",
                    "email": normalized_email,
                },
            )

        return LoginResponse(
            id=int(workshop["id"]),
            email=str(workshop["email"]),
            full_name=str(workshop["workshop_name"]),
            phone=str(workshop["phone"]),
            role=WORKSHOP_ROLE,
            status=str(workshop["approval_status"]),
            access_token=secrets.token_urlsafe(32),
            token_type="bearer",
        )

    client = get_client_by_email(normalized_email)

    if not client or not verify_password(payload.password, str(client["password_hash"])):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contraseña incorrectos",
        )

    if client["status"] != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cuenta suspendida",
        )

    return LoginResponse(
        id=int(client["id"]),
        email=str(client["email"]),
        full_name=str(client["full_name"]),
        phone=str(client["phone"]),
        role=str(client["role"]),
        status=str(client["status"]),
        access_token=secrets.token_urlsafe(32),
        token_type="bearer",
    )


@app.post(f"{settings.api_prefix}/workshops/change-password")
def change_workshop_password(payload: WorkshopPasswordChangeRequest) -> dict[str, str]:
    normalized_email = payload.email.lower().strip()
    workshop = get_workshop_by_email(normalized_email)

    if not workshop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Taller no encontrado")

    if workshop["approval_status"] != "activo":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El taller todavía no fue habilitado por el administrador",
        )

    password_hash = workshop.get("password_hash")
    if not isinstance(password_hash, str) or not verify_password(settings.workshop_initial_password, password_hash):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este taller ya no usa la contraseña temporal inicial",
        )

    updated = update_workshop_password(int(workshop["id"]), hash_password(payload.new_password))

    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Taller no encontrado")

    return {"message": "La contraseña del taller fue actualizada correctamente"}


@app.post(
    f"{settings.api_prefix}/technicians",
    response_model=TechnicianResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_technician(
    payload: TechnicianCreate,
    workshop_id: int | None = Query(default=None, ge=1),
) -> TechnicianResponse:
    target_workshop_id = workshop_id or payload.workshop_id
    technician_payload = {
        **payload.model_dump(),
        "workshop_id": target_workshop_id,
    }
    created = create_technician(technician_payload)
    return TechnicianResponse.model_validate(created)


@app.get(
    f"{settings.api_prefix}/technicians",
    response_model=list[TechnicianResponse],
)
def get_technicians(workshop_id: int | None = Query(default=None, ge=1)) -> list[TechnicianResponse]:
    rows = list_technicians_by_workshop(workshop_id) if workshop_id else list_technicians()
    return [TechnicianResponse.model_validate(row) for row in rows]


@app.put(
    f"{settings.api_prefix}/technicians/{{technician_id}}",
    response_model=TechnicianResponse,
)
def edit_technician(
    technician_id: int,
    payload: TechnicianCreate,
    workshop_id: int | None = Query(default=None, ge=1),
) -> TechnicianResponse:
    technician_payload = payload.model_dump()
    technician_payload["workshop_id"] = workshop_id or payload.workshop_id
    updated = (
        update_technician_for_workshop(technician_id, workshop_id, technician_payload)
        if workshop_id
        else update_technician(technician_id, technician_payload)
    )

    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tecnico no encontrado")

    return TechnicianResponse.model_validate(updated)


@app.delete(
    f"{settings.api_prefix}/technicians/{{technician_id}}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_technician(technician_id: int, workshop_id: int | None = Query(default=None, ge=1)) -> None:
    deleted = (
        delete_technician_for_workshop(technician_id, workshop_id)
        if workshop_id
        else delete_technician(technician_id)
    )

    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tecnico no encontrado")
