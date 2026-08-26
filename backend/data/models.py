from sqlalchemy import Column, String, Integer, Text, DateTime
from backend.data.database import Base
from datetime import datetime
import json

class Job(Base):
    __tablename__ = "jobs"
    
    id = Column(String, primary_key=True, index=True)
    status = Column(String)
    progress = Column(String)
    document = Column(Text, nullable=True) # JSON string
    url = Column(String, nullable=True)
    title = Column(String, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(String, default=lambda: datetime.now().isoformat())
    
class JobCheckpoint(Base):
    __tablename__ = "job_checkpoints"
    
    job_id = Column(String, primary_key=True)
    section_title = Column(String, primary_key=True)
    content = Column(Text)
    created_at = Column(String, default=lambda: datetime.now().isoformat())

class StudyGuide(Base):
    __tablename__ = "study_guides"
    
    id = Column(String, primary_key=True, index=True)
    url = Column(String)
    title = Column(String)
    image_url = Column(String, nullable=True)
    provider = Column(String, nullable=True)
    document = Column(Text) # JSON string
    learning_profile = Column(Text, nullable=True) # JSON string
    profile_message = Column(Text, nullable=True)
    generation_time_sec = Column(Integer, nullable=True)
    created_at = Column(String, default=lambda: datetime.now().isoformat())
    length_preset = Column(String, nullable=True)
    analogy_preset = Column(String, nullable=True)
    video_duration = Column(String, nullable=True)
    notes = Column(Text, nullable=True, default="[]") # JSON string
