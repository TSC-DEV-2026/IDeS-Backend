from __future__ import annotations

import os
from typing import Generator
from urllib.parse import quote_plus

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

load_dotenv()


def _build_database_url() -> str:
    db_host = (os.getenv("DB_HOST") or "").strip()
    db_port = (os.getenv("DB_PORT") or "").strip()
    db_name = (os.getenv("DB_NAME") or "").strip()
    db_user = (os.getenv("DB_USER") or "").strip()
    db_password = os.getenv("DB_PASSWORD") or ""
    db_sslmode = (os.getenv("DB_SSLMODE") or "disable").strip()

    missing = [k for k, v in {
        "DB_HOST": db_host,
        "DB_PORT": db_port,
        "DB_NAME": db_name,
        "DB_USER": db_user,
        "DB_PASSWORD": db_password,
    }.items() if not v]

    if missing:
        raise RuntimeError(f"Variáveis ausentes no .env: {', '.join(missing)}")

    # Protege caracteres especiais na senha (ex: @)
    pwd = quote_plus(db_password)

    # psycopg2 (recomendado) — se você estiver usando outro driver, troque aqui.
    return f"postgresql+psycopg2://{db_user}:{pwd}@{db_host}:{db_port}/{db_name}?sslmode={db_sslmode}"


DATABASE_URL = _build_database_url()


class Base(DeclarativeBase):
    pass


engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    future=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()