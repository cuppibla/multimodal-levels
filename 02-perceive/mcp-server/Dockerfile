FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir fastmcp>=2.12.0 google-genai>=1.0.0 pydantic>=2.0.0 anyio>=4.0.0
COPY main.py .
ENV PORT=8080
CMD ["python", "main.py"]
