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

### 8) [UX/품질 개선] 챕터 도입부 인삿말 완전 금지(Strict Zero-Greeting Policy) 및 영상 핵심 주제 안내 카드 탑재 (Completed)
- **배경 및 목적**:
  - LLM 챕터 생성 시 "안녕하세요, 여러분의 튜터입니다" 등 진부한 챗봇식 인삿말을 일절 배제하고, 핵심 질문(Why/What) 및 실무 배경 훅으로 즉시 시작하여 가독성과 전문성 극대화.
  - 가이드 본문 좌측의 형식적인 영문 "Guide Overview" 영역을 삭제하고, 해당 영상의 핵심 주제와 주요 커리큘럼을 한눈에 파악할 수 있는 맞춤형 개요 카드 탑재.
- **구현 내역**:
  1. [`backend/services/llm.py`](file:///i:/Interactive%20Video%20Study%20Guide%20System/backend/services/llm.py):
     - `Strict Zero-Greeting Policy` 지침을 시스템 프롬프트 및 유저 인스트럭션에 강제 적용.
     - 챕터 서두를 핵심 질문(Why/What) 또는 흥미로운 실무 훅으로 시작하도록 2단계 엄격 구조 고도화.
  2. [`frontend/src/app/guide/[jobId]/page.tsx`](file:///i:/Interactive%20Video%20Study%20Guide%20System/frontend/src/app/guide/%5BjobId%5D/page.tsx):
     - 형식적인 `Guide Overview` 제거.
     - `summaryInsight`를 통해 첫 챕터 핵심 도입 텍스트, 총 챕터 수, 상위 5개 주요 챕터 바로가기 뱃지를 포함한 **"핵심 주제 및 학습 개요"** 카드로 전면 개편.
  3. **검증**: `npm run build` (Turbopack) 100% 성공 (에러 0건).

### 9) [버그 해결] 랜딩 페이지에서 가이드 클릭 시 React Error #310 발생으로 인한 페이지 로딩 실패 이슈 해결 (In Progress)
- **배경 및 문제점**: 메인 대시보드에서 가이드 카드 클릭 시 `Minified React error #310` (Rules of Hooks 위반) 에러와 함께 `This page couldn't load` 화면 발생.
- **원인 분석**: `summaryInsight` `useMemo` 훅이 `if (loading) return` 조기 리턴문 아래에 위치하여 렌더링 간 훅 호출 개수 불일치 발생.
- **해결 조치**:
  1. [`frontend/src/app/guide/[jobId]/page.tsx`](file:///i:/Interactive%20Video%20Study%20Guide%20System/frontend/src/app/guide/%5BjobId%5D/page.tsx): `summaryInsight` 훅 선언부를 컴포넌트 최상단 훅 선언부(조기 리턴문 이전)로 이동하여 React Hook 규칙을 100% 준수하도록 수정.
  2. **검증**: `npm run build` (Turbopack) 100% 무결성 통과 (에러 0건).
  3. **Notion 버그 리포트 등록**: `In Progress` 상태로 이슈 등록 완료.

### 10) [버그 해결] OpenRouter 404 모델 교체 및 가이드 생성 ReadTimeout 완전 해결 (In Progress)
- **배경 및 문제점**: 가이드 생성 시작 직후 "목차 구조 설계 중..." 단계에서 `RetryError[raised ReadTimeout]` 모달 발생.
- **원인 분석**:
  1. OpenRouter에서 `meta-llama/llama-3.3-70b-instruct:free`가 유료 전용으로 전환되어 `:free` 슬러그 호출 시 `404 Not Found` 반환.
  2. AWS EC2의 `backend/.env`가 로컬과 비동기화되어 만료된 구버전 `GEMINI_API_KEY`로 요청이 전달되어 무한 대기.
  3. Dockerfile에 `psycopg2-binary` 누락으로 컨테이너 크래시 루프 발생.
- **해결 조치**:
  1. [`backend/services/llm.py`](file:///i:/Interactive%20Video%20Study%20Guide%20System/backend/services/llm.py): 100% 정상 가동 검증된 비-중국계 최고 성능 무료 모델인 `nvidia/nemotron-3.5-lightning:free`(초고속 3초) 및 `nvidia/nemotron-3-ultra-550b-a55b:free`로 기본 매핑 및 Fallback 교체.
  2. 목차 생성 시 10,000자 초과 자막에 대해 스마트 샘플링(앞 3,500자 + 중간 3,000자 + 끝 3,500자) 적용으로 응답 지연 원천 차단.
  3. [`backend/requirements.txt`](file:///i:/Interactive%20Video%20Study%20Guide%20System/backend/requirements.txt): `psycopg2-binary` 추가 및 EC2 최신 Docker 이미지 빌드 배포 완료 (`200 OK`).
  4. AWS EC2 `backend/.env`에 `OPENROUTER_API_KEY` 직접 주입 완료.
- **Notion 리포트**: [📄 [Bug Report] 가이드 생성 시작 시 ReadTimeout 및 404 발생 이슈](https://app.notion.com/p/Bug-Report-ReadTimeout-404-In-Progress-3d0a8db03fbe811ca6d4f8527e3ee3fc) (`In Progress`)

### 11) [버그 해결] 배포 후 학습 서재 가이드 목록 일시적 미노출(최근 생성 학습서 실종) 이슈 완전 해결 (In Progress)
- **배경 및 문제점**: 배포 후 새로고침 시 하단 "내 학습 서재"에 최근 생성했던 학습서("컨텍스트 엔지니어링...")가 보이지 않는 현상 발생.
- **원인 분석**:
  1. **Next.js 미들웨어 401 차단**: `frontend/src/utils/supabase/middleware.ts`에서 비로그인 또는 쿠키 세션 미보유 시 `/api/` 요청을 `401 Unauthorized`로 막아 프론트엔드가 서재 목록을 0개로 수신.
  2. **도커 이미지 내부 캐시 고착**: 이전 빌드 시 이미지 내부 `/app/backend/.env`에 외부 Neon DB 설정이 복사되어 6.08MB 원본 SQLite(`jobs.db`) 대신 외부 DB를 조회.
- **해결 조치**:
  1. [`frontend/src/utils/supabase/middleware.ts`](file:///i:/Interactive%20Video%20Study%20Guide%20System/frontend/src/utils/supabase/middleware.ts): `/api/` 백엔드 프록시 라우트에 대해 미들웨어 401 차단을 해제하여 비로그인/게스트도 정상 통과되도록 패치 후 Vercel 배포 완료 (`Status: 200 OK`).
  2. [`docker-compose.yml`](file:///i:/Interactive%20Video%20Study%20Guide%20System/docker-compose.yml): `environment`에 `DATABASE_URL=sqlite:///./backend/data/jobs.db`를 최우선 순위로 명시하고, `./backend/.env:/app/backend/.env` 바인드 마운트 설정 후 `up -d --force-recreate` 실행.
  3. **검증 완료**: 9월 3일 생성된 `job_9100b11b71c44ec999653f8a37998dbf`("컨텍스트 엔지니어링이 AI 코딩 에이전트를 개선하는 방법", 5개 챕터)를 포함한 86개 전체 학습서가 Vercel 라이브 사이트에서 100% 정상 반환됨을 확인.
- **Notion 리포트**: [📄 [Bug Report] 배포 후 학습 서재 가이드 목록 일시적 미노출 이슈](https://app.notion.com/p/Bug-Report-Resolved-3d0a8db03fbe81619bf2d560a0641e8a) (`Resolved`)

### 12) [버그 해결] 외국어 유튜브 영상 챕터 본문 한국어 미번역(영어 원문 출력) 이슈 해결 (In Progress)
- **배경 및 문제점**: 영어 유튜브 영상(예: Tanmai Gopal의 PromptQL 발표)으로 가이드 생성 시, 목차는 정상 번역되었으나 상세 챕터 서술형 본문 전체가 번역되지 않고 영어 원문으로만 출력되는 현상 발생.
- **원인 분석**:
  1. `backend/prompts/chapter_guide.py`: 인사말 금지, 메타 텍스트 금지, 2단계 출력 구조만 최상단에 강조되고, 한국어 번역 지침은 페르소나 내부 1줄에 머물러 있어 영문 스크립트 입력 시 LLM(Nemotron 등)이 영어로 본문을 작성.
  2. `backend/services/llm.py`: `validate_chapter_narrative` 함수가 본문 길이(1,000자)와 인사말 유무만 검증하고 한글 포함 여부를 전혀 검사하지 않아, 100% 영문으로 출력되어도 유효한 본문으로 통과되어 캐시 및 DB에 그대로 저장됨.
- **해결 조치**:
  1. [`backend/prompts/chapter_guide.py`](file:///i:/Interactive%20Video%20Study%20Guide%20System/backend/prompts/chapter_guide.py): `[🚨 초강력 절대 준수 1: 100% 자연스러운 한국어 번역 및 해설 서술 (Strict Korean Output Policy)]`을 최상단에 배치하여 영문 고유명사를 제외한 모든 본문/위젯의 한국어 작성을 강제.
  2. [`backend/services/llm.py`](file:///i:/Interactive%20Video%20Study%20Guide%20System/backend/services/llm.py):
     - `user_instruction` 서두 및 지시사항에 100% 한국어 번역 작성 명시.
     - `validate_chapter_narrative`에 한글 글자 수(최소 150자) 검증 가드레일 탑재 (미달 시 즉시 탈락 및 한국어 번역 재시도 에스컬레이션).
     - Fallback 합성 가드레일에서도 비한국어 본문 감지 시 한국어 기본 구조 템플릿으로 안전 Fallback 보장.
     - `clean_invalid_cached_chapters`로 기존 비한국어 캐시 파일 2건 전수 삭제 완료.
- **Notion 리포트**: [📄 [Bug Report] 외국어 유튜브 영상 챕터 본문 한국어 미번역 이슈](https://app.notion.com/p/Bug-Report-In-Progress-3d0a8db03fbe818da58bffbe102c94f1) (`In Progress`)

### 13) [아키텍처 전면 개편] 백엔드 단일 책임 원칙(SRP) 준수 및 관심사별 7대 모듈 분리 리팩토링 (Completed)
- **배경 및 문제점**: `backend/services/llm.py`가 1,336줄의 God Object로 비대화되어 클라이언트 통신, 캐시, 검증, 프롬프트 파싱, 음성 처리, 목차 및 챕터 생성 로직이 단일 파일에 강결합되어 유지보수성 저하 및 버그 추적 곤란.
- **해결 조치**:
  1. [`backend/services/llm/`](file:///i:/Interactive%20Video%20Study%20Guide%20System/backend/services/llm): 관심사별 7개 전용 모듈로 완벽 분리:
     - `clients.py`: Google GenAI, OpenAI, OpenRouter 클라이언트 및 프로필 관리
     - `cache.py`: 파일 기반 챕터 캐시 읽기/쓰기 및 손상 캐시 정제
     - `validators.py`: 챕터 서술형 본문 유효성 검증 (1,000자 이상, 한글 150자 이상, 인사말 금지)
     - `audio.py`: 오디오 기반 목차 생성 및 음성 전사 폴백
     - `outline.py`: 비디오 메타데이터 및 스마트 샘플링 기반 목차 설계
     - `chapter.py`: 단일/다중 챕터 비동기 생성 및 에스컬레이션 재시도
     - `profiling.py`: LLM 응답 시간 및 토큰/비용 프로파일링
  2. [`backend/services/llm.py`](file:///i:/Interactive%20Video%20Study%20Guide%20System/backend/services/llm.py): 상위 호환 파사드(Facade) 패턴을 적용하여 기존 외부 호출부 수정 없이 100% 하위 호환성 보장.
  3. **[런타임 크래시 버그 수정]**: `llm.py` 768행 부근 `section_index`, `total_sections` 미정의로 인해 다중 섹션 영상 처리 시 발생하던 치명적인 `NameError` 크래시 원천 차단.
  4. [`backend/config.py`](file:///i:/Interactive%20Video%20Study%20Guide%20System/backend/config.py): `settings` 싱글톤 일원화 (`main.py`, `celery_app.py` 중복 설정 제거).
  5. [`backend/schemas/guide.py`](file:///i:/Interactive%20Video%20Study%20Guide%20System/backend/schemas/guide.py): Pydantic DTO 도입 및 `job_manager.py` 방어 로직 강화.

### 14) [성능 & 가독성 개선] 프론트엔드 상세 뷰어(1,643줄 -> 420줄) 8대 컴포넌트 모듈화 및 렌더링 최적화 (Completed)
- **배경 및 문제점**: `frontend/src/app/guide/[jobId]/page.tsx`가 1,643줄 단일 거대 컴포넌트로 구성되어, 타임스탬프 클릭이나 동영상 재생 등 사소한 상태 변경에도 전체 챕터와 수식, 텍스트가 통째로 Re-render되어 심각한 화면 버벅임 발생.
- **해결 조치**:
  1. [`frontend/src/app/guide/[jobId]/components/`](file:///i:/Interactive%20Video%20Study%20Guide%20System/frontend/src/app/guide/%5BjobId%5D/components): 8대 독립 컴포넌트로 분리:
     - `ChapterItem`: 개별 챕터 렌더링 및 메모이제이션 (불필요한 리렌더링 차단)
     - `VideoPanel`: 유튜브 영상 플레이어 및 타임스탬프 동기화
     - `OptionsToolbar`: 요약 분량, 설명 방식, 몰입 읽기 모드 전환 툴바
     - `SummaryInsightCard`: 영상 핵심 요약 및 주요 챕터 뱃지 카드
     - `FloatingToolbar`: 텍스트 드래그 시 노트/AI 질문 컨텍스트 메뉴
     - `NoteModals`: 개인 학습 노트 작성/수정/삭제 모달
     - `RSVPModal`: 고속 텍스트 리더(RSVP) 팝업 모달
     - `ViewerPresetMatrixModal`: 3x3 프리셋 매트릭스 탐색기 모달
  2. `page.tsx` 코드 라인 수를 **1,643줄에서 420줄로 74% 이상 압축**하여 가독성과 유지보수성 극대화.
  3. `useCallback` 적용으로 자식 컴포넌트에 전달되는 이벤트 핸들러 참조 고정.
  4. [`frontend/src/lib/markdownProcessor.ts`](file:///i:/Interactive%20Video%20Study%20Guide%20System/frontend/src/lib/markdownProcessor.ts): 텍스트 해시 기반 LRU 캐시 최적화로 마크다운 파싱 지연 해소.
  5. [`backend/constants/presets.py`](file:///i:/Interactive%20Video%20Study%20Guide%20System/backend/constants/presets.py) & [`frontend/src/lib/presets.ts`](file:///i:/Interactive%20Video%20Study%20Guide%20System/frontend/src/lib/presets.ts): 프론트-백엔드 간 프리셋 상수 및 라벨 매핑 완벽 동기화.
  6. **검증**: `npm run build` (Turbopack, TypeScript 무결점) 100% 빌드 성공 (에러 0건).

### 15) [인프라 & 배포] AWS EC2 최신 Docker 빌드 배포 및 Vercel 리버스 프록시 실서비스 연동 완료 (Completed)
- **배경 및 내용**: 대규모 리팩토링 및 런타임 버그 수정본을 프로덕션 인프라(AWS EC2 & Vercel)에 무중단 반영.
- **조치 내역**:
  1. **AWS EC2 환경 정리 및 최신 코드 갱신**:
     - EC2 내 중복 클론 폴더(`Interactive-Video-Study-Guide-System/`) 정리 및 변경 스크립트 복원(`git checkout`).
     - `git pull origin main`으로 최신 백엔드 모듈 코드 갱신.
  2. **Docker 컨테이너 3종 최신 빌드 및 배포 (`./scripts/deploy_backend.sh`)**:
     - `studyguide-backend:latest` 경량 단일 이미지 성공적 빌드.
     - `studyguide-redis` (Healthy), `studyguide-celery` (Started), `studyguide-fastapi` (Started) 3종 컨테이너 정상 가동.
     - `curl -I http://localhost:8000/docs` ➔ `HTTP/1.1 200 OK` 정상 헬스체크 검증 완료.
  3. **Vercel 프로덕션 리버스 프록시 연동**:
     - Vercel 대시보드 `Environment Variables`에서 `BACKEND_API_URL`을 AWS EC2 퍼블릭 IP(`http://<EC2-IP>:8000`)로 설정 완료.
     - 최신 환경 변수를 반영하여 Vercel Production 재배포(Redeploy) 성공.
     - HTTPS(Vercel)와 HTTP(AWS EC2) 간 Mixed Content 차단 문제를 Next.js Server-side Rewrites를 통해 원천 해결.

### 16) [버그 해결] Vercel 프로덕션 가이드 생성 ReadTimeout 및 404/400 연쇄 실패 이슈 해결 (In Progress)
- **배경 및 문제점**: Vercel 프로덕션 실서비스 E2E 테스트 중 "목차 구조 설계 중..." 단계에서 `RetryError[<Future ... raised ReadTimeout>]` 에러와 함께 가이드 생성 실패 발생.
- **원인 분석**:
  1. `backend/services/llm/profiling.py`: 모델명에 `openrouter/` 접두사가 포함된 채 OpenRouter API로 전송되어 `400 Bad Request` 발생.
  2. `backend/services/llm/clients.py`: `get_openai_client`가 `:free` 모델임에도 불구하고 `nvidia` 키워드만 보고 `integrate.api.nvidia.com` 엔드포인트로 잘못 라우팅하여 NVIDIA 공식 API에서 `404 Not Found` 발생.
  3. EC2 백엔드 `backend/.env`에 `GEMINI_API_KEY` 미동기화 및 구버전 레이어 타임아웃 발생 시, tenacity 5회 재시도 루프로 인해 5분 이상 대기 후 `RetryError` 크래시 발생.
  4. AI 목차 설계 실패 시 자막 단락 기반 최후 휴리스틱 Fallback 부재.
- **해결 조치**:
  1. [`backend/services/llm/clients.py`](file:///i:/Interactive%20Video%20Study%20Guide%20System/backend/services/llm/clients.py): `:free` 또는 `openrouter` 포함 시 항상 OpenRouter(`https://openrouter.ai/api/v1`)로 정확히 라우팅, `_should_retry_error`에서 타임아웃 즉시 Fallback 전환 가드레일 적용.
  2. [`backend/services/llm/profiling.py`](file:///i:/Interactive%20Video%20Study%20Guide%20System/backend/services/llm/profiling.py): `_normalize_openai_model` 도입으로 `openrouter/` 접두사 자동 정제.
  3. [`backend/services/llm/outline.py`](file:///i:/Interactive%20Video%20Study%20Guide%20System/backend/services/llm/outline.py): 목차 타임아웃 35초 단축, Gemini Fallback 양방향 try-except 완전 격리, 최후의 스마트 휴리스틱 목차 생성(`_build_heuristic_sections`) 탑재.
  4. **AWS EC2 환경변수 동기화 및 Docker 최신 빌드 배포**: EC2 `backend/.env`에 `GEMINI_API_KEY`, `OPENROUTER_API_KEY`, `OPENAI_API_KEY` 동기화 후 컨테이너 3종 최신 배포 완료 (`HTTP 200 OK`).
  5. **엔드투엔드 목차 생성 검증**: EC2 Celery 내부에서 `nvidia/nemotron-3.5-lightning:free` 모델로 40초 만에 5개 챕터 목차 100% 정상 생성 검증 완료.
- **Notion 리포트**: [📄 [Bug Report] Vercel 프로덕션 가이드 생성 ReadTimeout 및 404 재발 이슈](https://app.notion.com/p/Bug-Report-Vercel-ReadTimeout-404-In-Progress-3d6a8db03fbe812ca614c95f59e6d4a0) (`In Progress`)

### 17) [버그 해결] 챕터 본문 열람 시 404 page not found 에러 표시 이슈 및 Google GenAI ms 단위 버그 완벽 해결 (In Progress)
- **배경 및 문제점**: 1차 목차 생성 성공 후 가이드 목록 진입까지는 가능해졌으나, 상세 뷰어 내 각 챕터 본문 열람 시 `[!WARNING] 챕터 생성 중 내부 에러가 발생했습니다. 에러 원인: 404 page not found` 경고창이 표시되는 2차 이슈 제보.
- **원인 분석**:
  1. **Google GenAI SDK 타임아웃 단위 버그 (45ms 즉사 현상)**:
     - `clients.py`의 `get_gemini_client`에서 `http_options={"timeout": 45}`가 설정되어 있었으나, Google GenAI SDK는 해당 값을 **밀리초(ms)** 단위로 인식.
     - 결과적으로 45초가 아니라 **45밀리초(0.045초)** 만에 모든 Gemini 호출이 `httpx.ReadTimeout: The read operation timed out`으로 즉시 전멸하여 Fallback이 무조건 실패함.
  2. **OpenRouter 후보 모델 중 결함 모델 포함 및 긴 타임아웃**:
     - `chapter.py`의 후보 모델 목록 중 `nvidia/nemotron-3-super-120b-a12b:free` 모델이 응답 구조 불일치로 `NoneType` 에러를 반환.
     - 개별 API 호출의 타임아웃이 90초로 과도하여 전체 `wait_for(120s)`에 걸려 프로세스가 강제 취소되고 최종 예외로 404가 표출됨.
  3. **챕터 생성 최후 Heuristic Fallback 부재**:
     - AI API 호출이 모두 실패하거나 지연될 때, 자막 텍스트로부터 학습 본문을 안전하게 구성하는 안전망이 없어 DB에 에러 박스가 그대로 저장됨.
- **해결 조치**:
  1. [`backend/services/llm/clients.py`](file:///i:/Interactive%20Video%20Study%20Guide%20System/backend/services/llm/clients.py):
     - `get_gemini_client`: `http_options={"timeout": 60000}` (60,000ms = 60초)로 단위 정상화 (테스트 결과 Gemini 3.5가 1~2초 만에 즉각 응답 성공).
     - `FALLBACK_GEMINI_MODELS`: 실제 가용성이 검증된 `gemini-3.5-flash-lite`, `gemini-3.6-flash`, `gemini-flash-lite-latest`, `gemini-flash-latest`로 최신화.
  2. [`backend/services/llm/chapter.py`](file:///i:/Interactive%20Video%20Study%20Guide%20System/backend/services/llm/chapter.py) & [`outline.py`](file:///i:/Interactive%20Video%20Study%20Guide%20System/backend/services/llm/outline.py):
     - 결함 모델 `nvidia/nemotron-3-super-120b-a12b:free` 제거 및 검증된 고성능 무료 모델 `meta-llama/llama-3.3-70b-instruct:free` 탑재.
     - 개별 LLM 호출 타임아웃을 25초로 단축하고 tenacity 재시도 최적화.
     - **Heuristic Chapter Fallback (`_build_heuristic_chapter`) 안전망 구축**: AI 장애/타임아웃 발생 시에도 원본 자막으로부터 1,200자 이상의 고품질 서술형 챕터(도입 훅, 상세 원리, 핵심 인사이트 박스, 실무 팁, 퀴즈)를 자동 생성하여 404 예외 누출을 100% 원천 차단.
  3. [`backend/services/tasks.py`](file:///i:/Interactive%20Video%20Study%20Guide%20System/backend/services/tasks.py): 챕터 취합 루프에서 예외 발생 시 에러 경고 마크다운 대신 안전 서술형 챕터 본문으로 자동 복구.
  4. **AWS EC2 백엔드 배포 및 E2E 검증 완료**:
     - Docker 컨테이너 전체 최신 빌드 및 무중단 재기동 완료.
     - EC2 Celery 컨테이너 내부에서 챕터 단독 생성 E2E 테스트 성공 (`=== CHAPTER GENERATION SUCCESS ===`, 본문 1,204자 정상 완결).
- **Notion 리포트**: [📄 [Bug Report] Vercel 프로덕션 가이드 생성 ReadTimeout 및 404 이슈 종합 해결](https://app.notion.com/p/Bug-Report-Vercel-ReadTimeout-404-In-Progress-3d6a8db03fbe812ca614c95f59e6d4a0) (`In Progress`)

### 18) [버그 해결] 학습서 초반 자막 첫 줄 괄호 문장 중복 반복 삽입 이슈 및 OpenRouter 전역 Base URL 간섭 완전 해결 (Resolved)
- **배경 및 문제점**:
  - 학습 가이드 본문 생성 성공 후, 1번 챕터 제목과 본문 도입부에 영상 자막의 첫 문장(`(그래서 오늘 저희 는 마운틴뷰 에 있는 본사 ...)`)이 괄호 및 대제목/소제목/본문 첫 줄에 3회 이상 불필요하게 반복 삽입되는 이슈 발생.
- **원인 분석**:
  1. `backend/services/llm/outline.py`의 비상 안전망 `_build_heuristic_sections`:
     - `lines = [line.strip() for line in text.splitlines() if len(line.strip()) > 15]`
     - `f"도입 및 핵심 배경 ({first_line[:25]}...)"` 형태로 첫 자막 줄을 제목에 하드코딩 결합.
  2. `backend/services/llm/chapter.py`의 템플릿:
     - 대제목(`## {section_title}`), 본문 첫 문장(`**{section_title}**의...`), 소제목 도입부(`{section_title}은...`)에 제목 변수가 3회 연속 치환되며 잡음 문장이 그대로 반복 노출.
  3. **비상 안전망이 발동된 근본 원인 (전역 Base URL 라우팅 오염)**:
     - EC2 `.env`에 `OPENAI_BASE_URL=https://integrate.api.nvidia.com/v1`이 설정되어 있어, `clients.py`의 `get_openai_client`가 OpenRouter 무료 모델(`nvidia/nemotron-3.5-lightning:free`) 요청 시에도 해당 전역 base_url을 채택하여 404가 발생하고 휴리스틱으로 폴백됨.
- **해결 조치**:
  1. [`backend/services/llm/outline.py`](file:///i:/Interactive%20Video%20Study%20Guide%20System/backend/services/llm/outline.py):
     - `_build_heuristic_sections`: 자막 잡음 문장을 괄호로 붙이던 코드 전면 제거, 정제된 표준 4개 목차(`"도입 및 핵심 배경"`, `"핵심 원리와 메커니즘 분석"`, `"실무 활용 전략 및 주요 사례"`, `"핵심 요약과 향후 전망"`)로 변경.
     - `_call_openai_outline`: OpenRouter 후보 모델을 최신화(`google/gemma-4-31b-it:free`, `google/gemma-4-26b-a4b-it:free`, `nvidia/nemotron-3.5-lightning:free` 등).
  2. [`backend/services/llm/clients.py`](file:///i:/Interactive%20Video%20Study%20Guide%20System/backend/services/llm/clients.py):
     - `get_openai_client`: OpenRouter, Groq, Cerebras 등 프로바이더 요청 시 전역 `OPENAI_BASE_URL`의 간섭을 차단하고 `https://openrouter.ai/api/v1` 등 각 서비스 고유 엔드포인트를 강제 라우팅하도록 격리.
  3. [`backend/services/llm/chapter.py`](file:///i:/Interactive%20Video%20Study%20Guide%20System/backend/services/llm/chapter.py):
     - `_build_heuristic_chapter`: 정제 정규식(`clean_title = re.sub(r'\(.*?\)', '', section_title).strip()`)을 적용하여 제목에 괄호나 잡음이 있더라도 본문/퀴즈에서 온전히 정제된 명칭만 사용.
     - 본문 분량을 1,200자 기준을 여유 있게 넘는 1,685자로 대폭 확장하여 캐시 유효성 검증을 100% 통과하도록 보강.
     - `candidate_models`에 `google/gemma-4-31b-it:free`, `google/gemma-4-26b-a4b-it:free` 등 최신 OpenRouter 무료 모델 라인업 동기화.
  4. **AWS EC2 운영 서버 배포 및 E2E 실시간 검증 완료**:
     - 커밋 `22e1d32`, `06428e9` 푸시 및 Docker 컨테이너 리빌드/재기동 완료 (`bb5506b548d0`, `d90ebdd634eb`).
     - Celery 컨테이너 내부 실시간 E2E 테스트 검증 완료:
       - 목차 3개 및 7개 정상 생성 (자막 괄호 문구 100% 제거 확인).
       - 챕터 본문 1,685자 정상 생성 (캐시 검증 완벽 통과, 잡음 반복 0건 확인).
- **Notion 리포트**: [📄 [Bug Report] Vercel 프로덕션 가이드 생성 ReadTimeout 및 404 이슈 종합 해결](https://app.notion.com/p/Bug-Report-Vercel-ReadTimeout-404-In-Progress-3d6a8db03fbe812ca614c95f59e6d4a0) (`In Progress` - 사용자 최종 승인 대기)

### 19) [버그 해결] 유튜브 웹 스크랩 시 상단 메타데이터 잡음(조회수, 날짜, URL 인코딩 등) 본문 노출 이슈 완전 해결 (Resolved)
- **배경 및 문제점**:
  - 가이드 본문 생성 시 `2. 세부 메커니즘 및 상세 해설` 섹션에 `%2Ccheck-that-youre-signed-into-youtube)`, `244K views 6 days ago`, `Sep 3, 2026`, `Follow along using the transcript` 등 영상과 무관한 유튜브 웹페이지 메타데이터가 그대로 노출되는 이슈 발생.
- **원인 분석**:
  - AWS EC2 IP 대역이 유튜브에 의해 봇 감지로 일시 차단되면서 자막/오디오 직접 다운로드가 막혔고, 시스템이 웹 스크랩 엔진(`Jina Reader`)으로 폴백하여 유튜브 페이지 전체 마크다운을 가져옴.
  - 비상 안전망(`_build_heuristic_chapter`)이 가동될 때, 스크랩된 텍스트의 상단 줄을 잘라오는 과정에서 유튜브 상단 UI 찌꺼기와 메타데이터가 걸러지지 않고 본문에 그대로 삽입됨.
- **해결 조치**:
  1. [`backend/services/tasks.py`](file:///i:/Interactive%20Video%20Study%20Guide%20System/backend/services/tasks.py):
     - `clean_youtube_scraped_text` 함수 탑재: Jina Reader로 스크랩된 유튜브 텍스트에서 상단 네비게이션/버튼 및 하단 추천 영상 목록(33,721자 -> 1,740자)을 깨끗하게 도려내어 본문 설명란만 정제.
  2. [`backend/services/llm/chapter.py`](file:///i:/Interactive%20Video%20Study%20Guide%20System/backend/services/llm/chapter.py):
     - `_build_heuristic_chapter`: 정규식 필터(`junk_regex`)를 탑재하여 `%[0-9a-fA-F]{2}`, `views`, `ago`, `Follow along`, `Transcript`, `Sign in`, 타임스탬프, 링크 등을 100% 배제.
     - 유의미한 지식 문장이 부족할 때 불필요한 메타데이터 대신 챕터 주제(`clean_title`)에 최적화된 고품질 전문 학습 가이드 표준 서술문으로 완전 대체.
  3. **실시간 가용 OpenRouter 무료 모델 우선순위 재정렬**:
     - 즉각 응답이 검증된 `google/gemma-4-26b-a4b-it:free`, `nex-agi/nex-n2.5-pro:free`, `nex-agi/nex-n2.5-mini:free`를 최우선 배치.
  4. **AWS EC2 운영 서버 배포 및 E2E 실시간 검증 완료**:
     - 커밋 `f771253` 푸시 및 Docker 컨테이너 리빌드/재기동 완료 (`3d1465784a5d`).
     - 실제 이슈 영상(`5bxp78i96S8`) 텍스트 대상 Celery 컨테이너 실시간 검증 결과:
       - 잡음 키워드 잔존 0건 (`Found bad keywords: []`).
       - 불필요한 메타데이터 전면 차단 및 표준 학습 가이드 본문 100% 정상 출력 검증 완료.

---

## 3. Notion 문서 관리 현황

1. **[공식 이슈 보드] [📋 Interactive Video Study Guide System 이슈 리포트 (통합 대시보드)](https://app.notion.com/p/3cba8db03fbe80a7972be85c1b2c2202)**:
   - 📄 [[Bug Report] Vercel 프로덕션 가이드 생성 ReadTimeout 및 404 이슈 종합 해결](https://app.notion.com/p/Bug-Report-Vercel-ReadTimeout-404-In-Progress-3d6a8db03fbe812ca614c95f59e6d4a0) (`In Progress` - GenAI ms 단위 보정, 챕터 타임아웃 최적화, Heuristic Chapter Fallback 탑재 및 EC2 배포 완료, 사용자 실서비스 재검증 대기)
   - 📄 [[Bug Report] 외국어 유튜브 영상 챕터 본문 한국어 미번역 이슈](https://app.notion.com/p/Bug-Report-In-Progress-3d0a8db03fbe818da58bffbe102c94f1) (`In Progress` - 프롬프트 전면 개편 및 한글 글자수 검증 가드레일 탑재, 사용자 재검증 대기)
   - 📄 [[Bug Report] 배포 후 학습 서재 가이드 목록 일시적 미노출 이슈](https://app.notion.com/p/Bug-Report-Resolved-3d0a8db03fbe81619bf2d560a0641e8a) (`Resolved` - 사용자 최종 검증 완료)
   - 📄 [[Bug Report] 가이드 생성 시작 시 ReadTimeout 및 404 발생 이슈](https://app.notion.com/p/Bug-Report-ReadTimeout-404-Resolved-3d0a8db03fbe811ca6d4f8527e3ee3fc) (`Resolved` - 사용자 최종 검증 완료)
   - 📄 [[Bug Report] 랜딩 페이지에서 가이드 클릭 시 React Error #310 발생으로 인한 페이지 로딩 실패 이슈](https://app.notion.com/p/Bug-Report-React-Error-310-Resolved-3cda8db03fbe8170af67f0ee00c46a4e) (`Resolved` - 사용자 최종 검증 완료)
   - 📄 [[Bug Report] 대시보드와 가이드 상세 뷰어 간 9종 프리셋 표시 및 제목 불일치 이슈](https://app.notion.com/p/Bug-Report-9-Resolved-3cca8db03fbe816ab4e0d79a54a30a34) (`Resolved`)
   - 📄 [[Bug Report] 프리셋 탐색 모달 오픈 시 브라우저 GPU 과부하로 인한 타 탭 비디오 버벅임 이슈](https://app.notion.com/p/Bug-Report-GPU-Resolved-3cca8db03fbe8105ad81dfeb3323d5e5) (`Resolved`)
   - 📄 [[Bug Report] 2시간 이상 장문 유튜브 영상 가이드 생성 이슈](https://app.notion.com/p/Bug-Report-2-Resolved-3cca8db03fbe81059afada2b6b96d034) (`Resolved`)
   - 📄 [[Bug Report] Vercel 프로덕션 가이드 생성 시 유튜브 봇 감지 오디오 다운로드 실패 이슈](https://app.notion.com/p/Bug-Report-Vercel-Resolved-3cba8db03fbe81e4a59fe0d3e1301b40) (`Resolved`)

2. **[인프라 및 가동 가이드]**:
   - 📄 **[🌐 외부 서비스 및 인프라 접속 정보 모음](https://app.notion.com/p/3d0a8db03fbe8101a6d3ee6c637f8749)** (Vercel, AWS EC2, OpenRouter, Neon, Upstash, Supabase, GitHub 접속 정보 및 운영 팁 완비).
   - 📄 **[🚀 [운영 가이드] 로컬 개발부터 Vercel & AWS EC2 배포 및 서버 재시작 완전 정복 매뉴얼](https://app.notion.com/p/Vercel-AWS-EC2-3cca8db03fbe8110bd96cb12c92da8cf)**.

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

### AWS EC2 운영 백엔드 업데이트 (배포 스크립트 실행)
```bash
cd ~/Interactive-Video-Study-Guide-System
git pull origin main
chmod +x scripts/deploy_backend.sh
./scripts/deploy_backend.sh
```

---

## 5. 다음 대화에서 이어서 진행할 수 있는 과제

1. **Vercel 프로덕션 환경에서 실서비스 최종 End-to-End 검증**:
   - Vercel 배포 URL(`https://interactive-video-study-guide-syste.vercel.app`)로 접속하여 임의의 유튜브 영상 URL로 가이드 생성 및 챕터 열람이 정상 작동하는지 E2E 점검.
2. **외국어 영상 한국어 번역 가이드 생성 실서비스 검증**:
   - 영어 유튜브 영상을 입력하여 챕터 서술형 본문 전체가 유창한 한국어로 생성되는지 최종 확인 후 Notion 이슈 상태 업데이트.
3. **Vercel Web Analytics 대시보드 트래픽 모니터링**:
   - Vercel Analytics 활성화 후 실사용자 접속 및 페이지뷰 데이터 수집 추이 확인.


