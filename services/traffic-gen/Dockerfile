FROM python:3.11-slim
WORKDIR /app

# dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copia app
COPY main.py .

# script para esperar servicios (opcional)
COPY wait-for-it.sh /usr/local/bin/wait-for-it.sh
RUN chmod +x /usr/local/bin/wait-for-it.sh

CMD ["python", "main.py"]
