import json
import os
import uuid
import traceback
from datetime import datetime
import time
import shutil

from fastapi import APIRouter, BackgroundTasks, HTTPException, File, Form, UploadFile
from pydantic import BaseModel
from typing import Optional, List
import asyncio

from backend.services.job_manager import create_job, update_job_status, finish_job, fail_job, get_job, cancel_job
from backend.services.job_manager import save_study_guide, get_all_study_guides, delete_study_guide
from backend.services.video import extract_video_id

# Import Celery task
from backend.services.tasks import celery_generate_guide_task

router = APIRouter()

class GuideRequest(BaseModel):
    url: str
    provider: str
    length_preset: str = "아주 상세하게"
    analogy_preset: str = "풍부한 비유"
    learner_profile: str = ""
    pdf_parsing_method: str = "basic"
    force_refresh: bool = False

@router.post("/start")
async def start_guide_generation(
    url: str = Form(""),
    files: List[UploadFile] = File(None),
    provider: str = Form(""),
    length_preset: str = Form("아주 상세하게"),
    analogy_preset: str = Form("풍부한 비유"),
    learner_profile: str = Form(""),
    pdf_parsing_method: str = Form("basic"),
    force_refresh: str = Form("false")
):
    job_id = f"job_{uuid.uuid4().hex}"
    create_job(job_id)
    
    file_paths = []
    if files:
        os.makedirs("backend/tmp", exist_ok=True)
        for f in files:
            if f and f.filename:
                path = f"backend/tmp/{job_id}_{f.filename}"
                with open(path, "wb") as buffer:
                    shutil.copyfileobj(f.file, buffer)
                file_paths.append(path)
            
    is_force = force_refresh.lower() == "true"
    
    request_data = {
        "url": url,
        "provider": provider,
        "length_preset": length_preset,
        "analogy_preset": analogy_preset,
        "learner_profile": learner_profile,
        "pdf_parsing_method": pdf_parsing_method,
        "force_refresh": is_force
    }
    
    # Launch background task via Celery
    celery_generate_guide_task.delay(job_id, request_data, file_paths)
    return {"job_id": job_id, "status": "processing"}

@router.get("/check")
async def check_existing_guide(url: str):
    vid = extract_video_id(url)
    if not vid:
        return {"exists": False}
        
    guides = get_all_study_guides()
    for row in guides:
        row_vid = extract_video_id(row.get("url", ""))
        if row_vid == vid:
            return {"exists": True, "job_id": row["id"]}
            
    return {"exists": False}

@router.get("/status/{job_id}")
async def check_job_status(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        "job_id": job_id,
        "status": job["status"],
        "progress": job["progress"],
        "error": job.get("error", "")
    }

@router.get("/result/{job_id}")
async def get_job_result(job_id: str):
    from backend.services.job_manager import get_study_guide
    guide = get_study_guide(job_id)
    if guide:
        # Ensure job_id is returned for backwards compatibility
        guide["job_id"] = guide["id"]
        return guide
        
    # If not in history, check active jobs
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail="Job is not completed yet")
    return {
        "job_id": job_id,
        "document": job.get("document", {}),
        "notes": job.get("notes", []),
        "title": job.get("title", "AI 맞춤형 학습 가이드"),
        "image_url": job.get("image_url", "https://images.unsplash.com/photo-1517842645767-c639042777db?q=80&w=800&auto=format&fit=crop"),
        "url": job.get("url", ""),
        "profile_message": job.get("profile_message", "")
    }

@router.delete("/{job_id}")
async def delete_guide_item(job_id: str):
    deleted = delete_study_guide(job_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"status": "success", "message": "Guide deleted successfully"}

@router.post("/{job_id}/cancel")
async def cancel_guide_job(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    cancel_job(job_id)
    return {"status": "success", "message": "Job cancelled successfully"}

@router.get("/history")
def get_history():
    """Returns all history items but without the bulky document content to save bandwidth"""
    history = get_all_study_guides()
    # Strip document content for the list view
    summary_history = []
    for item in history:
        summary_item = {
            "id": item["id"],
            "url": item.get("url", ""),
            "title": item.get("title", "Unknown Title"),
            "image_url": item.get("image_url", "https://images.unsplash.com/photo-1517842645767-c639042777db?q=80&w=800&auto=format&fit=crop"),
            "date": item.get("date", ""),
            "provider": item.get("provider", ""),
            "learning_profile": item.get("learning_profile"),
            "chapter_count": len(item.get("document", {})),
            "length_preset": item.get("length_preset"),
            "analogy_preset": item.get("analogy_preset"),
            "generation_time_sec": item.get("generation_time_sec"),
            "video_duration": item.get("video_duration")
        }
        summary_history.append(summary_item)
    return summary_history

class AskRequest(BaseModel):
    selected_text: str
    context: str
    question: str
    provider: str
    learner_profile: str = ""

@router.post("/ask")
async def ask_question(request: AskRequest):
    from backend.services.llm import generate_answer
    try:
        loop = asyncio.get_event_loop()
        answer = await loop.run_in_executor(None, generate_answer, request.selected_text, request.context, request.question, request.provider, request.learner_profile)
        return {"answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class UpdateDocumentRequest(BaseModel):
    document: dict
    notes: list = []

def process_latest_note_evaluation(job_id: str, latest_note: dict):
    # Evaluation feature disabled (Option B Rollback)
    pass

@router.put("/update/{job_id}")
async def update_document(job_id: str, request: UpdateDocumentRequest, background_tasks: BackgroundTasks):
    from backend.services.job_manager import update_study_guide_notes
    
    updated = update_study_guide_notes(job_id, request.document, request.notes)
            
    if not updated:
        job = get_job(job_id)
        if job and job["status"] == "completed":
            # For in-memory jobs not yet persisted, we can't easily update via DB
            pass
        else:
            raise HTTPException(status_code=404, detail="Job history not found")
        
    if request.notes:
        background_tasks.add_task(process_latest_note_evaluation, job_id, request.notes[-1])
        
    return {"status": "success"}
