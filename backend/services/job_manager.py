import json
import os
from typing import Dict, Any
from datetime import datetime
from backend.data.database import SessionLocal, engine
from backend.data.models import Base, Job, JobCheckpoint, StudyGuide

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)

def get_study_guide(job_id: str) -> dict:
    with SessionLocal() as db:
        guide = db.query(StudyGuide).filter(StudyGuide.id == job_id).first()
        if not guide:
            return None
            
        try:
            profile = json.loads(guide.learning_profile) if guide.learning_profile and guide.learning_profile.strip() else None
        except:
            profile = None
            
        try:
            document = json.loads(guide.document) if guide.document and guide.document.strip() else {}
        except:
            document = {}
            
        try:
            notes = json.loads(guide.notes) if guide.notes and guide.notes.strip() else []
        except:
            notes = []
            
        return {
            "id": guide.id,
            "url": guide.url,
            "title": guide.title,
            "image_url": guide.image_url,
            "date": guide.created_at,
            "provider": guide.provider,
            "document": document,
            "notes": notes,
            "learning_profile": profile,
            "profile_message": guide.profile_message,
            "generation_time_sec": guide.generation_time_sec,
            "length_preset": guide.length_preset,
            "analogy_preset": guide.analogy_preset,
            "video_duration": guide.video_duration
        }

def update_study_guide_notes(job_id: str, document: dict, notes: list) -> bool:
    with SessionLocal() as db:
        guide = db.query(StudyGuide).filter(StudyGuide.id == job_id).first()
        if not guide:
            return False
            
        guide.document = json.dumps(document, ensure_ascii=False)
        guide.notes = json.dumps(notes, ensure_ascii=False)
        db.commit()
        return True

def create_job(job_id: str) -> None:
    with SessionLocal() as db:
        new_job = Job(id=job_id, status="pending", progress="")
        db.add(new_job)
        db.commit()

def update_job_status(job_id: str, status: str, progress: str = "") -> None:
    with SessionLocal() as db:
        job = db.query(Job).filter(Job.id == job_id).first()
        if job:
            job.status = status
            if progress:
                job.progress = progress
            db.commit()

def finish_job(job_id: str, document: Dict[str, str], url: str = None, title: str = None) -> None:
    with SessionLocal() as db:
        job = db.query(Job).filter(Job.id == job_id).first()
        if job:
            job.status = "completed"
            job.progress = "100%"
            job.document = json.dumps(document, ensure_ascii=False)
            job.url = url
            job.title = title
            db.commit()

def fail_job(job_id: str, error_message: str) -> None:
    with SessionLocal() as db:
        job = db.query(Job).filter(Job.id == job_id).first()
        if job:
            job.status = "failed"
            job.error = error_message
            db.commit()
            
    os.makedirs("backend/data", exist_ok=True)
    with open("backend/data/last_error.txt", "w", encoding="utf-8") as f:
        f.write(f"Job: {job_id}\nError: {error_message}")

def get_job(job_id: str) -> Dict[str, Any]:
    with SessionLocal() as db:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return None
            
        job_dict = {
            "id": job.id,
            "status": job.status,
            "progress": job.progress,
            "document": json.loads(job.document) if job.document else {},
            "url": job.url,
            "title": job.title,
            "error": job.error,
            "created_at": job.created_at
        }
        return job_dict

def cancel_job(job_id: str) -> None:
    with SessionLocal() as db:
        job = db.query(Job).filter(Job.id == job_id).first()
        if job:
            job.status = "cancelled"
            job.progress = "작업이 중단되었습니다."
            db.commit()

def save_chapter_checkpoint(job_id: str, section_title: str, content: str) -> None:
    with SessionLocal() as db:
        checkpoint = db.query(JobCheckpoint).filter(JobCheckpoint.job_id == job_id, JobCheckpoint.section_title == section_title).first()
        if checkpoint:
            checkpoint.content = content
        else:
            checkpoint = JobCheckpoint(job_id=job_id, section_title=section_title, content=content)
            db.add(checkpoint)
        db.commit()

def get_completed_chapters(job_id: str) -> Dict[str, str]:
    with SessionLocal() as db:
        checkpoints = db.query(JobCheckpoint).filter(JobCheckpoint.job_id == job_id).all()
        return {cp.section_title: cp.content for cp in checkpoints}

def save_study_guide(job_id: str, url: str, title: str, image_url: str, provider: str, document: dict, learning_profile: str, profile_message: str, generation_time_sec: int, length_preset: str = None, analogy_preset: str = None, video_duration: str = None) -> None:
    with SessionLocal() as db:
        doc_json = json.dumps(document, ensure_ascii=False)
        notes_json = json.dumps([], ensure_ascii=False)
        
        guide = db.query(StudyGuide).filter(StudyGuide.id == job_id).first()
        if guide:
            guide.url = url
            guide.title = title
            guide.image_url = image_url
            guide.provider = provider
            guide.document = doc_json
            guide.learning_profile = learning_profile
            guide.profile_message = profile_message
            guide.generation_time_sec = generation_time_sec
            guide.length_preset = length_preset
            guide.analogy_preset = analogy_preset
            guide.video_duration = video_duration
            guide.notes = notes_json
        else:
            guide = StudyGuide(
                id=job_id, url=url, title=title, image_url=image_url, provider=provider,
                document=doc_json, learning_profile=learning_profile, profile_message=profile_message,
                generation_time_sec=generation_time_sec, length_preset=length_preset,
                analogy_preset=analogy_preset, video_duration=video_duration, notes=notes_json
            )
            db.add(guide)
        db.commit()

def get_all_study_guides() -> list:
    with SessionLocal() as db:
        guides = db.query(StudyGuide).order_by(StudyGuide.created_at.desc()).all()
        
        result = []
        for guide in guides:
            try:
                profile = json.loads(guide.learning_profile) if guide.learning_profile and guide.learning_profile.strip() else None
            except:
                profile = None
                
            try:
                document = json.loads(guide.document) if guide.document and guide.document.strip() else {}
            except:
                document = {}
                
            guide_dict = {
                "id": guide.id,
                "url": guide.url,
                "title": guide.title,
                "image_url": guide.image_url,
                "date": guide.created_at,
                "provider": guide.provider,
                "document": document,
                "learning_profile": profile,
                "length_preset": guide.length_preset,
                "analogy_preset": guide.analogy_preset,
                "generation_time_sec": guide.generation_time_sec,
                "video_duration": guide.video_duration
            }
            result.append(guide_dict)
        return result

def delete_study_guide(job_id: str) -> bool:
    with SessionLocal() as db:
        guide = db.query(StudyGuide).filter(StudyGuide.id == job_id).first()
        if guide:
            db.delete(guide)
            db.commit()
            return True
        return False
