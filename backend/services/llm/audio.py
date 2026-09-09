import os
import math
import time
from typing import List, Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception
from backend.services.llm.clients import (
    get_gemini_client,
    get_openai_client,
    is_gemini_provider,
    safe_gemini_generate_content,
    _should_retry_error
)
from backend.config import settings

def _split_audio_if_needed(audio_path: str, max_size_mb: int = 20) -> List[str]:
    """오디오 파일이 max_size_mb를 초과하면 분할하여 임시 파일 경로 목록을 반환합니다."""
    file_size_mb = os.path.getsize(audio_path) / (1024 * 1024)
    if file_size_mb <= max_size_mb:
        return [audio_path]
        
    print(f"오디오 크기가 {file_size_mb:.2f}MB로 제한({max_size_mb}MB)을 초과하여 분할합니다.")
    try:
        from pydub import AudioSegment
        audio = AudioSegment.from_file(audio_path)
    except Exception as e:
        print(f"pydub 로드 실패 또는 오디오 분할 불가: {e}. 원본 파일 사용.")
        return [audio_path]
    
    num_chunks = math.ceil(file_size_mb / max_size_mb)
    chunk_length_ms = len(audio) // num_chunks
    
    chunk_paths = []
    base_name = os.path.splitext(audio_path)[0]
    
    for i in range(num_chunks):
        start_ms = i * chunk_length_ms
        end_ms = (i + 1) * chunk_length_ms if i < num_chunks - 1 else len(audio)
        
        chunk = audio[start_ms:end_ms]
        chunk_path = f"{base_name}_part{i}.mp3"
        chunk.export(chunk_path, format="mp3")
        chunk_paths.append(chunk_path)
        
    return chunk_paths

def process_audio(audio_path: str, provider: str, url_hash: Optional[str] = None) -> str:
    """
    선택된 Provider에 맞게 오디오를 처리하여 텍스트 대본(Transcript)을 반환합니다.
    로컬 캐시가 있으면 API를 호출하지 않고 반환합니다.
    OpenAI Whisper 호출 실패 시 Gemini 멀티모달 오디오 변환으로 Fallback 처리합니다.
    """
    if not audio_path or not os.path.exists(audio_path):
        raise ValueError(f"오디오 파일이 존재하지 않거나 잘못된 경로입니다: {audio_path}")

    derived_hash = url_hash or os.path.splitext(os.path.basename(audio_path))[0]
    data_dir = "backend/data"
    if not os.path.exists(data_dir):
        os.makedirs(data_dir, exist_ok=True)
        
    cache_file = os.path.join(data_dir, f"{derived_hash}_transcript.txt")
    if os.path.exists(cache_file):
        with open(cache_file, "r", encoding="utf-8") as f:
            cached_text = f.read()
            if cached_text and cached_text.strip():
                return cached_text

    transcript = ""
    whisper_done = False

    openai_key = settings.openai_api_key or os.getenv("OPENAI_API_KEY")
    if openai_key and openai_key != "여기에_OPENAI_API_키를_입력하세요" and not is_gemini_provider(provider):
        try:
            client = get_openai_client("OpenAI (GPT-4o)")
            chunk_paths = _split_audio_if_needed(audio_path, max_size_mb=20)
            temp_transcript = ""
            
            for chunk_path in chunk_paths:
                with open(chunk_path, "rb") as audio_file:
                    transcript_response = client.audio.transcriptions.create(
                        model="whisper-1", 
                        file=audio_file, 
                        response_format="text"
                    )
                temp_transcript += transcript_response + " "
                
                if chunk_path != audio_path:
                    try:
                        os.remove(chunk_path)
                    except Exception:
                        pass
            
            if temp_transcript.strip():
                transcript = temp_transcript.strip()
                whisper_done = True
        except Exception as e:
            print(f"[Warning] OpenAI Whisper 변환 실패 ({e}). Gemini 멀티모달 오디오 변환으로 자동 Fallback합니다.")

    if not whisper_done:
        try:
            client = get_gemini_client()
            uploaded_file = client.files.upload(file=audio_path)
            
            while uploaded_file.state.name == "PROCESSING":
                print(f"Gemini 오디오 처리 중 대기... (상태: {uploaded_file.state.name})")
                time.sleep(3)
                uploaded_file = client.files.get(name=uploaded_file.name)
                
            if uploaded_file.state.name == "FAILED":
                raise Exception("Gemini 파일 업로드 처리 실패")
                
            @retry(retry=retry_if_exception(_should_retry_error), stop=stop_after_attempt(5), wait=wait_exponential(multiplier=2, min=4, max=30))
            def _call_gemini_audio():
                return safe_gemini_generate_content(
                    client=client,
                    model=settings.selected_gemini_version or "gemini-3.5-flash-lite",
                    contents=[uploaded_file, "Please provide a complete and highly accurate transcription of this audio in its original language. Do not summarize, format, or skip any parts. Return ONLY the transcribed text."]
                )

            response = _call_gemini_audio()
            if response and response.text:
                transcript = response.text
            else:
                raise Exception("Gemini 오디오 변환 결과 텍스트가 비어있습니다.")
        except Exception as e:
            print(f"Gemini API error during audio processing: {e}")
            raise Exception(f"오디오 변환(Whisper 및 Gemini Fallback) 처리에 실패했습니다: {e}")

    if transcript:
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                f.write(transcript)
        except Exception as e:
            print(f"[Warning] Transcript cache save failed: {e}")

    return transcript
