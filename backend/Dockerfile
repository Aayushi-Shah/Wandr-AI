FROM python:3.12-slim

WORKDIR /app

# libpq-dev: required by asyncpg at build time
# gcc: required by some C-extension packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies before copying source (layer cache)
COPY pyproject.toml .
RUN pip install --no-cache-dir -e ".[test]"

COPY . .

EXPOSE 8000
CMD ["uvicorn", "app.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
