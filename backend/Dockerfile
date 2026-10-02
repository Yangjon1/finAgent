FROM python:3.11-slim
WORKDIR /app/backend
COPY backend/pyproject.toml .
COPY backend/app ./app
COPY migrations /app/migrations
COPY backend/alembic.ini .
COPY backend/scripts ./scripts
RUN pip install --no-cache-dir --timeout 180 --retries 5 .
