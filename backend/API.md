# Backend API

Documentacion breve de los endpoints disponibles en el backend FastAPI.

## Base URL

- Desarrollo local: `http://localhost:8000`
- En red local: `http://192.168.0.50:8000` o `http://192.168.26.4:8000`

## Endpoints

### `GET /`

Endpoint basico para comprobar que el backend esta levantado.

Respuesta esperada:

```json
{
  "message": "Backend running"
}
```

Ejemplo:

```bash
curl http://localhost:8000/
```

### `GET /api/health`

Verifica el estado general del backend y la conexion con PostgreSQL.

Respuesta esperada:

```json
{
  "status": "ok",
  "environment": "development",
  "database": "connected"
}
```

Campo `database`:

- `connected`: la base de datos responde correctamente
- `unavailable`: el backend esta arriba, pero PostgreSQL no responde

Ejemplo:

```bash
curl http://localhost:8000/api/health
```

### `POST /api/workshops`

Registra un taller mecanico desde el formulario principal del frontend.

#### Body JSON

```json
{
  "workshop_name": "Taller Demo",
  "contact_name": "Noelia Demo",
  "phone": "77712345",
  "email": "demo@example.com",
  "zone": "Centro",
  "specialty": "Auxilio mecánico",
  "latitude": -17.7833,
  "longitude": -63.1821
}
```

#### Campos

- `workshop_name`: nombre del taller
- `contact_name`: nombre del responsable
- `phone`: telefono de contacto
- `email`: correo valido
- `zone`: zona o direccion referencial del taller
- `specialty`: especialidad principal
- `latitude`: latitud del punto en el mapa, opcional
- `longitude`: longitud del punto en el mapa, opcional

#### Validaciones

- `workshop_name`: entre 3 y 160 caracteres
- `contact_name`: entre 3 y 160 caracteres
- `phone`: entre 7 y 40 caracteres
- `email`: debe ser un correo valido
- `zone`: entre 2 y 120 caracteres
- `specialty`: entre 2 y 120 caracteres
- `latitude`: entre `-90` y `90`
- `longitude`: entre `-180` y `180`

#### Respuesta exitosa

Codigo: `201 Created`

```json
{
  "id": 1,
  "workshop_name": "Taller Demo",
  "contact_name": "Noelia Demo",
  "phone": "77712345",
  "email": "demo@example.com",
  "zone": "Centro",
  "specialty": "Auxilio mecánico",
  "latitude": -17.7833,
  "longitude": -63.1821,
  "created_at": "2026-04-09T05:35:45.417342Z"
}
```

Ejemplo:

```bash
curl -X POST http://localhost:8000/api/workshops \
  -H "Content-Type: application/json" \
  -d '{
    "workshop_name": "Taller Demo",
    "contact_name": "Noelia Demo",
    "phone": "77712345",
    "email": "demo@example.com",
    "zone": "Centro",
    "specialty": "Auxilio mecánico",
    "latitude": -17.7833,
    "longitude": -63.1821
  }'
```

## Persistencia

Los registros de talleres se guardan en PostgreSQL en la tabla:

- `workshop_registrations`

Columnas principales:

- `id`
- `workshop_name`
- `contact_name`
- `phone`
- `email`
- `zone`
- `specialty`
- `latitude`
- `longitude`
- `created_at`

## CORS

El backend acepta solicitudes desde estos origenes de desarrollo:

- `localhost`
- `127.0.0.1`
- direcciones `192.168.x.x`
- `177.222.97.205`

## Nota

La tabla `workshop_registrations` se crea automaticamente al iniciar el backend.
