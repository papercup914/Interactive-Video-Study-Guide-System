import os
import sys

# Windows 콘솔 출력 인코딩 처리
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# 프로젝트 루트 경로 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.services.video import get_cookie_file, get_transcript_session, COOKIE_PATHS

def main():
    print('=' * 60)
    print('[YouTube cookies.txt 유효성 및 로더 진단 스크립트]')
    print('=' * 60)
    
    print('\n1. 탐색 대상 쿠키 경로 목록:')
    for p in COOKIE_PATHS:
        exists = os.path.exists(p)
        size = os.path.getsize(p) if exists else 0
        status_str = f'🟢 [존재함] ({size} bytes)' if exists and size > 0 else '⚪ [없음]'
        print(f'   - {p:<35} : {status_str}')
        
    env_cookies = os.getenv('YOUTUBE_COOKIES_TEXT')
    if env_cookies:
        print(f'   - YOUTUBE_COOKIES_TEXT 환경변수    : 🟢 [설정됨] ({len(env_cookies)} chars)')
    else:
        print('   - YOUTUBE_COOKIES_TEXT 환경변수    : ⚪ [미설정]')
        
    detected = get_cookie_file()
    print('\n2. 최종 감지된 쿠키 파일:')
    if detected:
        print(f'   👉 🟢 감지 성공: {detected}')
        session = get_transcript_session(detected)
        cookie_count = len(session.cookies)
        print(f'   👉 로드된 세션 쿠키 개수: {cookie_count}개')
        if cookie_count > 0:
            print('   ✅ 쿠키 파일 형식이 올바르며 정상적으로 로드되었습니다.')
        else:
            print('   ⚠️ 쿠키 파일은 존재하나 유효한 Netscape 쿠키 항목을 찾지 못했습니다.')
    else:
        print('   👉 ⚪ 감지된 쿠키 파일이 없습니다. (기본 브라우저 헤더로 요청 진행)')
        print('   💡 자막이 없거나 봇 차단이 발생하는 영상을 처리하려면 cookies.txt 등록을 권장합니다.')
        
    print('=' * 60)

if __name__ == '__main__':
    main()
