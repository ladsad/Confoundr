from sqlalchemy import Column, String, DateTime, JSON, Float
from sqlalchemy.sql import func
from .database import Base

class JobHistory(Base):
    __tablename__ = "job_history"

    job_id = Column(String, primary_key=True, index=True)
    filename = Column(String, index=True)
    target_col = Column(String)
    treatment_col = Column(String, nullable=True)
    
    status = Column(String, index=True) # e.g., 'finished', 'failed'
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), onupdate=func.now())
    execution_time_seconds = Column(Float, nullable=True)
    
    results = Column(JSON, nullable=True)
    error_message = Column(String, nullable=True)
