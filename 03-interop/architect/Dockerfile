FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir fastapi uvicorn httpx python-dotenv
CMD ["python", "main.py"]
