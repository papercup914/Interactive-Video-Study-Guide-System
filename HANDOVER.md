# 🤖 HANDOVER DOCUMENT (FOR NEXT LLM)
<!-- [KR] 🤖 인수인계 문서 (다음 LLM을 위한 가이드) -->

**WARNING**: This document contains the 100% unvarnished, factual state of the `i:\Interactive Video Study Guide System` codebase. Do not hallucinate features. Read this carefully before generating any code or making assumptions.
<!-- [KR] 경고: 이 문서는 현재 코드베이스의 100% 가감 없는, 있는 그대로의 사실만을 담고 있습니다. 존재하지 않는 기능을 지어내지(Hallucinate) 마십시오. 코드를 생성하거나 가정하기 전에 이 문서를 주의 깊게 읽으십시오. -->

---

## 1. System Architecture & Stack
<!-- [KR] 1. 시스템 아키텍처 및 기술 스택 -->
- **Frontend**: Next.js 16.2.10 (App Router), React 19.2.4, Tailwind CSS v4, Vercel 배포 준비 완료.
- **Backend**: FastAPI (Python 3.12), Celery, Redis, AWS EC2 (Free Tier) Docker Compose 배포 준비 완료.
- **Authentication & Cloud DB**: Supabase Auth (Google OAuth, 이메일 가입/로그인, JWT 세션 쿠키, Edge Middleware 보호).
- **Strategy**: 1인용/BYOK (Bring Your Own Key) 기반 0원 운영 아키텍처.

## 2. Implemented Features (The Truth)
<!-- [KR] 2. 실제 구현된 기능 (가감 없는 사실) -->

### ✅ Supabase Auth & Security System (IMPLEMENTED & TESTED)
<!-- [KR] ✅ Supabase 인증 및 보안 시스템 (구현 및 로컬 테스트 완료) -->
- **Google OAuth & Email Auth**: `frontend/src/app/login/page.tsx`에 Google 1클릭 로그인 및 이메일 가입 폼 구현 완료.
- **Edge Middleware Session Guard**: `frontend/src/middleware.ts` 및 `src/utils/supabase/middleware.ts`를 통해 비인가 사용자의 메인/가이드/관리자 페이지 접근 시 `/login` 자동 리다이렉트.
- **Header Profile & Logout Widget**: `frontend/src/components/AuthStatusWidget.tsx`로 로그인 유저 아바타/이메일 표시 및 원클릭 로그아웃 지원.
- **Backend JWT Verification**: `backend/auth.py`의 `get_current_user` 의존성이 `SUPABASE_JWT_SECRET` (HS256)을 검증. 5개 단위 테스트(`backend/test_auth.py`) 100% 통과.
- **Production Build Verified**: Next.js 16 프로덕션 빌드(`npm run build`) 오류 없이 성공 확인.

### ✅ Guide Mode (Fully Functional)
<!-- [KR] ✅ 가이드 모드 (정상 작동 중) -->
- **Flow**: User inputs YouTube URL -> `tasks.py` extracts transcript -> `llm.py` calls Gemini 3.1 Flash-Lite -> Generates Markdown -> Saves to disk -> Notifies frontend.
- **UI (`frontend/src/app/guide/[jobId]/page.tsx`)**: Renders markdown using `react-markdown`.

### ✅ Discussion Mode (Fully Functional)
<!-- [KR] ✅ 토론 모드 (정상 작동 중) -->
- **Flow**: User highlights text -> Hits `/api/discussion/chat`.
- **Backend (`backend/routers/discussion.py`)**: Uses Gemini as a Socratic tutor based on highlighted text.

### ⚠️ Admin Health Dashboard (Mock Backend, Real UI)
<!-- [KR] ⚠️ 관리자 대시보드 (백엔드는 가짜 목업, UI는 진짜) -->
- **UI (`frontend/src/app/admin/health/page.tsx`)**: Recharts 기반 Time-Series, Donut 차트 및 로그 인스펙터.
- **State (`frontend/src/hooks/useAdminHealth.ts`)**: 동적 Mock 데이터 생성기 기반 동작.

### ✅ Automated AI Persona QA System (IMPLEMENTED - V2)
<!-- [KR] ✅ AI 페르소나 자동화 QA 시스템 (V2 고도화 완료) -->
- **Status**: `qa_harness/` 디렉터리에 블랙박스 API 테스트 하네스 및 페르소나 평가 체계 구축 완료.

### ❌ Curriculum Mode (COMPLETELY DELETED)
<!-- [KR] ❌ 커리큘럼 모드 (완전히 삭제됨) -->
- **Status**: 커리큘럼 모드는 유저 요청으로 완전 삭제되었으므로 존재한다고 가정하지 말 것.

---

## 3. Deployment Infrastructure Assets
<!-- [KR] 3. 배포 인프라 및 자동화 자산 -->
- `DEPLOYMENT_GUIDE.md`: Vercel(웹) 및 AWS EC2(백엔드) 분리 배포 완전 가이드.
- `scripts/ec2_setup.sh`: Ubuntu EC2 2GB Swap 메모리, Docker, 방화벽 원클릭 자동 셋업 스크립트.
- `scripts/deploy_backend.sh`: 백엔드 컨테이너 빌드 및 백그라운드 기동 스크립트.
- `scripts/health_check.py`: 백엔드 헬스체크 및 API 정상 여부 자동 진단 스크립트.
- `Dockerfile.backend` & `docker-compose.yml`: EC2 배포용 컨테이너 명세.
- `frontend/vercel.json`: Vercel 배포 및 보안 헤더 최적화 설정.

---

## 4. Current Deployment Progress (Next Steps for Next Agent)
<!-- [KR] 4. 현재 배포 진행 상태 및 다음 작업 가이드 -->
1. **GitHub 저장소 연동**:
   - `git add`, `git commit` 및 원격 저장소(`https://github.com/papercup914/Interactive-Video-Study-Guide-System.git`) 등록 완료.
   - 유저가 `git push -u origin main`을 실행하여 코드를 업로드할 예정.
2. **AWS EC2 인스턴스 생성 완료**:
   - 인스턴스 이름: `studyguide-backend` (Ubuntu 24.04, 서울 리전, 포트 8000/22 오픈 완료).
   - 접속 후 `ec2_setup.sh` ➡️ `backend/.env` 작성 ➡️ `deploy_backend.sh` 실행 대기 중.
3. **Vercel 프론트엔드 연동 대기**:
   - GitHub 저장소 Import 후 환경변수(`NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`, `BACKEND_API_URL=http://<EC2-IP>:8000`) 등록 및 배포.
4. **Supabase Redirect URL에 Vercel 도메인 추가**:
   - 배포 후 생성된 `https://<vercel-domain>/auth/callback` 등록.
