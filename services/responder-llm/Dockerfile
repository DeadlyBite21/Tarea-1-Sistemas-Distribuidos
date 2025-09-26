FROM python:3.11-slim
WORKDIR /app
COPY main.py .
RUN pip install fastapi uvicorn[standard] httpx kafka-python
RUN pip uninstall -y redis
EXPOSE 8001
CMD ["python", "main.py"]