# Mifos X Portfolio Health Agent

Prototype AI agent for monitoring loan portfolios in Mifos X / Apache Fineract.

## What Is Real Vs Planned

- Real: the FastAPI backend scaffold, `/health` route, shared Pydantic models, deterministic risk scoring engine, Fineract HTTP client, policy guard, LangChain/Ollama explanation workflow, audit persistence, dashboard APIs, and the React/Vite frontend dashboard.
- Planned: broader production hardening, deployment automation and more dashboard polish.

## Current Scaffold

- FastAPI backend entrypoint with `/health`
- Shared Pydantic models for clients, loans, risk scores, decisions, audit logs, and autonomy settings
- Agent workflow, policy, audit, and API layers are implemented for the backend MVP
- React/Vite frontend dashboard reads the live backend and portfolio endpoints

## Backend Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
FINERACT_BASE_URL='https://demo.mifos.io/fineract-provider/api/v1' \
FINERACT_TENANT='default' \
FINERACT_USERNAME='mifos' \
FINERACT_PASSWORD='password' \
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Set these environment variables before connecting to a live Fineract instance:

- `FINERACT_BASE_URL`
- `FINERACT_TENANT`
- `FINERACT_USERNAME`
- `FINERACT_PASSWORD`
- `FINERACT_TIMEOUT_SECONDS` (optional, defaults to 300)

## Frontend Setup

```bash
cd frontend/dashboard
npm install
VITE_API_BASE_URL='http://127.0.0.1:8000' npm run dev
```

## Next Steps

1. Add more live Fineract field mappings and dashboard charts
2. Expand tests around the API layer and workflow orchestration
3. Add deploy scripts for the backend and frontend