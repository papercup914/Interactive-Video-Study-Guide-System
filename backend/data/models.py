from sqlalchemy import Column, String, Integer, Text, DateTime
from sqlalchemy.sql import func
from backend.data.database import Base
from datetime import datetime, timezone
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
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), server_default=func.now())
    
class JobCheckpoint(Base):
    __tablename__ = "job_checkpoints"
    
    job_id = Column(String, primary_key=True)
    section_title = Column(String, primary_key=True)
    content = Column(Text)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), server_default=func.now())

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
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), server_default=func.now())
    length_preset = Column(String, nullable=True)
    analogy_preset = Column(String, nullable=True)
    video_duration = Column(String, nullable=True)
    notes = Column(Text, nullable=True, default="[]") # JSON string

class BatchJob(Base):
    __tablename__ = "batch_jobs"
    
    id = Column(String, primary_key=True, index=True)
    url = Column(String)
    title = Column(String, nullable=True)
    total_videos = Column(Integer, default=0)
    completed_videos = Column(Integer, default=0)
    failed_videos = Column(Integer, default=0)
    skipped_videos = Column(Integer, default=0)
    status = Column(String, default="pending") # pending, collecting, processing, completed, failed, cancelled
    sync_status = Column(String, default="idle") # idle, syncing, synced, failed
    sync_error = Column(Text, nullable=True)
    provider = Column(String, nullable=True)
    force_refresh = Column(Integer, default=0)
    exclude_shorts = Column(Integer, default=1)
    max_limit = Column(Integer, default=30)
    error = Column(Text, nullable=True)
    logs = Column(Text, nullable=True, default="[]") # JSON list of log items
    remote_url = Column(String, nullable=True)
    sync_key = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), server_default=func.now(), onupdate=lambda: datetime.now(timezone.utc))


class BatchVideoItem(Base):
    __tablename__ = "batch_video_items"
    
    id = Column(String, primary_key=True, index=True)
    batch_job_id = Column(String, index=True)
    video_id = Column(String, index=True)
    url = Column(String)
    title = Column(String, nullable=True)
    duration = Column(String, nullable=True)
    status = Column(String, default="pending") # pending, processing, completed, skipped, failed
    error = Column(Text, nullable=True)
    sync_status = Column(String, default="pending") # pending, synced, failed
    presets_generated = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), server_default=func.now(), onupdate=lambda: datetime.now(timezone.utc))

