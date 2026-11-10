#!/bin/sh
set -eu

if [ "${ALLOW_DATABASE_MIGRATION:-}" != "1" ]; then
    echo "Refusing migration: set ALLOW_DATABASE_MIGRATION=1 after reviewing the target database." >&2
    exit 2
fi

if [ -z "${DATABASE_URL:-}" ]; then
    echo "Refusing migration: DATABASE_URL must be explicitly configured." >&2
    exit 2
fi

exec python -m alembic upgrade head
