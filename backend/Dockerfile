# Dockerfile
FROM python:3.11-slim

# --- Environment ---
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# --- Working Directory ---
WORKDIR /app

# --- System Dependencies (CRITICAL FIX) ---
# Installs gcc, g++, cmake, and make required for llama-cpp-python
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    git \
    && rm -rf /var/lib/apt/lists/*

# --- Copy dependencies ---
COPY requirements.txt .
# Install Python packages
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# --- Copy only app folder ---
COPY app/ .

# --- Expose & Run ---
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]