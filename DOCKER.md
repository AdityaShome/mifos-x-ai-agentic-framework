# Docker & docker-compose

This repo includes simple Dockerfiles for the backend and frontend and a `docker-compose.yml` to run both together.

Prerequisites:
- Docker and docker-compose installed.

Build and run:

```bash
# from repository root
docker compose build
docker compose up
```

This will:
- build the backend image and start the FastAPI server on port 8000
- build the frontend image and serve the Vite-built app on port 3000

Environment variables for the backend (pass via your shell or an env file):

- `FINERACT_BASE_URL` (required for connecting to a Fineract instance)
- `FINERACT_TENANT`
- `FINERACT_USERNAME`
- `FINERACT_PASSWORD`
- `FINERACT_TIMEOUT_SECONDS` (optional, default 300)

Note: No mock Fineract service is included. Add a `mock` service explicitly if you decide to include one later.
