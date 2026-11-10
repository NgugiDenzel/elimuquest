FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_ENV=production

WORKDIR /app
COPY pyproject.toml .
COPY app ./app
COPY content-packages/mathematics-learning-pack.json ./content-packages/
COPY content-packages/mathematics-learning-sequences.json ./content-packages/
COPY content-packages/mathematics-number-systems-phase-b.json ./content-packages/
COPY content-packages/mathematics-number-systems-assessment-phase-b.json ./content-packages/
COPY content-packages/mathematics-curriculum-register.json ./content-packages/
COPY alembic.ini .
COPY alembic ./alembic
RUN pip install --no-cache-dir .

USER 10001:10001
EXPOSE 8000
COPY start.sh .
COPY migrate.sh .
CMD ["sh", "start.sh"]
