# 🤖 인수인계 문서 (HANDOVER DOCUMENT FOR NEXT AGENT)

**경고**: 이 문서는 `i:\Interactive Video Study Guide System` 코드베이스 및 프로덕션 인프라의 100% 가감 없는 최신 실황을 담고 있습니다. 존재하지 않는 기능을 지어내지(Hallucinate) 마십시오.

---

## 1. 시스템 아키텍처 및 실제 배포 현황 (Production Live)

| 계층 | 기술 스택 | 배포 위치 및 프로덕션 URL | 상태 |
| :--- | :--- | :--- | :--- |
| **Frontend** | Next.js 16.2.10 (App Router), React 19.2.4, Tailwind CSS v4 | **Vercel**: `https://interactive-video-study-guide-syste.vercel.app` | 🟢 라이브 가동 중 |
| **Backend** | FastAPI (Python 3.12), Celery, Redis | **AWS EC2 (Free Tier)**: `http://13.209.73.143:8000` | 🟢 200 OK 가동 중 |
| **Auth & DB** | Supabase Auth (Google OAuth, JWT 쿠키 세션, Edge Guard) | **Supabase Cloud**: `https://app.notion.com/...` | 🟢 연동 완료 |
| **AI Engine** | Google GenAI SDK (Gemini 3.6 Flash) | BYOK / Cloudflare Tunnel / Direct REST | 🟢 정상 연동 (E2E 검증 완료) |
| **Worker & Queue** | Celery 5.6, Redis 8.1 | AWS EC2 (Single-Worker Concurrency 3) | 🟢 안정적 비동기 처리 |

---

## 2. 구현 및 버그 해결 완료 내역 (Verified Features)

### ✅ 가이드 생성 서버 오류 완전 해결 (E2E 실기 검증 100% 완료)
1. **Celery/Redis 브로커 통신 복구**: `REDIS_URL` 환경변수 폴백 및 `docker-compose.yml` Celery 브로커 환경변수 명시.
2. **Next.js 미들웨어 API 307 충돌 해결**: API 요청(`/api/...`) 미인증 시 307 HTML 리다이렉트 대신 401 JSON을 반환하도록 개선하고, 프론트엔드 에러 파싱 및 alert 방어 로직 강화.
3. **오디오 다운로드 ffmpeg 설치**: `Dockerfile.backend`에 `ffmpeg`를 추가하여 자막이 없는 영상도 100% 오디오 추출 및 Gemini STT 변환 지원.
4. **Gemini 3.6 Flash 모델 업그레이드 & Fallback 강화**:
   - Google 공식 지원 모델인 `gemini-3.6-flash`로 전면 교체.
   - `is_gemini_provider` 헬퍼를 통해 프론트엔드/백엔드 provider 판별 일원화.
   - OpenAI API 키 만료/부재 시 401 에러 즉시 감지 후 지체 없이 Gemini로 자동 Fallback 처리.
   - Gemini 분당 요청 한도(RPM) 고려하여 비동기 챕터 생성 동시성 한도를 3으로 최적화.

### ✅ Supabase Auth & Security System (프로덕션 라이브 & 모바일 검증 완료)
- **Google 1클릭 로그인 & 이메일 가입**: `frontend/src/app/login/page.tsx`
- **Edge Middleware Session Guard**: `frontend/src/middleware.ts` (비인가 사용자 자동 `/login` 리다이렉트)
- **Header Profile & Auth Widget**: `frontend/src/components/AuthStatusWidget.tsx` (유저 프로필 및 원클릭 로그아웃)
- **Supabase URL Configuration**:
  - `Site URL`: `https://interactive-video-study-guide-syste.vercel.app`
  - `Redirect URLs`: `https://interactive-video-study-guide-syste.vercel.app/auth/callback`, `https://interactive-video-study-guide-syste.vercel.app/**`

### ✅ Guide Mode (가이드 모드)
- 유튜브 URL 입력 ➡️ 자막/오디오 추출 ➡️ Gemini 3.6 Flash 기반 목차 및 7개 챕터/퀴즈/Feynman 비유 완벽 생성 (`backend/routers/guide.py`).

### ✅ Discussion Mode (토론 모드)
- 학습서 본문 텍스트 드래그/하이라이트 ➡️ 소크라테스식 AI 튜터 챗팅 (`backend/routers/discussion.py`).

### ⚠️ Admin Health Dashboard
- UI (`frontend/src/app/admin/health/page.tsx`): Recharts 기반 시계열/도넛 차트 및 로그 인스펙터.

### ❌ Curriculum Mode (완전 삭제됨)
- 커리큘럼 모드는 유저 요청으로 완전 삭제되었으므로 존재한다고 가정하지 말 것.

---

## 3. 백엔드 인프라 최적화 완료 내역 (AWS EC2)

1. **초경량 도커 컨테이너화 (1.8GB ➡️ 150MB)**:
   - 미사용 대용량 패키지(`torch`, `transformers`, `chromadb`, `pymupdf`)를 완전 제거하고, 순수 파이썬 `pypdf`, `google-genai`, `yt-dlp`, `celery`, `redis`, `sqlalchemy`, `python-multipart`로 다이어트 완료.
2. **도커 단일 빌드(Single-Pass) 구조**:
   - `studyguide-backend:latest` 1회 빌드 후 FastAPI와 Celery Worker가 동일 이미지를 즉시 공유 기동.
3. **EBS 볼륨 및 메모리 설정**:
   - AWS EBS 볼륨: 20GB 확장 완료 (Free Tier 매월 30GB 무료 범위 내)
   - Swap Memory: 1GB 가상 메모리 활성화 완료

---

## 4. 환경변수 관리 가이드

### 프론트엔드 (Vercel Environment Variables)
- `BACKEND_API_URL`: `http://13.209.73.143:8000`
- `NEXT_PUBLIC_SUPABASE_URL`: Supabase Project URL
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`: Supabase Public Anon Key

### 백엔드 (AWS EC2 `backend/.env`)
- `APP_ENV`: `production`
- `SUPABASE_JWT_SECRET`: Supabase JWT Secret (HS256 서명 검증)
- `GEMINI_API_KEY`: Google Gemini API Key
- `REDIS_URL`: `redis://redis:6379/0`
- `CORS_ORIGINS`: `*`
- `DISABLE_AUTH`: `false`

---

## 5. 다음 작업(Next Steps) 추천 과제

1. **HTTPS / 도메인 보안 강화 (선택 사항)**:
   - 현재 프론트엔드(Vercel)는 HTTPS이나 백엔드(EC2)는 HTTP(`http://13.209.73.143:8000`)로 통신 중.
   - 브라우저 Mixed Content 경고 방지를 위해 Cloudflare Tunnel 또는 Let's Encrypt Nginx SSL 적용 고려.
2. **PostgreSQL / Neon DB 영구 데이터베이스 연동**:
   - 현재 SQLite 로컬 파일 기반(`jobs.db`) 동작 중이며, 필요시 Supabase/Neon PostgreSQL로 전환 가능.
3. **관리자 대시보드 백엔드 실데이터 API 연결**:
   - 현재 동적 Mock 데이터 기반인 Admin Health Dashboard를 실제 Celery/Redis 모니터링 API와 연결.
