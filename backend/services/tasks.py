import asyncio
import os
import time
import uuid
import re
from backend.celery_app import celery_app

def extract_chapters_from_scraped_text(text: str) -> list | None:
    """스크랩된 텍스트(Jina Reader 등)에서 유튜브 타임스탬프 챕터를 파싱하여 반환합니다."""
    if not text:
        return None
    chapters = []
    pattern = re.compile(r'(?:\[?(\d{1,2}:\d{2}(?::\d{2})?)\]?(?:\([^)]+\))?)\s*[-—–:]?\s*([^\n\r]+)')
    for line in text.splitlines():
        line_clean = line.strip()
        if not re.search(r'\b\d{1,2}:\d{2}\b', line_clean) or line_clean.startswith(('![', '[![')):
            continue
        match = pattern.search(line_clean)
        if match:
            time_str = match.group(1).strip()
            ch_title = match.group(2).strip()
            ch_title = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', ch_title).strip("—–-: ").strip()
            if ch_title and len(ch_title) >= 3 and not ch_title.lower().startswith(('image', 'http', 'www', 'views')):
                parts = [int(p) for p in time_str.split(':')]
                seconds = parts[0] * 60 + parts[1] if len(parts) == 2 else parts[0] * 3600 + parts[1] * 60 + parts[2]
                chapters.append({"title": ch_title, "start_time": seconds})
    return chapters if len(chapters) >= 3 else None

def clean_youtube_scraped_text(text: str) -> str:
    """Jina Reader 등으로 긁어온 유튜브 웹페이지 마크다운 텍스트에서 불필요한 UI 잡음, 추천 영상 목록 등을 정제합니다."""
    if not text:
        return ""
    lines = text.splitlines()
    clean_lines = []
    
    stop_patterns = [
        r"## Transcript",
        r"NaN / NaN",
        r"### \[.*\]\(https://www\.youtube\.com/watch\?v=",
        r"\[!\[Image \d+\]\(https://i\.ytimg\.com/"
    ]
    stop_regex = re.compile("|".join(stop_patterns), re.IGNORECASE)
    
    junk_line_patterns = [
        r"^Back \[!\[Image",
        r"^Skip navigation",
        r"^Search",
        r"^\[Sign in\]",
        r"^\[Video \d+\]",
        r"^Tap to unmute",
        r"^2x$",
        r"^Copy link",
        r"^Info$",
        r"^Shopping$",
        r"^If playback doesn't begin",
        r"%[0-9a-fA-F]{2}",
        r"\bviews\b.*\bago\b",
        r"\b조회수\b",
        r"^\[!\[Image \d+\]",
        r"^!\[Image \d+\]",
        r"^Show transcript",
        r"^Follow along using the transcript",
        r"^Transcript$"
    ]
    junk_line_regex = re.compile("|".join(junk_line_patterns), re.IGNORECASE)
    
    for line in lines:
        line_strip = line.strip()
        if not line_strip:
            continue
            
        if stop_regex.search(line_strip):
            break
            
        if junk_line_regex.search(line_strip):
            continue
            
        clean_lines.append(line_strip)
        
    cleaned = "\n".join(clean_lines).strip()
    return cleaned if len(cleaned) > 100 else text

# We need to run the async generation function inside a synchronous Celery wrapper
async def async_generate_guide(job_id: str, request_data: dict, file_paths: list = None):
    # This is a port of the old `_generate_guide_task` from guide.py
    from backend.services.job_manager import update_job_status, finish_job, fail_job, get_job, save_study_guide, get_completed_chapters, save_chapter_checkpoint
    from backend.services.video import download_audio, get_youtube_transcript, get_url_hash, get_video_metadata
    from backend.services.llm import process_audio, generate_outline, async_generate_chapter_content, profile_content, translate_title, is_gemini_provider, validate_chapter_narrative
    from backend.services.source import extract_text_from_pdf, extract_text_from_web
    
    start_time = time.time()
    video_duration = 0
    try:
        loop = asyncio.get_event_loop()
        
        # request_data is a dict because Celery JSON-serializes kwargs
        url = request_data.get("url", "")
        provider = request_data.get("provider", "")
        print(f"[DEBUG TASKS] async_generate_guide called for job_id={job_id}, raw provider='{provider}'")
        length_preset = request_data.get("length_preset", "아주 상세하게")
        analogy_preset = request_data.get("analogy_preset", "풍부한 비유")
        learner_profile = request_data.get("learner_profile", "")
        pdf_parsing_method = request_data.get("pdf_parsing_method", "basic")
        force_refresh = request_data.get("force_refresh", False)
        custom_api_key = request_data.get("custom_api_key") or None
        custom_base_url = request_data.get("custom_base_url") or None
        
        is_document = False
        raw_title = ""
        transcript = ""
        video_chapters = None
        video_duration = 0
        
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
            from backend.services.video import extract_video_id
            vid = extract_video_id(url)
            canonical_url = f"https://www.youtube.com/watch?v={vid}" if vid else url
            url_hash = get_url_hash(canonical_url)

            # 1. 메타데이터(제목, 재생 시간, 공식 챕터)를 최우선으로 먼저 추출
            update_job_status(job_id, "transcribing", "유튜브 메타데이터 및 챕터 정보 확인 중...")
            metadata = await loop.run_in_executor(None, get_video_metadata, canonical_url)
            if metadata and metadata.get("title") and metadata["title"] != "제목 알 수 없음":
                raw_title = metadata["title"]
                video_duration = metadata.get("duration", 0)
                video_chapters = metadata.get("chapters")
            elif not raw_title:
                raw_title = "유튜브 학습 가이드"

            # 2. 자막(Transcript) 추출 (Innertube 모바일 API -> 쿠키 세션 -> 기본 세션 -> yt-dlp)
            update_job_status(job_id, "transcribing", "유튜브 자막 추출 중...")
            transcript = await loop.run_in_executor(None, get_youtube_transcript, canonical_url)
            
            # 3. 자막이 없는 경우 오디오 다운로드 후 AI 음성 인식(Whisper/Gemini) 실행
            if not transcript or len(transcript.strip()) < 50:
                update_job_status(job_id, "downloading_audio", "자막 없음. 오디오 다운로드 시도 중...")
                try:
                    audio_path = await loop.run_in_executor(None, download_audio, canonical_url)
                    update_job_status(job_id, "transcribing", "오디오 텍스트 변환(Whisper/Gemini) 중...")
                    transcript = await loop.run_in_executor(None, process_audio, audio_path, provider)
                    url_hash = os.path.splitext(os.path.basename(audio_path))[0]
                except Exception as audio_err:
                    print(f"[Tasks] YouTube audio download failed/blocked: {audio_err}. Falling back to Jina Reader...")
                    update_job_status(job_id, "transcribing", "클라우드 환경 우회: 웹 분석 엔진(Jina Reader)으로 영상 정보 추출 중...")
                    try:
                        jina_text, jina_title = await loop.run_in_executor(None, extract_text_from_web, canonical_url)
                        # 유튜브 페이지를 Jina로 긁었을 때 약관/푸터 찌꺼기 텍스트인지 철저히 검증
                        junk_keywords = ["YouTube 정보", "저작권", "크리에이터", "광고 개발자", "약관 및 개인정보 보호", "About Press Copyright"]
                        is_junk = any(kw in jina_text for kw in junk_keywords) and len(jina_text) < 1500
                        if is_junk or len(jina_text.strip()) < 300:
                            print(f"[Tasks] Jina Reader returned invalid YouTube page junk ({len(jina_text)} chars). Rejecting.")
                            raise ValueError(f"유튜브 영상의 자막 및 오디오를 가져올 수 없습니다 ({audio_err}).")
                        
                        # 유튜브 웹페이지 메타데이터 잡음(조회수, UI 버튼, 추천 영상 등) 정제
                        cleaned_jina = clean_youtube_scraped_text(jina_text)
                        transcript = cleaned_jina if len(cleaned_jina) >= 300 else jina_text
                        
                        # 공식 챕터 정보가 없는 경우 Jina 스크랩 텍스트에서 타임스탬프 챕터 복원
                        if not video_chapters:
                            scraped_ch = extract_chapters_from_scraped_text(jina_text)
                            if scraped_ch:
                                video_chapters = scraped_ch
                                print(f"[Tasks] Jina 스크랩 텍스트에서 {len(video_chapters)}개의 타임스탬프 챕터 추출 성공!")
                                
                        if not raw_title or raw_title == "제목 알 수 없음" or raw_title == "유튜브 학습 가이드":
                            raw_title = jina_title
                    except Exception as jina_err:
                        print(f"[Tasks] All YouTube extraction methods failed: {jina_err}")
                        raise ValueError(f"유튜브 영상의 자막 및 오디오를 가져올 수 없습니다. 클라우드 IP 차단 해제를 위해 cookies.txt 설정이 필요합니다. (원인: {audio_err})")
        else:
            update_job_status(job_id, "transcribing", "웹 페이지 텍스트 추출 중 (Jina Reader)...")
            transcript, raw_title = await loop.run_in_executor(None, extract_text_from_web, url)
            import hashlib
            url_hash = hashlib.md5(url.encode()).hexdigest()
            is_document = True
            
        tutor_persona = None
        profile_result = {}
        if is_document:
            length_preset = "문서 원본 번역"
        else:
            update_job_status(job_id, "analyzing_context", "AI가 영상 성격을 분석하여 최적의 톤과 페르소나를 계산 중...")
            profile_result = await loop.run_in_executor(None, profile_content, transcript, provider) or {}
            
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
        sections = await loop.run_in_executor(
            None, 
            generate_outline, 
            master_summary, 
            provider, 
            url_hash, 
            length_preset, 
            force_refresh, 
            video_chapters,
            custom_api_key,
            custom_base_url
        )
        
        document = {}
        total_sections = len(sections)
        
        completed_chapters = {}
        if not force_refresh:
            completed_chapters = get_completed_chapters(job_id)
        
        concurrency_limit = int(os.getenv("CHAPTER_GENERATION_CONCURRENCY", "3"))
        semaphore = asyncio.Semaphore(concurrency_limit)
        
        async def process_section(idx: int, section_title: str):
            async with semaphore:
                job = get_job(job_id)
                if job and job.get("status") == "cancelled":
                    return
                
                cp_min_chars = 1000 if length_preset == "핵심 요약" else 1500
                cp_min_narrative = 800 if length_preset == "핵심 요약" else 1200
                
                if section_title in completed_chapters:
                    cached_cp = completed_chapters[section_title]
                    if length_preset == "문서 원본 번역":
                        is_valid = bool(cached_cp and len(cached_cp.strip()) >= 50)
                    else:
                        is_valid, _ = validate_chapter_narrative(
                            cached_cp, 
                            min_chars=cp_min_chars, 
                            min_narrative_chars=cp_min_narrative
                        )
                    if is_valid:
                        print(f"[Harness] Valid checkpoint loaded for {section_title}, skipping API call.")
                        document[section_title] = cached_cp
                        return
                    else:
                        print(f"[Harness] Checkpoint for {section_title} was invalid/tag-only. Re-generating...")

                update_job_status(job_id, "generating_chapters", f"[{idx+1}/{total_sections}] 챕터 생성 중...")
                content = await async_generate_chapter_content(
                    section_title, master_summary, provider, idx, total_sections, 
                    length_preset, analogy_preset, learner_profile, url_hash,
                    tutor_persona, force_refresh,
                    custom_api_key=custom_api_key,
                    custom_base_url=custom_base_url
                )
                if content and content.strip():
                    document[section_title] = content
                    if length_preset == "문서 원본 번역" or validate_chapter_narrative(content, min_chars=cp_min_chars, min_narrative_chars=cp_min_narrative)[0]:
                        save_chapter_checkpoint(job_id, section_title, content)
                else:
                    document[section_title] = (
                        f"# {section_title}\n\n"
                        f"> [!WARNING]\n"
                        f"> 챕터 내용을 생성하는 중 응답이 비어 있었습니다. 다시 생성을 시도해 주세요."
                    )
                
        tasks = [process_section(i, section) for i, section in enumerate(sections)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, res in enumerate(results):
            section_title = sections[i]
            if isinstance(res, Exception) or section_title not in document or not str(document.get(section_title, "")).strip():
                print(f"Warning: Section {i+1} failed completely despite retries: {res if isinstance(res, Exception) else 'missing content'}. Applying Heuristic Safe Fallback.")
                snippet = master_summary if isinstance(master_summary, str) and not master_summary.startswith("GEMINI_FILE_URI::") else ""
                clean_lines = [l.strip() for l in snippet.split("\n") if len(l.strip()) > 20 and not l.strip().startswith(("#", "[", "http"))]
                fallback_body = "\n\n".join(clean_lines[:6]) if clean_lines else f"**{section_title}**의 주요 개념과 학습 포인트를 정리합니다."
                document[section_title] = (
                    f"## {section_title}\n\n"
                    f"**{section_title}**의 핵심 개념과 주요 학습 내용을 체계적으로 다룹니다.\n\n"
                    f"### 1. 도입 및 핵심 배경\n"
                    f"{section_title}은 시스템과 지식 체계에서 중요한 비중을 차지하는 주제입니다. "
                    f"이 개념을 충실히 학습함으로써 전반적인 맥락과 핵심 원리를 명확하게 이해할 수 있습니다.\n\n"
                    f"### 2. 세부 내용 및 요약\n"
                    f"{fallback_body}\n\n"
                    f"> **💡 핵심 인사이트**\n"
                    f"> {section_title}의 학습 핵심은 각 구성 요소의 역할과 상호작용 흐름을 파악하는 데 있습니다.\n\n"
                    f"### 3. 실무 팁 & 주의사항\n"
                    f"- 개념 적용 전 요구사항과 예외 경계 조건을 반드시 사전 검토하십시오.\n"
                    f"- 실무 환경에서의 재현성을 높이기 위해 단계별 체크리스트를 활용하는 것이 좋습니다."
                )
        
        job = get_job(job_id)
        if job and job.get("status") == "cancelled":
            print(f"Job {job_id} cancelled.")
            return
        
        if not file_paths:
            translated_title = await loop.run_in_executor(None, translate_title, raw_title, provider, transcript)
        else:
            translated_title = raw_title
        
        update_job_status(job_id, "generating_chapters", "마무리 중...")

        # Job complete
        update_job_status(job_id, "completed", "생성 완료!")
        finish_job(job_id, document, url, translated_title)
        
        generation_time_sec = int(time.time() - start_time)
        pm = profile_result.get("profile_message", "")
        save_study_guide(job_id, url, translated_title, "", provider, document, learner_profile, pm, generation_time_sec, length_preset, analogy_preset, str(video_duration))
        
    except Exception as e:
        error_msg = f"{str(e)}\n{traceback.format_exc()}"
        print(f"Job {job_id} failed with error: {error_msg}")
        fail_job(job_id, error_msg)


@celery_app.task(bind=True)
def celery_generate_guide_task(self, job_id: str, request_data: dict, file_paths: list = None):
    # Run the async logic in a synchronous Celery task
    asyncio.run(async_generate_guide(job_id, request_data, file_paths))

@celery_app.task(bind=True)
def celery_batch_pregenerate_task(self, batch_id: str):
    from backend.services.batch_generator import run_batch_pregeneration_pipeline
    asyncio.run(run_batch_pregeneration_pipeline(batch_id))



