from datetime import datetime
import hashlib
import secrets

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import AliasChoices, BaseModel, ConfigDict, EmailStr, Field, model_validator
from sqlalchemy.exc import IntegrityError

from app.config import settings
from app.db import (
    check_database_connection,
    create_client,
    create_technician,
    create_workshop_registration,
    delete_client,
    delete_workshop_registration,
    delete_technician,
    get_client_by_email,
    init_database,
    list_clients,
    list_technicians,
    list_workshop_registrations,
    update_client,
    update_client_status,
    update_workshop_registration,
    update_technician,
)


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
    latitude: float | None = None
    longitude: float | None = None
    timezone: str | None = None
    utc_offset_minutes: int | None = None
    created_at: datetime


class TechnicianBase(BaseModel):
    full_name: str = Field(min_length=3, max_length=160)
    phone: str = Field(min_length=7, max_length=40)
    email: EmailStr
    specialty: str = Field(min_length=2, max_length=120)
    status: str = Field(pattern="^(disponible|ocupado|fuera_de_servicio)$")


class TechnicianCreate(TechnicianBase):
    pass


class TechnicianResponse(TechnicianBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
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


class ClientStatusUpdate(BaseModel):
    status: str = Field(pattern="^(active|suspended)$")


class ClientUpdate(BaseModel):
    identity_card: str = Field(min_length=5, max_length=40)
    full_name: str = Field(min_length=3, max_length=160)
    email: EmailStr
    phone: str = Field(min_length=7, max_length=40)
    role: str = Field(min_length=2, max_length=40)
    status: str = Field(pattern="^(active|suspended)$")
    accepted_terms: bool = True


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


app = FastAPI(
    title=settings.app_name,
    debug=settings.app_debug,
    version="0.1.0",
)

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
    init_database()


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
    created = create_workshop_registration(payload.model_dump())
    return WorkshopRegistrationResponse.model_validate(created)


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
    updated = update_workshop_registration(workshop_id, payload.model_dump())

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
    client_payload = {
        "identity_card": payload.identity_card,
        "full_name": payload.full_name,
        "email": payload.email,
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
    try:
        updated = update_client(client_id, payload.model_dump())
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
    client = get_client_by_email(payload.email)

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
    f"{settings.api_prefix}/technicians",
    response_model=TechnicianResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_technician(payload: TechnicianCreate) -> TechnicianResponse:
    created = create_technician(payload.model_dump())
    return TechnicianResponse.model_validate(created)


@app.get(
    f"{settings.api_prefix}/technicians",
    response_model=list[TechnicianResponse],
)
def get_technicians() -> list[TechnicianResponse]:
    rows = list_technicians()
    return [TechnicianResponse.model_validate(row) for row in rows]


@app.put(
    f"{settings.api_prefix}/technicians/{{technician_id}}",
    response_model=TechnicianResponse,
)
def edit_technician(technician_id: int, payload: TechnicianCreate) -> TechnicianResponse:
    updated = update_technician(technician_id, payload.model_dump())

    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tecnico no encontrado")

    return TechnicianResponse.model_validate(updated)


@app.delete(
    f"{settings.api_prefix}/technicians/{{technician_id}}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_technician(technician_id: int) -> None:
    deleted = delete_technician(technician_id)

    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tecnico no encontrado")
