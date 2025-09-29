# score/Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY app.py .
RUN pip install flask requests google-generativeai
CMD ["python", "app.py"]
