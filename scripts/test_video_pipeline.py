import os
import sys

# Windows 콘솔 출력 인코딩 처리
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.services.video import get_video_metadata, get_youtube_transcript, download_audio, get_cookie_file

def test_pipeline():
    print('=' * 60)
    print('[YouTube 비디오/자막/오디오 다운로드 파이프라인 실기 테스트]')
    print('=' * 60)
    
    cookie_file = get_cookie_file()
    print(f'1. 적용된 쿠키 파일: {cookie_file}')
    
    test_url = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
    print(f'\n2. 메타데이터 추출 테스트 URL: {test_url}')
    meta = get_video_metadata(test_url)
    title = meta.get('title')
    duration = meta.get('duration')
    print(f'   - 영상 제목: {title}')
    print(f'   - 영상 길이: {duration}초')
    
    print('\n3. 자막(CC) 추출 테스트:')
    transcript = get_youtube_transcript(test_url)
    if transcript:
        preview = transcript[:100] + '...' if len(transcript) > 100 else transcript
        print(f'   🟢 자막 추출 성공! (총 길이: {len(transcript)}자)')
        print(f'   미리보기: {preview}')
    else:
        print('   ⚪ 자막 없음 (오디오 다운로드 단계로 fallback 대상)')
        
    print('\n4. 오디오 다운로드(yt-dlp + ffmpeg + 쿠키) 실기 테스트:')
    try:
        audio_path = download_audio(test_url)
        print(f'   🟢 오디오 다운로드 및 mp3 변환 성공: {audio_path}')
        if os.path.exists(audio_path):
            file_size = os.path.getsize(audio_path)
            print(f'   - 파일 크기: {file_size} bytes')
    except Exception as e:
        print(f'   ❌ 다운로드 실패: {e}')
        
    print('=' * 60)

if __name__ == '__main__':
    test_pipeline()
