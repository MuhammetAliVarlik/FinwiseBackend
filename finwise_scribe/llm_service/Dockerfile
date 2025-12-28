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

# Copy the app code
COPY app/ app/

# --- NEW SECTION: AUTOMATION ---
# Copy the entrypoint script
COPY entrypoint.sh .
# Make it executable
RUN chmod +x entrypoint.sh

# Set the entrypoint (runs every time container starts)
ENTRYPOINT ["./entrypoint.sh"]

# Default command (passed to entrypoint as $@)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]