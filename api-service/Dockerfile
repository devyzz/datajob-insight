# 1. Builder stage: Install dependencies with Poetry
FROM python:3.11-slim as builder

# Install poetry
RUN pip install poetry

# Set the working directory
WORKDIR /app
ENV PYTHONPATH="/app:$PYTHONPATH"

# Disable poetry virtualenv creation globally // Changed
RUN poetry config virtualenvs.create false

# Copy the pyproject.toml and poetry.lock files
COPY api-service/pyproject.toml ./pyproject.toml
COPY api-service/poetry.lock ./poetry.lock

# Copy the common module (path dependency)
COPY ./_common /app/_common

# Install dependencies globally (no .venv) // Changed
RUN poetry install --no-root --without dev

# Copy application source code
COPY api-service/app ./api-service/app


# 2. Final stage: Create the final, lean image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV FASTAPI_ENV=production

# Set working directory
WORKDIR /app

# Copy installed packages and app code from builder // Changed
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY --from=builder /app /app

# Expose port
EXPOSE 8000

# Run the application directly (no poetry or .venv) // Changed
CMD ["uvicorn", "api-service.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
