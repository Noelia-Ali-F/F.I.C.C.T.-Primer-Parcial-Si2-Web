# F.I.C.C.T.-Primer-Parcial-Si2-Diagramador-Web

Estructura base del proyecto web para el primer parcial de SI2.

## Estructura

- `frontend`: aplicacion Angular para desarrollo web
- `backend`: API FastAPI y configuracion de acceso a PostgreSQL
- `docker-compose.yml`: entorno de desarrollo con frontend, backend y base de datos
- `backend/API.md`: documentacion de endpoints del backend

## Desarrollo con Docker

1. Copiar `.env.example` a `.env`
2. Copiar `backend/.env.example` a `backend/.env`
3. Ejecutar `docker compose up --build`

## Puertos

- Frontend: `http://localhost:4200`
- Backend: `http://localhost:8000`
- API healthcheck: `http://localhost:8000/api/health`
- PostgreSQL: `localhost:5432`
