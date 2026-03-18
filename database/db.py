import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import logging

from .models import Base

logger = logging.getLogger(__name__)

def get_db_path():
    db_dir = os.path.expanduser('~/.bioscale')
    os.makedirs(db_dir, exist_ok=True)
    return os.path.join(db_dir, 'bioscale.db')

engine = create_engine(f"sqlite:///{get_db_path()}", echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def _migrate_add_columns():
    """Add new columns to existing tables (safe for fresh DBs too)."""
    import sqlite3
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    # Check if 'language' column exists in users table
    cursor.execute("PRAGMA table_info(users)")
    columns = [row[1] for row in cursor.fetchall()]
    if 'language' not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN language VARCHAR(5) DEFAULT 'pt'")
        conn.commit()
        logger.info("Migração: coluna 'language' adicionada à tabela users")
    conn.close()


def init_db():
    logger.info(f"Inicializando banco de dados em {get_db_path()}")
    Base.metadata.create_all(bind=engine)
    try:
        _migrate_add_columns()
    except Exception as e:
        logger.debug(f"Migração ignorada: {e}")
    
def get_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
