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

## Status

Working end-to-end, verified live in Codespaces: React → Spring Boot → model-service → back, covering consent (enforced server-side, persisted in Postgres), scoring, real Gemini-based explanation, per-applicant score history (persisted), right-to-erasure, and a real fairness audit of the trained model (`GET /api/fairness-report`). AWS deployment is in progress — see [DESIGN.md](DESIGN.md) for current status.
