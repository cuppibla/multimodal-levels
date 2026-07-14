# The A2A analyst service — ONE image, THREE deployments (ANALYST env picks the specialist).
# Used by the "Ship it — one crew, two shapes" tutorial (Shape 2). The monolith (Shape 1)
# doesn't use this file: `adk deploy cloud_run` generates its own container source.
FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml ./
RUN pip install --no-cache-dir uv && uv pip install --system -r pyproject.toml --extra a2a
COPY agent/ ./agent/
COPY a2a_crew/ ./a2a_crew/
ENV PORT=8080
# Cloud Run sets PORT; ANALYST comes from --set-env-vars (geological | botanical | astronomical)
CMD ["python", "-m", "a2a_crew.serve_analyst"]
