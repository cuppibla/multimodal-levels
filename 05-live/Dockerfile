# Single container: build the SPA, serve it + the live WebSocket from one FastAPI origin.
FROM node:20-slim AS webbuild
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json* ./frontend/
RUN cd frontend && npm install
COPY frontend/ ./frontend/
RUN cd frontend && npm run build

FROM python:3.11-slim
WORKDIR /app
RUN pip install --no-cache-dir "fastapi>=0.115" "google-adk>=1.18" "google-genai>=1.0" \
    "python-dotenv>=1.0" "uvicorn>=0.30" "websockets>=13"
COPY backend/ ./backend/
COPY --from=webbuild /app/frontend/dist ./frontend/dist
ENV FRONTEND_DIST=/app/frontend/dist PORT=8080
WORKDIR /app/backend
# Cloud Run: deploy with --no-cpu-throttling --timeout 3600 (long-lived WebSockets)
CMD ["python", "main.py"]
