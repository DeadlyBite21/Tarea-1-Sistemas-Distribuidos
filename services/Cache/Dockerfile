FROM python:3.11-slim
WORKDIR /app
COPY main.py .
RUN pip install kafka-python
EXPOSE 8004
CMD ["python", "main.py"]
