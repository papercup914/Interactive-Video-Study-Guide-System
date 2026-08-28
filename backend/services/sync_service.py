import os
import json
import asyncio
import httpx
from typing import Dict, List, Any, Optional

from backend.services.job_manager import (
    get_batch_job,
    get_batch_video_items,
    get_all_presets_for_video,
    update_batch_job_sync,
    update_batch_video_item
)

async def sync_batch_to_remote_server(
    batch_id: str,
    remote_url: Optional[str] = None,
    sync_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    배치에서 생성된 모든 StudyGuide 프리셋 데이터를 운영 서버(AWS)로 전송(동기화)합니다.
    """
    target_url = (remote_url or os.getenv("PROD_BACKEND_URL") or "").strip().rstrip("/")
    target_key = (sync_key or os.getenv("ADMIN_SYNC_SECRET") or "").strip()
    
    if not target_url:
        print(f"[Sync] PROD_BACKEND_URL is not set. Skipping remote synchronization.")
        update_batch_job_sync(batch_id, sync_status="idle")
        return {"status": "skipped", "message": "PROD_BACKEND_URL이 설정되지 않아 로컬 저장을 유지합니다."}
        
    if not target_key:
        err = "ADMIN_SYNC_SECRET(동기화 시크릿 키)가 설정되지 않았습니다."
        print(f"[Sync Error] {err}")
        update_batch_job_sync(batch_id, sync_status="failed", sync_error=err)
        return {"status": "failed", "error": err}
        
    update_batch_job_sync(batch_id, sync_status="syncing")
    
    items = get_batch_video_items(batch_id)
    if not items:
        update_batch_job_sync(batch_id, sync_status="synced")
        return {"status": "synced", "synced_count": 0}
        
    endpoint = f"{target_url}/api/admin/sync-guide"
    headers = {
        "Content-Type": "application/json",
        "X-Admin-Sync-Key": target_key
    }
    
    total_synced_guides = 0
    failed_items = 0
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        # 먼저 엔드포인트 가용성 1회 사전 핑(Health / Endpoint Check)
        endpoint_available = True
        
        for item in items:
            if item.get("status") not in ("completed", "skipped"):
                continue
                
            video_url = item["url"]
            presets = get_all_presets_for_video(video_url)
            if not presets:
                continue
                
            payload = {
                "batch_id": batch_id,
                "video_id": item["video_id"],
                "video_url": video_url,
                "guides": presets
            }
            
            success = False
            last_error = ""
            for attempt in range(1, 4):
                try:
                    res = await client.post(endpoint, json=payload, headers=headers)
                    if res.status_code == 200:
                        success = True
                        total_synced_guides += len(presets)
                        break
                    elif res.status_code == 404:
                        last_error = "HTTP 404 Not Found (운영 서버에 /api/admin/sync-guide 엔드포인트가 배포되지 않음)"
                        endpoint_available = False
                        break # 404는 재시도하지 않음
                    elif res.status_code == 403:
                        last_error = "HTTP 403 Forbidden (동기화 시크릿 키가 운영 서버와 일치하지 않음)"
                        endpoint_available = False
                        break # 403은 재시도하지 않음
                    else:
                        last_error = f"HTTP {res.status_code}: {res.text}"
                except Exception as req_e:
                    last_error = f"연결 실패: {str(req_e)}"
                    
                if attempt < 3 and endpoint_available:
                    await asyncio.sleep(2)
                    
            if success:
                update_batch_video_item(item["id"], sync_status="synced")
            else:
                failed_items += 1
                update_batch_video_item(item["id"], sync_status="failed", error=f"Sync Error: {last_error}")
                # 엔드포인트 미배포(404) 또는 키 불일치(403) 시 나머지 비디오 반복 생략(Fast Fail)
                if not endpoint_available:
                    break
                
    if failed_items > 0:
        err_summary = f"{last_error} (성공: {total_synced_guides}개 가이드)"
        update_batch_job_sync(batch_id, sync_status="failed", sync_error=err_summary)
        return {"status": "failed", "synced_count": total_synced_guides, "error": err_summary}
    else:
        update_batch_job_sync(batch_id, sync_status="synced")
        return {"status": "synced", "synced_count": total_synced_guides}
