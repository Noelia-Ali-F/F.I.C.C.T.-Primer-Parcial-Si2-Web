from collections.abc import Mapping

from sqlalchemy import create_engine, text

from app.config import settings


engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    connect_args={"connect_timeout": settings.postgres_connect_timeout},
)


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
        approval_status VARCHAR(30) NOT NULL DEFAULT 'pendiente',
        password_hash VARCHAR(255),
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

CREATE_CLIENTS_TABLE_SQL = text(
    """
    CREATE TABLE IF NOT EXISTS clients (
        id BIGSERIAL PRIMARY KEY,
        identity_card VARCHAR(40) NOT NULL UNIQUE,
        full_name VARCHAR(160) NOT NULL,
        email VARCHAR(160) NOT NULL UNIQUE,
        phone VARCHAR(40) NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        role VARCHAR(40) NOT NULL DEFAULT 'client',
        status VARCHAR(30) NOT NULL DEFAULT 'active',
        accepted_terms BOOLEAN NOT NULL DEFAULT FALSE,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
    """
)

CREATE_VEHICLES_TABLE_SQL = text(
    """
    CREATE TABLE IF NOT EXISTS vehicles (
        id BIGSERIAL PRIMARY KEY,
        client_id BIGINT REFERENCES clients(id) ON DELETE CASCADE,
        brand VARCHAR(120) NOT NULL,
        model VARCHAR(120) NOT NULL,
        year INTEGER NOT NULL,
        plate VARCHAR(40) NOT NULL UNIQUE,
        color VARCHAR(80) NOT NULL,
        is_primary BOOLEAN NOT NULL DEFAULT FALSE,
        photo_path VARCHAR(255),
        photo_url VARCHAR(255),
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
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
        approval_status,
        password_hash,
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
        :approval_status,
        :password_hash,
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
        approval_status,
        password_hash,
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
        approval_status,
        password_hash,
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
        approval_status = COALESCE(:approval_status, approval_status),
        password_hash = COALESCE(:password_hash, password_hash),
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
        approval_status,
        password_hash,
        latitude,
        longitude,
        timezone,
        utc_offset_minutes,
        created_at
    """
)

UPDATE_WORKSHOP_APPROVAL_STATUS_SQL = text(
    """
    UPDATE workshop_registrations
    SET
        approval_status = :approval_status,
        password_hash = COALESCE(:password_hash, password_hash)
    WHERE id = :id
    RETURNING
        id,
        workshop_name,
        contact_name,
        phone,
        email,
        zone,
        specialty,
        approval_status,
        password_hash,
        latitude,
        longitude,
        timezone,
        utc_offset_minutes,
        created_at
    """
)

GET_WORKSHOP_BY_EMAIL_SQL = text(
    """
    SELECT
        id,
        workshop_name,
        contact_name,
        phone,
        email,
        zone,
        specialty,
        approval_status,
        password_hash,
        latitude,
        longitude,
        timezone,
        utc_offset_minutes,
        created_at
    FROM workshop_registrations
    WHERE email = :email
    LIMIT 1
    """
)

GET_WORKSHOP_BY_ID_SQL = text(
    """
    SELECT
        id,
        workshop_name,
        contact_name,
        phone,
        email,
        zone,
        specialty,
        approval_status,
        password_hash,
        latitude,
        longitude,
        timezone,
        utc_offset_minutes,
        created_at
    FROM workshop_registrations
    WHERE id = :id
    LIMIT 1
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

INSERT_CLIENT_SQL = text(
    """
    INSERT INTO clients (
        identity_card,
        full_name,
        email,
        phone,
        password_hash,
        role,
        status,
        accepted_terms
    )
    VALUES (
        :identity_card,
        :full_name,
        :email,
        :phone,
        :password_hash,
        :role,
        :status,
        :accepted_terms
    )
    RETURNING
        id,
        identity_card,
        full_name,
        email,
        phone,
        role,
        status,
        accepted_terms,
        created_at,
        updated_at
    """
)

UPDATE_CLIENT_SQL = text(
    """
    UPDATE clients
    SET
        identity_card = :identity_card,
        full_name = :full_name,
        email = :email,
        phone = :phone,
        password_hash = COALESCE(:password_hash, password_hash),
        role = :role,
        status = :status,
        accepted_terms = :accepted_terms,
        updated_at = NOW()
    WHERE id = :id
    RETURNING
        id,
        identity_card,
        full_name,
        email,
        phone,
        role,
        status,
        accepted_terms,
        created_at,
        updated_at
    """
)

LIST_CLIENTS_SQL = text(
    """
    SELECT
        id,
        identity_card,
        full_name,
        email,
        phone,
        role,
        status,
        accepted_terms,
        created_at,
        updated_at
    FROM clients
    ORDER BY created_at DESC, id DESC
    """
)

GET_CLIENT_BY_EMAIL_SQL = text(
    """
    SELECT
        id,
        identity_card,
        full_name,
        email,
        phone,
        password_hash,
        role,
        status,
        accepted_terms,
        created_at,
        updated_at
    FROM clients
    WHERE email = :email
    LIMIT 1
    """
)

GET_CLIENT_BY_ID_SQL = text(
    """
    SELECT
        id,
        identity_card,
        full_name,
        email,
        phone,
        password_hash,
        role,
        status,
        accepted_terms,
        created_at,
        updated_at
    FROM clients
    WHERE id = :id
    LIMIT 1
    """
)

UPDATE_CLIENT_STATUS_SQL = text(
    """
    UPDATE clients
    SET
        status = :status,
        updated_at = NOW()
    WHERE id = :id
    RETURNING
        id,
        identity_card,
        full_name,
        email,
        phone,
        role,
        status,
        accepted_terms,
        created_at,
        updated_at
    """
)

DELETE_CLIENT_SQL = text(
    """
    DELETE FROM clients
    WHERE id = :id
    RETURNING id
    """
)

DELETE_CLIENT_VEHICLES_SQL = text(
    """
    DELETE FROM vehicles
    WHERE client_id = :client_id
    """
)

INSERT_VEHICLE_SQL = text(
    """
    INSERT INTO vehicles (
        client_id,
        brand,
        model,
        year,
        plate,
        color,
        is_primary,
        photo_path,
        photo_url
    )
    VALUES (
        :client_id,
        :brand,
        :model,
        :year,
        :plate,
        :color,
        :is_primary,
        :photo_path,
        :photo_url
    )
    RETURNING
        id,
        client_id,
        brand,
        model,
        year,
        plate,
        color,
        is_primary,
        photo_path,
        photo_url,
        created_at
    """
)

LIST_VEHICLES_SQL = text(
    """
    SELECT
        id,
        client_id,
        brand,
        model,
        year,
        plate,
        color,
        is_primary,
        photo_path,
        photo_url,
        created_at
    FROM vehicles
    WHERE client_id = :client_id
    ORDER BY created_at DESC, id DESC
    """
)

GET_VEHICLE_BY_ID_SQL = text(
    """
    SELECT
        id,
        client_id,
        brand,
        model,
        year,
        plate,
        color,
        is_primary,
        photo_path,
        photo_url,
        created_at
    FROM vehicles
    WHERE id = :id AND client_id = :client_id
    LIMIT 1
    """
)

UPDATE_VEHICLE_SQL = text(
    """
    UPDATE vehicles
    SET
        client_id = :client_id,
        brand = :brand,
        model = :model,
        year = :year,
        plate = :plate,
        color = :color,
        is_primary = :is_primary,
        photo_path = :photo_path,
        photo_url = :photo_url
    WHERE id = :id AND client_id = :client_id
    RETURNING
        id,
        client_id,
        brand,
        model,
        year,
        plate,
        color,
        is_primary,
        photo_path,
        photo_url,
        created_at
    """
)

DELETE_VEHICLE_SQL = text(
    """
    DELETE FROM vehicles
    WHERE id = :id AND client_id = :client_id
    RETURNING id, client_id, photo_path
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
        connection.execute(CREATE_CLIENTS_TABLE_SQL)
        connection.execute(CREATE_VEHICLES_TABLE_SQL)
        connection.execute(text("ALTER TABLE technicians ADD COLUMN IF NOT EXISTS email VARCHAR(160)"))
        connection.execute(
            text("ALTER TABLE workshop_registrations ADD COLUMN IF NOT EXISTS timezone VARCHAR(120)")
        )
        connection.execute(
            text("ALTER TABLE workshop_registrations ADD COLUMN IF NOT EXISTS utc_offset_minutes INTEGER")
        )
        connection.execute(
            text(
                "ALTER TABLE workshop_registrations "
                "ADD COLUMN IF NOT EXISTS approval_status VARCHAR(30) NOT NULL DEFAULT 'pendiente'"
            )
        )
        connection.execute(
            text(
                "ALTER TABLE workshop_registrations "
                "ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255)"
            )
        )
        connection.execute(
            text(
                "UPDATE workshop_registrations "
                "SET approval_status = 'pendiente' "
                "WHERE approval_status IS NULL OR approval_status = ''"
            )
        )
        connection.execute(text("ALTER TABLE clients ADD COLUMN IF NOT EXISTS role VARCHAR(40) DEFAULT 'client'"))
        connection.execute(
            text("ALTER TABLE clients ADD COLUMN IF NOT EXISTS status VARCHAR(30) NOT NULL DEFAULT 'active'")
        )
        connection.execute(
            text("ALTER TABLE clients ADD COLUMN IF NOT EXISTS accepted_terms BOOLEAN NOT NULL DEFAULT FALSE")
        )
        connection.execute(text("ALTER TABLE vehicles ADD COLUMN IF NOT EXISTS client_id BIGINT"))
        connection.execute(
            text(
                """
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1
                        FROM pg_constraint
                        WHERE conname = 'vehicles_client_id_fkey'
                    ) THEN
                        ALTER TABLE vehicles
                        ADD CONSTRAINT vehicles_client_id_fkey
                        FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE;
                    END IF;
                END$$;
                """
            )
        )
        connection.execute(text("ALTER TABLE vehicles ADD COLUMN IF NOT EXISTS photo_path VARCHAR(255)"))
        connection.execute(text("ALTER TABLE vehicles ADD COLUMN IF NOT EXISTS photo_url VARCHAR(255)"))


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


def update_workshop_approval_status(workshop_id: int, approval_status: str) -> dict[str, object] | None:
    with engine.begin() as connection:
        result = connection.execute(
            UPDATE_WORKSHOP_APPROVAL_STATUS_SQL,
            {
                "id": workshop_id,
                "approval_status": approval_status,
                "password_hash": None,
            },
        )
        row = result.mappings().one_or_none()
    return dict(row) if row else None


def get_workshop_by_email(email: str) -> dict[str, object] | None:
    with engine.connect() as connection:
        result = connection.execute(GET_WORKSHOP_BY_EMAIL_SQL, {"email": email})
        row = result.mappings().one_or_none()
    return dict(row) if row else None


def get_workshop_by_id(workshop_id: int) -> dict[str, object] | None:
    with engine.connect() as connection:
        result = connection.execute(GET_WORKSHOP_BY_ID_SQL, {"id": workshop_id})
        row = result.mappings().one_or_none()
    return dict(row) if row else None


def update_workshop_approval_status_with_password(
    workshop_id: int,
    approval_status: str,
    password_hash: str | None,
) -> dict[str, object] | None:
    with engine.begin() as connection:
        result = connection.execute(
            UPDATE_WORKSHOP_APPROVAL_STATUS_SQL,
            {
                "id": workshop_id,
                "approval_status": approval_status,
                "password_hash": password_hash,
            },
        )
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


def create_client(payload: Mapping[str, object]) -> dict[str, object]:
    with engine.begin() as connection:
        result = connection.execute(INSERT_CLIENT_SQL, payload)
        row = result.mappings().one()
    return dict(row)


def list_clients() -> list[dict[str, object]]:
    with engine.connect() as connection:
        result = connection.execute(LIST_CLIENTS_SQL)
        rows = result.mappings().all()
    return [dict(row) for row in rows]


def get_client_by_email(email: str) -> dict[str, object] | None:
    with engine.connect() as connection:
        result = connection.execute(GET_CLIENT_BY_EMAIL_SQL, {"email": email})
        row = result.mappings().one_or_none()
    return dict(row) if row else None


def get_client_by_id(client_id: int) -> dict[str, object] | None:
    with engine.connect() as connection:
        result = connection.execute(GET_CLIENT_BY_ID_SQL, {"id": client_id})
        row = result.mappings().one_or_none()
    return dict(row) if row else None


def update_client_status(client_id: int, status: str) -> dict[str, object] | None:
    with engine.begin() as connection:
        result = connection.execute(UPDATE_CLIENT_STATUS_SQL, {"id": client_id, "status": status})
        row = result.mappings().one_or_none()
    return dict(row) if row else None


def update_client(client_id: int, payload: Mapping[str, object]) -> dict[str, object] | None:
    with engine.begin() as connection:
        result = connection.execute(UPDATE_CLIENT_SQL, {"id": client_id, **payload})
        row = result.mappings().one_or_none()
    return dict(row) if row else None


def delete_client(client_id: int) -> bool:
    with engine.begin() as connection:
        connection.execute(DELETE_CLIENT_VEHICLES_SQL, {"client_id": client_id})
        result = connection.execute(DELETE_CLIENT_SQL, {"id": client_id})
        row = result.mappings().one_or_none()
    return row is not None


def create_vehicle(payload: Mapping[str, object]) -> dict[str, object]:
    with engine.begin() as connection:
        result = connection.execute(INSERT_VEHICLE_SQL, payload)
        row = result.mappings().one()
    return dict(row)


def list_vehicles(client_id: int) -> list[dict[str, object]]:
    with engine.connect() as connection:
        result = connection.execute(LIST_VEHICLES_SQL, {"client_id": client_id})
        rows = result.mappings().all()
    return [dict(row) for row in rows]


def get_vehicle_by_id(vehicle_id: int, client_id: int) -> dict[str, object] | None:
    with engine.connect() as connection:
        result = connection.execute(GET_VEHICLE_BY_ID_SQL, {"id": vehicle_id, "client_id": client_id})
        row = result.mappings().one_or_none()
    return dict(row) if row else None


def update_vehicle(vehicle_id: int, payload: Mapping[str, object]) -> dict[str, object] | None:
    with engine.begin() as connection:
        result = connection.execute(UPDATE_VEHICLE_SQL, {"id": vehicle_id, **payload})
        row = result.mappings().one_or_none()
    return dict(row) if row else None


def delete_vehicle(vehicle_id: int, client_id: int) -> dict[str, object] | None:
    with engine.begin() as connection:
        result = connection.execute(DELETE_VEHICLE_SQL, {"id": vehicle_id, "client_id": client_id})
        row = result.mappings().one_or_none()
    return dict(row) if row else None
