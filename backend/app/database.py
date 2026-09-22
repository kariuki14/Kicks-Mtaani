import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./kicks_mtaani.db")

# Fix for Render's postgres:// vs postgresql:// URL format
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine_kwargs = {}
if DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}
elif DATABASE_URL.startswith("postgresql"):
    engine_kwargs.update({
        "pool_pre_ping": True,
        "pool_recycle": 300,
    })
    # Enforce SSL for remote Postgres (e.g. Render, Neon, Supabase)
    if "localhost" not in DATABASE_URL and "127.0.0.1" not in DATABASE_URL and "db" not in DATABASE_URL:
        engine_kwargs["connect_args"] = {"sslmode": "require"}

engine = create_engine(DATABASE_URL, **engine_kwargs)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()