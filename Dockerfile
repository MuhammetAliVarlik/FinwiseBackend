FROM python:3.11-slim

# --- Environment ---
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH=/app

# --- Working Directory ---
WORKDIR /app

# --- Copy dependencies ---
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# --- Copy only app folder ---
COPY app/ .

# --- Expose & Run ---
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
