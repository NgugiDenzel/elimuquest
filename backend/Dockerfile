FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_ENV=production

WORKDIR /app
COPY pyproject.toml .
COPY app ./app
COPY alembic.ini .
COPY alembic ./alembic
RUN pip install --no-cache-dir .

EXPOSE 8000
COPY start.sh .
CMD ["sh", "start.sh"]
