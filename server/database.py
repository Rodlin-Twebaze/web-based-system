import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

BASE_DIR = Path(__file__).resolve().parent
ENV_FILE = BASE_DIR / ".env.example"

if ENV_FILE.exists():
    _ = load_dotenv(ENV_FILE)


def get_database_url() -> str:
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        print(database_url)
        return database_url

    username = os.getenv("user") or os.getenv("DB_USER") or "postgres"
    password = os.getenv("password") or os.getenv("DB_PASSWORD")
    host = os.getenv("host") or os.getenv("DB_HOST") or "localhost"
    port = os.getenv("port") or os.getenv("DB_PORT") or "5432"
    database_name = os.getenv("dbname") or os.getenv("DB_NAME") or "postgres"

    return f"postgresql+psycopg2://{username}:{password}@{host}:{port}/{database_name}?sslmode=require"


engine = None
SessionLocal = None


def init_db():
    global engine, SessionLocal

    if engine is not None and SessionLocal is not None:
        return engine

    database_url = get_database_url()
    engine = create_engine(database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return engine


_ = init_db()


def get_db():
    if SessionLocal is None:
        _ = init_db()

    if SessionLocal is None:
        raise RuntimeError("Database session factory could not be initialized")

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
