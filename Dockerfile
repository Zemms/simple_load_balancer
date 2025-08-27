# Ставим базовые зависимости
FROM python:3.12-slim as builder

RUN pip install poetry

WORKDIR /app

COPY pyproject.toml poetry.lock ./

RUN poetry config virtualenvs.in-project true && \
    poetry install --no-root --without dev

# Собираем окончательный образ
FROM python:3.12-slim

WORKDIR /app

COPY --from=builder /app/.venv ./.venv

COPY src/ ./src

# Активируем виртуальное окружение для последующих команд
ENV PATH="/app/.venv/bin:$PATH"

# Запускаем
CMD ["uvicorn", "src.main:fastapi_instance", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
