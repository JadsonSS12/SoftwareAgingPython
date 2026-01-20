import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import create_engine
from typing import Generator
import logging
from contextlib import contextmanager

from .config import BrokerConfig

logger = logging.getLogger(__name__)

Base = declarative_base()

class DatabaseManager:
    def __init__(self, config: BrokerConfig):
        self.config = config
        self.engine = create_engine(
            config.database.url,
            echo=config.database.echo,
            pool_size=20,
            max_overflow=30,
            pool_pre_ping=True
        )
        self.SessionLocal = sessionmaker(
            bind=self.engine,
            autocommit=False,
            autoflush=False
        )
        
    def create_tables(self):
        """Create all tables"""
        Base.metadata.create_all(bind=self.engine)
        logger.info("Database tables created")
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Get database session context manager"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def get_db(self) -> Generator[Session, None, None]:
        """FastAPI dependency for database sessions"""
        with self.get_session() as session:
            yield session