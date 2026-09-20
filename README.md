# Setu — Progressive Trust Scoring

Synchrony Hackathon submission (PS-II Sem II 2026-27) — problem statement: *"AI-Powered Financial Inclusion: Dynamic Risk Assessment for Underserved Segments."*

One-line thesis and full design rationale: see [DESIGN.md](DESIGN.md).

## Architecture

```
React (frontend) -> Spring Boot (backend API) -> Python model-service (FastAPI, owns the ML) -> Postgres+pgvector (planned)
```

## Running in Codespaces

1. Open this repo in a Codespace and wait for the container build to finish (first boot takes a few minutes — it's installing Java 21, Node 20, and Python 3.12).
2. Start Postgres: `docker compose up -d`
3. Start the model service:
   ```bash
   cd model-service
   pip install -r requirements.txt
   uvicorn app:app --reload --port 8000
   ```
4. Start the backend (new terminal):
   ```bash
   cd backend
   mvn spring-boot:run
   ```
5. Start the frontend (new terminal):
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
6. Open the forwarded port for **5173** (Codespaces will prompt you, or check the Ports tab).

## Running the tests

```bash
cd model-service
python -m pytest tests/ -v
```

## Optional: real LLM explanations

Set `ANTHROPIC_API_KEY` as an environment variable or a Codespaces secret before starting the model-service to get real LLM-generated explanations instead of the template fallback. Never commit a real key — copy `.env.example` to `.env`, which is gitignored.

## Regenerating the synthetic dataset

```bash
cd data
python generate_synthetic_data.py
```

## Status

Working thin vertical slice: React → Spring Boot → model-service → back, with real (synthetic-data-trained) scoring and explanation logic, unit-tested. Postgres/pgvector schema is defined (`db/init.sql`) but not yet wired into the running services — see "Current build status" in [DESIGN.md](DESIGN.md) for what's next.
