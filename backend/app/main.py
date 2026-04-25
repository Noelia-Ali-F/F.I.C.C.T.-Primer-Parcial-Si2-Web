from collections.abc import Mapping
from datetime import datetime
import base64
import hashlib
import json
import logging
import mimetypes
import os
from pathlib import Path
import re
import secrets
import shutil
from threading import Lock
import unicodedata
from urllib.parse import urlparse
from uuid import uuid4

from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import AliasChoices, BaseModel, ConfigDict, EmailStr, Field, model_validator
from sqlalchemy.exc import IntegrityError, OperationalError

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

try:
    import whisper
except ImportError:
    whisper = None

try:
    import firebase_admin
    from firebase_admin import credentials, messaging
except ImportError:
    firebase_admin = None
    credentials = None
    messaging = None

from app.config import settings
from app.db import (
    assign_emergency_technician,
    check_database_connection,
    create_client,
    create_emergency_report,
    create_technician,
    create_vehicle,
    create_workshop_registration,
    delete_emergency_report,
    delete_client,
    delete_vehicle,
    delete_workshop_registration,
    delete_technician,
    delete_technician_for_workshop,
    get_client_by_email,
    get_client_by_id,
    get_technician_by_workshop,
    get_vehicle_by_id,
    get_workshop_by_id,
    get_workshop_by_email,
    init_database,
    list_active_device_fcm_tokens,
    list_emergency_reports,
    list_clients,
    list_technicians,
    list_technicians_by_workshop,
    list_vehicles,
    list_workshop_registrations,
    update_client,
    update_client_password,
    update_client_status,
    update_emergency_status,
    update_technician,
    update_technician_for_workshop,
    update_vehicle,
    update_workshop_approval_status_with_password,
    update_workshop_password,
    update_workshop_registration,
    upsert_device_fcm_token,
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
_firebase_app_initialized = False

# Limites y formatos aceptados para el flujo de emergencias.
MAX_EMERGENCY_PHOTOS = 6
MAX_EMERGENCY_PHOTO_BYTES = 20 * 1024 * 1024
MAX_EMERGENCY_AUDIO_BYTES = 40 * 1024 * 1024
ALLOWED_PHOTO_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_AUDIO_SUFFIXES = {".aac", ".m4a", ".mp3", ".wav", ".ogg", ".webm"}
ALLOWED_EMERGENCY_PROBLEM_TYPES = {
    "Batería",
    "Neumático",
    "Combustible",
    "Motor",
    "Sistema eléctrico",
    "Accidente",
    "Cerrajería / llaves",
    "Otro",
}
STANDARDIZED_EMERGENCY_PROBLEM_TYPES = ALLOWED_EMERGENCY_PROBLEM_TYPES - {"Otro"}
_whisper_model = None
_whisper_model_lock = Lock()


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
    role: str | None = None


class LoginResponse(BaseModel):
    id: int
    email: EmailStr
    full_name: str | None = None
    phone: str | None = None
    role: str
    status: str
    requires_password_change: bool = False
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
    emergency_status: str | None = None
    problem_type_standardized: str | None = None
    photo_problem_type_standardized: str | None = None
    photo_classification_confidence: float | None = None
    photo_classification_error: str | None = None
    description: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    address: str | None = None
    zone: str | None = None
    nearest_workshop_id: int | None = None
    nearest_workshop_name: str | None = None
    nearest_workshop_specialty: str | None = None
    nearest_workshop_zone: str | None = None
    nearest_workshop_distance_meters: float | None = None
    audio_duration_seconds: float | None = None
    audio_transcript: str | None = None
    audio_transcript_status: str | None = None
    audio_transcript_error: str | None = None
    photo_paths: list[str] = Field(default_factory=list)
    photo_urls: list[str] = Field(default_factory=list)
    audio_path: str | None = None
    audio_url: str | None = None
    created_at: datetime
    assignment_id: int | None = None
    assignment_status: str | None = None
    assigned_technician_id: int | None = None
    assigned_technician_name: str | None = None
    assigned_technician_phone: str | None = None
    assigned_technician_email: str | None = None
    assigned_technician_specialty: str | None = None


class EmergencyReportListResponse(EmergencyReportResponse):
    client_name: str | None = None


class EmergencyStatusUpdate(BaseModel):
    emergency_status: str = Field(pattern="^(activo|rechazado)$")


class EmergencyTechnicianAssignmentRequest(BaseModel):
    technician_id: int = Field(ge=1)


class DeviceFcmTokenCreate(BaseModel):
    user_id: int = Field(ge=1)
    fcm_token: str = Field(min_length=20, max_length=4096)
    platform: str = Field(default="android", pattern="^(android|ios|web)$")


class DeviceFcmTokenResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    fcm_token: str
    platform: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


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


def normalize_problem_type(problem_type: str) -> str:
    normalized = problem_type.strip()

    if normalized not in ALLOWED_EMERGENCY_PROBLEM_TYPES:
        allowed_values = ", ".join(sorted(ALLOWED_EMERGENCY_PROBLEM_TYPES))
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"problem_type invalido. Valores permitidos: {allowed_values}",
        )

    return normalized


def normalize_text_for_matching(value: str | None) -> str:
    if not value:
        return ""

    normalized = unicodedata.normalize("NFKD", value)
    without_accents = "".join(char for char in normalized if not unicodedata.combining(char))
    lowered = without_accents.lower()
    return re.sub(r"\s+", " ", lowered).strip()


def standardize_problem_type(
    problem_type: str,
    description: str | None,
    audio_transcript: str | None = None,
    photo_problem_type_standardized: str | None = None,
) -> str | None:
    if problem_type != "Otro":
        return problem_type if problem_type in STANDARDIZED_EMERGENCY_PROBLEM_TYPES else None

    candidate_text = " ".join(
        part for part in [normalize_optional_text(description), normalize_optional_text(audio_transcript)] if part
    )
    haystack = normalize_text_for_matching(candidate_text)

    if not haystack:
        return None

    rules: list[tuple[str, tuple[str, ...]]] = [
        ("Batería", ("bateria", "arranque", "no enciende", "sin corriente", "descargada", "pasar corriente")),
        ("Neumático", ("neumatico", "llanta", "pinch", "rueda", "revent", "desinflad")),
        ("Combustible", ("combustible", "gasolina", "diesel", "tanque", "sin gasolina", "sin diesel")),
        ("Motor", ("motor", "sobrecalent", "humo", "temperatura", "radiador", "recalent")),
        ("Sistema eléctrico", ("electrico", "eléctrico", "fusible", "cable", "corto", "tablero", "luces")),
        ("Accidente", ("accidente", "choque", "colision", "colisión", "impacto", "atropell")),
        ("Cerrajería / llaves", ("llave", "llaves", "cerrajer", "cerrajeria", "cerrado", "quedaron dentro")),
    ]

    best_match: str | None = None
    best_score = 0

    for category, keywords in rules:
        score = sum(1 for keyword in keywords if keyword in haystack)
        if score > best_score:
            best_match = category
            best_score = score

    if best_match is not None:
        return best_match

    if photo_problem_type_standardized in STANDARDIZED_EMERGENCY_PROBLEM_TYPES:
        return photo_problem_type_standardized

    return None


def extract_response_text(response: object) -> str:
    output_text = getattr(response, "output_text", None)
    if isinstance(output_text, str) and output_text.strip():
        return output_text

    output = getattr(response, "output", None)
    if isinstance(output, list):
        parts: list[str] = []
        for item in output:
            content = getattr(item, "content", None)
            if not isinstance(content, list):
                continue
            for part in content:
                text = getattr(part, "text", None)
                if isinstance(text, str) and text.strip():
                    parts.append(text)
        if parts:
            return "\n".join(parts)

    return ""


def build_data_url_for_image(relative_path: str) -> str:
    absolute_path = (UPLOADS_ROOT / relative_path).resolve()

    try:
        absolute_path.relative_to(UPLOADS_ROOT.resolve())
    except ValueError as exc:
        raise RuntimeError("Ruta de imagen invalida") from exc

    if not absolute_path.is_file():
        raise RuntimeError("No se encontro la imagen a clasificar")

    mime_type, _ = mimetypes.guess_type(absolute_path.name)
    mime_type = mime_type or "application/octet-stream"
    encoded = base64.b64encode(absolute_path.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def classify_emergency_photos(photo_relative_paths: list[str]) -> tuple[str | None, float | None, str | None]:
    if not photo_relative_paths or not settings.photo_classification_enabled:
        return None, None, None

    if OpenAI is None:
        return None, None, "La dependencia openai no esta instalada"

    if not os.getenv("OPENAI_API_KEY"):
        return None, None, "OPENAI_API_KEY no esta configurada"

    try:
        content: list[dict[str, object]] = [
            {
                "type": "input_text",
                "text": (
                    "Clasifica estas fotos de una emergencia vehicular en exactamente una categoria. "
                    "Categorias permitidas: Batería, Neumático, Combustible, Motor, Sistema eléctrico, "
                    "Accidente, Cerrajería / llaves. "
                    "Responde solo JSON con este formato exacto: "
                    '{"category":"<categoria>","confidence":0.0,"reason":"<breve>"}'
                ),
            }
        ]

        for photo_relative_path in photo_relative_paths:
            content.append(
                {
                    "type": "input_image",
                    "image_url": build_data_url_for_image(photo_relative_path),
                    "detail": "low",
                }
            )

        client = OpenAI()
        response = client.responses.create(
            model=settings.photo_classification_model,
            input=[{"role": "user", "content": content}],
        )
        parsed = json.loads(extract_response_text(response))

        category = parsed.get("category")
        confidence_raw = parsed.get("confidence")

        if category not in STANDARDIZED_EMERGENCY_PROBLEM_TYPES:
            return None, None, "La clasificacion visual devolvio una categoria invalida"

        confidence = None
        if isinstance(confidence_raw, (int, float)):
            confidence = max(0.0, min(float(confidence_raw), 1.0))

        return str(category), confidence, None
    except Exception as exc:
        logger.exception("No se pudo clasificar visualmente la emergencia")
        return None, None, str(exc)


def determine_standardized_problem_type(
    problem_type: str,
    description: str | None,
    audio_transcript: str | None = None,
    photo_problem_type_standardized: str | None = None,
) -> str | None:
    return standardize_problem_type(
        problem_type=problem_type,
        description=description,
        audio_transcript=audio_transcript,
        photo_problem_type_standardized=photo_problem_type_standardized,
    )


def get_whisper_model():
    global _whisper_model

    if _whisper_model is not None:
        return _whisper_model

    with _whisper_model_lock:
        if _whisper_model is None:
            if whisper is None:
                raise RuntimeError("La dependencia openai-whisper no esta instalada")

            _whisper_model = whisper.load_model(settings.whisper_model)

    return _whisper_model


def transcribe_emergency_audio(audio_relative_path: str | None) -> tuple[str | None, str | None, str | None]:
    if not audio_relative_path:
        return None, None, None

    if not settings.whisper_enabled:
        return None, "disabled", None

    if shutil.which("ffmpeg") is None:
        return None, "error", "ffmpeg no esta disponible en el contenedor"

    absolute_path = (UPLOADS_ROOT / audio_relative_path).resolve()

    try:
        absolute_path.relative_to(UPLOADS_ROOT.resolve())
    except ValueError:
        return None, "error", "Ruta de audio invalida"

    if not absolute_path.is_file():
        return None, "error", "No se encontro el archivo de audio"

    try:
        model = get_whisper_model()
        options: dict[str, object] = {"fp16": False}

        language = normalize_optional_text(settings.whisper_language)
        if language:
            options["language"] = language

        result = model.transcribe(str(absolute_path), **options)
        transcript = normalize_optional_text(str(result.get("text", "")))
        return transcript, "completed", None
    except Exception as exc:
        logger.exception("No se pudo transcribir el audio de la emergencia")
        return None, "error", str(exc)


def is_protected_admin_email(email: str) -> bool:
    return email.lower().strip() == PROTECTED_ADMIN_EMAIL


def is_protected_admin_role(role: str) -> bool:
    return role.lower().strip() == PROTECTED_ADMIN_ROLE


def workshop_login_status(approval_status: object) -> str:
    return "active" if str(approval_status) == "activo" else "pending"


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


def ensure_firebase_app() -> bool:
    global _firebase_app_initialized

    if _firebase_app_initialized:
        return True

    if not settings.fcm_enabled:
        return False

    if firebase_admin is None or credentials is None:
        logger.warning("FCM habilitado, pero firebase-admin no esta instalado")
        return False

    credentials_path = normalize_optional_text(settings.firebase_credentials_path)
    if not credentials_path:
        logger.warning("FCM habilitado, pero FIREBASE_CREDENTIALS_PATH no esta configurado")
        return False

    try:
        if not firebase_admin._apps:
            firebase_admin.initialize_app(credentials.Certificate(credentials_path))
        _firebase_app_initialized = True
        return True
    except Exception:
        logger.exception("No se pudo inicializar Firebase Admin SDK")
        return False


def send_push_to_client(client_id: int | None, title: str, body: str, data: dict[str, str]) -> None:
    if client_id is None:
        return

    try:
        devices = list_active_device_fcm_tokens(client_id)
    except OperationalError:
        logger.exception("No se pudieron consultar tokens FCM del cliente %s", client_id)
        return

    if not devices or not ensure_firebase_app() or messaging is None:
        return

    for device in devices:
        token = str(device.get("fcm_token", "")).strip()
        if not token:
            continue

        try:
            message = messaging.Message(
                notification=messaging.Notification(title=title, body=body),
                data=data,
                token=token,
            )
            messaging.send(message)
        except Exception:
            logger.exception("No se pudo enviar push FCM al cliente %s", client_id)


def compact_push_text(value: object, *, fallback: str, max_length: int = 120) -> str:
    text_value = normalize_optional_text(str(value)) if value is not None else None
    if not text_value:
        return fallback

    single_line = re.sub(r"\s+", " ", text_value)
    if len(single_line) <= max_length:
        return single_line

    return f"{single_line[: max_length - 3].rstrip()}..."


def emergency_incident_label(report: Mapping[str, object]) -> str:
    return compact_push_text(
        report.get("description")
        or report.get("problem_type_standardized")
        or report.get("problem_type")
        or report.get("vehicle_name"),
        fallback="Incidente reportado",
    )


def push_coordinate(value: object) -> str | None:
    if value is None:
        return None

    try:
        return str(float(value))
    except (TypeError, ValueError):
        return None


def add_coordinate_pair(
    data: dict[str, str],
    *,
    latitude_key: str,
    longitude_key: str,
    latitude: object,
    longitude: object,
) -> None:
    normalized_latitude = push_coordinate(latitude)
    normalized_longitude = push_coordinate(longitude)

    if normalized_latitude is None or normalized_longitude is None:
        return

    data[latitude_key] = normalized_latitude
    data[longitude_key] = normalized_longitude


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


def relative_upload_path_from_url(value: str | None) -> str | None:
    normalized = normalize_optional_text(value)

    if not normalized:
        return None

    parsed_path = urlparse(normalized).path if normalized.startswith(("http://", "https://")) else normalized
    parsed_path = parsed_path.lstrip("/")

    if parsed_path.startswith("uploads/"):
        parsed_path = parsed_path.removeprefix("uploads/")

    if not parsed_path:
        return None

    candidate = (UPLOADS_ROOT / parsed_path).resolve()

    try:
        candidate.relative_to(UPLOADS_ROOT.resolve())
    except ValueError:
        return None

    return parsed_path if candidate.is_file() else None


def existing_upload_urls_from_media_lists(photo_paths: object, photo_urls: object) -> tuple[list[str], list[str]]:
    existing_paths: list[str] = []

    for raw_value in [*parse_json_string_list(photo_paths), *parse_json_string_list(photo_urls)]:
        relative_path = relative_upload_path_from_url(raw_value)

        if relative_path and relative_path not in existing_paths:
            existing_paths.append(relative_path)

    return existing_paths, [build_public_upload_url(relative_path) for relative_path in existing_paths]


def normalize_emergency_media_fields(row: dict[str, object]) -> dict[str, object]:
    existing_photo_paths, existing_photo_urls = existing_upload_urls_from_media_lists(
        row.get("photo_paths"),
        row.get("photo_urls"),
    )
    row["photo_paths"] = existing_photo_paths
    row["photo_urls"] = existing_photo_urls

    audio_path = relative_upload_path_from_url(str(row.get("audio_path"))) if row.get("audio_path") else None
    audio_url_path = relative_upload_path_from_url(str(row.get("audio_url"))) if row.get("audio_url") else None
    existing_audio_path = audio_path or audio_url_path
    row["audio_path"] = existing_audio_path
    row["audio_url"] = build_public_upload_url(existing_audio_path) if existing_audio_path else None

    return row


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
    f"{settings.api_prefix}/devices/fcm-token",
    response_model=DeviceFcmTokenResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_device_fcm_token(payload: DeviceFcmTokenCreate) -> DeviceFcmTokenResponse:
    ensure_client_exists(payload.user_id)

    try:
        device = upsert_device_fcm_token(
            {
                "user_id": payload.user_id,
                "fcm_token": payload.fcm_token.strip(),
                "platform": payload.platform,
            }
        )
    except OperationalError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Base de datos no disponible",
        ) from exc

    return DeviceFcmTokenResponse.model_validate(device)


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
    nearest_workshop_id: int | None = Form(default=None, ge=1),
    nearest_workshop_name: str | None = Form(default=None, max_length=160),
    nearest_workshop_specialty: str | None = Form(default=None, max_length=120),
    nearest_workshop_zone: str | None = Form(default=None, max_length=120),
    nearest_workshop_distance_meters: float | None = Form(default=None, ge=0),
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
    audio_transcript: str | None = None
    audio_transcript_status: str | None = None
    audio_transcript_error: str | None = None
    photo_problem_type_standardized: str | None = None
    photo_classification_confidence: float | None = None
    photo_classification_error: str | None = None

    try:
        for photo in valid_photos:
            relative_path, public_url = save_emergency_photo(photo)
            photo_paths.append(relative_path)
            photo_urls.append(public_url)

        audio_path, audio_url = save_emergency_audio(audio)
        audio_transcript, audio_transcript_status, audio_transcript_error = transcribe_emergency_audio(audio_path)
        (
            photo_problem_type_standardized,
            photo_classification_confidence,
            photo_classification_error,
        ) = classify_emergency_photos(photo_paths)
        normalized_problem_type = normalize_problem_type(problem_type)
        standardized_problem_type = determine_standardized_problem_type(
            problem_type=normalized_problem_type,
            description=description,
            audio_transcript=audio_transcript,
            photo_problem_type_standardized=photo_problem_type_standardized,
        )

        payload = {
            "client_id": client_id,
            "vehicle_name": vehicle_name.strip(),
            "vehicle_plate": normalize_plate(vehicle_plate),
            "problem_type": normalized_problem_type,
            "emergency_status": "pendiente",
            "problem_type_standardized": standardized_problem_type,
            "photo_problem_type_standardized": photo_problem_type_standardized,
            "photo_classification_confidence": photo_classification_confidence,
            "photo_classification_error": normalize_optional_text(photo_classification_error),
            "description": normalize_optional_text(description),
            "latitude": latitude,
            "longitude": longitude,
            "address": normalize_optional_text(address),
            "zone": normalize_optional_text(zone),
            "nearest_workshop_id": nearest_workshop_id,
            "nearest_workshop_name": normalize_optional_text(nearest_workshop_name),
            "nearest_workshop_specialty": normalize_optional_text(nearest_workshop_specialty),
            "nearest_workshop_zone": normalize_optional_text(nearest_workshop_zone),
            "nearest_workshop_distance_meters": nearest_workshop_distance_meters,
            "audio_duration_seconds": audio_duration_seconds,
            "audio_transcript": audio_transcript,
            "audio_transcript_status": audio_transcript_status,
            "audio_transcript_error": normalize_optional_text(audio_transcript_error),
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

    normalize_emergency_media_fields(created)
    return EmergencyReportResponse.model_validate(created)


@app.get(
    f"{settings.api_prefix}/emergencias",
    response_model=list[EmergencyReportListResponse],
)
def get_emergency_reports(
    nearest_workshop_id: int | None = Query(default=None, ge=1),
    emergency_status: str | None = Query(default=None, pattern="^(pendiente|activo|rechazado)$"),
) -> list[EmergencyReportListResponse]:
    try:
        rows = list_emergency_reports(
            nearest_workshop_id=nearest_workshop_id,
            emergency_status=emergency_status,
        )
    except OperationalError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Base de datos no disponible",
        ) from exc

    for row in rows:
        normalize_emergency_media_fields(row)

    return [EmergencyReportListResponse.model_validate(row) for row in rows]


@app.put(
    f"{settings.api_prefix}/emergencias/{{report_id}}/status",
    response_model=EmergencyReportResponse,
)
def edit_emergency_status(
    report_id: int,
    payload: EmergencyStatusUpdate,
    workshop_id: int | None = Query(default=None, ge=1),
) -> EmergencyReportResponse:
    if payload.emergency_status == "activo" and workshop_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo un taller puede cambiar una emergencia a activo",
        )

    try:
        updated = update_emergency_status(
            report_id,
            payload.emergency_status,
            nearest_workshop_id=workshop_id,
        )
    except OperationalError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Base de datos no disponible",
        ) from exc

    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Emergencia no encontrada o no pertenece al taller indicado",
        )

    normalize_emergency_media_fields(updated)

    if payload.emergency_status == "activo":
        workshop_name = compact_push_text(
            updated.get("nearest_workshop_name"),
            fallback="El taller",
            max_length=80,
        )
        incident_label = emergency_incident_label(updated)
        send_push_to_client(
            int(updated["client_id"]) if updated.get("client_id") is not None else None,
            "Emergencia aceptada",
            f"{workshop_name} acepto tu emergencia: {incident_label}",
            {
                "type": "emergency_accepted",
                "emergency_id": str(report_id),
                "workshop_id": str(workshop_id or updated.get("nearest_workshop_id") or ""),
                "workshop_name": workshop_name,
                "incident_description": incident_label,
            },
        )

    return EmergencyReportResponse.model_validate(updated)


@app.put(
    f"{settings.api_prefix}/emergencias/{{report_id}}/technician-assignment",
    response_model=EmergencyReportListResponse,
)
def assign_technician_to_emergency(
    report_id: int,
    payload: EmergencyTechnicianAssignmentRequest,
    workshop_id: int = Query(ge=1),
) -> EmergencyReportListResponse:
    try:
        technician = get_technician_by_workshop(payload.technician_id, workshop_id)
        workshop_reports = list_emergency_reports(nearest_workshop_id=workshop_id)
    except OperationalError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Base de datos no disponible",
        ) from exc

    if not technician:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tecnico no encontrado para este taller",
        )

    report = next((item for item in workshop_reports if int(item["id"]) == report_id), None)

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Emergencia no encontrada o no pertenece a este taller",
        )

    if report.get("emergency_status") != "activo":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Primero debes aceptar la emergencia para asignar un tecnico",
        )

    current_assigned_technician_id = report.get("assigned_technician_id")
    technician_status = str(technician.get("status"))
    if technician_status != "disponible" and current_assigned_technician_id != payload.technician_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El tecnico seleccionado no esta disponible",
        )

    try:
        assign_emergency_technician(report_id, workshop_id, payload.technician_id)
        refreshed_reports = list_emergency_reports(nearest_workshop_id=workshop_id)
    except OperationalError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Base de datos no disponible",
        ) from exc

    updated_report = next((item for item in refreshed_reports if int(item["id"]) == report_id), None)

    if not updated_report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Emergencia no encontrada")

    normalize_emergency_media_fields(updated_report)
    workshop_name = compact_push_text(
        updated_report.get("nearest_workshop_name"),
        fallback="El taller",
        max_length=80,
    )
    technician_name = compact_push_text(
        updated_report.get("assigned_technician_name") or technician.get("full_name"),
        fallback="Tecnico asignado",
        max_length=80,
    )
    incident_label = emergency_incident_label(updated_report)
    try:
        workshop = get_workshop_by_id(workshop_id)
    except OperationalError:
        logger.exception("No se pudo consultar coordenadas del taller %s para push", workshop_id)
        workshop = None
    push_data = {
        "type": "technician_assigned",
        "emergency_id": str(report_id),
        "workshop_id": str(workshop_id),
        "technician_id": str(payload.technician_id),
        "workshop_name": workshop_name,
        "technician_name": technician_name,
        "incident_description": incident_label,
    }
    add_coordinate_pair(
        push_data,
        latitude_key="technician_latitude",
        longitude_key="technician_longitude",
        latitude=workshop.get("latitude") if workshop else None,
        longitude=workshop.get("longitude") if workshop else None,
    )
    send_push_to_client(
        int(updated_report["client_id"]) if updated_report.get("client_id") is not None else None,
        "Tecnico asignado",
        f"{technician_name} de {workshop_name} atendera: {incident_label}",
        push_data,
    )
    return EmergencyReportListResponse.model_validate(updated_report)


@app.delete(
    f"{settings.api_prefix}/emergencias/{{report_id}}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_emergency_report(
    report_id: int,
    workshop_id: int | None = Query(default=None, ge=1),
) -> None:
    try:
        deleted = delete_emergency_report(
            report_id,
            nearest_workshop_id=workshop_id,
        )
    except OperationalError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Base de datos no disponible",
        ) from exc

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Emergencia no encontrada o no pertenece al taller indicado",
        )


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

    password_hash = workshop.get("password_hash")
    uses_initial_password = (
        isinstance(password_hash, str) and verify_password(settings.workshop_initial_password, password_hash)
    )
    accepts_missing_initial_password = not isinstance(password_hash, str) and (
        workshop["approval_status"] != "activo"
    )

    if not uses_initial_password and not accepts_missing_initial_password:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este taller ya no usa la contraseña temporal inicial",
        )

    updated = update_workshop_approval_status_with_password(
        int(workshop["id"]),
        "activo",
        hash_password(payload.new_password),
    )

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
    response_model_exclude_none=True,
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
            requires_password_change=False,
            access_token=secrets.token_urlsafe(32),
            token_type="Bearer",
        )

    workshop = get_workshop_by_email(normalized_email)

    if workshop:
        password_hash = workshop.get("password_hash")
        uses_initial_password = (
            isinstance(password_hash, str) and verify_password(settings.workshop_initial_password, password_hash)
        )
        accepts_missing_initial_password = (
            not isinstance(password_hash, str)
            and workshop["approval_status"] != "activo"
            and payload.password == settings.workshop_initial_password
        )

        if not accepts_missing_initial_password and (
            not isinstance(password_hash, str) or not verify_password(payload.password, password_hash)
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Correo o contraseña incorrectos",
            )

        if uses_initial_password or accepts_missing_initial_password:
            return LoginResponse(
                id=int(workshop["id"]),
                email=str(workshop["email"]),
                role=WORKSHOP_ROLE,
                status=workshop_login_status(workshop["approval_status"]),
                requires_password_change=True,
            )

        if workshop["approval_status"] != "activo":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="El taller todavía no fue habilitado por el administrador",
            )

        return LoginResponse(
            id=int(workshop["id"]),
            email=str(workshop["email"]),
            full_name=str(workshop["workshop_name"]),
            phone=str(workshop["phone"]),
            role=WORKSHOP_ROLE,
            status=workshop_login_status(workshop["approval_status"]),
            requires_password_change=False,
            access_token=secrets.token_urlsafe(32),
            token_type="Bearer",
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
        requires_password_change=False,
        access_token=secrets.token_urlsafe(32),
        token_type="Bearer",
    )


@app.post(
    f"{settings.api_prefix}/auth/account-type",
    response_model=AccountTypeLookupResponse,
)
def lookup_account_type(payload: AccountTypeLookupRequest) -> AccountTypeLookupResponse:
    normalized_email = payload.email.lower().strip()

    workshop = get_workshop_by_email(normalized_email)
    if workshop:
        return AccountTypeLookupResponse(role=WORKSHOP_ROLE)

    client = get_client_by_email(normalized_email)
    if client:
        return AccountTypeLookupResponse(role=str(client["role"]))

    return AccountTypeLookupResponse(role=None)


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
