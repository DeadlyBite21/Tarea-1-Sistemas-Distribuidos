FROM python:3.11-slim
WORKDIR /app
COPY main.py .
RUN pip install rouge-score sentence-transformers numpy kafka-python
EXPOSE 8002
CMD ["python", "main.py"]