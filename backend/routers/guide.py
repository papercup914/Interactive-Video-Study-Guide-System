import json
import os

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
import asyncio
import uuid
import traceback
from datetime import datetime
import time

from backend.services.job_manager import create_job, update_job_status, finish_job, fail_job, get_job, cancel_job
from backend.services.video import download_audio, get_video_title
from backend.services.llm import process_audio, generate_outline, async_generate_chapter_content, async_map_reduce_transcript

router = APIRouter()

class GuideRequest(BaseModel):
    url: str
    provider: str
    length_preset: str = "아주 상세하게"
    analogy_preset: str = "풍부한 비유"
    learner_profile: str = ""
    pdf_parsing_method: str = "basic"

# History storage handling (Simple JSON file for now)
SAVE_FILE = "backend/data/saved_guides.json"

def _load_history():
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                return data.get("history", [])
            except Exception:
                return []
    return []

def _save_to_history(job_id: str, url: str, provider: str, document: dict, title: str, image_url: str, learner_profile: str = "", profile_message: str = "", generation_time_sec: int = 0):
    history = _load_history()
    new_entry = {
        "id": job_id,
        "url": url,
        "title": title,
        "image_url": image_url,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "provider": provider,
        "document": document,
        "notes": [],
        "learning_profile": learner_profile,
        "profile_message": profile_message,
        "generation_time_sec": generation_time_sec
    }
    history.insert(0, new_entry)
    
    os.makedirs(os.path.dirname(SAVE_FILE), exist_ok=True)
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump({"history": history}, f, ensure_ascii=False, indent=2)

def _delete_from_history(job_id: str):
    history = _load_history()
    new_history = [item for item in history if item["id"] != job_id]
    
    if len(history) == len(new_history):
        return False # Not found
        
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump({"history": new_history}, f, ensure_ascii=False, indent=2)
    return True

from backend.services.video import download_audio, get_video_title, get_youtube_transcript, get_url_hash
import tempfile
import shutil

async def _generate_guide_task(job_id: str, request: GuideRequest, file_path: str = None):
    start_time = time.time()
    try:
        loop = asyncio.get_event_loop()
        
        # Determine source type and extract text
        is_document = False
        
        if file_path:
            if request.pdf_parsing_method == "option_c":
                request.provider = "Google Gemini"
                update_job_status(job_id, "transcribing", "Gemini 3.6 Flash로 PDF 원본 분석 중...")
                from backend.services.source import upload_pdf_to_gemini
                transcript = await loop.run_in_executor(None, upload_pdf_to_gemini, file_path)
            elif request.pdf_parsing_method == "option_b":
                update_job_status(job_id, "transcribing", "PDF 텍스트 마크다운 추출 중 (pymupdf4llm)...")
                from backend.services.source import extract_text_with_pymupdf4llm
                transcript = await loop.run_in_executor(None, extract_text_with_pymupdf4llm, file_path)
            else:
                update_job_status(job_id, "transcribing", "PDF 텍스트 추출 중 (PyMuPDF)...")
                from backend.services.source import extract_text_from_pdf
                transcript = await loop.run_in_executor(None, extract_text_from_pdf, file_path)
            
            url_hash = job_id
            raw_title = os.path.basename(file_path)
            if raw_title.startswith(f"{job_id}_"):
                raw_title = raw_title[len(f"{job_id}_"):]
            is_document = True
        elif "youtube.com" in request.url or "youtu.be" in request.url:
            update_job_status(job_id, "transcribing", "유튜브 자막 및 오디오 추출 중...")
            transcript = await loop.run_in_executor(None, get_youtube_transcript, request.url)
            url_hash = get_url_hash(request.url) if transcript else None
            
            if not transcript:
                update_job_status(job_id, "downloading_audio", "자막 없음. 오디오 다운로드 중...")
                audio_path = await loop.run_in_executor(None, download_audio, request.url)
                update_job_status(job_id, "transcribing", "오디오 텍스트 변환(Whisper) 중...")
                transcript = await loop.run_in_executor(None, process_audio, audio_path, request.provider)
                url_hash = os.path.splitext(os.path.basename(audio_path))[0]
            raw_title = get_video_title(request.url)
        else:
            update_job_status(job_id, "transcribing", "웹 페이지 텍스트 추출 중 (Jina Reader)...")
            from backend.services.source import extract_text_from_web
            transcript, raw_title = await loop.run_in_executor(None, extract_text_from_web, request.url)
            import hashlib
            url_hash = hashlib.md5(request.url.encode()).hexdigest()
            is_document = True
            
        if is_document:
            request.length_preset = "문서 원본 번역"
        else:
            if request.length_preset == "Auto" or request.analogy_preset == "Auto":
                update_job_status(job_id, "analyzing_context", "AI가 영상 성격을 분석하여 최적의 톤과 분량을 계산 중...")
                from backend.services.llm import profile_content
                profile_result = await loop.run_in_executor(None, profile_content, transcript, request.provider)
                
                if request.length_preset == "Auto":
                    request.length_preset = profile_result.get("length_preset", "적당한 설명")
                if request.analogy_preset == "Auto":
                    request.analogy_preset = profile_result.get("analogy_preset", "적절한 비유 추가")
                
                job = get_job(job_id)
                if job:
                    job["profile_message"] = profile_result.get("profile_message", "")
            
        if not is_document:
            update_job_status(job_id, "mapping_reduce", "원본 영상 분석 및 병렬 마스터 요약 생성 중...")
            master_summary = await async_map_reduce_transcript(transcript, request.provider, url_hash)
        else:
            master_summary = transcript
            
        update_job_status(job_id, "generating_outline", "목차 구조 설계 중...")
        sections = await loop.run_in_executor(None, generate_outline, master_summary, request.provider, url_hash, request.length_preset)
        
        document = {}
        total_sections = len(sections)
        
        # Concurrency limit setup based on job size to prevent Rate Limits
        # Map-Reduce 도입으로 컨텍스트가 가벼워졌으므로 동시성을 10개로 대폭 상향
        concurrency_limit = 10
        semaphore = asyncio.Semaphore(concurrency_limit)
        
        async def process_section(idx: int, section_title: str):
            async with semaphore:
                job = get_job(job_id)
                if job and job.get("status") == "cancelled":
                    return
                update_job_status(job_id, "generating_chapters", f"[{idx+1}/{total_sections}] 챕터 생성 중...")
                content = await async_generate_chapter_content(
                    section_title, master_summary, request.provider, idx, total_sections, 
                    request.length_preset, request.analogy_preset, request.learner_profile, url_hash
                )
                if content:
                    document[section_title] = content
                
        # Run all sections concurrently with limit
        tasks = [process_section(i, section) for i, section in enumerate(sections)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle complete failures for specific sections
        for i, res in enumerate(results):
            if isinstance(res, Exception):
                print(f"Warning: Section {i+1} failed completely despite retries: {res}")
                section_title = sections[i]
                error_detail = str(res)
                document[section_title] = f"> [!WARNING]\n> 챕터 생성 중 내부 에러가 발생했습니다.\n> 에러 원인: `{error_detail}`\n\n추후 서버를 재시작하거나 설정(.env)을 확인한 뒤 다시 시도해주세요."
        
        job = get_job(job_id)
        if job and job.get("status") == "cancelled":
            print(f"Job {job_id} cancelled.")
            return

        
        if not file_path:
            # Get and translate title for URL based sources
            from backend.services.llm import translate_title
            translated_title = await asyncio.get_event_loop().run_in_executor(None, translate_title, raw_title, request.provider)
        else:
            translated_title = raw_title
        
        update_job_status(job_id, "generating_chapters", "마무리 중...")

        # Job complete
        update_job_status(job_id, "completed", "생성 완료!")
        finish_job(job_id, document, request.url, translated_title)
        
        # Save to history
        generation_time_sec = int(time.time() - start_time)
        pm = job.get("profile_message", "") if job else ""
        _save_to_history(job_id, request.url, request.provider, document, translated_title, "", request.learner_profile, pm, generation_time_sec)
        
    except Exception as e:
        error_msg = f"{str(e)}\n{traceback.format_exc()}"
        print(f"Job {job_id} failed with error: {error_msg}")
        fail_job(job_id, error_msg)

from fastapi import File, Form, UploadFile
from typing import Optional

@router.post("/start")
async def start_guide_generation(
    background_tasks: BackgroundTasks,
    url: str = Form(""),
    file: Optional[UploadFile] = File(None),
    provider: str = Form(""),
    length_preset: str = Form("아주 상세하게"),
    analogy_preset: str = Form("풍부한 비유"),
    learner_profile: str = Form(""),
    pdf_parsing_method: str = Form("basic")
):
    job_id = f"job_{uuid.uuid4().hex}"
    create_job(job_id)
    
    file_path = None
    if file and file.filename:
        os.makedirs("backend/tmp", exist_ok=True)
        file_path = f"backend/tmp/{job_id}_{file.filename}"
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
    request = GuideRequest(
        url=url,
        provider=provider,
        length_preset=length_preset,
        analogy_preset=analogy_preset,
        learner_profile=learner_profile,
        pdf_parsing_method=pdf_parsing_method
    )
    
    background_tasks.add_task(_generate_guide_task, job_id, request, file_path)
    return {"job_id": job_id, "status": "processing"}

@router.get("/status/{job_id}")
async def check_job_status(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        "job_id": job_id,
        "status": job["status"],
        "progress": job["progress"]
    }

@router.get("/result/{job_id}")
async def get_job_result(job_id: str):
    job = get_job(job_id)
    if not job:
        # Check if it's in history instead
        history = _load_history()
        for entry in history:
            if entry["id"] == job_id:
                return {
                    "job_id": job_id, 
                    "document": entry["document"], 
                    "notes": entry.get("notes", []),
                    "title": entry.get("title", "AI 맞춤형 학습 가이드"),
                    "image_url": entry.get("image_url", "https://images.unsplash.com/photo-1517842645767-c639042777db?q=80&w=800&auto=format&fit=crop"),
                    "url": entry.get("url", ""),
                    "profile_message": entry.get("profile_message", "")
                }
        raise HTTPException(status_code=404, detail="Job not found")
        
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail="Job is not completed yet")
    return {
        "job_id": job_id,
        "document": job["document"],
        "notes": job.get("notes", []),
        "title": job.get("title", "AI 맞춤형 학습 가이드"),
        "image_url": job.get("image_url", "https://images.unsplash.com/photo-1517842645767-c639042777db?q=80&w=800&auto=format&fit=crop"),
        "url": job.get("url", ""),
        "profile_message": job.get("profile_message", "")
    }

@router.delete("/{job_id}")
async def delete_guide(job_id: str):
    deleted = _delete_from_history(job_id)
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
async def get_history():
    """Returns all history items but without the bulky document content to save bandwidth"""
    history = _load_history()
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
            "chapter_count": len(item.get("document", {}))
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
    history = _load_history()
    updated = False
    for item in history:
        if item["id"] == job_id:
            item["document"] = request.document
            item["notes"] = request.notes
            updated = True
            break
            
    if not updated:
        raise HTTPException(status_code=404, detail="Job history not found")
        
    os.makedirs(os.path.dirname(SAVE_FILE), exist_ok=True)
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump({"history": history}, f, ensure_ascii=False, indent=2)
        
    job = get_job(job_id)
    if job and job["status"] == "completed":
        job["document"] = request.document
        job["notes"] = request.notes
        
    # Trigger background evaluation if there are notes
    if request.notes:
        background_tasks.add_task(process_latest_note_evaluation, job_id, request.notes[-1])
        
    return {"status": "success"}


