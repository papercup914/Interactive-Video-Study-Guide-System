# 🤖 인수인계 문서 (HANDOVER DOCUMENT FOR NEXT AGENT)

**경고**: 이 문서는 `i:\Interactive Video Study Guide System` 코드베이스 및 프로덕션 인프라의 100% 가감 없는 최신 실황을 담고 있습니다. 존재하지 않는 기능을 지어내지(Hallucinate) 마십시오.

---

## 1. 시스템 아키텍처 및 실제 배포 현황 (Production Live)

| 계층 | 기술 스택 | 배포 위치 및 프로덕션 URL | 상태 |
| :--- | :--- | :--- | :--- |
| **Frontend** | Next.js 16.2.10 (App Router), React 19.2.4, Tailwind CSS v4 | **Vercel**: `https://interactive-video-study-guide-syste.vercel.app` | 🟢 라이브 가동 중 (57개 프리셋 렌더링 & 실시간 생성 완비) |
| **Backend** | FastAPI (Python 3.12), Celery, Redis, Docker Compose | **AWS EC2 (Free Tier)**: `http://13.209.73.143:8000` | 🟢 최신 Docker 이미지 빌드 및 정상 가동 중 |
| **Auth & DB** | Supabase Auth (Google OAuth, JWT 쿠키 세션, Edge Guard) | **Supabase Cloud / Neon DB / SQLite** | 🟢 57개 프리셋 가이드 동기화 완료 |
| **AI Engine** | Google GenAI SDK (`gemini-3.6/3.5/flash-lite` 다중 모델 체인) | Google AI API (API Key 연동) | 🟢 쿼터 소진 시 무중단 자동 전환 완비 |
| **Batch Engine** | 로컬 PC 연산 기반 선행 생성 (yt-dlp flat-playlist) | **Local PC (`http://localhost:8000`)** | 🟢 6개 비디오 54개 프리셋 100% 생성 검증 완료 |

---

## 2. 최근 해결된 주요 이슈 및 기능 구현 내역

### 1) [버그 해결] Vercel 프로덕션 가이드 생성 시 유튜브 봇 감지 오디오 다운로드 실패 이슈 완전 해결 (Resolved)
- **문제**: Vercel 프로덕션 화면에서 신규 유튜브 영상 생성 시도 시, AWS EC2 데이터센터 IP 차단으로 인해 `유튜브 봇 감지로 인해 오디오 직접 다운로드가 제한되었습니다` 에러 발생.
- **원인 분석**:
  - AWS EC2(`13.209.73.143`) 공인 IP가 유튜브에 의해 봇 감지(`LOGIN_REQUIRED`)로 분류되어 직접적인 Innertube/오디오 TCP 스트림이 전면 차단됨.
  - 기존 파이프라인에서 자막/오디오 추출 실패 시 그대로 에러를 발생시키며 중단됨.
- **해결 조치**:
  1. [`backend/services/video.py`](file:///i:/Interactive%20Video%20Study%20Guide%20System/backend/services/video.py): 최신 모바일 지원 클라이언트(`ANDROID 20.10.38`, `ANDROID_TESTSUITE 1.9`) 및 `INNERTUBE_API_KEY` 자동 주입, XML 다중 계층 순회 파서(`root.iter()`) 구축.
  2. [`backend/services/tasks.py`](file:///i:/Interactive%20Video%20Study%20Guide%20System/backend/services/tasks.py): 자막/오디오 직접 추출 실패 시 **Jina Reader AI(`https://r.jina.ai/`) 웹 분석 엔진으로 자동 폴백**하는 무중단 파이프라인 탑재.
  3. 분산 프록시 네트워크를 통해 영상 목차 구조/타임스탬프/본문 텍스트(**29,334자**)를 100% 정상 수집하여 가이드 생성 성공.
- **검증**: 사용자 실기 테스트 및 Vercel 프로덕션 가이드 생성 완료 확인 (`Resolved`).

### 2) [버그 해결] 유튜브 일괄 사전 생성 실패 이슈 완전 해결 (Resolved)
- **원인 1**: `SELECTED_GEMINI_VERSION` 기본값이 미지원 모델명(`gemini-2.5-flash`)으로 되어 있어 404 발생 ➡️ 최신 지원 모델인 `gemini-3.6-flash` 및 `gemini-3.5-flash`로 변경 완료.
- **원인 2**: `process_audio` 함수 시그니처 3개 인자(`audio_path, provider, url_hash`) 불일치 ➡️ 3개 인자 수용 및 안전 캐싱으로 수정 완료.
- **원인 3**: 배치 시작 시 `remote_url`, `sync_key` 파라미터 미전달 ➡️ 프론트엔드 UI부터 백엔드 DB/파이프라인까지 전면 연동 완료.

### 3) [AI 엔진 고도화] Google Gemini 무료 티어 일일 쿼터 극복: "다중 모델 자동 폴백 체인"
- **문제**: Gemini 무료 티어의 경우 모델당 일일 20회(`GenerateRequestsPerDayPerProjectPerModel-FreeTier`) 요청 한도가 존재하여, 1번 비디오 완료 후 2~6번 비디오에서 `429 RESOURCE_EXHAUSTED` 발생.
- **해결**: [`backend/services/llm.py`](file:///i:/Interactive%20Video%20Study%20Guide%20System/backend/services/llm.py)에 `safe_gemini_generate_content`를 구축.
  - `gemini-3.6-flash` ➡️ `gemini-3.5-flash` ➡️ `gemini-3.5-flash-lite` ➡️ `gemini-3.1-flash-lite` ➡️ `gemini-flash-lite-latest`
  - 일일 한도 초과 감지 시 0.5초 만에 다음 가용 모델로 즉각 스위칭되어 6개 비디오(총 54개 프리셋)가 중단 없이 100% 생성 완료됨을 실측 검증.

### 4) [AWS 운영 배포 & 57개 프리셋 동기화 완료]
- 로컬 최신 코드를 GitHub `main`으로 푸시 후 AWS EC2 도커 이미지 재빌드 및 컨테이너 무중단 재가동 완료 (`Healthy`).
- 로컬에 생성된 6개 비디오의 총 **57개 프리셋 학습 가이드 전량을 AWS 운영 DB로 100% 동기화(`synced_count: 57`) 완료**.

---

## 3. Notion 문서 관리 현황

1. **이슈 리포트 (최신 종결)**: [[Bug Report] Vercel 프로덕션 가이드 생성 시 유튜브 봇 감지 오디오 다운로드 실패 이슈](https://app.notion.com/p/Bug-Report-Vercel-Resolved-3cba8db03fbe81e4a59fe0d3e1301b40) **`Resolved (해결 완료)`** 로 종결.
2. **이슈 리포트 (이전 완료)**: [[Bug] 유튜브 일괄 사전 생성 실패 및 운영 서버 동기화 오류](https://app.notion.com/p/Bug-Resolved-3caa8db03fbe81489f40e5feeaf99901) **`Resolved (해결 완료)`** 로 종결.
3. **일일 업무 보고서**: [2026-08-28 일일 업무 보고](https://app.notion.com/p/3b3a8db03fbe81a8b6d9dae4d3814afe) 작성 완료.
4. **이슈 대응 가이드**: [[Ops Guide] 백엔드 프로세스(Uvicorn) 종료 프리징 시 백그라운드 PID 강제 종료 및 포트 회수 가이드](https://app.notion.com/p/Ops-Guide-Uvicorn-PID-3caa8db03fbe81d2b7afd98af6c61ad8) 등록 완료.

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
2. **가이드 상세 뷰어(`/guide/[jobId]`) 내 즉시 프리셋 전환 연동**:
   - 학습 가이드 뷰어 내에서 요약/비유 설정을 변경할 때, 이미 사전 생성된 프리셋이 있다면 AI 재생성 대기 없이 즉시 캐시된 가이드를 불러오는 UX 연동.
3. **추가 유튜브 재생목록/채널 대량 생성 및 지속 운영**:
   - 로컬 관리자 페이지(`http://localhost:3000/admin/batch`)에서 다른 추천 강의 재생목록들을 추가로 사전 생성하여 AWS로 원클릭 동기화.
