# Etapa de build: instala dependências em wheels para acelerar
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --upgrade pip && \
    pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

# Etapa final (runtime)
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Usuário não root (boa prática)
RUN useradd -m appuser
WORKDIR /app

# Instala somente runtime + wheels prontos
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels

# Copia o projeto (será sobreposto por bind mount no dev, mas funciona em prod)
COPY . .

# Pastas usadas pela app
RUN mkdir -p media staticfiles data && chown -R appuser:appuser /app
USER appuser

# Coleta estáticos (ignora erro se settings não estiver pronto no build)
RUN python manage.py collectstatic --noinput || true

EXPOSE 8000

ENTRYPOINT ["./start.sh"]
