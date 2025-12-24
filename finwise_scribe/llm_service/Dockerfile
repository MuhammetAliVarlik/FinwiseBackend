# finwise_scribe/llm_service/Dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# --- FIXED SECTION ---
COPY app/ app/

# Run app.main:app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]