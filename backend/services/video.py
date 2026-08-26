import os
import yt_dlp
import hashlib
from urllib.parse import urlparse, parse_qs
from youtube_transcript_api import YouTubeTranscriptApi

TMP_DIR = "backend/tmp"

def _ensure_dir_exists():
    if not os.path.exists(TMP_DIR):
        os.makedirs(TMP_DIR)

def get_url_hash(url: str) -> str:
    """URL의 MD5 해시값을 반환합니다. 유튜브의 경우 video_id를 추출하여 정규화합니다."""
    vid = extract_video_id(url)
    key = f"youtube_{vid}" if vid else url
    return hashlib.md5(key.encode('utf-8')).hexdigest()

def download_audio(url: str) -> str:
    """
    유튜브 또는 X(트위터) URL에서 오디오를 추출하여 임시 MP3 파일로 저장한 뒤 경로를 반환합니다.
    """
    _ensure_dir_exists()
    
    file_id = get_url_hash(url)
    expected_file = os.path.join(TMP_DIR, f"{file_id}.mp3")
    
    # 캐싱 로직: 이미 다운로드된 파일이 있으면 그대로 반환
    if os.path.exists(expected_file):
        return expected_file
        
    outtmpl = os.path.join(TMP_DIR, f"{file_id}.%(ext)s")
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': outtmpl,
        'quiet': True,
        'no_warnings': True,
        'extractor_args': {'youtube': ['player_client=android,web']},
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            
        if os.path.exists(expected_file):
            return expected_file
        else:
            raise Exception("오디오 파일을 찾을 수 없습니다.")
    except Exception as e:
        raise Exception(f"영상 다운로드 중 오류가 발생했습니다: {e}")

def get_video_metadata(url: str) -> dict:
    """URL에서 영상 제목과 길이(초)를 추출합니다."""
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': True,
        'extractor_args': {'youtube': ['player_client=android,web']},
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            duration_sec = info.get('duration', 0)
            return {
                "title": info.get('title', '제목 알 수 없음'),
                "duration": duration_sec
            }
    except Exception:
        return {"title": '제목 알 수 없음', "duration": 0}

def extract_video_id(url: str) -> str:
    """Extract YouTube video ID from URL"""
    parsed_url = urlparse(url)
    if parsed_url.hostname == 'youtu.be':
        return parsed_url.path[1:]
    if parsed_url.hostname in ('www.youtube.com', 'youtube.com'):
        if parsed_url.path == '/watch':
            p = parse_qs(parsed_url.query)
            return p.get('v', [None])[0]
        if parsed_url.path.startswith('/embed/'):
            return parsed_url.path.split('/')[2]
        if parsed_url.path.startswith('/v/'):
            return parsed_url.path.split('/')[2]
    return None

def get_youtube_transcript(url: str) -> str:
    """
    유튜브 URL에서 자막(CC)을 추출하여 텍스트로 반환합니다.
    자막이 없으면 None을 반환합니다.
    """
    video_id = extract_video_id(url)
    if not video_id:
        return None
        
    try:
        # 우선 한국어, 없으면 영어 시도
        ytt_api = YouTubeTranscriptApi()
        transcript_list = ytt_api.list(video_id)
        transcript = None
        
        try:
            # 수동 생성 한국어 자막 찾기
            transcript = transcript_list.find_transcript(['ko'])
        except Exception:
            try:
                # 자동 생성 한국어 찾기
                transcript = transcript_list.find_generated_transcript(['ko'])
            except Exception:
                try:
                    # 영어를 한국어로 번역
                    en_transcript = transcript_list.find_transcript(['en'])
                    transcript = en_transcript.translate('ko')
                except Exception:
                    # 아무 언어나 가져와서 한국어로 번역 시도
                    for t in transcript_list:
                        transcript = t.translate('ko')
                        break
                        
        if transcript:
            fetched = transcript.fetch()
            text_blocks = []
            for item in fetched:
                if isinstance(item, dict):
                    text_blocks.append(item['text'])
                else:
                    text_blocks.append(getattr(item, 'text', str(item)))
            return " ".join(text_blocks)
            
    except Exception as e:
        print(f"Transcript fetch failed for {url}: {e}")
        pass
        
    return None
