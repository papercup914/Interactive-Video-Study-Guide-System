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

### 5) [기능 구현] 가이드 상세 뷰어(`/guide/[jobId]`) 내 실시간 9종 프리셋 전환 & 매트릭스 탐색기 탑재 (Completed)
- **배경 및 문제점**: 가이드 뷰어 내에서 요약 분량이나 설명 방식을 변경할 때, 이미 생성된 프리셋이 존재함에도 불구하고 무조건 재생성 대기 및 홈 리다이렉트가 발생하던 한계 해결.
- **해결 내역**:
  1. [`backend/routers/guide.py`](file:///i:/Interactive%20Video%20Study%20Guide%20System/backend/routers/guide.py):
     - 동일 비디오 ID/문서의 9종 형제 프리셋 목록을 즉시 조회하는 `GET /api/guide/presets` 엔드포인트 구현.
     - `normalize_length_preset`, `normalize_analogy_preset` 정규화 함수 탑재로 영문/비표준 프리셋 값을 표준 3x3 한글 명칭으로 자동 변환.
  2. [`frontend/src/app/guide/[jobId]/page.tsx`](file:///i:/Interactive%20Video%20Study%20Guide%20System/frontend/src/app/guide/%5BjobId%5D/page.tsx):
     - 요약 분량/설명 방식 드롭다운 변경 시, 이미 생성된 프리셋이면 즉시 해당 가이드로 화면 전환.
     - 상단 툴바에 **"9종 프리셋 탐색기 (3x3 매트릭스)" 팝업 모달 (`ViewerPresetMatrixModal`)** 탑재.
     - 현재 열람 중인 가이드에 대한 강제 Fallback 주입 로직으로 어떤 상황에서도 현재 가이드가 "현재 열람 중" 뱃지로 100% 매핑되도록 보장.
     - 타이틀 정제 로직 탑재 (`- YouTube` 접미사 제거).
### 6) [버그 해결] 대시보드와 가이드 상세 뷰어 간 9종 프리셋 목록 및 제목 불일치 이슈 완전 해결 (Resolved)
- **배경 및 문제점**: 메인 대시보드에서는 동일 영상(예: `LLM을 사용하는 방법`)의 프리셋 2개가 정상 표시되나, 가이드 상세 페이지에서는 1개만 표시되거나 미생성으로 나타나는 현상 발생.
- **원인 분석**:
  1. AWS EC2 백엔드에 `GET /api/guide/presets` 엔드포인트가 아직 배포(git pull & restart)되지 않아 405/404 오류 발생.
  2. 프론트엔드 상세 페이지에서 백엔드 API 실패 시 전체 히스토리(`/api/guide/history`) 기반 클라이언트 Fallback 매핑이 없어 현재 가이드 1개만 기본값으로 주입됨.
- **해결 조치**:
  1. [`frontend/src/app/guide/[jobId]/page.tsx`](file:///i:/Interactive%20Video%20Study%20Guide%20System/frontend/src/app/guide/%5BjobId%5D/page.tsx):
     - `fetchSiblingPresets`에 **2단계 강력한 Fallback 메커니즘** 탑재 (1차: `/api/guide/presets`, 실패 시 2차: `/api/guide/history`에서 `extractVideoKey` 기반으로 완벽 자동 조립).
     - `ViewerPresetMatrixModal` 타이틀 정제 로직 강화 (기본 텍스트인 경우 형제 가이드의 실제 유효한 비디오 제목을 우선 탐색 및 적용).
### 7) [기능 구현] 파인만 및 인터랙티브 학습 모드 On/Off (몰입 읽기 모드) 탑재 (Completed)
- **배경 및 목적**: 퀴즈 및 파인만 롤플레잉 위젯에 대한 학습자의 인지적 부담과 피로도를 해소하고, 서술형 텍스트 본문 읽기에만 100% 집중할 수 있는 환경 제공.
- **구현 내역**:
  1. [`frontend/src/app/guide/[jobId]/page.tsx`](file:///i:/Interactive%20Video%20Study%20Guide%20System/frontend/src/app/guide/%5BjobId%5D/page.tsx):
     - `isInteractiveMode` 상태 관리 및 브라우저 `localStorage`(`interactive_mode_enabled`) 연동으로 사용자 설정 영구 유지.
     - 좌측 옵션 툴바 및 우측 탭 헤더에 직관적인 모드 전환 스위치(`💡 인터랙티브 모드` <-> `📖 몰입 읽기 모드`) 탑재.
     - 모드 OFF 시 `<feynman>`, `<quiz>`, `<steptracer>`, `<mnemonic>`, `<procedure>` 컴포넌트를 `null` 처리하여 순수 본문 텍스트만 깔끔하게 렌더링.
  2. **검증**: `npm run build` (Turbopack) 100% 성공 (에러 0건).

---

## 3. Notion 문서 관리 현황

1. **[공식 이슈 보드] [📋 Interactive Video Study Guide System 이슈 리포트 (통합 대시보드)](https://app.notion.com/p/3cba8db03fbe80a7972be85c1b2c2202)**:
   - 📄 [[Bug Report] 대시보드와 가이드 상세 뷰어 간 9종 프리셋 표시 및 제목 불일치 이슈](https://app.notion.com/p/Bug-Report-9-Resolved-3cca8db03fbe816ab4e0d79a54a30a34) (`Resolved` - 사용자 검증 완료)
   - 📄 [[Bug Report] 프리셋 탐색 모달 오픈 시 브라우저 GPU 과부하로 인한 타 탭 비디오 버벅임 이슈](https://app.notion.com/p/Bug-Report-GPU-Resolved-3cca8db03fbe8105ad81dfeb3323d5e5) (`Resolved` - 사용자 검증 완료)
   - 📄 [[Bug Report] 2시간 이상 장문 유튜브 영상 가이드 생성 이슈](https://app.notion.com/p/Bug-Report-2-Resolved-3cca8db03fbe81059afada2b6b96d034) (`Resolved`)
   - 📄 [[Bug Report] Vercel 프로덕션 가이드 생성 시 유튜브 봇 감지 오디오 다운로드 실패 이슈](https://app.notion.com/p/Bug-Report-Vercel-Resolved-3cba8db03fbe81e4a59fe0d3e1301b40) (`Resolved`)
2. **[개발/가동 가이드]**:
   - 📄 **[🚀 [운영 가이드] 로컬 개발부터 Vercel & AWS EC2 배포 및 서버 재시작 완전 정복 매뉴얼](https://app.notion.com/p/Vercel-AWS-EC2-3cca8db03fbe8110bd96cb12c92da8cf)** (전체 아키텍처, 터미널 & SSH 명령어, 실전 트러블슈팅 및 퀵 치트시트 완비).
   - 📄 [[프로젝트 작업 시작 및 터미널 3대 프로세스 가이드]](https://app.notion.com/p/3-3cba8db03fbe81b9aedcf37d7f5b68b5).

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

### AWS EC2 운영 백엔드 업데이트
```bash
cd ~/Interactive-Video-Study-Guide-System
git pull origin main
docker compose restart fastapi
```

---

## 5. 다음 대화에서 이어서 진행할 수 있는 과제

1. **9종 프리셋 탐색기 사용자 최종 테스트 확인 후 Notion 상태를 `Resolved`로 전환**:
   - Notion 이슈 페이지(`3cca8db0-3fbe-81e8-a896-ec1fcb14d163`) 상태 업데이트.
2. **추가 유튜브 재생목록 대량 사전 생성 및 AWS 동기화**:
   - 관리자 대시보드(`/admin/batch`)에서 신규 추천 강의 재생목록(CS 전공 지식, 알고리즘, 최신 AI 기술 등)을 일괄 생성하여 AWS 운영 DB로 푸시.


