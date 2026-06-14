FROM python:3.12-slim

WORKDIR /app

# Install dependencies first for better layer caching
COPY pyproject.toml ./
RUN pip install --no-cache-dir \
    "fastapi>=0.111" "uvicorn[standard]>=0.29" "beanie>=1.26,<2.0" "motor>=3.4" \
    "pydantic>=2.7" "pydantic-settings>=2.2" "python-jose[cryptography]>=3.3" \
    "passlib[argon2]>=1.7.4" "slowapi>=0.1.9" "apscheduler>=3.10.4"

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
