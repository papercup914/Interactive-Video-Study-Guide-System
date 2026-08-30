# 🤖 인수인계 문서 (HANDOVER DOCUMENT FOR NEXT AGENT)

**경고**: 이 문서는 `i:\Interactive Video Study Guide System` 코드베이스 및 프로덕션 인프라의 100% 가감 없는 최신 실황을 담고 있습니다. 존재하지 않는 기능을 지어내지(Hallucinate) 마십시오.

---

## 1. 시스템 아키텍처 및 실제 배포 현황 (Production Live)

| 계층 | 기술 스택 | 배포 위치 및 프로덕션 URL | 상태 |
| :--- | :--- | :--- | :--- |
| **Frontend** | Next.js 16.2.10 (App Router), React 19.2.4, Tailwind CSS v4 | **Vercel**: `https://interactive-video-study-guide-syste.vercel.app` | 🟢 라이브 가동 중 (대표 영상 그룹핑 & 9종 프리셋 셀렉터 적용) |
| **Backend** | FastAPI (Python 3.12), Celery, Redis, Docker Compose | **AWS EC2 (Free Tier)**: `http://13.209.73.143:8000` | 🟢 최신 Docker 이미지 빌드 및 정상 가동 중 |
| **Auth & DB** | Supabase Auth (Google OAuth, JWT 쿠키 세션, Edge Guard) | **Supabase Cloud / Neon DB / SQLite** | 🟢 57개 프리셋 가이드 동기화 완료 |
| **AI Engine** | Google GenAI SDK (`gemini-3.6/3.5/flash-lite` 다중 모델 체인) | Google AI API (API Key 연동) | 🟢 쿼터 소진 시 무중단 자동 전환 완비 |
| **Batch Engine** | 로컬 PC 연산 기반 선행 생성 (yt-dlp flat-playlist) | **Local PC (`http://localhost:8000`)** | 🟢 6개 비디오 54개 프리셋 100% 생성 검증 완료 |

---

## 2. 최근 해결된 주요 이슈 및 기능 구현 내역

### 1) [UX 전면 개편] 메인 페이지 학습 가이드 목록 비디오 단위 그룹핑 및 9종 프리셋 탐색기 탑재 (Completed)
- **배경 및 문제점**: 57개의 사전 생성된 프리셋 가이드가 메인 페이지에 개별 카드로 나열되어 심각한 화면 중복 및 스크롤 피로도 발생.
- **해결 내역**:
  1. [`frontend/src/app/page.tsx`](file:///i:/Interactive%20Video%20Study%20Guide%20System/frontend/src/app/page.tsx): 동일한 영상 URL/비디오 ID를 기준으로 **"1개의 대표 영상 카드"**로 그룹핑하여 깔끔하게 정리 (총 57개 ➡️ 6~7개 대표 카드로 정돈).
  2. **카드 내 인터랙티브 9종 프리셋 셀렉터**: 요약 분량(3종) × 설명 방식(3종) 드롭다운을 통해 원하는 맞춤형 가이드로 원클릭 즉시 이동.
  3. **3x3 프리셋 탐색 모달 (`PresetMatrixModal`)**: `9종 전체보기` 클릭 시 생성된 프리셋과 미생성 프리셋을 한눈에 매트릭스로 확인하고 바로 열 수 있는 팝업 뷰어 제공.
  4. **그룹 일괄 삭제 지원**: 해당 영상의 모든 프리셋(N개)을 한 번에 안전하게 삭제할 수 있는 확인 모달 탑재.

### 2) [버그 해결] Vercel 프로덕션 가이드 생성 시 유튜브 봇 감지 오디오 다운로드 실패 이슈 완전 해결 (Resolved)
- **문제**: AWS EC2 데이터센터 IP 차단으로 인해 `Sign in to confirm you're not a bot` 오류 발생.
- **해결 조치**:
  1. [`backend/services/video.py`](file:///i:/Interactive%20Video%20Study%20Guide%20System/backend/services/video.py): 최신 Android 20.10.38 모바일 Innertube API 및 API Key 자동 주입.
  2. [`backend/services/tasks.py`](file:///i:/Interactive%20Video%20Study%20Guide%20System/backend/services/tasks.py): 자막/오디오 직접 다운로드 차단 시 **Jina Reader AI 웹 분석 엔진(`https://r.jina.ai/`)으로 자동 폴백**하여 29,334자 분석 텍스트 확보 및 무중단 가이드 생성 성공.

### 4) [버그 해결] 2시간 이상 장문 유튜브 영상 가이드 생성 및 2단계 엄격 출력 체계(2-Stage Strict Output Structure) 반영 (Resolved)
- **문제**: 2시간 11분 장문 영상(Andrej Karpathy 등)에서 구버전 캐시 오염 및 본문 서술 누락으로 질문식 태그만 노출되던 현상.
- **해결 조치**:
  1. [`backend/services/llm.py`](file:///i:/Interactive%20Video%20Study%20Guide%20System/backend/services/llm.py): [Part 1: 1,500~3,000자 서술형 본문] + [Part 2: 최하단 인터랙티브 태그] 2단계 엄격 프롬프트 전면 개편.
  2. **캐시 무결성 검증 및 자동 정제**: 1,000자 미만이거나 태그 단독 캐시 파일(291개) 일괄 삭제 및 서버 기동 시 자동 정제 훅 탑재.
  3. **서버 사이드 본문 누락 감지 및 3회 에스컬레이션 재시도 가드레일**: 본문 누락 시 강력한 경고 지침으로 자동 재시도.
  4. **운영 서버(AWS EC2) 최신 배포 및 컨테이너 재기동 완료**: 전 챕터 2,300자 이상의 풍부한 서술형 본문 생성 검증 완료.

---

## 3. Notion 문서 관리 현황

1. **[공식 이슈 보드] [📋 Interactive Video Study Guide System 이슈 리포트 (통합 대시보드)](https://app.notion.com/p/3cba8db03fbe80a7972be85c1b2c2202)**:
   - 📄 [[AI 가이드 생성] 자막 없는 유튜브 오디오 Whisper 변환 시 Quota 소진으로 인한 생성 실패](https://app.notion.com/p/AI-Whisper-Quota-3c6a8db03fbe81ed95b1e6fa2f24bb14) (`Resolved`)
   - 📄 [[Bug] 유튜브 일괄 사전 생성 실패 및 운영 서버 동기화 오류](https://app.notion.com/p/Bug-Resolved-3caa8db03fbe81489f40e5feeaf99901) (`Resolved`)
   - 📄 [[Bug Report] Vercel 프로덕션 가이드 생성 시 유튜브 봇 감지 오디오 다운로드 실패 이슈](https://app.notion.com/p/Bug-Report-Vercel-Resolved-3cba8db03fbe81e4a59fe0d3e1301b40) (`Resolved`)
   - 📄 [[Bug Report] 2시간 이상 장문 유튜브 영상 가이드 생성 이슈](https://app.notion.com/p/Bug-Report-2-Resolved-3cca8db03fbe81059afada2b6b96d034) (`Resolved`)
2. **[개발/가동 가이드] [🚀 프로젝트 작업 시작 및 터미널 3대 프로세스 가이드](https://app.notion.com/p/3-3cba8db03fbe81b9aedcf37d7f5b68b5)** (대분류 및 하위 4개 세부 매뉴얼 완비).

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

### 로컬 Celery 워커 실행
```powershell
docker run -d --name studyguide-local-redis -p 6379:6379 redis:7-alpine
cd "I:\Interactive Video Study Guide System"
celery -A backend.celery_app worker --loglevel=info -P solo
```

---

## 5. 다음 대화에서 이어서 진행할 수 있는 과제

1. **가이드 상세 뷰어(`/guide/[jobId]`) 내 실시간 프리셋 전환 연동**:
   - 뷰어 내부에서 요약 분량/설명 방식 토글 변경 시, 이미 생성된 다른 8종 프리셋이 있으면 AI 재생성 대기 없이 즉시 해당 프리셋으로 전환 렌더링하는 UX 연동.
2. **추가 유튜브 재생목록 대량 사전 생성 및 AWS 동기화**:
   - 관리자 대시보드(`/admin/batch`)에서 신규 추천 강의 재생목록(CS 전공 지식, 알고리즘, 최신 AI 기술 등)을 일괄 생성하여 AWS 운영 DB로 푸시.
