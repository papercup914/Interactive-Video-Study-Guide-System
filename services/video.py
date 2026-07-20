import os
import yt_dlp
import hashlib
TMP_DIR = "tmp"

def _ensure_dir_exists():
    if not os.path.exists(TMP_DIR):
        os.makedirs(TMP_DIR)

def get_url_hash(url: str) -> str:
    """URL의 MD5 해시값을 반환합니다."""
    return hashlib.md5(url.encode('utf-8')).hexdigest()

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

def get_video_title(url: str) -> str:
    """URL에서 영상 제목을 추출합니다."""
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info.get('title', '제목 알 수 없음')
    except Exception:
        return '제목 알 수 없음'
