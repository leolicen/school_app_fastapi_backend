# STAGE 1: Build
FROM python:3.13-slim AS builder

# Install UV
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Change the working directory to the `app` directory
WORKDIR /app

# Variable to improve caching
ENV UV_LINK_MODE=copy

# Install dependencies
# cache mount => persistent cache for packages 
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project

# Copy the project into the image
COPY . /app

# Disable development dependencies
ENV UV_NO_DEV=1

# Sync the project
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked


# STAGE 2: runtime
FROM python:3.13-slim AS runtime 

# Copy virtual environment
COPY --from=builder /app/.venv /app/.venv

# Copy app source code
WORKDIR /app
COPY --from=builder /app .

# Activate virtual environment
ENV PATH="/app/.venv/bin:$PATH"

# Start application
CMD ["uvicorn", "app.app:app", "--host", "0.0.0.0", "--port", "8000"]