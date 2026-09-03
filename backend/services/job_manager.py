import json
import os
from typing import Dict, Any
from datetime import datetime, timezone
from backend.data.database import SessionLocal, engine
from backend.data.models import Base, Job, JobCheckpoint, StudyGuide, BatchJob, BatchVideoItem
from typing import List, Optional

from sqlalchemy import text, or_, inspect

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)

def _ensure_schema_columns():
    """DB 테이블에 필요한 컬럼 누락 여부를 안전하게 검사하고 보완합니다."""
    try:
        inspector = inspect(engine)
        
        # 1. batch_jobs 테이블 검사
        batch_cols = {c["name"] for c in inspector.get_columns("batch_jobs")}
        allowed_batch_cols = {
            "logs": "TEXT DEFAULT '[]'",
            "remote_url": "TEXT",
            "sync_key": "TEXT"
        }
        with engine.begin() as conn:
            for col, col_type in allowed_batch_cols.items():
                if col not in batch_cols:
                    conn.execute(text(f"ALTER TABLE batch_jobs ADD COLUMN {col} {col_type}"))
                    
        # 2. study_guides 테이블의 video_id 컬럼 검사
        guide_cols = {c["name"] for c in inspector.get_columns("study_guides")}
        if "video_id" not in guide_cols:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE study_guides ADD COLUMN video_id VARCHAR"))
    except Exception as e:
        print(f"[DB Schema Init Notice] {e}")

_ensure_schema_columns()


def _format_datetime(val) -> str:
    """datetime 객체 또는 ISO 문자열을 안전하게 ISO 포맷 문자열로 통일합니다."""
    if val is None:
        return ""
    if hasattr(val, "isoformat"):
        return val.isoformat()
    return str(val)

def _parse_datetime(val) -> datetime:
    """문자열 또는 None을 datetime 객체로 안전하게 변환합니다."""
    if val is None:
        return datetime.now(timezone.utc)
    if isinstance(val, datetime):
        return val
    try:
        return datetime.fromisoformat(str(val))
    except Exception:
        return datetime.now(timezone.utc)

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
            "date": _format_datetime(guide.created_at),
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
            "created_at": _format_datetime(job.created_at)
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
        from backend.services.video import extract_video_id
        vid = extract_video_id(url) if url else None
        
        doc_json = json.dumps(document, ensure_ascii=False)
        notes_json = json.dumps([], ensure_ascii=False)
        
        guide = db.query(StudyGuide).filter(StudyGuide.id == job_id).first()
        if guide:
            guide.video_id = vid
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
                id=job_id, video_id=vid, url=url, title=title, image_url=image_url, provider=provider,
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
                "date": _format_datetime(guide.created_at),
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

# ==================== BATCH JOB MANAGEMENT ====================

def create_batch_job(
    batch_id: str,
    url: str,
    title: str = "",
    provider: str = "Google Gemini",
    max_limit: int = 30,
    exclude_shorts: bool = True,
    force_refresh: bool = False,
    remote_url: str = None,
    sync_key: str = None
) -> dict:
    with SessionLocal() as db:
        now_dt = datetime.now(timezone.utc)
        initial_log = json.dumps([
            {"timestamp": now_dt.isoformat(), "message": "배치 작업이 생성되었습니다. 수집을 준비합니다.", "level": "info"}
        ], ensure_ascii=False)
        
        existing = db.query(BatchJob).filter(BatchJob.id == batch_id).first()
        if existing:
            existing.url = url or ""
            existing.title = title or existing.title
            existing.provider = provider or "Google Gemini"
            existing.max_limit = max_limit or 30
            existing.exclude_shorts = 1 if exclude_shorts else 0
            existing.force_refresh = 1 if force_refresh else 0
            existing.remote_url = remote_url or existing.remote_url
            existing.sync_key = sync_key or existing.sync_key
            existing.status = "pending"
            existing.logs = initial_log
            existing.updated_at = now_dt
        else:
            job = BatchJob(
                id=batch_id,
                url=url or "",
                title=title or "유튜브 일괄 생성 작업",
                total_videos=0,
                completed_videos=0,
                failed_videos=0,
                skipped_videos=0,
                status="pending",
                sync_status="idle",
                sync_error=None,
                provider=provider or "Google Gemini",
                force_refresh=1 if force_refresh else 0,
                exclude_shorts=1 if exclude_shorts else 0,
                max_limit=max_limit or 30,
                remote_url=remote_url,
                sync_key=sync_key,
                logs=initial_log,
                created_at=now_dt,
                updated_at=now_dt
            )
            db.add(job)
        db.commit()
        return get_batch_job(batch_id)


def append_batch_log(batch_id: str, message: str, level: str = "info") -> None:
    """배치 작업에 실시간 로그 항목을 추가합니다."""
    with SessionLocal() as db:
        job = db.query(BatchJob).filter(BatchJob.id == batch_id).first()
        if not job:
            return
        now_str = datetime.now().isoformat()
        try:
            log_list = json.loads(job.logs) if job.logs else []
        except:
            log_list = []
            
        log_list.append({
            "timestamp": now_str,
            "message": str(message),
            "level": level
        })
        # 최대 최근 300개 로그 유지
        if len(log_list) > 300:
            log_list = log_list[-300:]
            
        job.logs = json.dumps(log_list, ensure_ascii=False)
        job.updated_at = datetime.now(timezone.utc)
        db.commit()

def update_batch_job_status(batch_id: str, status: str = None, total: int = None, completed: int = None, failed: int = None, skipped: int = None, error: str = None, title: str = None) -> None:
    with SessionLocal() as db:
        job = db.query(BatchJob).filter(BatchJob.id == batch_id).first()
        if not job:
            return
        if status is not None:
            job.status = status
        if total is not None:
            job.total_videos = total
        if completed is not None:
            job.completed_videos = completed
        if failed is not None:
            job.failed_videos = failed
        if skipped is not None:
            job.skipped_videos = skipped
        if error is not None:
            job.error = error
        if title is not None:
            job.title = title
        job.updated_at = datetime.now(timezone.utc)
        db.commit()

def update_batch_job_sync(batch_id: str, sync_status: str, sync_error: str = None) -> None:
    with SessionLocal() as db:
        job = db.query(BatchJob).filter(BatchJob.id == batch_id).first()
        if not job:
            return
        job.sync_status = sync_status
        job.sync_error = sync_error
        job.updated_at = datetime.now(timezone.utc)
        db.commit()

def get_batch_job(batch_id: str) -> Optional[dict]:
    with SessionLocal() as db:
        job = db.query(BatchJob).filter(BatchJob.id == batch_id).first()
        if not job:
            return None
            
        try:
            log_list = json.loads(job.logs) if job.logs else []
        except:
            log_list = []
            
        return {
            "id": job.id,
            "url": job.url,
            "title": job.title,
            "total_videos": job.total_videos or 0,
            "completed_videos": job.completed_videos or 0,
            "failed_videos": job.failed_videos or 0,
            "skipped_videos": job.skipped_videos or 0,
            "status": job.status or "pending",
            "sync_status": job.sync_status or "idle",
            "sync_error": job.sync_error,
            "provider": job.provider,
            "force_refresh": bool(job.force_refresh),
            "exclude_shorts": bool(job.exclude_shorts),
            "max_limit": job.max_limit or 30,
            "remote_url": job.remote_url,
            "sync_key": job.sync_key,
            "error": job.error,
            "logs": log_list,
            "created_at": _format_datetime(job.created_at),
            "updated_at": _format_datetime(job.updated_at)
        }

def get_all_batch_jobs() -> List[dict]:

    with SessionLocal() as db:
        jobs = db.query(BatchJob).order_by(BatchJob.created_at.desc()).all()
        result = []
        for job in jobs:
            result.append({
                "id": job.id,
                "url": job.url,
                "title": job.title,
                "total_videos": job.total_videos or 0,
                "completed_videos": job.completed_videos or 0,
                "failed_videos": job.failed_videos or 0,
                "skipped_videos": job.skipped_videos or 0,
                "status": job.status or "pending",
                "sync_status": job.sync_status or "idle",
                "sync_error": job.sync_error,
                "provider": job.provider,
                "force_refresh": bool(job.force_refresh),
                "exclude_shorts": bool(job.exclude_shorts),
                "max_limit": job.max_limit or 30,
                "remote_url": job.remote_url,
                "sync_key": job.sync_key,
                "error": job.error,
                "created_at": _format_datetime(job.created_at),
                "updated_at": _format_datetime(job.updated_at)
            })
        return result

def cancel_batch_job(batch_id: str) -> None:
    with SessionLocal() as db:
        job = db.query(BatchJob).filter(BatchJob.id == batch_id).first()
        if job:
            job.status = "cancelled"
            job.updated_at = datetime.now(timezone.utc)
            db.commit()

def create_batch_video_items(batch_id: str, videos: List[dict]) -> List[dict]:
    with SessionLocal() as db:
        now_dt = datetime.now(timezone.utc)
        items = []
        for v in videos:
            vid = v.get("id") or v.get("video_id") or ""
            item_id = f"{batch_id}_{vid}"
            # Check existing item
            existing = db.query(BatchVideoItem).filter(BatchVideoItem.id == item_id).first()
            if not existing:
                item = BatchVideoItem(
                    id=item_id,
                    batch_job_id=batch_id,
                    video_id=vid,
                    url=v.get("url") or f"https://www.youtube.com/watch?v={vid}",
                    title=v.get("title") or "",
                    duration=str(v.get("duration") or ""),
                    status="pending",
                    error=None,
                    sync_status="pending",
                    presets_generated=0,
                    created_at=now_dt,
                    updated_at=now_dt
                )
                db.add(item)
        db.commit()
    return get_batch_video_items(batch_id)

def update_batch_video_item(item_id: str, status: str = None, error: str = None, presets_generated: int = None, sync_status: str = None) -> None:
    with SessionLocal() as db:
        item = db.query(BatchVideoItem).filter(BatchVideoItem.id == item_id).first()
        if not item:
            return
        if status is not None:
            item.status = status
        if error is not None:
            item.error = error
        if presets_generated is not None:
            item.presets_generated = presets_generated
        if sync_status is not None:
            item.sync_status = sync_status
        item.updated_at = datetime.now(timezone.utc)
        db.commit()

def get_batch_video_items(batch_id: str) -> List[dict]:
    with SessionLocal() as db:
        items = db.query(BatchVideoItem).filter(BatchVideoItem.batch_job_id == batch_id).order_by(BatchVideoItem.created_at.asc(), BatchVideoItem.id.asc()).all()
        result = []

        for item in items:
            result.append({
                "id": item.id,
                "batch_job_id": item.batch_job_id,
                "video_id": item.video_id,
                "url": item.url,
                "title": item.title or "",
                "duration": item.duration or "",
                "status": item.status or "pending",
                "error": item.error,
                "sync_status": item.sync_status or "pending",
                "presets_generated": item.presets_generated or 0,
                "created_at": _format_datetime(item.created_at),
                "updated_at": _format_datetime(item.updated_at)
            })
        return result

def get_all_presets_for_video(video_url: str) -> List[dict]:
    """해당 비디오 URL에 대해 생성되어 저장된 모든 프리셋 가이드 목록을 반환합니다."""
    if not video_url:
        return []
        
    with SessionLocal() as db:
        from backend.services.video import extract_video_id
        target_vid = extract_video_id(video_url) if video_url else ""
        
        # DB 레벨 필터링: video_id 인덱스 컬럼 또는 완전 일치 url을 사용하여 와일드카드 주입 및 풀스캔 방지
        if target_vid:
            guides = db.query(StudyGuide).filter(
                or_(StudyGuide.video_id == target_vid, StudyGuide.url == video_url)
            ).all()
        else:
            guides = db.query(StudyGuide).filter(StudyGuide.url == video_url).all()
            
        matched = []
        for g in guides:
            g_vid = extract_video_id(g.url or "")
            if (target_vid and g_vid == target_vid) or (g.url == video_url):
                try:
                    doc = json.loads(g.document) if g.document else {}
                except:
                    doc = {}
                matched.append({
                    "id": g.id,
                    "url": g.url,
                    "title": g.title,
                    "image_url": g.image_url,
                    "provider": g.provider,
                    "document": doc,
                    "learning_profile": g.learning_profile,
                    "profile_message": g.profile_message,
                    "generation_time_sec": g.generation_time_sec,
                    "length_preset": g.length_preset,
                    "analogy_preset": g.analogy_preset,
                    "video_duration": g.video_duration,
                    "notes": g.notes,
                    "created_at": _format_datetime(g.created_at)
                })
        return matched

def upsert_study_guide_from_sync(guide_data: dict) -> bool:
    """운영 서버에서 동기화 요청을 받아 StudyGuide를 생성 또는 갱신(Upsert)합니다."""
    if not guide_data or not isinstance(guide_data, dict):
        return False
    
    guide_id = guide_data.get("id")
    if not guide_id:
        return False
        
    with SessionLocal() as db:
        doc = guide_data.get("document", {})
        doc_json = json.dumps(doc, ensure_ascii=False) if isinstance(doc, (dict, list)) else str(doc)
        
        notes = guide_data.get("notes", "[]")
        notes_json = json.dumps(notes, ensure_ascii=False) if isinstance(notes, list) else str(notes)
        
        profile = guide_data.get("learning_profile")
        profile_str = json.dumps(profile, ensure_ascii=False) if isinstance(profile, (dict, list)) else (str(profile) if profile else None)

        existing = db.query(StudyGuide).filter(StudyGuide.id == guide_id).first()
        if existing:
            existing.url = guide_data.get("url") or existing.url
            existing.title = guide_data.get("title") or existing.title
            existing.image_url = guide_data.get("image_url") or existing.image_url
            existing.provider = guide_data.get("provider") or existing.provider
            existing.document = doc_json
            existing.learning_profile = profile_str
            existing.profile_message = guide_data.get("profile_message")
            existing.generation_time_sec = guide_data.get("generation_time_sec")
            existing.length_preset = guide_data.get("length_preset")
            existing.analogy_preset = guide_data.get("analogy_preset")
            existing.video_duration = guide_data.get("video_duration")
            existing.notes = notes_json
        else:
            new_guide = StudyGuide(
                id=guide_id,
                url=guide_data.get("url") or "",
                title=guide_data.get("title") or "",
                image_url=guide_data.get("image_url") or "",
                provider=guide_data.get("provider") or "",
                document=doc_json,
                learning_profile=profile_str,
                profile_message=guide_data.get("profile_message"),
                generation_time_sec=guide_data.get("generation_time_sec"),
                length_preset=guide_data.get("length_preset"),
                analogy_preset=guide_data.get("analogy_preset"),
                video_duration=guide_data.get("video_duration"),
                notes=notes_json,
                created_at=_parse_datetime(guide_data.get("created_at"))
            )
            db.add(new_guide)
        db.commit()
        return True

