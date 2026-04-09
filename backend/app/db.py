from collections.abc import Mapping

from sqlalchemy import create_engine, text

from app.config import settings


engine = create_engine(settings.database_url, pool_pre_ping=True)


CREATE_WORKSHOPS_TABLE_SQL = text(
    """
    CREATE TABLE IF NOT EXISTS workshop_registrations (
        id BIGSERIAL PRIMARY KEY,
        workshop_name VARCHAR(160) NOT NULL,
        contact_name VARCHAR(160) NOT NULL,
        phone VARCHAR(40) NOT NULL,
        email VARCHAR(160) NOT NULL,
        zone VARCHAR(120) NOT NULL,
        specialty VARCHAR(120) NOT NULL,
        latitude DOUBLE PRECISION,
        longitude DOUBLE PRECISION,
        timezone VARCHAR(120),
        utc_offset_minutes INTEGER,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
    """
)

CREATE_TECHNICIANS_TABLE_SQL = text(
    """
    CREATE TABLE IF NOT EXISTS technicians (
        id BIGSERIAL PRIMARY KEY,
        full_name VARCHAR(160) NOT NULL,
        phone VARCHAR(40) NOT NULL,
        email VARCHAR(160) NOT NULL DEFAULT '',
        specialty VARCHAR(120) NOT NULL,
        status VARCHAR(30) NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
    """
)

INSERT_WORKSHOP_SQL = text(
    """
    INSERT INTO workshop_registrations (
        workshop_name,
        contact_name,
        phone,
        email,
        zone,
        specialty,
        latitude,
        longitude,
        timezone,
        utc_offset_minutes
    )
    VALUES (
        :workshop_name,
        :contact_name,
        :phone,
        :email,
        :zone,
        :specialty,
        :latitude,
        :longitude,
        :timezone,
        :utc_offset_minutes
    )
    RETURNING
        id,
        workshop_name,
        contact_name,
        phone,
        email,
        zone,
        specialty,
        latitude,
        longitude,
        timezone,
        utc_offset_minutes,
        created_at
    """
)

LIST_WORKSHOPS_SQL = text(
    """
    SELECT
        id,
        workshop_name,
        contact_name,
        phone,
        email,
        zone,
        specialty,
        latitude,
        longitude,
        timezone,
        utc_offset_minutes,
        created_at
    FROM workshop_registrations
    ORDER BY created_at DESC, id DESC
    """
)

UPDATE_WORKSHOP_SQL = text(
    """
    UPDATE workshop_registrations
    SET
        workshop_name = :workshop_name,
        contact_name = :contact_name,
        phone = :phone,
        email = :email,
        zone = :zone,
        specialty = :specialty,
        latitude = :latitude,
        longitude = :longitude,
        timezone = :timezone,
        utc_offset_minutes = :utc_offset_minutes
    WHERE id = :id
    RETURNING
        id,
        workshop_name,
        contact_name,
        phone,
        email,
        zone,
        specialty,
        latitude,
        longitude,
        timezone,
        utc_offset_minutes,
        created_at
    """
)

DELETE_WORKSHOP_SQL = text(
    """
    DELETE FROM workshop_registrations
    WHERE id = :id
    RETURNING id
    """
)

INSERT_TECHNICIAN_SQL = text(
    """
    INSERT INTO technicians (
        full_name,
        phone,
        email,
        specialty,
        status
    )
    VALUES (
        :full_name,
        :phone,
        :email,
        :specialty,
        :status
    )
    RETURNING
        id,
        full_name,
        phone,
        email,
        specialty,
        status,
        created_at,
        updated_at
    """
)

LIST_TECHNICIANS_SQL = text(
    """
    SELECT
        id,
        full_name,
        phone,
        email,
        specialty,
        status,
        created_at,
        updated_at
    FROM technicians
    ORDER BY updated_at DESC, id DESC
    """
)

UPDATE_TECHNICIAN_SQL = text(
    """
    UPDATE technicians
    SET
        full_name = :full_name,
        phone = :phone,
        email = :email,
        specialty = :specialty,
        status = :status,
        updated_at = NOW()
    WHERE id = :id
    RETURNING
        id,
        full_name,
        phone,
        email,
        specialty,
        status,
        created_at,
        updated_at
    """
)

DELETE_TECHNICIAN_SQL = text(
    """
    DELETE FROM technicians
    WHERE id = :id
    RETURNING id
    """
)


def check_database_connection() -> bool:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return True


def init_database() -> None:
    with engine.begin() as connection:
        connection.execute(CREATE_WORKSHOPS_TABLE_SQL)
        connection.execute(CREATE_TECHNICIANS_TABLE_SQL)
        connection.execute(text("ALTER TABLE technicians ADD COLUMN IF NOT EXISTS email VARCHAR(160)"))
        connection.execute(
            text("ALTER TABLE workshop_registrations ADD COLUMN IF NOT EXISTS timezone VARCHAR(120)")
        )
        connection.execute(
            text("ALTER TABLE workshop_registrations ADD COLUMN IF NOT EXISTS utc_offset_minutes INTEGER")
        )


def create_workshop_registration(payload: Mapping[str, object]) -> dict[str, object]:
    with engine.begin() as connection:
        result = connection.execute(INSERT_WORKSHOP_SQL, payload)
        row = result.mappings().one()
    return dict(row)


def list_workshop_registrations() -> list[dict[str, object]]:
    with engine.connect() as connection:
        result = connection.execute(LIST_WORKSHOPS_SQL)
        rows = result.mappings().all()
    return [dict(row) for row in rows]


def update_workshop_registration(workshop_id: int, payload: Mapping[str, object]) -> dict[str, object] | None:
    with engine.begin() as connection:
        result = connection.execute(UPDATE_WORKSHOP_SQL, {"id": workshop_id, **payload})
        row = result.mappings().one_or_none()
    return dict(row) if row else None


def delete_workshop_registration(workshop_id: int) -> bool:
    with engine.begin() as connection:
        result = connection.execute(DELETE_WORKSHOP_SQL, {"id": workshop_id})
        row = result.mappings().one_or_none()
    return row is not None


def create_technician(payload: Mapping[str, object]) -> dict[str, object]:
    with engine.begin() as connection:
        result = connection.execute(INSERT_TECHNICIAN_SQL, payload)
        row = result.mappings().one()
    return dict(row)


def list_technicians() -> list[dict[str, object]]:
    with engine.connect() as connection:
        result = connection.execute(LIST_TECHNICIANS_SQL)
        rows = result.mappings().all()
    return [dict(row) for row in rows]


def update_technician(technician_id: int, payload: Mapping[str, object]) -> dict[str, object] | None:
    with engine.begin() as connection:
        result = connection.execute(UPDATE_TECHNICIAN_SQL, {"id": technician_id, **payload})
        row = result.mappings().one_or_none()
    return dict(row) if row else None


def delete_technician(technician_id: int) -> bool:
    with engine.begin() as connection:
        result = connection.execute(DELETE_TECHNICIAN_SQL, {"id": technician_id})
        row = result.mappings().one_or_none()
    return row is not None
