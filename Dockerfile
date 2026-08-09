FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY pyproject.toml README.md ./
COPY core ./core
COPY apps ./apps
COPY modules ./modules
COPY integrations ./integrations

RUN pip install --upgrade pip && pip install ".[api,scheduler,storage,redis]"

CMD ["automation", "--help"]
