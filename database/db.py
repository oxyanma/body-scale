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

def init_db():
    logger.info(f"Inicializando banco de dados em {get_db_path()}")
    Base.metadata.create_all(bind=engine)
    
def get_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
