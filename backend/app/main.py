from datetime import datetime

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.config import settings
from app.db import (
    check_database_connection,
    create_technician,
    create_workshop_registration,
    delete_workshop_registration,
    delete_technician,
    init_database,
    list_technicians,
    list_workshop_registrations,
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
