import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from dotenv import load_dotenv

load_dotenv()

# Example: sqlite:///./deal_db.sqlite
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./deal_db.sqlite")

# For SQLite, we need connect_args={"check_same_thread": False}
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, echo=False, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class DealLinkRun(Base):
    __tablename__ = "deal_link_runs"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    source_name = Column(String, index=True)

    results = relationship("DealLinkResult", back_populates="run")

class DealLinkResult(Base):
    __tablename__ = "deal_link_results"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("deal_link_runs.id"))
    retailer = Column(String, index=True)
    original_product = Column(String)
    original_size = Column(String)
    resolved_product_name = Column(String, nullable=True)
    resolved_product_url = Column(String, nullable=True)
    resolved_image_url = Column(String, nullable=True)
    confidence_score = Column(Float, nullable=True)
    resolution_method = Column(String, nullable=True)
    status = Column(String, index=True) # e.g., 'resolved', 'unresolved'
    notes = Column(Text, nullable=True)

    run = relationship("DealLinkRun", back_populates="results")

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
