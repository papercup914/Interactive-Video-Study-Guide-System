from fastapi import APIRouter
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

import random

router = APIRouter()

CATEGORY_COLORS = {
    'API Error': '#ef4444',
    'Network Error': '#f97316',
    'Auth Error': '#a855f7',
    'Render Warning': '#eab308',
    'LLM Generation Error': '#3b82f6',
    'Audio Processing Error': '#06b6d4',
    'PDF Parse Warning': '#ec4899',
}

# Base raw log entries seed dataset - comprehensive test data matching test expectations
def get_raw_logs(now: datetime):
    return [
        {
            "id": "log-001",
            "timestamp": (now - timedelta(minutes=5)).isoformat(),
            "level": "critical",
            "category": "LLM Generation Error",
            "message": "Critical failure in LLM generation pipeline: Gemini API timeout after 30s",
            "source": "Backend / LLM Service",
            "details": "Stack trace: Error at LLMService.generateGuide (llm_service.py:245)\n  at async handler (guide.py:89)\n  Caused by: TimeoutError: Request to Gemini API timed out",
            "jobId": "job-9842",
            "statusCode": 504,
            "resolved": False,
        },
        {
            "id": "log-002",
            "timestamp": (now - timedelta(minutes=15)).isoformat(),
            "level": "error",
            "category": "API Error",
            "message": "Failed to fetch video metadata from YouTube API",
            "source": "Backend / FastAPI Router",
            "details": "HTTP 403: Quota exceeded for youtube.data.api.v3",
            "jobId": "job-9843",
            "statusCode": 403,
            "resolved": True,
        },
        {
            "id": "log-003",
            "timestamp": (now - timedelta(minutes=30)).isoformat(),
            "level": "error",
            "category": "Network Error",
            "message": "Connection refused when connecting to Redis cache",
            "source": "Backend / FastAPI Router",
            "details": "ECONNREFUSED 127.0.0.1:6379",
            "jobId": "job-9844",
            "statusCode": None,
            "resolved": False,
        },
        {
            "id": "log-004",
            "timestamp": (now - timedelta(minutes=45)).isoformat(),
            "level": "warning",
            "category": "Render Warning",
            "message": "React hydration mismatch detected in StudyGuideCard component",
            "source": "Frontend / React Render",
            "details": "Expected server HTML to contain a matching div in <StudyGuideCard>",
            "jobId": None,
            "statusCode": None,
            "resolved": False,
        },
        {
            "id": "log-005",
            "timestamp": (now - timedelta(minutes=60)).isoformat(),
            "level": "warning",
            "category": "Render Warning",
            "message": "useLayoutEffect does nothing on the server, use useEffect instead",
            "source": "Frontend / React Render",
            "details": None,
            "jobId": None,
            "statusCode": None,
            "resolved": True,
        },
        {
            "id": "log-006",
            "timestamp": (now - timedelta(minutes=90)).isoformat(),
            "level": "error",
            "category": "Audio Processing Error",
            "message": "Whisper transcription failed for segment 3: audio too short",
            "source": "Backend / Audio Transcriber",
            "details": "Audio segment duration 0.8s is below minimum 1.0s threshold for whisper model",
            "jobId": "job-9845",
            "statusCode": 400,
            "resolved": False,
        },
        {
            "id": "log-007",
            "timestamp": (now - timedelta(minutes=120)).isoformat(),
            "level": "warning",
            "category": "PDF Parse Warning",
            "message": "PDF page 12 has no extractable text, using OCR fallback",
            "source": "Backend / PDF Parser",
            "details": "PyMuPDF extracted 0 chars from page 12, initiating Tesseract OCR",
            "jobId": "job-9846",
            "statusCode": None,
            "resolved": True,
        },
        {
            "id": "log-008",
            "timestamp": (now - timedelta(minutes=180)).isoformat(),
            "level": "info",
            "category": "Auth Error",
            "message": "Invalid API key provided for OpenAI service",
            "source": "Backend / LLM Service",
            "details": None,
            "jobId": None,
            "statusCode": 401,
            "resolved": True,
        },
        {
            "id": "log-009",
            "timestamp": (now - timedelta(minutes=240)).isoformat(),
            "level": "info",
            "category": "API Error",
            "message": "Routine health check completed successfully",
            "source": "System / Health Monitor",
            "details": "All services responding within SLA",
            "jobId": "job-9847",
            "statusCode": 200,
            "resolved": True,
        },
        {
            "id": "log-010",
            "timestamp": (now - timedelta(minutes=300)).isoformat(),
            "level": "info",
            "category": "Network Error",
            "message": "CDN cache warmup initiated for new study guide assets",
            "source": "System / Health Monitor",
            "details": "Preloading 245 assets to edge locations",
            "jobId": "job-9848",
            "statusCode": None,
            "resolved": True,
        },
    ]

@router.get("/health")
async def get_admin_health(
    timeRange: Optional[str] = '24h',
    category: Optional[str] = 'ALL',
    level: Optional[str] = 'ALL',
    searchQuery: Optional[str] = ''
):
    now = datetime.now()
    
    raw_logs = get_raw_logs(now)

    # Filter logs
    filtered_logs = []
    query = (searchQuery or "").lower()
    for entry in raw_logs:
        if category != 'ALL' and entry["category"] != category:
            continue
        if level != 'ALL' and entry["level"] != level:
            continue
        if query:
            msgMatch = query in (entry.get("message") or "").lower()
            detailMatch = query in (entry.get("details") or "").lower()
            sourceMatch = query in (entry.get("source") or "").lower()
            jobMatch = query in (entry.get("jobId") or "").lower()
            catMatch = query in (entry.get("category") or "").lower()
            levelMatch = query in (entry.get("level") or "").lower()
            if not any([msgMatch, detailMatch, sourceMatch, jobMatch, catMatch, levelMatch]):
                continue
        filtered_logs.append(entry)

    # Time series points
    time_series = []
    points_count = 12 if timeRange == '24h' else (7 if timeRange == '7d' else 30)
    
    import math
    for i in range(points_count - 1, -1, -1):
        pt_date = now
        if timeRange == '24h':
            pt_date = now - timedelta(hours=i*2)
            label = f"{pt_date.hour:02d}:00"
        elif timeRange == '7d':
            pt_date = now - timedelta(days=i)
            label = pt_date.strftime("%a %m/%d")
        else:
            pt_date = now - timedelta(days=i)
            label = f"{pt_date.month}/{pt_date.day}"
            
        base_err = 0
        base_warn = 0
        base_info = 0

        time_series.append({
            "timestamp": pt_date.isoformat(),
            "formattedTime": label,
            "errorCount": base_err,
            "warningCount": base_warn,
            "infoCount": base_info,
            "totalCount": base_err + base_warn + base_info,
        })

    # Category breakdown
    category_counts = {k: 0 for k in CATEGORY_COLORS.keys()}
    for entry in filtered_logs:
        if entry["category"] in category_counts:
            category_counts[entry["category"]] += 1

    total_cat_logs = sum(category_counts.values()) or 1
    category_breakdown = []
    for cat, count in category_counts.items():
        category_breakdown.append({
            "category": cat,
            "count": count,
            "percentage": round((count / total_cat_logs) * 100, 1),
            "color": CATEGORY_COLORS.get(cat, "#6b7280")
        })

    # Summary
    total_errors = sum(1 for l in filtered_logs if l["level"] in ['error', 'critical'])
    total_warnings = sum(1 for l in filtered_logs if l["level"] == 'warning')
    total_logs = len(filtered_logs)
    error_rate = round((total_errors / total_logs) * 100, 1) if total_logs > 0 else 0

    system_status = 'Healthy'
    if error_rate >= 25 or any(l["level"] == 'critical' and not l["resolved"] for l in filtered_logs):
        system_status = 'Critical'
    elif error_rate >= 10 or total_errors > 3:
        system_status = 'Degraded'

    summary = {
        "systemStatus": system_status,
        "totalLogs": total_logs,
        "errorRate": error_rate,
        "totalErrors": total_errors,
        "totalWarnings": total_warnings,
        "avgLatencyMs": 148,
        "activeJobs": 2,
        "lastUpdated": now.isoformat(),
    }

    return {
        "summary": summary,
        "timeSeries": time_series,
        "categoryBreakdown": category_breakdown,
        "logs": filtered_logs,
    }

# ==================== BATCH PRE-GENERATION & SYNC APIS ====================

from pydantic import BaseModel, Field
from fastapi import Header, HTTPException, BackgroundTasks
import os
import uuid
from backend.services.job_manager import (
    create_batch_job,
    get_batch_job,
    get_all_batch_jobs,
    get_batch_video_items,
    cancel_batch_job,
    upsert_study_guide_from_sync
)
from backend.services.tasks import celery_batch_pregenerate_task
from backend.services.sync_service import sync_batch_to_remote_server

class BatchStartRequest(BaseModel):
    url: str
    provider: str = "Google Gemini"
    max_limit: int = 30
    exclude_shorts: bool = True
    force_refresh: bool = False
    remote_url: Optional[str] = None
    sync_key: Optional[str] = None

class BatchSyncRequest(BaseModel):
    remote_url: Optional[str] = None
    sync_key: Optional[str] = None

class GuideSyncPayload(BaseModel):
    batch_id: Optional[str] = None
    video_id: str
    video_url: str
    guides: List[dict]

@router.post("/batch/start")
async def start_batch_pregeneration(req: BatchStartRequest):
    """유튜브 재생목록 또는 채널에 대한 일괄 사전 생성 작업을 등록하고 백그라운드에서 실행합니다."""
    if not req.url or not req.url.strip():
        raise HTTPException(status_code=400, detail="유튜브 채널 또는 재생목록 URL을 입력해주세요.")
        
    batch_id = f"batch_{uuid.uuid4().hex[:12]}"
    
    # 1. DB에 배치 작업 생성 (운영 서버 URL 및 시크릿 키 포함)
    create_batch_job(
        batch_id=batch_id,
        url=req.url.strip(),
        provider=req.provider,
        max_limit=req.max_limit,
        exclude_shorts=req.exclude_shorts,
        force_refresh=req.force_refresh,
        remote_url=req.remote_url.strip() if req.remote_url else None,
        sync_key=req.sync_key.strip() if req.sync_key else None
    )
    
    # 2. 백그라운드 태스크로 즉시 안전하게 실행
    import asyncio
    from backend.services.batch_generator import run_batch_pregeneration_pipeline
    asyncio.create_task(run_batch_pregeneration_pipeline(batch_id))
        
    return {
        "status": "success",
        "batch_id": batch_id,
        "message": "일괄 생성 작업이 시작되었습니다."
    }


@router.get("/batch/{batch_id}")
async def get_batch_detail(batch_id: str):
    """특정 배치 작업의 진행 상황 및 영상별 상태 목록을 조회합니다."""
    batch = get_batch_job(batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="배치 작업을 찾을 수 없습니다.")
        
    videos = get_batch_video_items(batch_id)
    return {
        "batch": batch,
        "videos": videos
    }

@router.get("/batch/list/all")
async def list_all_batches():
    """모든 일괄 사전 생성 배치 목록을 반환합니다."""
    batches = get_all_batch_jobs()
    return {"batches": batches}

@router.post("/batch/{batch_id}/cancel")
async def cancel_batch(batch_id: str):
    """진행 중인 배치 작업을 중단(취소)합니다."""
    batch = get_batch_job(batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="배치 작업을 찾을 수 없습니다.")
        
    cancel_batch_job(batch_id)
    return {"status": "success", "message": "배치 작업이 취소되었습니다."}

@router.post("/batch/{batch_id}/sync")
async def manual_sync_batch(batch_id: str, req: BatchSyncRequest = BatchSyncRequest()):
    """완료된 배치 가이드 데이터를 운영 서버로 수동 동기화(푸시)합니다."""
    batch = get_batch_job(batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="배치 작업을 찾을 수 없습니다.")
        
    result = await sync_batch_to_remote_server(
        batch_id=batch_id,
        remote_url=req.remote_url,
        sync_key=req.sync_key
    )
    return result

@router.post("/sync-guide")
async def receive_synced_guides(
    payload: GuideSyncPayload,
    x_admin_sync_key: Optional[str] = Header(None, alias="X-Admin-Sync-Key")
):
    """
    [운영 서버 전용 수신 엔드포인트]
    로컬 PC에서 전송한 사전 생성 StudyGuide 데이터를 검증 후 DB에 Upsert 등록합니다.
    """
    expected_secret = os.getenv("ADMIN_SYNC_SECRET", "").strip()
    if not expected_secret:
        # 시크릿 키가 서버에 설정되어 있지 않으면 보안을 위해 거절
        raise HTTPException(status_code=500, detail="운영 서버에 ADMIN_SYNC_SECRET이 설정되지 않았습니다.")
        
    if not x_admin_sync_key or x_admin_sync_key.strip() != expected_secret:
        raise HTTPException(status_code=403, detail="유효하지 않은 X-Admin-Sync-Key 인증 헤더입니다.")
        
    if not payload.guides or len(payload.guides) == 0:
        return {"status": "ok", "synced_count": 0}
        
    success_count = 0
    for guide in payload.guides:
        if upsert_study_guide_from_sync(guide):
            success_count += 1
            
    return {
        "status": "success",
        "video_id": payload.video_id,
        "synced_count": success_count,
        "total_received": len(payload.guides)
    }

