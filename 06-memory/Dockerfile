FROM python:3.11-slim
WORKDIR /app
RUN pip install --no-cache-dir "google-adk>=1.18" "google-cloud-aiplatform[agent-engines]>=1.133" \
    "google-genai>=1.0" "python-dotenv>=1.0" "fastapi>=0.115" "uvicorn>=0.30"
COPY agent/ ./agent/
COPY server.py .
ENV PORT=8080
CMD ["python", "server.py"]
