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

### `POST /api/clientes`

Registra un cliente desde la app movil despues de la validacion OTP.

#### Body JSON

```json
{
  "identityCard": "12345678",
  "fullName": "Juan Perez Gomez",
  "email": "juan@example.com",
  "phone": "71234567",
  "password": "ClaveSegura123",
  "confirmPassword": "ClaveSegura123",
  "acceptedTerms": true,
  "role": "client"
}
```

#### Claves aceptadas

El backend acepta tanto nombres en camelCase como en snake_case para facilitar compatibilidad con el telefono:

- `identityCard`, `identity_card`, `ci`
- `fullName`, `full_name`, `name`
- `phone`, `telefono`
- `confirmPassword`, `confirm_password`
- `acceptedTerms`, `accepted_terms`, `termsAccepted`

#### Validaciones

- `identity_card`: entre 5 y 40 caracteres
- `full_name`: entre 3 y 160 caracteres
- `email`: debe ser un correo valido
- `phone`: entre 7 y 40 caracteres
- `password`: minimo 6 caracteres
- `confirm_password`: si se envia, debe coincidir con `password`
- `accepted_terms`: debe ser `true`

#### Respuesta exitosa

Codigo: `201 Created`

```json
{
  "id": 1,
  "identity_card": "12345678",
  "full_name": "Juan Perez Gomez",
  "email": "juan@example.com",
  "phone": "71234567",
  "role": "client",
  "accepted_terms": true,
  "created_at": "2026-04-11T20:45:00.000000Z",
  "updated_at": "2026-04-11T20:45:00.000000Z"
}
```

#### Errores posibles

- `409 Conflict`: ya existe un cliente con ese carnet o correo
- `422 Unprocessable Entity`: datos invalidos o terminos no aceptados

Ejemplo:

```bash
curl -X POST http://localhost:8000/api/clientes \
  -H "Content-Type: application/json" \
  -d '{
    "identityCard": "12345678",
    "fullName": "Juan Perez Gomez",
    "email": "juan@example.com",
    "phone": "71234567",
    "password": "ClaveSegura123",
    "confirmPassword": "ClaveSegura123",
    "acceptedTerms": true,
    "role": "client"
  }'
```

### `GET /api/clientes`

Lista los clientes registrados.

Ejemplo:

```bash
curl http://localhost:8000/api/clientes
```

### `PUT /api/clientes/{client_id}/status`

Actualiza el estado de un cliente desde el panel administrativo.

#### Body JSON

```json
{
  "status": "suspended"
}
```

Valores permitidos:

- `active`
- `suspended`

Ejemplo:

```bash
curl -X PUT http://localhost:8000/api/clientes/4/status \
  -H "Content-Type: application/json" \
  -d '{
    "status": "active"
  }'
```

### `PUT /api/clientes/{client_id}`

Actualiza los datos administrativos de un cliente.

#### Body JSON

```json
{
  "identity_card": "7700476",
  "full_name": "Jhasmany Fernandez",
  "email": "jhasmany@gmail.com",
  "phone": "72992000",
  "role": "client",
  "status": "active",
  "accepted_terms": true
}
```

### `DELETE /api/clientes/{client_id}`

Elimina un cliente por su identificador.

Ejemplo:

```bash
curl -X DELETE http://localhost:8000/api/clientes/4
```

### `POST /api/auth/login`

Autentica un cliente registrado desde la app movil.

#### Body JSON

```json
{
  "email": "jhasmany@gmail.com",
  "password": "claveSegura123"
}
```

#### Respuesta exitosa

Codigo: `200 OK`

```json
{
  "id": 4,
  "email": "jhasmany@gmail.com",
  "full_name": "Jhasmany Fernandez",
  "phone": "72992000",
  "role": "client",
  "status": "active",
  "access_token": "token_generado_por_el_backend",
  "token_type": "bearer"
}
```

#### Errores posibles

- `401 Unauthorized`: `{"detail":"Correo o contraseña incorrectos"}`
- `403 Forbidden`: `{"detail":"Cuenta suspendida"}`

Ejemplo:

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "jhasmany@gmail.com",
    "password": "claveSegura123"
  }'
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
  "longitude": -63.1821,
  "timezone": "America/La_Paz",
  "utc_offset_minutes": -240
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
- `timezone`: zona horaria IANA, opcional
- `utc_offset_minutes`: diferencia respecto a UTC en minutos, opcional

#### Validaciones

- `workshop_name`: entre 3 y 160 caracteres
- `contact_name`: entre 3 y 160 caracteres
- `phone`: entre 7 y 40 caracteres
- `email`: debe ser un correo valido
- `zone`: entre 2 y 120 caracteres
- `specialty`: entre 2 y 120 caracteres
- `latitude`: entre `-90` y `90`
- `longitude`: entre `-180` y `180`
- `timezone`: entre 2 y 120 caracteres
- `utc_offset_minutes`: entre `-840` y `840`

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
  "timezone": "America/La_Paz",
  "utc_offset_minutes": -240,
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
    "longitude": -63.1821,
    "timezone": "America/La_Paz",
    "utc_offset_minutes": -240
  }'
```

### `GET /api/workshops`

Lista todos los talleres registrados en orden descendente de creacion.

Ejemplo:

```bash
curl http://localhost:8000/api/workshops
```

### `PUT /api/workshops/{workshop_id}`

Actualiza el registro de un taller existente usando la misma estructura JSON de creacion.

Ejemplo:

```bash
curl -X PUT http://localhost:8000/api/workshops/1 \
  -H "Content-Type: application/json" \
  -d '{
    "workshop_name": "Taller Demo Actualizado",
    "contact_name": "Noelia Demo",
    "phone": "77712345",
    "email": "demo@example.com",
    "zone": "Centro",
    "specialty": "Auxilio mecánico",
    "latitude": -17.7833,
    "longitude": -63.1821,
    "timezone": "America/La_Paz",
    "utc_offset_minutes": -240
  }'
```

### `DELETE /api/workshops/{workshop_id}`

Elimina un taller por su identificador.

Ejemplo:

```bash
curl -X DELETE http://localhost:8000/api/workshops/1
```

### `POST /api/technicians`

Registra un tecnico asociado al sistema.

#### Body JSON

```json
{
  "full_name": "Carlos Perez",
  "phone": "77799911",
  "email": "carlos@example.com",
  "specialty": "Electricidad automotriz",
  "status": "disponible"
}
```

#### Validaciones

- `full_name`: entre 3 y 160 caracteres
- `phone`: entre 7 y 40 caracteres
- `email`: debe ser un correo valido
- `specialty`: entre 2 y 120 caracteres
- `status`: uno de `disponible`, `ocupado` o `fuera_de_servicio`

### `GET /api/technicians`

Lista todos los tecnicos registrados.

Ejemplo:

```bash
curl http://localhost:8000/api/technicians
```

### `PUT /api/technicians/{technician_id}`

Actualiza un tecnico existente usando la misma estructura JSON de creacion.

Ejemplo:

```bash
curl -X PUT http://localhost:8000/api/technicians/1 \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Carlos Perez",
    "phone": "77799911",
    "email": "carlos@example.com",
    "specialty": "Electricidad automotriz",
    "status": "ocupado"
  }'
```

### `DELETE /api/technicians/{technician_id}`

Elimina un tecnico por su identificador.

Ejemplo:

```bash
curl -X DELETE http://localhost:8000/api/technicians/1
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
- `timezone`
- `utc_offset_minutes`
- `created_at`

Los registros de clientes se guardan en PostgreSQL en la tabla:

- `clients`

Los registros de tecnicos se guardan en PostgreSQL en la tabla:

- `technicians`

## CORS

El backend acepta solicitudes desde estos origenes de desarrollo:

- `localhost`
- `127.0.0.1`
- rangos privados `10.x.x.x`, `172.16.x.x` a `172.31.x.x` y `192.168.x.x`
- otras direcciones IPv4 cuando se accede por IP en desarrollo local

## Nota

La tabla `workshop_registrations` se crea automaticamente al iniciar el backend.
