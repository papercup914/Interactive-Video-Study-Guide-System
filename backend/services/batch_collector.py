import os
import re
from typing import List, Dict, Any, Tuple
import yt_dlp

def is_shorts_video(info: dict) -> bool:
    """비디오 정보가 쇼츠(Shorts)인지 판별합니다."""
    if not info:
        return False
    duration = info.get("duration")
    if duration is not None:
        try:
            if float(duration) <= 60:
                return True
        except (ValueError, TypeError):
            pass
            
    title = (info.get("title") or "").lower()
    url = (info.get("url") or info.get("webpage_url") or "").lower()
    if "#shorts" in title or "/shorts/" in url or "#short" in title:
        return True
        
    return False

def collect_videos_from_source(
    url: str,
    max_limit: int = 30,
    exclude_shorts: bool = True
) -> Tuple[str, List[Dict[str, Any]]]:
    """
    유튜브 채널 또는 재생목록 URL에서 비디오 목록과 제목을 고속으로 추출합니다.
    (yt-dlp flat-playlist 모드 사용으로 할당량 소모 없음)
    
    Returns:
        (collection_title, list_of_video_dicts)
    """
    if not url or not url.strip():
        raise ValueError("유효하지 않은 URL입니다.")
        
    clean_url = url.strip()
    
    # yt-dlp 옵션: 영상 다운로드 없이 메타데이터만 초고속 추출
    ydl_opts = {
        'extract_flat': 'in_playlist',
        'skip_download': True,
        'quiet': True,
        'no_warnings': True,
        'ignoreerrors': True,
        'playlist_items': f"1-{max_limit * 2}" if max_limit else None # 쇼츠 필터링 여유분을 위해 2배수 탐색
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(clean_url, download=False)
            if not info:
                raise ValueError("유튜브 메타데이터를 불러올 수 없습니다.")
                
            collection_title = info.get("title") or info.get("uploader") or "유튜브 컬렉션"
            
            entries = []
            if "entries" in info and info["entries"]:
                entries = list(info["entries"])
            else:
                # 단일 비디오인 경우
                entries = [info]
                
            videos = []
            for item in entries:
                if not item:
                    continue
                    
                # 쇼츠 필터링
                if exclude_shorts and is_shorts_video(item):
                    continue
                    
                video_id = item.get("id")
                if not video_id:
                    continue
                    
                video_title = item.get("title") or f"Video {video_id}"
                video_url = f"https://www.youtube.com/watch?v={video_id}"
                duration_sec = item.get("duration")
                
                duration_str = ""
                if duration_sec:
                    try:
                        m, s = divmod(int(duration_sec), 60)
                        h, m = divmod(m, 60)
                        duration_str = f"{h:02d}:{m:02d}:{s:02d}" if h > 0 else f"{m:02d}:{s:02d}"
                    except:
                        duration_str = str(duration_sec)
                        
                videos.append({
                    "id": video_id,
                    "video_id": video_id,
                    "title": video_title,
                    "url": video_url,
                    "duration": duration_str,
                    "duration_sec": duration_sec
                })
                
                if max_limit and len(videos) >= max_limit:
                    break
                    
            return collection_title, videos
            
    except Exception as e:
        error_msg = f"비디오 목록 수집 중 오류 발생: {str(e)}"
        print(f"[BatchCollector Error] {error_msg}")
        raise RuntimeError(error_msg)
