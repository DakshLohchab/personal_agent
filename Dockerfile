FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_SYSTEM_PYTHON=1

RUN pip install --no-cache-dir uv

WORKDIR /app

COPY . /app

RUN uv sync --frozen --no-dev

EXPOSE 8000

CMD ["sh", "-c", "exec uv run uvicorn services.api.main:app --host \"${API_HOST:-0.0.0.0}\" --port \"${PORT:-${API_PORT:-8000}}\""]
