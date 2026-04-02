from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime
import os

Base = declarative_base()

class AuditLog(Base):
    __tablename__ = 'audit_logs'
    id = Column(Integer, primary_key=True)
    user_id = Column(String)
    original_text = Column(String)
    scrubbed_text = Column(String)
    pii_count = Column(Integer)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

class TokenUsage(Base):
    __tablename__ = 'token_usage'
    id = Column(Integer, primary_key=True)
    user_id = Column(String)
    prompt_tokens = Column(Integer)
    completion_tokens = Column(Integer)
    total_tokens = Column(Integer)
    cost = Column(Float)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

DB_PATH = "sqlite:///./data/safegate.db"
engine = create_engine(DB_PATH)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
