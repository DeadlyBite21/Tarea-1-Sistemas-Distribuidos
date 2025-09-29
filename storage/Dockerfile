FROM python:3.11-slim
WORKDIR /app
COPY app.py .
COPY train.csv .
RUN pip install flask
CMD ["python", "app.py"]
