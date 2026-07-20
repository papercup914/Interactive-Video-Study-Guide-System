이제 프로젝트 전체 구조를 잘 파악했습니다. 종합 리뷰를 작성하겠습니다.

---

## 📋 Interactive Video Study Guide System — 프로젝트 리뷰

### 🏗️ 전체 아키텍처

| 레이어 | 기술 스택 | 주요 파일 |
|---------|----------|----------|
| **Backend** | FastAPI + Uvicorn | `backend/main.py`, `backend/routers/guide.py` |
| **LLM 연동** | Google Gemini / OpenAI / NVIDIA Nemotron / GLM | `backend/services/llm.py` |
| **비디오 처리** | yt-dlp + FFmpeg (오디오 추출) | `backend/services/video.py` |
| **작업 관리** | In-memory job queue + BackgroundTasks | `backend/services/job_manager.py` |
| **Frontend** | Next.js 16 (App Router) + React 19 + TailwindCSS v4 | `frontend/src/app/` |
| **상태 관리** | React Context (`TaskContext`) + LocalStorage | `frontend/src/app/contexts/TaskContext.tsx` |
| **데이터 저장** | 로컬 JSON 파일 (guides, cache, transcripts) | `backend/data/` |

---

### ✅ 강점 (Well-Designed Parts)

| 영역 | 세부 사항 |
|------|----------|
| **멀티 프로바이더 LLM 추상화** | `llm.py`에서 `get_openai_client()` / `get_gemini_client()` 팩토리로 OpenAI, Gemini, Nemotron, GLM을 통합 관리 |
| **캐싱 전략** | URL 해시 기반으로 transcript, outline, chapter 단위까지 세분화 캐싱 (`backend/data/cache_chapters/`) |
| **비동기 챕터 병렬 생성** | `asyncio.Semaphore(3)`로 3개 동시 실행 → 전체 영상 처리 시간 단축 (`guide.py:86`) |
| **학습자 프로필 기반 페르소나** | `learner_profile`을 시스템 프롬프트에 주입 → 어조/비유/눈높이 맞춤형 튜터링 (`llm.py:228-237`) |
| **텍스트 선택 → AI 질문 플로우** | `SelectionState` + Floating Toolbar + Modal Q&A + 포스트잇 저장 → 자연스러운 학습 흐름 (`page.tsx:172-228`) |
| **가상화된 챕터 렌더링** | `react-virtuoso`로 긴 문서도 부드럽게 스크롤 (`page.tsx:450`) |
| **히스토리/라이브러리 UI** | 썸네일(결정적 SVG 패턴) + 챕터 수 + 날짜 + 삭제 모달 (`page.tsx:224-266`) |
| **테마 시스템** | e-ink 스타일 8가지 테마 + 다크모드 + localStorage 영속 (`theme.ts`, `ThemeToggle.tsx`) |

---

### ⚠️ 개선 필요 / 리스크 영역

| 영역 | 이슈 | 심각도 | 권장 조치 |
|------|------|--------|----------|
| **Job Manager** | In-memory dict → 프로세스 재시작 시 작업 손실, 멀티 워커 불가 | 🔴 Critical | Redis 또는 SQLite + persistent queue로 교체 |
| **API 인증/인가** | CORS `allow_origins=["*"]`, 인증 미들웨어 없음 | 🟡 High | JWT/Session 인증 + CORS origin 제한 |
| **에러 처리** | `guide.py:126`에서 `traceback.format_exc()` 전체를 클라이언트에 노출 | 🟡 High | 프로덕션에서는 상세 에러 숨김, 로그만 남기기 |
| **비디오 다운로드** | `yt_dlp` 단일 포맷(`bestaudio`), 자막/자동번역 미지원 | 🟡 Medium | 자막 우선 사용 → 없으면 오디오 추출, 다국어 지원 |
| **LLM 스트리밍** | 챕터/답변 생성 시 스트리밍 미지원 → 긴 응답 시 UX 저하 | 🟡 Medium | SSE/WebSocket으로 토큰 스트리밍 구현 |
| **캐시 키 충돌 위험** | `url_hash`만으로 캐시 키 생성 → 다른 설정(프로바이더, 프리셋) 동일 URL 시 덮어씀 | 🟡 Medium | 캐시 키에 `provider + preset + profile` 해시 포함 (이미 `llm.py:195`에서 chapter 캐시는 개선됨) |
| **프론트엔드 API 프록시** | Next.js API routes 없이 직접 FastAPI 호출 → CORS/배포 복잡도 증가 | 🟡 Medium | Next.js Route Handlers(`/api/guide/*`)로 프록시 또는 통합 배포 구성 |
| **테스트 코드 부재** | 단위/통합 테스트 없음 | 🟢 Low | `pytest` + `httpx` (backend), `vitest` + `react-testing-library` (frontend) 추가 |

---

### 📁 파일 구조 요약

```
Interactive Video Study Guide System/
├── backend/
│   ├── main.py                      # FastAPI 앱 엔트리포인트
│   ├── routers/
│   │   └── guide.py                 # 전체 API 라우트 (/start, /status, /result, /ask, /history...)
│   ├── services/
│   │   ├── llm.py                   # 멀티 LLM 클라이언트 + 프롬프트 엔지니어링 (핵심)
│   │   ├── video.py                 # yt-dlp 오디오 다운로드 + 제목 추출
│   │   ├── job_manager.py           # In-memory 잡 큐
│   │   ├── evaluator.py             # 학습 프로필 평가 (Gemini)
│   │   └── image.py                 # (비어있음/미구현)
│   └── data/                        # JSON 저장소 + 캐시 디렉토리
│       ├── saved_guides.json        # 히스토리 저장
│       ├── cache_chapters/          # 챕터별 캐시 (MD5 해시 키)
│       └── *.json / *.txt           # 아웃라인, 트랜스크립트
│
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx             # 랜딩 + URL 입력 + 히스토리 그리드
│   │   │   ├── guide/[jobId]/page.tsx  # 가이드 뷰어 (챕터 + Q&A + 노트)
│   │   │   ├── layout.tsx           # 루트 레이아웃 + Provider
│   │   │   ├── globals.css          # Tailwind v4 + 커스텀 테마 CSS
│   │   │   └── contexts/TaskContext.tsx  # 백그라운드 작업 상태 관리
│   │   ├── components/
│   │   │   ├── LearnerProfileWidget.tsx
│   │   │   ├── TaskWidget.tsx
│   │   │   └── ThemeToggle.tsx
│   │   └── lib/
│   │       ├── theme.ts             # 8가지 e-ink 테마 + 결정적 해시 매핑
│   │       └── utils.ts
│   ├── package.json                 # Next.js 16, React 19, Tailwind 4
│   └── next.config.ts
│
└── requirements.txt                 # fastapi, uvicorn, pydantic, python-dotenv 등
```

---

### 🚀 즉시 개선 가능한 Quick Wins

1. **Job Manager 영속화** (30분)
   ```python
   # backend/services/job_manager.py → SQLite + aiosqlite
   import aiosqlite
   DB_PATH = "backend/data/jobs.db"
   ```

2. **에러 메시지 정제** (`guide.py:126`)
   ```python
   # Before: error_msg = f"{str(e)}\n{traceback.format_exc()}"
   # After:
   import logging
   logging.error(f"Job {job_id} failed", exc_info=e)
   error_msg = "서버 내부 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
   ```

3. **캐시 키 개선** (`llm.py:136-137`)
   ```python
   # outline 캐시에도 provider/preset/profile 포함
   cache_key = f"{url_hash}_{provider}_{length_preset}_{hash(learner_profile)}"
   ```

4. **스트리밍 응답 추가** → `async_generate_chapter_content`를 `AsyncGenerator[str, None]`로 변경 + SSE 엔드포인트

---

### 🎯 다음 단계 추천 우선순위

| 우선순위 | 작업 | 예상 소요 |
|----------|------|----------|
| **P0** | Job Manager → Redis/SQLite 영속화 | 1-2시간 |
| **P0** | 인증 미들웨어 + CORS 제한 | 1시간 |
| **P1** | LLM 스트리밍 응답 (SSE) | 2-3시간 |
| **P1** | 자막 우선 추출 로직 (yt-dlp `--write-subs`) | 1시간 |
| **P2** | 단위/통합 테스트 추가 | 3-4시간 |
| **P2** | Next.js API Routes 프록시 레이어 | 2시간 |
| **P3** | Docker Compose / 배포 설정 | 1시간 |

---

### 💡 아키텍처 관점 코멘트

> **잘한 점**: 프롬프트 엔지니어링이 매우 정교함. `PERSONA_DIRECTIVE` 블록으로 학습자 프로필을 시스템 프롬프트에 강제 주입하는 방식은 실서비스급 품질. 캐시 키에 해시 포함으로 동일 조건 재실행 시 비용 절감도 훌륭.

> **주의할 점**: 현재는 **단일 프로세스 인메모리**라 수평 확장 불가능. `background_tasks`도 FastAPI 프로세스 내에서 돌므로 워커 늘리면 잡 상태 공유 안 됨. **Redis + Celery/RQ** 또는 **SQLite + 별도 워커 프로세스**로 분리해야 운영 가능.