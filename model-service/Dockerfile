# Build context is the REPO ROOT (see docker-compose.yml), not
# model-service/, so this can also reach the sibling data/ directory.
FROM python:3.12-slim

WORKDIR /app

COPY model-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY model-service/ .
COPY data/synthetic_applicants.csv ./data/synthetic_applicants.csv
ENV SYNTHETIC_DATA_PATH=/app/data/synthetic_applicants.csv

EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
