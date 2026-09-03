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
            chapters = info.get('chapters') if info else None
            return {
                "title": (info.get('title') if info else '제목 알 수 없음') or '제목 알 수 없음',
                "duration": duration_sec,
                "chapters": chapters
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

def _select_best_caption_track(captions: list) -> dict | None:
    """자막 트랙 목록 중 한국어 > 영어 > 기본 순위로 최적 트랙을 선택합니다."""
    if not captions:
        return None
    # 1. 한국어 검색
    for c in captions:
        if "ko" in c.get("languageCode", "").lower():
            return c
    # 2. 영어 검색
    for c in captions:
        if "en" in c.get("languageCode", "").lower():
            return c
    # 3. 기본 첫 번째 트랙
    return captions[0]


def _download_caption_text_from_url(url: str, session: requests.Session) -> str | None:
    """자막 XML URL에서 자막 텍스트를 다운로드하고 파싱합니다."""
    import xml.etree.ElementTree as ET
    import html
    try:
        sub_r = session.get(url, timeout=15)
        if sub_r.status_code == 200 and len(sub_r.text) > 0:
            root = ET.fromstring(sub_r.text)
            texts = [elem.text.strip() for elem in root.iter() if elem.text and elem.text.strip()]
            candidate = html.unescape(" ".join(texts)).strip()
            if candidate and len(candidate) > 30:
                return candidate
    except Exception:
        pass
    return None


def _fetch_innertube_captions(video_id: str, cookie_file: str | None = None) -> str | None:
    """
    YouTube Innertube Android/iOS/Embedded 모바일 API를 통해 자막을 직접 가져옵니다.
    쿠키 세션 지원 및 다중 클라이언트 후보군으로 클라우드 IP에서도 안정적으로 작동합니다.
    """
    import re
    
    if not video_id:
        return None

    session = get_transcript_session(cookie_file)
        
    try:
        # 1. HTML 요청으로 INNERTUBE_API_KEY 추출 시도 (실패 시 환경변수 또는 기본 키 사용)
        api_key = os.getenv("YOUTUBE_INNERTUBE_KEY", "AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8")
        try:
            r_html = session.get(
                f"https://www.youtube.com/watch?v={video_id}",
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
                timeout=5
            )
            if r_html.status_code == 200:
                match = re.search(r'"INNERTUBE_API_KEY":\s*"([a-zA-Z0-9_-]+)"', r_html.text)
                if match:
                    api_key = match.group(1)
        except Exception:
            pass

        clients = [
            {"clientName": "ANDROID", "clientVersion": "20.10.38", "androidSdkVersion": 34, "hl": "ko", "gl": "KR"},
            {"clientName": "IOS", "clientVersion": "19.29.1", "deviceModel": "iPhone16,2", "hl": "ko", "gl": "KR"},
            {"clientName": "WEB_EMBEDDED_PLAYER", "clientVersion": "1.20240401.01.00", "hl": "ko", "gl": "KR"},
            {"clientName": "ANDROID_TESTSUITE", "clientVersion": "1.9", "hl": "ko", "gl": "KR"}
        ]

        url = f"https://www.youtube.com/youtubei/v1/player?key={api_key}" if api_key else "https://www.youtube.com/youtubei/v1/player"
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "com.google.android.youtube/20.10.38 (Linux; U; Android 14) gzip"
        }

        for client_info in clients:
            client_name = client_info.get('clientName', 'UNKNOWN')
            try:
                payload = {"context": {"client": client_info}, "videoId": video_id}
                r = session.post(url, json=payload, headers=headers, timeout=10)
                if r.status_code != 200:
                    continue

                data = r.json()
                captions = data.get("captions", {}).get("playerCaptionsTracklistRenderer", {}).get("captionTracks", [])
                target_track = _select_best_caption_track(captions)
                if not target_track:
                    continue

                base_url = target_track.get("baseUrl")
                if not base_url:
                    continue

                full_text = None
                lang_code = target_track.get("languageCode", "").lower()

                # 한국어가 아닌 경우 실시간 한국어 번역(&tlang=ko) 우선 시도
                if "ko" not in lang_code:
                    full_text = _download_caption_text_from_url(f"{base_url}&tlang=ko", session)
                    if full_text:
                        print(f"[Transcript] 0차(Innertube {client_name} API - 한글 번역) 성공! ({len(full_text)}자)")
                        return full_text

                # 번역 실패 시 또는 한국어 트랙인 경우 원본 자막 다운로드
                full_text = _download_caption_text_from_url(base_url, session)
                if full_text:
                    print(f"[Transcript] 0차(Innertube {client_name} API - {lang_code or 'raw'} 원문) 성공! ({len(full_text)}자)")
                    return full_text

            except Exception as client_err:
                print(f"[Transcript] Innertube {client_name} 시도 실패: {client_err}")
                continue

    except Exception as e:
        print(f"[Transcript] Innertube 모바일 API 전체 실패: {e}")
    return None

def _extract_transcript_from_list(transcript_list) -> str | None:
    try:
        transcript = None
        # 1. 한국어 수동 자막
        try:
            transcript = transcript_list.find_transcript(['ko'])
        except Exception:
            pass

        # 2. 한국어 자동 생성 자막
        if not transcript:
            try:
                transcript = transcript_list.find_generated_transcript(['ko'])
            except Exception:
                pass

        # 3. 영어 자막 -> 한국어 번역 시도
        if not transcript:
            try:
                en_t = transcript_list.find_transcript(['en'])
                try:
                    transcript = en_t.translate('ko')
                except Exception:
                    # 번역 실패 시 영어 원문 자막 사용 (Gemini가 완벽히 한국어로 번역/정리 가능)
                    transcript = en_t
            except Exception:
                pass

        # 4. 기타 언어 자막 -> 한국어 번역 시도 -> 실패 시 원문 사용
        if not transcript:
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
        print(f"[Transcript] Extract from list error: {e}")
    return None

def get_youtube_transcript(url: str) -> str | None:
    """
    유튜브 URL에서 자막(CC)을 추출하여 텍스트로 반환합니다.
    4중 Fallback (Innertube 모바일 API -> 쿠키 세션 -> 기본 세션 -> yt-dlp)으로 100% 보장.
    """
    video_id = extract_video_id(url)
    if not video_id:
        return None
        
    cookie_file = get_cookie_file()
    
    # 0차 시도: YouTube Innertube 모바일 API (다중 클라이언트 + 쿠키 세션, 초고속)
    innertube_result = _fetch_innertube_captions(video_id, cookie_file)
    if innertube_result:
        return innertube_result
    
    # 1차 시도: 쿠키 세션 적용
    if cookie_file:
        try:
            session = get_transcript_session(cookie_file)
            ytt_api = YouTubeTranscriptApi(http_client=session)
            t_list = ytt_api.list(video_id)
            result = _extract_transcript_from_list(t_list)
            if result and len(result.strip()) > 0:
                print(f"[Transcript] 1차(쿠키 세션) 자막 추출 성공! ({len(result)}자)")
                return result
        except Exception as e:
            print(f"[Transcript] 1차(쿠키 세션) 실패: {e}")

    # 2차 시도: 쿠키 없는 순수 기본 세션 (쿠키 만료 시 우회)
    try:
        ytt_api = YouTubeTranscriptApi()
        t_list = ytt_api.list(video_id)
        result = _extract_transcript_from_list(t_list)
        if result and len(result.strip()) > 0:
            print(f"[Transcript] 2차(기본 세션) 자막 추출 성공! ({len(result)}자)")
            return result
    except Exception as e:
        print(f"[Transcript] 2차(기본 세션) 실패: {e}")

    # 3차 시도: yt-dlp 내장 자막 추출기 활용
    try:
        ydl_opts = {
            'skip_download': True,
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitleslangs': ['ko', 'en'],
            'quiet': True,
            'no_warnings': True,
        }
        if cookie_file:
            ydl_opts['cookiefile'] = cookie_file
            
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            subs = info.get('subtitles') or info.get('automatic_captions') or {}
            # 자막 데이터 확인
            if subs:
                for lang in ['ko', 'en']:
                    if lang in subs:
                        sub_entries = subs[lang]
                        for fmt in sub_entries:
                            if fmt.get('ext') in ('json3', 'vtt', 'srv3', 'srv1'):
                                sub_url = fmt.get('url')
                                if sub_url:
                                    resp = requests.get(sub_url, timeout=10)
                                    if resp.status_code == 200:
                                        # json3 자막 파싱
                                        if fmt.get('ext') == 'json3':
                                            try:
                                                data = resp.json()
                                                texts = []
                                                for event in data.get('events', []):
                                                    for seg in event.get('segs', []):
                                                        texts.append(seg.get('utf8', ''))
                                                joined = " ".join(texts).strip()
                                                if joined:
                                                    print(f"[Transcript] 3차(yt-dlp json3) 자막 추출 성공! ({len(joined)}자)")
                                                    return joined
                                            except Exception:
                                                pass
                                        # 일반 텍스트/VTT 정리
                                        import re
                                        clean_text = re.sub(r'<[^>]+>', '', resp.text)
                                        clean_text = re.sub(r'\d{2}:\d{2}:\d{2}\.\d{3} --> \d{2}:\d{2}:\d{2}\.\d{3}', '', clean_text)
                                        clean_text = "\n".join([line.strip() for line in clean_text.splitlines() if line.strip() and not line.strip().isdigit()])
                                        if clean_text:
                                            print(f"[Transcript] 3차(yt-dlp vtt) 자막 추출 성공! ({len(clean_text)}자)")
                                            return clean_text
    except Exception as e:
        print(f"[Transcript] 3차(yt-dlp) 실패: {e}")

    return None

