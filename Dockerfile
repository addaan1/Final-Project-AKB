FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    APP_CONFIG=production \
    DEMO_ONLY=1 \
    ALLOW_REGISTRATION=0 \
    ALLOW_WAITLIST=0 \
    ALLOW_OAUTH=0 \
    PERSIST_LOCAL_WRITES=0 \
    PORT=7860

WORKDIR /app

COPY requirements-runtime.txt .
RUN pip install --no-cache-dir -r requirements-runtime.txt

COPY . .

EXPOSE 7860

CMD ["gunicorn", "--bind", "0.0.0.0:7860", "run:app"]
