
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./projetodb/database.db"
)

configuracao = {}

if DATABASE_URL.startswith("sqlite"):
    configuracao["check_same_thread"] = False

engine = create_engine(
    DATABASE_URL,
    connect_args=configuracao
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


def criar_tabelas():
    from app import models

    Base.metadata.create_all(bind=engine)
    print("Tabelas verificadas/criadas com sucesso!")
