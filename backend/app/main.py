from datetime import datetime
import hashlib
import json
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
    create_emergency_report,
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
    update_client_password,
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
EMERGENCY_UPLOADS_DIR = UPLOADS_ROOT / "emergencias"
EMERGENCY_PHOTOS_DIR = EMERGENCY_UPLOADS_DIR / "photos"
EMERGENCY_AUDIO_DIR = EMERGENCY_UPLOADS_DIR / "audio"
UPLOADS_ROOT.mkdir(parents=True, exist_ok=True)
VEHICLE_UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
EMERGENCY_PHOTOS_DIR.mkdir(parents=True, exist_ok=True)
EMERGENCY_AUDIO_DIR.mkdir(parents=True, exist_ok=True)
logger = logging.getLogger(__name__)
PROTECTED_ADMIN_EMAIL = settings.protected_admin_email.lower().strip()
PROTECTED_ADMIN_ROLE = "admin"
PROTECTED_ADMIN_ID = 0
WORKSHOP_ROLE = "workshop"

# Limites y formatos aceptados para el flujo de emergencias.
MAX_EMERGENCY_PHOTOS = 6
MAX_EMERGENCY_PHOTO_BYTES = 20 * 1024 * 1024
MAX_EMERGENCY_AUDIO_BYTES = 40 * 1024 * 1024
ALLOWED_PHOTO_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_AUDIO_SUFFIXES = {".aac", ".m4a", ".mp3", ".wav", ".ogg", ".webm"}


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


class WorkshopRegistrationUpdate(WorkshopRegistrationCreate):
    password: str | None = Field(default=None, min_length=6, max_length=255)


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


class AccountTypeLookupRequest(BaseModel):
    email: EmailStr


class AccountTypeLookupResponse(BaseModel):
    exists: bool
    role: str | None = None


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


class ClientPasswordChangeRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    email: EmailStr
    current_password: str = Field(
        min_length=1,
        max_length=255,
        validation_alias=AliasChoices("current_password", "currentPassword"),
    )
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
    def validate_passwords(self) -> "ClientPasswordChangeRequest":
        if self.new_password != self.confirm_password:
            raise ValueError("Las contraseñas no coinciden")

        if self.current_password == self.new_password:
            raise ValueError("La nueva contraseña debe ser distinta a la actual")

        return self


class ClientForgotPasswordRequest(BaseModel):
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
    def validate_passwords(self) -> "ClientForgotPasswordRequest":
        if self.new_password != self.confirm_password:
            raise ValueError("Las contraseñas no coinciden")

        return self


class WorkshopForgotPasswordRequest(BaseModel):
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
    def validate_passwords(self) -> "WorkshopForgotPasswordRequest":
        if self.new_password != self.confirm_password:
            raise ValueError("Las contraseñas no coinciden")

        return self


class UnifiedForgotPasswordRequest(BaseModel):
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
    def validate_passwords(self) -> "UnifiedForgotPasswordRequest":
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


class EmergencyReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    client_id: int | None = None
    vehicle_name: str
    vehicle_plate: str
    problem_type: str
    description: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    address: str | None = None
    zone: str | None = None
    audio_duration_seconds: float | None = None
    photo_paths: list[str] = Field(default_factory=list)
    photo_urls: list[str] = Field(default_factory=list)
    audio_path: str | None = None
    audio_url: str | None = None
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


def normalize_optional_text(value: str | None) -> str | None:
    if value is None:
        return None

    normalized = value.strip()
    return normalized or None


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


def build_public_upload_url(relative_path: str) -> str:
    return f"/uploads/{relative_path}"


def remove_file_if_exists(path: Path) -> None:
    if path.is_file():
        path.unlink()


def save_upload_with_limit(
    upload: UploadFile,
    *,
    destination_dir: Path,
    relative_dir: str,
    allowed_suffixes: set[str],
    max_bytes: int | None,
    invalid_type_detail: str,
    too_large_detail: str | None = None,
) -> tuple[str, str]:
    suffix = Path(upload.filename or "").suffix.lower()

    if suffix not in allowed_suffixes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=invalid_type_detail)

    filename = f"{uuid4().hex}{suffix}"
    relative_path = f"{relative_dir}/{filename}"
    absolute_path = destination_dir / filename
    bytes_written = 0

    with absolute_path.open("wb") as buffer:
        while chunk := upload.file.read(1024 * 1024):
            bytes_written += len(chunk)
            if max_bytes is not None and bytes_written > max_bytes:
                buffer.close()
                remove_file_if_exists(absolute_path)
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=too_large_detail)
            buffer.write(chunk)

    return relative_path, build_public_upload_url(relative_path)


def cleanup_uploaded_files(*relative_paths: str | None) -> None:
    for relative_path in relative_paths:
        remove_uploaded_file(relative_path)


def save_vehicle_photo(photo: UploadFile | None) -> tuple[str | None, str | None]:
    if photo is None or not photo.filename:
        return None, None

    return save_upload_with_limit(
        photo,
        destination_dir=VEHICLE_UPLOADS_DIR,
        relative_dir="vehicles",
        allowed_suffixes=ALLOWED_PHOTO_SUFFIXES,
        max_bytes=None,
        invalid_type_detail="La foto debe ser JPG, JPEG, PNG o WEBP",
    )


def save_emergency_photo(photo: UploadFile) -> tuple[str, str]:
    return save_upload_with_limit(
        photo,
        destination_dir=EMERGENCY_PHOTOS_DIR,
        relative_dir="emergencias/photos",
        allowed_suffixes=ALLOWED_PHOTO_SUFFIXES,
        max_bytes=MAX_EMERGENCY_PHOTO_BYTES,
        invalid_type_detail="Cada foto debe ser JPG, JPEG, PNG o WEBP",
        too_large_detail="Cada foto puede pesar como maximo 20 MB",
    )


def save_emergency_audio(audio: UploadFile | None) -> tuple[str | None, str | None]:
    if audio is None or not audio.filename:
        return None, None

    return save_upload_with_limit(
        audio,
        destination_dir=EMERGENCY_AUDIO_DIR,
        relative_dir="emergencias/audio",
        allowed_suffixes=ALLOWED_AUDIO_SUFFIXES,
        max_bytes=MAX_EMERGENCY_AUDIO_BYTES,
        invalid_type_detail="El audio debe ser AAC, M4A, MP3, WAV, OGG o WEBM",
        too_large_detail="El audio puede pesar como maximo 40 MB",
    )


def remove_vehicle_photo(photo_path: str | None) -> None:
    if not photo_path:
        return

    candidate = (UPLOADS_ROOT / photo_path).resolve()

    try:
        candidate.relative_to(UPLOADS_ROOT.resolve())
    except ValueError:
        return

    remove_file_if_exists(candidate)


def remove_uploaded_file(relative_path: str | None) -> None:
    if not relative_path:
        return

    candidate = (UPLOADS_ROOT / relative_path).resolve()

    try:
        candidate.relative_to(UPLOADS_ROOT.resolve())
    except ValueError:
        return

    remove_file_if_exists(candidate)


def parse_json_string_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]

    if isinstance(value, str):
        try:
            decoded = json.loads(value)
        except json.JSONDecodeError:
            return []

        if isinstance(decoded, list):
            return [str(item) for item in decoded]

    return []


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


@app.post(
    f"{settings.api_prefix}/emergencias",
    response_model=EmergencyReportResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_emergency(
    client_id: int | None = Form(default=None, ge=1),
    vehicle_name: str = Form(min_length=1, max_length=160),
    vehicle_plate: str = Form(min_length=3, max_length=40),
    problem_type: str = Form(min_length=2, max_length=120),
    description: str | None = Form(default=None, min_length=3, max_length=4000),
    latitude: float | None = Form(default=None, ge=-90, le=90),
    longitude: float | None = Form(default=None, ge=-180, le=180),
    address: str | None = Form(default=None, max_length=255),
    zone: str | None = Form(default=None, max_length=120),
    audio_duration_seconds: float | None = Form(default=None, ge=0),
    photos: list[UploadFile] = File(default=[]),
    audio: UploadFile | None = File(default=None),
) -> EmergencyReportResponse:
    if client_id is not None:
        ensure_client_exists(client_id)

    # FastAPI entrega todos los campos `photos`; filtramos entradas vacias para
    # mantener el contrato flexible con clientes moviles.
    valid_photos = [photo for photo in photos if photo.filename]

    if len(valid_photos) > MAX_EMERGENCY_PHOTOS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Se permiten como maximo {MAX_EMERGENCY_PHOTOS} fotos por emergencia",
        )

    photo_paths: list[str] = []
    photo_urls: list[str] = []
    audio_path: str | None = None

    try:
        for photo in valid_photos:
            relative_path, public_url = save_emergency_photo(photo)
            photo_paths.append(relative_path)
            photo_urls.append(public_url)

        audio_path, audio_url = save_emergency_audio(audio)

        payload = {
            "client_id": client_id,
            "vehicle_name": vehicle_name.strip(),
            "vehicle_plate": normalize_plate(vehicle_plate),
            "problem_type": problem_type.strip(),
            "description": normalize_optional_text(description),
            "latitude": latitude,
            "longitude": longitude,
            "address": normalize_optional_text(address),
            "zone": normalize_optional_text(zone),
            "audio_duration_seconds": audio_duration_seconds,
            "photo_paths": json.dumps(photo_paths),
            "photo_urls": json.dumps(photo_urls),
            "audio_path": audio_path,
            "audio_url": audio_url,
        }

        created = create_emergency_report(payload)
    except HTTPException:
        cleanup_uploaded_files(*photo_paths, audio_path)
        raise
    except OperationalError as exc:
        cleanup_uploaded_files(*photo_paths, audio_path)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Base de datos no disponible",
        ) from exc

    created["photo_paths"] = parse_json_string_list(created.get("photo_paths"))
    created["photo_urls"] = parse_json_string_list(created.get("photo_urls"))
    return EmergencyReportResponse.model_validate(created)


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


@app.api_route(f"{settings.api_prefix}/workshops/forgot-password", methods=["POST", "PUT"])
def forgot_workshop_password(payload: WorkshopForgotPasswordRequest) -> dict[str, str]:
    normalized_email = payload.email.lower().strip()
    workshop = get_workshop_by_email(normalized_email)

    if not workshop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Taller no encontrado")

    if workshop["approval_status"] != "activo":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El taller todavía no fue habilitado por el administrador",
        )

    updated = update_workshop_password(int(workshop["id"]), hash_password(payload.new_password))

    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Taller no encontrado")

    return {"message": "La contraseña del taller fue restablecida correctamente"}


@app.put(
    f"{settings.api_prefix}/workshops/{{workshop_id}}",
    response_model=WorkshopRegistrationResponse,
)
def edit_workshop(workshop_id: int, payload: WorkshopRegistrationUpdate) -> WorkshopRegistrationResponse:
    updated = update_workshop_registration(
        workshop_id,
        {
            **payload.model_dump(exclude={"password"}),
            "approval_status": None,
            "password_hash": hash_password(payload.password) if payload.password else None,
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


@app.post(f"{settings.api_prefix}/clientes/change-password")
def change_client_password(payload: ClientPasswordChangeRequest) -> dict[str, str]:
    normalized_email = payload.email.lower().strip()
    client = get_client_by_email(normalized_email)

    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente no encontrado")

    if client["status"] != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cuenta suspendida",
        )

    password_hash = client.get("password_hash")
    if not isinstance(password_hash, str) or not verify_password(payload.current_password, password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="La contraseña actual es incorrecta",
        )

    updated = update_client_password(int(client["id"]), hash_password(payload.new_password))

    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente no encontrado")

    return {"message": "La contraseña del cliente fue actualizada correctamente"}


@app.api_route(f"{settings.api_prefix}/clientes/forgot-password", methods=["POST", "PUT"])
def forgot_client_password(payload: ClientForgotPasswordRequest) -> dict[str, str]:
    normalized_email = payload.email.lower().strip()
    client = get_client_by_email(normalized_email)

    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente no encontrado")

    if client["status"] != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cuenta suspendida",
        )

    updated = update_client_password(int(client["id"]), hash_password(payload.new_password))

    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente no encontrado")

    return {"message": "La contraseña del cliente fue restablecida correctamente"}


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


@app.post(
    f"{settings.api_prefix}/auth/account-type",
    response_model=AccountTypeLookupResponse,
)
def lookup_account_type(payload: AccountTypeLookupRequest) -> AccountTypeLookupResponse:
    normalized_email = payload.email.lower().strip()

    workshop = get_workshop_by_email(normalized_email)
    if workshop:
        return AccountTypeLookupResponse(exists=True, role=WORKSHOP_ROLE)

    client = get_client_by_email(normalized_email)
    if client:
        return AccountTypeLookupResponse(exists=True, role=str(client["role"]))

    return AccountTypeLookupResponse(exists=False, role=None)


@app.api_route(f"{settings.api_prefix}/auth/forgot-password", methods=["POST", "PUT"])
def forgot_password(payload: UnifiedForgotPasswordRequest) -> dict[str, str]:
    normalized_email = payload.email.lower().strip()

    client = get_client_by_email(normalized_email)
    if client:
        if client["status"] != "active":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cuenta suspendida",
            )

        updated = update_client_password(int(client["id"]), hash_password(payload.new_password))

        if not updated:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente no encontrado")

        return {"message": "La contraseña del cliente fue restablecida correctamente"}

    workshop = get_workshop_by_email(normalized_email)
    if workshop:
        if workshop["approval_status"] != "activo":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="El taller todavía no fue habilitado por el administrador",
            )

        updated = update_workshop_password(int(workshop["id"]), hash_password(payload.new_password))

        if not updated:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Taller no encontrado")

        return {"message": "La contraseña del taller fue restablecida correctamente"}

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No existe una cuenta con ese correo")


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
