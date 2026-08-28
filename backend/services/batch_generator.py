import asyncio
import os
import time
import uuid
import json
import traceback
from typing import Dict, List, Any, Optional

from backend.services.job_manager import (
    save_study_guide,
    update_batch_video_item,
    update_batch_job_status,
    get_batch_job,
    get_batch_video_items,
    get_all_presets_for_video,
    append_batch_log
)
from backend.services.video import (
    download_audio,
    get_youtube_transcript,
    get_url_hash,
    get_video_metadata,
    extract_video_id
)
from backend.services.llm import (
    process_audio,
    generate_outline,
    async_generate_chapter_content,
    translate_title,
    is_gemini_provider
)

LENGTH_PRESETS = ["핵심 요약", "적당한 설명", "아주 상세하게"]
ANALOGY_PRESETS = ["비유 없이 담백하게", "적절한 비유 추가", "풍부한 비유"]

def get_preset_slug(preset_name: str) -> str:
    """프리셋 명칭을 URL-safe 및 ID-safe 문자열로 변환합니다."""
    mapping = {
        "핵심 요약": "summary",
        "적당한 설명": "normal",
        "아주 상세하게": "detailed",
        "비유 없이 담백하게": "no_analogy",
        "적절한 비유 추가": "moderate_analogy",
        "풍부한 비유": "rich_analogy"
    }
    return mapping.get(preset_name, preset_name.replace(" ", "_"))

async def generate_single_video_9_presets(
    batch_id: str,
    item_id: str,
    video_url: str,
    item_index: int,
    total_items: int,
    provider: str = "Google Gemini",
    force_refresh: bool = False
) -> Dict[str, Any]:
    """
    단일 비디오에 대해 자막/오디오를 1회만 추출하고,
    3x3 (총 9개 프리셋) 가이드를 모두 생성하여 StudyGuide에 저장합니다.
    """
    loop = asyncio.get_event_loop()
    start_time = time.time()
    video_id = extract_video_id(video_url) or "unknown"
    url_hash = get_url_hash(video_url)
    prefix = f"[{item_index}/{total_items}]"
    
    # 0. 중복 검사: force_refresh가 아니고 이미 9개 프리셋이 모두 생성되어 있다면 Skip
    if not force_refresh:
        existing = get_all_presets_for_video(video_url)
        if len(existing) >= 9:
            msg = f"{prefix} 비디오 '{video_id}'는 이미 9개 프리셋이 모두 존재하여 스킵합니다."
            print(f"[Batch] {msg}")
            append_batch_log(batch_id, msg, level="warn")
            update_batch_video_item(item_id, status="skipped", presets_generated=len(existing))
            return {"status": "skipped", "presets_generated": len(existing)}
            
    update_batch_video_item(item_id, status="processing")
    append_batch_log(batch_id, f"{prefix} 비디오 처리 시작: {video_url}", level="info")
    
    try:
        # 1. 메타데이터 및 자막/오디오 1회 추출 (중복 다운로드 방지)
        raw_meta = get_video_metadata(video_url)
        raw_title = raw_meta.get("title") or f"Video {video_id}"
        image_url = raw_meta.get("thumbnail") or f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
        video_duration = raw_meta.get("duration", 0)
        
        append_batch_log(batch_id, f"{prefix} 영상 제목: '{raw_title}' (재생시간: {raw_meta.get('duration_string', str(video_duration))})", level="info")
        
        # 제목 번역/정제 (Gemini / LLM)
        translated_title = raw_title
        if provider:
            try:
                translated_title = await loop.run_in_executor(None, translate_title, raw_title, provider)
            except Exception as e:
                print(f"[Batch] Title translation warning: {e}")
                translated_title = raw_title
                
        # 자막 추출 (1차: 공식/자동자막 -> 2차: Whisper 오디오 추출)
        append_batch_log(batch_id, f"{prefix} 자막 및 오디오 컨텍스트 추출 중...", level="info")
        transcript = await loop.run_in_executor(None, get_youtube_transcript, video_url)
        is_audio_needed = False
        
        if not transcript or len(transcript.strip()) < 100:
            is_audio_needed = True
            
        if is_audio_needed:
            append_batch_log(batch_id, f"{prefix} 자막이 없어 오디오를 다운로드하여 음성 인식을 진행합니다...", level="info")
            res = await loop.run_in_executor(None, download_audio, video_url)
            if isinstance(res, (tuple, list)):
                audio_path = res[0] if len(res) > 0 else ""
                if len(res) > 1 and res[1]:
                    video_duration = res[1]
            else:
                audio_path = res
            context_data = await loop.run_in_executor(None, process_audio, audio_path, provider, url_hash)
            master_summary = context_data
        else:
            master_summary = transcript

            
        if not master_summary or len(master_summary.strip()) < 50:
            raise ValueError(f"비디오 '{raw_title}'의 자막/오디오 컨텍스트를 추출할 수 없습니다.")
            
        append_batch_log(batch_id, f"{prefix} 자막 추출 완료 ({len(master_summary):,}자). 3종 요약 분량 목차 생성 중...", level="info")
            
        # 2. 요약 분량 3종(핵심/적당/상세)에 대한 아웃라인(목차) 생성
        outlines_by_length: Dict[str, List[str]] = {}
        for length_preset in LENGTH_PRESETS:
            sections = await loop.run_in_executor(
                None,
                generate_outline,
                master_summary,
                provider,
                url_hash,
                length_preset,
                force_refresh
            )
            if not sections or len(sections) == 0:
                sections = ["1. 핵심 개념 정리", "2. 상세 내용 분석", "3. 요약 및 결론"]
            outlines_by_length[length_preset] = sections
            
        append_batch_log(batch_id, f"{prefix} 목차 생성 완료. 3×3 = 총 9개 프리셋 가이드 상세 내용 생성 시작...", level="info")
            
        # 3. 3x3 = 9개 프리셋 매트릭스 가이드 생성 및 StudyGuide에 저장
        presets_count = 0
        for length_preset in LENGTH_PRESETS:
            sections = outlines_by_length[length_preset]
            for analogy_preset in ANALOGY_PRESETS:
                # 챕터 생성 작업 병렬 실행
                chapter_tasks = []
                for idx, section in enumerate(sections):
                    task = async_generate_chapter_content(
                        section_title=section,
                        context_data=master_summary,
                        provider=provider,
                        chunk_index=idx,
                        total_chunks=len(sections),
                        length_preset=length_preset,
                        analogy_preset=analogy_preset,
                        learner_profile="",
                        url_hash=url_hash,
                        tutor_persona=None,
                        force_refresh=force_refresh
                    )
                    chapter_tasks.append(task)
                    
                # 챕터 결과 취합
                chapter_contents = await asyncio.gather(*chapter_tasks, return_exceptions=True)
                document = {}
                for idx, section in enumerate(sections):
                    content = chapter_contents[idx]
                    if isinstance(content, Exception):
                        content = f"> ⚠️ 이 섹션 생성 중 오류가 발생했습니다: {str(content)}"
                    document[section] = str(content)
                    
                # 프리셋 고유 ID 생성 (guide_{url_hash}_{length_slug}_{analogy_slug})
                l_slug = get_preset_slug(length_preset)
                a_slug = get_preset_slug(analogy_preset)
                guide_job_id = f"guide_{url_hash}_{l_slug}_{a_slug}"
                
                gen_time_sec = int(time.time() - start_time)
                profile_msg = f"로컬 사전 생성 프리셋 ({length_preset} / {analogy_preset})"
                
                # StudyGuide 테이블에 영속 저장
                save_study_guide(
                    job_id=guide_job_id,
                    url=video_url,
                    title=translated_title,
                    image_url=image_url,
                    provider=provider,
                    document=document,
                    learning_profile="",
                    profile_message=profile_msg,
                    generation_time_sec=gen_time_sec,
                    length_preset=length_preset,
                    analogy_preset=analogy_preset,
                    video_duration=str(video_duration)
                )
                presets_count += 1
                update_batch_video_item(item_id, presets_generated=presets_count)
                append_batch_log(batch_id, f"{prefix} [{presets_count}/9] 프리셋 생성 완료 ({length_preset} × {analogy_preset})", level="info")
                
        update_batch_video_item(item_id, status="completed", presets_generated=presets_count)
        elapsed = int(time.time() - start_time)
        append_batch_log(batch_id, f"{prefix} ✅ '{translated_title}' 9개 프리셋 생성 완료 ({elapsed}초 소요)", level="success")
        return {"status": "completed", "presets_generated": presets_count}
        
    except Exception as e:
        err_str = f"{type(e).__name__}: {str(e)}"
        print(f"[Batch Video Error] {video_url}: {traceback.format_exc()}")
        update_batch_video_item(item_id, status="failed", error=err_str)
        append_batch_log(batch_id, f"{prefix} ❌ 비디오 생성 실패: {err_str}", level="error")
        return {"status": "failed", "error": err_str}

async def run_batch_pregeneration_pipeline(batch_id: str) -> None:
    """배치 작업의 전체 파이프라인을 실행합니다 (수집 ➡️ 9개 프리셋 생성 ➡️ 완료 후 동기화)"""
    from backend.services.batch_collector import collect_videos_from_source
    from backend.services.job_manager import create_batch_video_items
    from backend.services.sync_service import sync_batch_to_remote_server
    
    batch = get_batch_job(batch_id)
    if not batch:
        print(f"[Batch] Batch job {batch_id} not found.")
        return
        
    try:
        update_batch_job_status(batch_id, status="collecting")
        append_batch_log(batch_id, f"🔍 유튜브 URL({batch['url']})에서 영상 메타데이터 수집을 시작합니다...", level="info")
        
        # 1. 영상 목록 수집
        title, videos = collect_videos_from_source(
            url=batch["url"],
            max_limit=batch["max_limit"],
            exclude_shorts=batch["exclude_shorts"]
        )
        
        if not videos:
            msg = f"수집된 비디오가 없습니다. URL을 확인해 주세요: {batch['url']}"
            append_batch_log(batch_id, msg, level="warn")
            update_batch_job_status(batch_id, status="completed", total=0, completed=0, skipped=0, failed=0, title=title)
            return
            
        items = create_batch_video_items(batch_id, videos)
        update_batch_job_status(batch_id, status="processing", total=len(videos), title=title)
        
        append_batch_log(batch_id, f"📋 총 {len(videos)}개의 비디오를 수집하였습니다 (제목: '{title}'). 개별 가이드 생성을 시작합니다.", level="info")
        
        completed_count = 0
        skipped_count = 0
        failed_count = 0
        
        # 2. 비디오별 9개 프리셋 순차 생성 (LLM Rate Limit 방지)
        for idx, item in enumerate(items):
            current_batch = get_batch_job(batch_id)
            if current_batch and current_batch.get("status") == "cancelled":
                append_batch_log(batch_id, "⚠️ 사용자에 의해 작업이 중단(취소)되었습니다.", level="warn")
                print(f"[Batch] Batch {batch_id} was cancelled by user.")
                break
                
            res = await generate_single_video_9_presets(
                batch_id=batch_id,
                item_id=item["id"],
                video_url=item["url"],
                item_index=idx + 1,
                total_items=len(items),
                provider=batch["provider"],
                force_refresh=batch["force_refresh"]
            )
            
            st = res.get("status")
            if st == "completed":
                completed_count += 1
            elif st == "skipped":
                skipped_count += 1
            else:
                failed_count += 1
                
            update_batch_job_status(
                batch_id=batch_id,
                completed=completed_count,
                skipped=skipped_count,
                failed=failed_count
            )
            
            # API Rate Limit 방지를 위한 비디오 간 안전 쿨다운
            if idx < len(items) - 1:
                await asyncio.sleep(2.0)
            
        # 3. 배치 완료 상태 전환
        final_status = "completed"
        update_batch_job_status(batch_id, status=final_status)
        summary_msg = f"🎉 전체 {len(items)}개 비디오 중 {completed_count}개 완료, {skipped_count}개 스킵, {failed_count}개 실패로 일괄 생성이 마무리되었습니다."
        append_batch_log(batch_id, summary_msg, level="success")
        print(f"[Batch {batch_id}] {summary_msg}")
        
        # 4. 100% 완료 후 운영 서버 자동 일괄 동기화 (설정되어 있을 경우)
        try:
            latest_batch = get_batch_job(batch_id) or batch
            append_batch_log(batch_id, "☁️ 운영 서버(AWS) 동기화 확인 중...", level="info")
            sync_res = await sync_batch_to_remote_server(
                batch_id,
                remote_url=latest_batch.get("remote_url"),
                sync_key=latest_batch.get("sync_key")
            )
            if sync_res.get("status") == "synced":
                append_batch_log(batch_id, f"✅ 운영 서버 동기화 완료: 총 {sync_res.get('synced_count', 0)}개 프리셋 전송 완료", level="success")
            elif sync_res.get("status") == "skipped":
                append_batch_log(batch_id, "ℹ️ 운영 서버 URL이 설정되지 않아 로컬 DB에 안전하게 보관을 완료했습니다.", level="info")
            elif sync_res.get("status") == "failed":
                append_batch_log(batch_id, f"⚠️ 운영 서버 동기화 실패: {sync_res.get('error')}", level="warn")

        except Exception as sync_e:
            append_batch_log(batch_id, f"⚠️ 운영 서버 동기화 오류: {str(sync_e)}", level="warn")
            
    except Exception as e:
        err_msg = f"배치 파이프라인 실행 실패: {str(e)}"
        print(f"[Batch Pipeline Error] {traceback.format_exc()}")
        update_batch_job_status(batch_id, status="failed", error=err_msg)
        append_batch_log(batch_id, f"❌ {err_msg}", level="error")
