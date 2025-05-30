"""
Database configuration and session management for the internet service application.
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlite3 import Connection as SQLite3Connection
from contextlib import contextmanager
from sqlalchemy import event
import os

# Determine environment and database URL
TESTING = os.getenv("TESTING", "False").lower() == "true"
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "sqlite:///test.db" if TESTING else "sqlite:///internet_service.db"
)

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    pool_pre_ping=True,
    echo=True  # Set to False in production
)

# Enable foreign keys for SQLite
@event.listens_for(engine, "connect")
def enable_foreign_keys(dbapi_connection, connection_record):
    if isinstance(dbapi_connection, SQLite3Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()

# ORM base and session
Base = declarative_base()

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Context manager for session
@contextmanager
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
