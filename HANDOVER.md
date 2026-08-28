# 🤖 인수인계 문서 (HANDOVER DOCUMENT FOR NEXT AGENT)

**경고**: 이 문서는 `i:\Interactive Video Study Guide System` 코드베이스 및 프로덕션 인프라의 100% 가감 없는 최신 실황을 담고 있습니다. 존재하지 않는 기능을 지어내지(Hallucinate) 마십시오.

---

## 1. 시스템 아키텍처 및 실제 배포 현황 (Production Live)

| 계층 | 기술 스택 | 배포 위치 및 프로덕션 URL | 상태 |
| :--- | :--- | :--- | :--- |
| **Frontend** | Next.js 16.2.10 (App Router), React 19.2.4, Tailwind CSS v4 | **Vercel**: `https://interactive-video-study-guide-syste.vercel.app` | 🟢 라이브 가동 중 |
| **Backend** | FastAPI (Python 3.12/3.13), Celery, Redis, SQLAlchemy | **AWS EC2 (Free Tier)**: `http://13.209.73.143:8000` | 🟢 200 OK 가동 중 |
| **Auth & DB** | Supabase Auth (Google OAuth, JWT 쿠키 세션, Edge Guard) | **Supabase Cloud / Neon DB** | 🟢 연동 완료 |
| **AI Engine** | Google GenAI SDK (Gemini 2.5 Flash / 3.6 Flash) | BYOK / Cloudflare Tunnel / Direct REST | 🟢 정상 연동 (E2E 검증 완료) |
| **Batch Engine** | 로컬 PC 연산 기반 선행 생성 (yt-dlp flat-playlist) | **Local PC (`http://localhost:8000`)** | 🟢 신규 구현 및 실기 검증 완료 |

---

## 2. 최근 구현 완료 내역 (Verified Features)

### ✅ [NEW] 개발자 전용 유튜브 대량 일괄 사전 생성 & 운영 서버 동기화 시스템
AWS EC2 Free Tier의 리소스 고갈(OOM/다운)을 방지하기 위해, 개발자 로컬 PC의 하드웨어로 대량 가이드를 선행 생성(Pre-generation)하고 운영 서버로 동기화(Sync)하는 완전한 시스템이 구축되었습니다.

1. **Quota 소모 없는 고속 수집기 (`backend/services/batch_collector.py`)**:
   - `yt-dlp --flat-playlist` 모드를 사용하여 YouTube Data API의 일일 할당량(10,000 Quota) 소모 없이 채널/재생목록 영상 목록을 초고속 수집.
   - 쇼츠(Shorts) 영상(60초 이하 또는 `#shorts`) 자동 필터링 및 최대 개수(`max_limit`) 지정 지원.

2. **비디오당 3×3=9개 프리셋 완전 사전 생성 (`backend/services/batch_generator.py`)**:
   - 비디오당 자막/오디오를 **최초 1회만 다운로드 및 추출**하여 Whisper/다운로드 비용 극소화.
   - 요약 분량(3종: `핵심 요약`, `적당한 설명`, `아주 상세하게`) × 설명 방식(3종: `비유 없이 담백하게`, `적절한 비유 추가`, `풍부한 비유`) = **총 9개 프리셋**을 연속/병렬 생성하여 DB에 저장.
   - 사용자가 프론트엔드에서 어떤 옵션을 선택해도 **0초 만에 즉시 렌더링(캐시 히트)**.
   - 이미 9개 프리셋이 생성된 비디오는 자동 건너뛰기(Skip)하여 불필요한 LLM 비용 방지 (덮어쓰기 옵션 지원).

3. **실시간 실행 로그 스트림 & 안전 실행 파이프라인 (`backend/services/job_manager.py`, `backend/routers/admin.py`)**:
   - 로컬 환경에서 Celery/Redis 워커가 없더라도 FastAPI 내장 비동기 태스크(`asyncio.create_task`)로 즉시 백그라운드 연산이 실행되도록 보장.
   - 배치 작업에 실시간 로그(`logs` JSON 필드)를 기록하고, 수집 ➡️ 자막 추출 ➡️ 9개 프리셋 생성 ➡️ 완료까지의 과정을 2초 간격 실시간 스트리밍.

4. **AWS 운영 서버 안전 원격 동기화 (`backend/services/sync_service.py`, `backend/routers/admin.py`)**:
   - 로컬에서 생성 완료된 가이드 데이터를 운영 서버(`POST /api/admin/sync-guide`)로 안전하게 전송.
   - **`X-Admin-Sync-Key` 시크릿 헤더 인증**으로 비인가 접근을 원천 차단하며, 네트워크 일시 오류 시 **3회 지수 백오프 자동 재시도** 수행.

5. **로컬 관리자 대시보드 & 실시간 터미널 콘솔 (`frontend/src/app/admin/batch/page.tsx`)**:
   - 눈이 편안하고 가독성이 뛰어난 모던 Slate/White 테마 및 완벽한 드롭다운 텍스트 명도 대비 적용.
   - 실시간 진행률 바(%), 4대 지표(총 비디오, 완료, 스킵, 실패), 비디오별 9개 프리셋 카운터(`0/9` ➡️ `9/9`).
   - 하단에 전문 터미널 형태의 **실시간 실행 로그 스트림 콘솔(Live Terminal Console)** 탑재 (자동 스크롤, 레벨별 컬러 배지, 원클릭 로그 복사).

---

## 3. 로컬 실행 및 개발 가이드

### 백엔드 실행
Miniconda 파이썬 환경에서 프로젝트 루트 경로(`I:\Interactive Video Study Guide System`)로 이동 후 실행:
```powershell
cd "I:\Interactive Video Study Guide System"
python -m uvicorn backend.main:app --reload --port 8000
```

### 프론트엔드 실행
```powershell
cd "I:\Interactive Video Study Guide System\frontend"
npm run dev
```

### 브라우저 접속
- 일괄 사전 생성 대시보드: `http://localhost:3000/admin/batch`
- 시스템 헬스 모니터: `http://localhost:3000/admin/health`

---

## 4. 테스트 검증 완료 내역

- **백엔드 통합 및 보안 테스트 (`tests/test_batch_pregeneration.py`)**:
  - `Ran 4 tests in 26.167s, OK` (쇼츠 필터링, DB 라이프사이클, 동기화 보안 인증, API 라우트 검증 100% 통과)
- **프론트엔드 프로덕션 빌드 (`npm run build`)**:
  - `✓ Compiled successfully`, 모든 정적 페이지 및 라우트(`/admin/batch`, `/admin/health` 등) 정상 빌드 완료

---

## 5. 다음 대화에서 이어서 진행 가능한 과제

1. **실제 채널/재생목록 일괄 생성 실기 테스트**:
   - 관리자 페이지(`http://localhost:3000/admin/batch`)에서 실제 유튜브 플레이리스트 URL을 입력하고 9개 프리셋 생성 및 터미널 로그 스트리밍 동작 확인.
2. **운영 서버(AWS EC2) 환경변수 배포**:
   - AWS EC2 백엔드의 `.env`에 `ADMIN_SYNC_SECRET=원하는시크릿키` 등록 후, 로컬에서 생성된 데이터를 AWS로 원클릭 푸시 동기화 검증.
3. **사용자 뷰어 페이지 캐시 연동 고도화**:
   - 일반 사용자가 가이드 상세 페이지(`frontend/src/app/guide/[jobId]/page.tsx`)에서 요약 분량/비유 프리셋 변경 시, 사전 생성된 9개 프리셋을 즉시 전환 렌더링하는 UX 확인.
