# storage/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copia el script de ingestión
COPY ingest_dataset.py /app/ingest_dataset.py

# Instala dependencias
RUN pip install --no-cache-dir psycopg2-binary

# Ejecuta el script por defecto (se puede sobreescribir con docker compose run)
CMD ["python", "ingest_dataset.py"]
