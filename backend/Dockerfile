FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# 1. apply migrations  2. idempotent bootstrap (specializations, first super
# admin from INITIAL_ADMIN_* env, demo data only if SEED_DEMO_DATA=true)
# 3. serve. Render/Railway/Fly inject $PORT; locally it falls back to 8000.
CMD ["sh", "-c", "alembic upgrade head && python -m app.bootstrap && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips='*'"]
