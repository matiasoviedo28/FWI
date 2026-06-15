# Imagen única para la API y el pipeline (cambia solo el comando en compose).
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

WORKDIR /app

# Dependencias del sistema para netCDF / geoespacial (por si algún wheel no las trae)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libexpat1 && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

COPY shared/ ./shared/
COPY pipeline/ ./pipeline/
COPY api/ ./api/
COPY data/CSV/ ./data/CSV/
COPY data/JSON/ ./data/JSON/

EXPOSE 9000
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "9000"]
