# 🤖 인수인계 문서 (HANDOVER DOCUMENT FOR NEXT AGENT)

**경고**: 이 문서는 `i:\Interactive Video Study Guide System` 코드베이스 및 프로덕션 인프라의 100% 가감 없는 최신 실황을 담고 있습니다. 존재하지 않는 기능을 지어내지(Hallucinate) 마십시오.

---

## 1. 시스템 아키텍처 및 실제 배포 현황 (Production Live)

| 계층 | 기술 스택 | 배포 위치 및 프로덕션 URL | 상태 |
| :--- | :--- | :--- | :--- |
| **Frontend** | Next.js 16.2.10 (App Router), React 19.2.4, Tailwind CSS v4 | **Vercel**: `https://interactive-video-study-guide-syste.vercel.app` | 🟢 라이브 가동 중 (57개 프리셋 렌더링 확인) |
| **Backend** | FastAPI (Python 3.12), Celery, Redis, Docker Compose | **AWS EC2 (Free Tier)**: `http://13.209.73.143:8000` | 🟢 최신 Docker 이미지 빌드 및 정상 가동 중 |
| **Auth & DB** | Supabase Auth (Google OAuth, JWT 쿠키 세션, Edge Guard) | **Supabase Cloud / Neon DB / SQLite** | 🟢 57개 프리셋 가이드 동기화 완료 |
| **AI Engine** | Google GenAI SDK (`gemini-3.6/3.5/flash-lite` 다중 모델 체인) | Google AI API (API Key 연동) | 🟢 쿼터 소진 시 무중단 자동 전환 완비 |
| **Batch Engine** | 로컬 PC 연산 기반 선행 생성 (yt-dlp flat-playlist) | **Local PC (`http://localhost:8000`)** | 🟢 6개 비디오 54개 프리셋 100% 생성 검증 완료 |

---

## 2. 최근 해결된 주요 이슈 및 기능 구현 내역

### 1) [버그 해결] 유튜브 일괄 사전 생성 실패 이슈 완전 해결 (Resolved)
- **원인 1**: `SELECTED_GEMINI_VERSION` 기본값이 미지원 모델명(`gemini-2.5-flash`)으로 되어 있어 404 발생 ➡️ 최신 지원 모델인 `gemini-3.6-flash` 및 `gemini-3.5-flash`로 변경 완료.
- **원인 2**: `process_audio` 함수 시그니처 3개 인자(`audio_path, provider, url_hash`) 불일치 ➡️ 3개 인자 수용 및 안전 캐싱으로 수정 완료.
- **원인 3**: 배치 시작 시 `remote_url`, `sync_key` 파라미터 미전달 ➡️ 프론트엔드 UI부터 백엔드 DB/파이프라인까지 전면 연동 완료.

### 2) [AI 엔진 고도화] Google Gemini 무료 티어 일일 쿼터 극복: "다중 모델 자동 폴백 체인"
- **문제**: Gemini 무료 티어의 경우 모델당 일일 20회(`GenerateRequestsPerDayPerProjectPerModel-FreeTier`) 요청 한도가 존재하여, 1번 비디오 완료 후 2~6번 비디오에서 `429 RESOURCE_EXHAUSTED` 발생.
- **해결**: [`backend/services/llm.py`](file:///i:/Interactive%20Video%20Study%20Guide%20System/backend/services/llm.py)에 `safe_gemini_generate_content`를 구축.
  - `gemini-3.6-flash` ➡️ `gemini-3.5-flash` ➡️ `gemini-3.5-flash-lite` ➡️ `gemini-3.1-flash-lite` ➡️ `gemini-flash-lite-latest`
  - 일일 한도 초과 감지 시 0.5초 만에 다음 가용 모델로 즉각 스위칭되어 6개 비디오(총 54개 프리셋)가 중단 없이 100% 생성 완료됨을 실측 검증.

### 3) [AWS 운영 배포 & 동기화 완료]
- 로컬의 최신 코드를 GitHub `main` 브랜치로 커밋/푸시 완료 (`81d1651`).
- AWS EC2(`13.209.73.143`)에 SSH로 접속하여 `docker build -f Dockerfile.backend -t studyguide-backend:latest .` 최신 이미지 빌드 및 컨테이너 무중단 재가동 완료.
- 로컬에 생성된 6개 비디오의 총 **57개 프리셋 학습 가이드 전량을 AWS 운영 DB로 100% 동기화(`synced_count: 57`) 완료**.

### 4) [동기화 최적화 & 안정성]
- [`backend/services/sync_service.py`](file:///i:/Interactive%20Video%20Study%20Guide%20System/backend/services/sync_service.py): 타임아웃을 10초로 최적화하고 404/403 발생 시 즉시 중단(Fast-Fail)하여 불필요한 대기(18분 지연) 원천 제거.
- 프로세스 종료 시 Windows 소켓 락에 의한 터미널 프리징 대응 매뉴얼을 Notion에 구축.

---

## 3. Notion 문서 관리 현황

1. **일일 업무 보고서**: [2026-08-28 일일 업무 보고](https://app.notion.com/p/3b3a8db03fbe81a8b6d9dae4d3814afe) 작성 완료.
2. **이슈 리포트**: [[Bug] 유튜브 일괄 사전 생성 실패 및 운영 서버 동기화 오류](https://app.notion.com/p/Bug-Resolved-3caa8db03fbe81489f40e5feeaf99901) **`Resolved (해결 완료)`** 로 종결.
3. **이슈 대응 가이드**: [[Ops Guide] 백엔드 프로세스(Uvicorn) 종료 프리징 시 백그라운드 PID 강제 종료 및 포트 회수 가이드](https://app.notion.com/p/Ops-Guide-Uvicorn-PID-3caa8db03fbe81d2b7afd98af6c61ad8) 등록 완료.

---

## 4. 로컬 및 프로덕션 실행 가이드

### 로컬 백엔드 실행
```powershell
cd "I:\Interactive Video Study Guide System"
python -m uvicorn backend.main:app --reload --port 8000
```

### 로컬 프론트엔드 실행
```powershell
cd "I:\Interactive Video Study Guide System\frontend"
npm run dev
```

### AWS EC2 운영 서버 재배포 시 (필요 시)
```bash
ssh -i "C:\Users\radia\.ssh\studyguide-key.pem" ubuntu@13.209.73.143 "cd ~/Interactive-Video-Study-Guide-System && git pull origin main && docker build -f Dockerfile.backend -t studyguide-backend:latest . && docker compose up -d --force-recreate"
```

---

## 5. 다음 대화에서 이어서 진행할 수 있는 과제

1. **프론트엔드 메인 목록 UI 그룹핑 개선 (UX)**:
   - 현재 메인 페이지(`https://interactive-video-study-guide-syste.vercel.app/`)에서 동일 영상에 대해 9개의 프리셋 카드가 모두 개별 나열되는 현상을 **"1개의 대표 영상 카드"**로 묶고, 카드 클릭 시 9종 프리셋을 선택할 수 있도록 목록 UI 뷰 개선.
2. **추가 유튜브 재생목록/채널 대량 생성 및 지속 운영**:
   - 로컬 관리자 페이지(`http://localhost:3000/admin/batch`)에서 다른 추천 강의 재생목록들을 추가로 사전 생성하여 AWS로 원클릭 동기화./White 테마 및 완벽한 드롭다운 텍스트 명도 대비 적용.
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
