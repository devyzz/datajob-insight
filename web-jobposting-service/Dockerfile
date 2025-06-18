# 1. Builder stage: Install dependencies with Poetry
FROM python:3.11-slim as builder

# Install poetry
RUN pip install poetry

# Set the working directory
WORKDIR /app
ENV PYTHONPATH="/app:$PYTHONPATH"

# Disable virtualenv creation by poetry globally // Changed
RUN poetry config virtualenvs.create false

# Copy the pyproject.toml and poetry.lock files
COPY web-jobposting-service/pyproject.toml ./pyproject.toml  
COPY web-jobposting-service/poetry.lock ./poetry.lock       

# Copy the common module, as it is a path dependency
COPY ./_common /app/_common

# Install dependencies globally (no .venv) // Changed
RUN poetry install --no-root --without dev

# Copy the application source code
COPY web-jobposting-service/app ./web-jobposting-service/app


# 2. Final stage: Create the final, lean image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV FASTAPI_ENV=production

# Set working directory
WORKDIR /app

# Copy installed dependencies and app code // Changed
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /app /app

# Expose the port
EXPOSE 8001

# Run the application directly without poetry or .venv // Changed
CMD ["uvicorn", "web-jobposting-service.app.main:app", "--host", "0.0.0.0", "--port", "8001"]
