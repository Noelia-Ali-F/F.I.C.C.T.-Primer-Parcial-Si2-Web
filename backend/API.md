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
  "password": "NuevaClave123",
  "role": "client",
  "status": "active",
  "accepted_terms": true
}
```

El campo `password` es opcional en esta edición. Si se envía, el backend actualiza la contraseña del cliente; si se omite o va vacío, conserva la actual.

### `DELETE /api/clientes/{client_id}`

Elimina un cliente por su identificador.

Ejemplo:

```bash
curl -X DELETE http://localhost:8000/api/clientes/4
```

### `POST /api/auth/login`

Autentica un cliente registrado desde la app movil.

Tambien autentica al administrador web del sistema con estas credenciales:

- `email`: `administrador@acb.com`
- `password`: `123ppp+++`

Importante:

- El administrador es un usuario virtual del sistema.
- No se guarda en la tabla `clients`.
- Si el correo es `administrador@acb.com`, el backend valida ese acceso fuera del CRUD normal de clientes.

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

### `POST /api/vehiculos`

Registra un vehiculo desde la app movil usando `multipart/form-data`.

#### Campos enviados

- `client_id`: identificador del cliente propietario del vehiculo
- `brand`: marca del vehiculo
- `model`: modelo del vehiculo
- `year`: anio del vehiculo
- `plate`: placa
- `color`: color
- `is_primary`: `true` o `false`
- `photo`: archivo opcional en formato `jpg`, `jpeg`, `png` o `webp`

#### Ejemplo con curl

```bash
curl -X POST http://localhost:8000/api/vehiculos \
  -F "client_id=15" \
  -F "brand=Toyota" \
  -F "model=Corolla" \
  -F "year=2018" \
  -F "plate=1023HHNNI" \
  -F "color=gris" \
  -F "is_primary=true" \
  -F "photo=@/ruta/opcional/vehiculo.jpg"
```

#### Respuesta exitosa

Codigo: `201 Created`

```json
{
  "id": 1,
  "client_id": 15,
  "brand": "Toyota",
  "model": "Corolla",
  "year": 2018,
  "plate": "1023HHNNI",
  "color": "gris",
  "is_primary": true,
  "photo_path": "vehicles/archivo_generado.jpg",
  "photo_url": "/uploads/vehicles/archivo_generado.jpg",
  "created_at": "2026-04-11T21:10:00.000000Z"
}
```

#### Errores posibles

- `400 Bad Request`: foto con formato no permitido
- `404 Not Found`: cliente no encontrado
- `409 Conflict`: ya existe un vehiculo con esa placa
- `422 Unprocessable Entity`: datos faltantes o invalidos

### `GET /api/vehiculos`

Lista los vehiculos registrados de un cliente en orden descendente de creacion.

#### Ejemplo

```bash
curl "http://localhost:8000/api/vehiculos?client_id=15"
```

#### Respuesta exitosa

Codigo: `200 OK`

```json
[
  {
    "id": 2,
    "client_id": 15,
    "brand": "Suzuki",
    "model": "Vitara",
    "year": 2021,
    "plate": "REMOTE20260411",
    "color": "negro",
    "is_primary": false,
    "photo_path": null,
    "photo_url": null,
    "created_at": "2026-04-11T06:12:01.102533Z"
  },
  {
    "id": 1,
    "client_id": 15,
    "brand": "Suzuki",
    "model": "Vitara",
    "year": 2021,
    "plate": "PRUEBA20260411",
    "color": "negro",
    "is_primary": false,
    "photo_path": null,
    "photo_url": null,
    "created_at": "2026-04-11T06:07:52.203747Z"
  }
]
```

#### Reglas

- `client_id` es obligatorio como query param
- el backend filtra por `client_id`
- si el cliente no existe, responde `404 Not Found`

### `DELETE /api/vehiculos/{vehicle_id}`

Elimina un vehiculo por su identificador. Si el vehiculo tenia foto guardada, tambien elimina el archivo asociado.
La eliminacion valida pertenencia usando `client_id`.

#### Ejemplo

```bash
curl -X DELETE "http://localhost:8000/api/vehiculos/1?client_id=15"
```

#### Respuestas

- `204 No Content`: vehiculo eliminado
- `404 Not Found`: vehiculo no encontrado
- `503 Service Unavailable`: base de datos no disponible

### `PUT /api/vehiculos/{vehicle_id}`

Actualiza un vehiculo existente usando `multipart/form-data`. La foto es opcional; si no se envia una nueva, se conserva la actual.

#### Campos enviados

- `client_id`
- `brand`
- `model`
- `year`
- `plate`
- `color`
- `is_primary`
- `photo` opcional

#### Ejemplo

```bash
curl -X PUT http://localhost:8000/api/vehiculos/3 \
  -F "client_id=15" \
  -F "brand=Suzuki" \
  -F "model=Vitara GLX" \
  -F "year=2022" \
  -F "plate=REMOTE20260411B" \
  -F "color=gris grafito" \
  -F "is_primary=true"
```

#### Respuestas

- `200 OK`: vehiculo actualizado
- `404 Not Found`: vehiculo no encontrado
- `409 Conflict`: placa duplicada
- `503 Service Unavailable`: base de datos no disponible

#### Reglas

- `client_id` es obligatorio
- el backend valida que el vehiculo pertenezca a ese `client_id`
- si el vehiculo no pertenece al cliente indicado, responde `404 Not Found`

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

El administrador `administrador@acb.com` no forma parte de esta tabla porque su acceso es virtual y exclusivo del sistema.

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
