FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir \
    fastapi \
    uvicorn \
    passlib \
    pydantic \
    python-dotenv \
    python-jose \
    pyasn1 \
    pytz \
    email-validator \
    bcrypt \
    SQLAlchemy \
    psycopg2-binary \
    python-multipart

COPY . .

RUN useradd -r -u 1000 -m -s /bin/bash appuser 2>/dev/null || true

USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
