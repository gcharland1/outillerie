
# syntax=docker/dockerfile:1

FROM python:3.13-slim

# Installer uv depuis son image officielle, en version fixe
COPY --from=ghcr.io/astral-sh/uv:0.9.5 /uv /uvx /bin/

WORKDIR /app

# Configuration uv
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_NO_DEV=1 \
    PATH="/app/.venv/bin:$PATH"

# Installer les dépendances avant de copier le code
# pour profiter du cache Docker
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-install-project

# Copier le code et installer le projet
COPY . .
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-editable

# Ne pas exécuter l'application comme root
RUN useradd --create-home outillerie \
    && chown -R outillerie:outillerie /app
USER outillerie

EXPOSE 5000

CMD ["uv", "run", "main.py"]

