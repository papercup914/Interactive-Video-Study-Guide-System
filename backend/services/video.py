import os
import yt_dlp
import hashlib
import http.cookiejar
import requests
from urllib.parse import urlparse, parse_qs
from youtube_transcript_api import YouTubeTranscriptApi

TMP_DIR = "backend/tmp"

COOKIE_PATHS = [
    "backend/data/cookies.txt",
    "/app/backend/data/cookies.txt",
    "backend/cookies.txt",
    "/app/backend/cookies.txt",
    "cookies.txt",
    "/app/cookies.txt"
]

def _ensure_dir_exists():
    try:
        if not os.path.exists(TMP_DIR):
            os.makedirs(TMP_DIR, exist_ok=True)
    except Exception as e:
        print(f"[VideoService] Error creating temp dir: {e}")

def get_cookie_file() -> str | None:
    """존재하는 cookies.txt 경로를 반환하거나 환경변수에서 로드합니다."""
    for p in COOKIE_PATHS:
        try:
            if os.path.exists(p) and os.path.isfile(p) and os.path.getsize(p) > 0:
                return p
        except Exception:
            continue
            
    cookies_text = os.getenv("YOUTUBE_COOKIES_TEXT")
    if cookies_text and len(cookies_text.strip()) > 0:
        target = os.path.join(TMP_DIR, "env_cookies.txt")
        _ensure_dir_exists()
        try:
            with open(target, "w", encoding="utf-8") as f:
                f.write(cookies_text.strip())
            return target
        except Exception as e:
            print(f"[VideoService] Error writing env_cookies.txt: {e}")
    return None

def get_transcript_session(cookie_file: str | None = None) -> requests.Session:
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
    })
    if cookie_file and os.path.exists(cookie_file):
        try:
            cj = http.cookiejar.MozillaCookieJar(cookie_file)
            cj.load(ignore_discard=True, ignore_expires=True)
            session.cookies = cj
        except Exception as e:
            print(f"[CookieJar] Failed to load cookiejar: {e}")
    return session

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
    cookie_file = get_cookie_file()
    
    ydl_opts = {
        'format': 'ba/b/bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': outtmpl,
        'quiet': True,
        'no_warnings': True,
        'js_runtimes': {'node': {}},
        'extractor_args': {
            'youtube': {
                'player_client': ['mweb', 'web', 'android', 'ios']
            }
        },
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        }
    }
    
    if cookie_file:
        ydl_opts['cookiefile'] = cookie_file
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            
        if os.path.exists(expected_file):
            return expected_file
        else:
            raise Exception("오디오 파일을 찾을 수 없습니다.")
    except Exception as e:
        err_msg = str(e)
        if "Sign in to confirm you’re not a bot" in err_msg or "Sign in to confirm you're not a bot" in err_msg:
            raise Exception("유튜브 봇 감지로 인해 오디오 직접 다운로드가 제한되었습니다. 유튜브 쿠키(cookies.txt) 설정이 필요하거나, 자막(CC)이 지원되는 영상을 권장합니다.")
        raise Exception(f"영상 다운로드 중 오류가 발생했습니다: {err_msg}")

def get_video_metadata(url: str) -> dict:
    """URL에서 영상 제목과 길이(초)를 추출합니다."""
    cookie_file = get_cookie_file()
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': True,
        'js_runtimes': {'node': {}},
        'extractor_args': {
            'youtube': {
                'player_client': ['mweb', 'web', 'android', 'ios']
            }
        },
    }
    if cookie_file:
        ydl_opts['cookiefile'] = cookie_file
        
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            duration_sec = info.get('duration', 0) if info else 0
            return {
                "title": (info.get('title') if info else '제목 알 수 없음') or '제목 알 수 없음',
                "duration": duration_sec
            }
    except Exception:
        return {"title": '제목 알 수 없음', "duration": 0}

def extract_video_id(url: str) -> str:
    """Extract YouTube video ID from URL"""
    if not url:
        return None
    parsed_url = urlparse(url)
    if parsed_url.hostname == 'youtu.be':
        return parsed_url.path[1:] if len(parsed_url.path) > 1 else None
    if parsed_url.hostname in ('www.youtube.com', 'youtube.com'):
        if parsed_url.path == '/watch':
            p = parse_qs(parsed_url.query)
            return p.get('v', [None])[0]
        if parsed_url.path.startswith('/embed/'):
            return parsed_url.path.split('/')[2]
        if parsed_url.path.startswith('/v/'):
            return parsed_url.path.split('/')[2]
        if parsed_url.path.startswith('/shorts/'):
            return parsed_url.path.split('/')[2]
    return None

def get_youtube_transcript(url: str) -> str | None:
    """
    유튜브 URL에서 자막(CC)을 추출하여 텍스트로 반환합니다.
    자막이 없으면 None을 반환합니다.
    """
    video_id = extract_video_id(url)
    if not video_id:
        return None
        
    cookie_file = get_cookie_file()
    session = get_transcript_session(cookie_file)
    
    try:
        # 우선 한국어, 없으면 영어 시도
        ytt_api = YouTubeTranscriptApi(http_client=session)
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
                        try:
                            transcript = t.translate('ko')
                            break
                        except Exception:
                            transcript = t
                            break
                            
        if transcript:
            fetched = transcript.fetch()
            text_blocks = []
            for item in fetched:
                if isinstance(item, dict):
                    text_blocks.append(item.get('text', ''))
                else:
                    text_blocks.append(getattr(item, 'text', str(item)))
            return " ".join(text_blocks)
            
    except Exception as e:
        print(f"Transcript fetch failed for {url}: {e}")
        pass
        
    return None

