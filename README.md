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

Set `GEMINI_API_KEY` as an environment variable or a Codespaces secret before starting the model-service to get real LLM-generated explanations instead of the template fallback. Free key: [aistudio.google.com/apikey](https://aistudio.google.com/apikey). Never commit a real key — copy `.env.example` to `.env`, which is gitignored.

## Regenerating the synthetic dataset

```bash
cd data
python generate_synthetic_data.py
```

## Deploying (Docker Compose — e.g. on an EC2 instance)

All four services are containerized (`docker-compose.yml`, plus a `Dockerfile` in `backend/`, `model-service/`, and `frontend/`). This is the same compose file used for local dev (`postgres`), extended to build and run the other three services too, wired together by their Compose service names instead of `localhost`.

1. `cp .env.example .env` and fill in `GEMINI_API_KEY` (and change `POSTGRES_PASSWORD` if you want) — Compose loads `.env` automatically.
2. `docker compose up -d --build`
3. Open `http://<host-ip>/` — nginx serves the built React app and reverse-proxies `/api/*` to the backend container (see `frontend/nginx.conf`).

Only port 80 (and 22 for SSH) needs to be open to the internet; 8080/8000/5432 are reached only inside the Compose network, not published externally in this configuration.

## Status

Working end-to-end, verified in the Codespace: React → Spring Boot → model-service → back, covering consent (enforced server-side, persisted in Postgres), scoring (cohort lookup now backed by a real pgvector similarity search over a PCA-learned embedding, not just scikit-learn), real Gemini-based explanation, per-applicant score history (persisted), right-to-erasure, API-key auth, real input validation, and a real fairness audit of the trained model (`GET /api/fairness-report`).

**Also live on AWS:** http://43.204.147.211/ — reflects an earlier point before the pgvector/embeddings/auth/validation work above (that instance's tight memory means redeploys need care, see DESIGN.md). See [DESIGN.md](DESIGN.md) for full status.
