# Build from the repository root:  docker build -f backend/Dockerfile -t documind-api .
FROM python:3.12-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ .
RUN useradd -m appuser && chown -R appuser /app
USER appuser
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
