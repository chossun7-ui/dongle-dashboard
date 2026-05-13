FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# WeasyPrint(PDF export) 의존성. PDF가 필요 없으면 이 줄을 줄여도 됨.
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential libpango-1.0-0 libpangoft2-1.0-0 \
        libcairo2 libffi-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml /app/pyproject.toml
COPY app /app/app

RUN pip install -e .

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
