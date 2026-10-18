# Cloud Run 用的映像：uv 安裝套件 → collectstatic → gunicorn
FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.8.17 /uv /bin/uv

ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY . .
# collectstatic 不需要真的金鑰，給一個暫時值讓 settings 能載入
RUN DJANGO_SECRET_KEY=build-only python manage.py collectstatic --noinput

# Cloud Run 會設定 PORT（預設 8080）
CMD exec gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8080} --workers 1 --threads 8 --timeout 120
