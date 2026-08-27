import asyncio
import os
import time
import uuid
import traceback
from backend.celery_app import celery_app

# We need to run the async generation function inside a synchronous Celery wrapper
async def async_generate_guide(job_id: str, request_data: dict, file_paths: list = None):
    # This is a port of the old `_generate_guide_task` from guide.py
    from backend.services.job_manager import update_job_status, finish_job, fail_job, get_job, save_study_guide, get_completed_chapters, save_chapter_checkpoint
    from backend.services.video import download_audio, get_youtube_transcript, get_url_hash, get_video_metadata
    from backend.services.llm import process_audio, generate_outline, async_generate_chapter_content, profile_content, translate_title, is_gemini_provider
    from backend.services.source import extract_text_from_pdf, extract_text_from_web
    
    start_time = time.time()
    video_duration = 0
    try:
        loop = asyncio.get_event_loop()
        
        # request_data is a dict because Celery JSON-serializes kwargs
        url = request_data.get("url", "")
        provider = request_data.get("provider", "")
        length_preset = request_data.get("length_preset", "아주 상세하게")
        analogy_preset = request_data.get("analogy_preset", "풍부한 비유")
        learner_profile = request_data.get("learner_profile", "")
        pdf_parsing_method = request_data.get("pdf_parsing_method", "basic")
        force_refresh = request_data.get("force_refresh", False)
        
        is_document = False
        
        if file_paths and len(file_paths) > 0:
            is_document = True
            combined_transcript = ""
            raw_title = ""
            
            for i, path in enumerate(file_paths):
                current_title = os.path.basename(path)
                if current_title.startswith(f"{job_id}_"):
                    current_title = current_title[len(f"{job_id}_"):]
                
                update_job_status(job_id, "transcribing", f"[{i+1}/{len(file_paths)}] {current_title} 텍스트 추출 중...")
                
                if pdf_parsing_method == "option_c":
                    provider = "Google Gemini"
                    from backend.services.source import upload_pdf_to_gemini
                    text = await loop.run_in_executor(None, upload_pdf_to_gemini, path)
                elif pdf_parsing_method == "option_b":
                    from backend.services.source import extract_text_with_pymupdf4llm
                    text = await loop.run_in_executor(None, extract_text_with_pymupdf4llm, path)
                else:
                    text = await loop.run_in_executor(None, extract_text_from_pdf, path)
                
                combined_transcript += f"\n\n# Document {i+1}: {current_title}\n\n" + text
                if i == 0:
                    raw_title = current_title
            
            transcript = combined_transcript
            url_hash = job_id
            if len(file_paths) > 1:
                raw_title = f"{raw_title} 외 {len(file_paths)-1}건"
        elif "youtube.com" in url or "youtu.be" in url:
            update_job_status(job_id, "transcribing", "유튜브 자막 및 오디오 추출 중...")
            transcript = await loop.run_in_executor(None, get_youtube_transcript, url)
            url_hash = get_url_hash(url) if transcript else None
            
            if not transcript:
                update_job_status(job_id, "downloading_audio", "자막 없음. 오디오 다운로드 중...")
                audio_path = await loop.run_in_executor(None, download_audio, url)
                update_job_status(job_id, "transcribing", "오디오 텍스트 변환(Whisper/Gemini) 중...")
                transcript = await loop.run_in_executor(None, process_audio, audio_path, provider)
                url_hash = os.path.splitext(os.path.basename(audio_path))[0]
                
            metadata = await loop.run_in_executor(None, get_video_metadata, url)
            raw_title = metadata["title"]
            video_duration = metadata["duration"]
        else:
            update_job_status(job_id, "transcribing", "웹 페이지 텍스트 추출 중 (Jina Reader)...")
            transcript, raw_title = await loop.run_in_executor(None, extract_text_from_web, url)
            import hashlib
            url_hash = hashlib.md5(url.encode()).hexdigest()
            is_document = True
            
        tutor_persona = None
        if is_document:
            length_preset = "문서 원본 번역"
        else:
            update_job_status(job_id, "analyzing_context", "AI가 영상 성격을 분석하여 최적의 톤과 페르소나를 계산 중...")
            profile_result = await loop.run_in_executor(None, profile_content, transcript, provider)
            
            if length_preset == "Auto":
                length_preset = profile_result.get("length_preset", "적당한 설명")
            if analogy_preset == "Auto":
                analogy_preset = profile_result.get("analogy_preset", "적절한 비유 추가")
            
            tutor_persona = profile_result.get("tutor_persona")
            # Currently we can't easily update the in-memory job dict safely across processes without the DB
            # We'll rely on the final save_study_guide
            
        master_summary = transcript
        
        # 앱 토큰 절감 방안: Gemini Context Caching 도입
        if is_gemini_provider(provider):
            from backend.services.llm import get_gemini_client
            try:
                update_job_status(job_id, "uploading_cache", "Gemini Context Caching을 위해 텍스트 업로드 중...")
                txt_path = f"backend/data/{url_hash}_transcript.txt"
                with open(txt_path, "w", encoding="utf-8") as f:
                    f.write(master_summary)
                
                client = get_gemini_client()
                uploaded_file = client.files.upload(file=txt_path)
                
                # ACTIVE 상태가 될 때까지 폴링 대기
                while uploaded_file.state.name == "PROCESSING":
                    await asyncio.sleep(2)
                    uploaded_file = client.files.get(name=uploaded_file.name)
                    
                if uploaded_file.state.name == "ACTIVE":
                    master_summary = f"GEMINI_FILE_URI::{uploaded_file.name}"
            except Exception as e:
                print(f"Failed to upload transcript for Context Caching: {e}")
            
        update_job_status(job_id, "generating_outline", "목차 구조 설계 중...")
        sections = await loop.run_in_executor(None, generate_outline, master_summary, provider, url_hash, length_preset, force_refresh)
        
        document = {}
        total_sections = len(sections)
        
        completed_chapters = {}
        if not force_refresh:
            completed_chapters = get_completed_chapters(job_id)
        
        concurrency_limit = 10
        semaphore = asyncio.Semaphore(concurrency_limit)
        
        async def process_section(idx: int, section_title: str):
            async with semaphore:
                job = get_job(job_id)
                if job and job.get("status") == "cancelled":
                    return
                
                if section_title in completed_chapters:
                    print(f"[Harness] Checkpoint loaded for {section_title}, skipping API call.")
                    document[section_title] = completed_chapters[section_title]
                    return

                update_job_status(job_id, "generating_chapters", f"[{idx+1}/{total_sections}] 챕터 생성 중...")
                content = await async_generate_chapter_content(
                    section_title, master_summary, provider, idx, total_sections, 
                    length_preset, analogy_preset, learner_profile, url_hash,
                    tutor_persona, force_refresh
                )
                if content:
                    document[section_title] = content
                    save_chapter_checkpoint(job_id, section_title, content)
                
        tasks = [process_section(i, section) for i, section in enumerate(sections)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
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
        
        if not file_paths:
            translated_title = await loop.run_in_executor(None, translate_title, raw_title, provider)
        else:
            translated_title = raw_title
        
        update_job_status(job_id, "generating_chapters", "마무리 중...")

        # Job complete
        update_job_status(job_id, "completed", "생성 완료!")
        finish_job(job_id, document, url, translated_title)
        
        generation_time_sec = int(time.time() - start_time)
        pm = profile_result.get("profile_message", "") if 'profile_result' in locals() else ""
        save_study_guide(job_id, url, translated_title, "", provider, document, learner_profile, pm, generation_time_sec, length_preset, analogy_preset, str(video_duration))
        
    except Exception as e:
        error_msg = f"{str(e)}\n{traceback.format_exc()}"
        print(f"Job {job_id} failed with error: {error_msg}")
        fail_job(job_id, error_msg)


@celery_app.task(bind=True)
def celery_generate_guide_task(self, job_id: str, request_data: dict, file_paths: list = None):
    # Run the async logic in a synchronous Celery task
    asyncio.run(async_generate_guide(job_id, request_data, file_paths))


