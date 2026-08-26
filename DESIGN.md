# Interactive Video Study Guide System: Architecture Design
<!-- [KR] 인터랙티브 비디오 학습 가이드 시스템: 아키텍처 명세서 -->

## 1. System Overview
<!-- [KR] 1. 시스템 개요 -->
The Interactive Video Study Guide System is an advanced AI-powered educational application. It generates structured, highly detailed study guides from various sources including YouTube videos, PDF documents, and standard web pages. It features a zero-setup local architecture, ensuring maximum privacy and ease of deployment.
<!-- [KR] 이 시스템은 고급 AI 기반 교육 애플리케이션입니다. 유튜브 비디오, PDF 문서, 일반 웹페이지 등 다양한 출처에서 구조화되고 상세한 스터디 가이드를 생성합니다. 무설치 로컬 아키텍처를 특징으로 하여 최대의 프라이버시와 배포 용이성을 보장합니다. -->

## 2. Technical Stack
<!-- [KR] 2. 기술 스택 -->
### 2.1 Frontend (User Interface)
<!-- [KR] 2.1 프론트엔드 (사용자 인터페이스) -->
- **Framework**: Next.js 16+ (React)
- **Styling**: TailwindCSS (Productivity SaaS aesthetic, Soft Pastel Glass Light Mode)
- **Icons**: Lucide React
- **Animations**: Framer Motion (for premium micro-animations)
- **Features**: Real-time task polling, Markdown rendering (`react-markdown`), dark mode support.
<!-- [KR] 프레임워크: Next.js 16+ / 스타일링: TailwindCSS / 아이콘: Lucide React / 애니메이션: Framer Motion / 기능: 실시간 폴링, 마크다운 렌더링 -->

#### 2.1.1 Responsive UI/UX Strategy (PC, Tablet, Mobile)
<!-- [KR] 2.1.1 반응형 UI/UX 전략 (PC, 태블릿, 모바일 3종 환경) -->
- **Desktop (PC)**: 50:50 or 40:60 Split-Pane layout (Lilys.ai/Readray style). Video pinned on the left, tabbed text content (Summary, Transcript, Quiz) scrolling independently on the right.
  <!-- [KR] 데스크톱: 50:50 또는 40:60 좌우 분할 화면(Lilys.ai 스타일). 좌측에 고정된 영상 플레이어, 우측에 탭(요약, 스크립트, 퀴즈) 기반으로 독립 스크롤되는 콘텐츠 패널. -->
- **Tablet**: Adaptive layout. Video pinned at the top (30% height), text content below (70% height).
  <!-- [KR] 태블릿: 적응형 레이아웃. 상단 30%에 영상 플레이어 고정, 하단 70%에 텍스트 콘텐츠 배치. -->
- **Mobile**: Stacked layout with strict **Full-Bleed Text UI**. Left/right margins and card paddings are entirely removed (`px-0 md:px-4`). Video fixed at the absolute top, with a sticky tab bar directly below it.
  <!-- [KR] 모바일: 텍스트 꽉 찬(Full-Bleed) UI 강제. 좌우 여백을 완전히 제거하며, 영상은 최상단에 고정하고 바로 밑에 탭 바 배치. -->
- **Visual Aesthetic (Soft Pastel Glass)**: Light mode base with translucent frosted glass panels over subtle peach and sky blue blurry backgrounds. Completely replaces playful emojis/gradients with a highly professional, friendly SaaS interface.
  <!-- [KR] 시각적 미학 (소프트 파스텔 글래스): 라이트 모드 기반에 피치/스카이블루 그라데이션과 반투명 유리 질감 패널 사용. 기존 이모지를 완전히 제거하고 매우 전문적이면서도 친근한 SaaS 인터페이스 구축. -->
- **RSVP Speed Reading Mode (ReadRay inspired)**: A zero-cost frontend React hook for speed-reading AI summaries. On mobile, this activates a full-screen overlay for distraction-free RSVP.
  <!-- [KR] RSVP 속독 모드: API 비용이 없는 프론트엔드 모듈. 모바일에서는 방해 요소 없는 전체 화면 오버레이로 전환됨. -->

### 2.2 Backend (API & Processing)
<!-- [KR] 2.2 백엔드 (API 및 처리 로직) -->
- **Framework**: FastAPI (Python)
- **Concurrency**: Asynchronous `asyncio` task queue.
- **State Management**: Zero-backend multi-tenant architecture utilizing local state where possible, and basic file/sqlite persistence for jobs.
<!-- [KR] 프레임워크: FastAPI (파이썬) / 비동기 큐 처리 / 무서버 다중 사용자 아키텍처 및 로컬 파일 상태 관리 -->

### 2.3 AI Models & Integrations
<!-- [KR] 2.3 AI 모델 및 통합 연동 -->
- **Text Generation**: Google Gemini 3.6 Pro / NVIDIA Nemotron 3 Ultra (for high-level reasoning and final guide generation).
- **Audio Extraction / Transcription**: Whisper API / Gemini 3.5 Flash-Lite.
- **Vision & PDF Analysis**: PyMuPDF, `pymupdf4llm` (Markdown extraction), and Gemini Vision 3.5 Flash for multimodal reasoning.
<!-- [KR] 텍스트 생성: Gemini 3.6 Pro, Nemotron 3 Ultra / 오디오 변환: Whisper, Gemini Flash-Lite / PDF 분석: pymupdf4llm, Gemini Vision -->

## 3. Data Processing Pipelines
<!-- [KR] 3. 데이터 처리 파이프라인 -->

### 3.1 Video Processing Pipeline (YouTube)
<!-- [KR] 3.1 비디오 처리 파이프라인 (유튜브) -->
1. **Subtitle Fetching**: Attempts to retrieve built-in CC/subtitles directly first (to save costs and time).
2. **Audio Fallback**: If subtitles are unavailable, `yt-dlp` extracts the audio.
3. **Transcription**: The audio is processed via Whisper (chunked if >25MB) or Gemini Flash-Lite.
4. **Generation**: The transcript is passed to the LLM to generate the structured guide.
<!-- [KR] 1. 유튜브 내장 자막 우선 추출 / 2. 자막 없을 시 오디오 다운로드 / 3. Whisper 또는 Gemini로 텍스트 변환 / 4. LLM 가이드 생성 -->

### 3.2 Document Processing Pipeline (PDF)
<!-- [KR] 3.2 문서 처리 파이프라인 (PDF) -->
Supports three processing options depending on user needs:
- **Option A (PyMuPDF)**: Fast, basic text extraction. Best for simple text PDFs.
- **Option B (pymupdf4llm)**: Extracts text with markdown structure (tables, headers). Recommended for complex layouts.
- **Option C (Gemini Native)**: Uploads the raw PDF directly to Gemini via the Files API for full multimodal understanding (charts, images).
<!-- [KR] 3가지 옵션 지원: A(PyMuPDF 기본 텍스트 추출), B(pymupdf4llm 마크다운 구조 유지 - 추천), C(Gemini Files API를 통한 시각적 멀티모달 분석) -->

### 3.3 Web Page Pipeline
<!-- [KR] 3.3 웹페이지 처리 파이프라인 -->
- URL is processed using Jina Reader (or equivalent HTML-to-Markdown scraper) to extract main content text cleanly.
<!-- [KR] Jina Reader를 사용하여 URL에서 불필요한 태그를 제거하고 핵심 텍스트만 마크다운으로 추출 -->

## 4. Token Optimization & Context Caching (Option B)
<!-- [KR] 4. 토큰 최적화 및 컨텍스트 캐싱 (옵션 B) -->
> [!TIP]
> This architecture relies heavily on proactive token cost management.
> <!-- [KR] 이 아키텍처는 선제적인 토큰 비용 관리에 크게 의존합니다. -->

1. **Context Caching Layer**: For large documents (e.g., PDFs > 100 pages, long video transcripts), the system utilizes the `google-genai` Context Caching API. This reduces input token costs by up to 75% for subsequent requests against the same document.
<!-- [KR] 1. 컨텍스트 캐싱 레이어: 대용량 문서는 Gemini의 Context Caching API를 사용하여 이후 동일 문서 요청 시 입력 토큰 비용을 75% 절감합니다. -->

2. **Local RAG (Retrieval-Augmented Generation)**: (Planned) A zero-setup local vector store (`chromadb` or `sqlite-vss`) will embed chunked documents. This allows users to perform chat/Q&A against specific chapters without resending the entire context to the LLM.
<!-- [KR] 2. 로컬 RAG (예정): 무설치 로컬 벡터 DB(chromadb 등)에 문서를 청크 단위로 임베딩하여, 특정 챕터에 대한 채팅 시 전체 텍스트 대신 관련 문맥만 LLM에 전송합니다. -->

## 5. Deployment & Tunneling
<!-- [KR] 5. 배포 및 터널링 -->
- Exposes the local Next.js frontend to the public internet using **Cloudflare Quick Tunnels** (`cloudflared`).
- Bypasses Next.js dev server WebSocket/HMR limitations by running in strictly **Production Mode** (`npm run build && npm run start`).
<!-- [KR] Cloudflare Quick Tunnels를 통해 로컬 서버를 외부 인터넷에 노출하며, HMR 웹소켓 에러 방지를 위해 반드시 프로덕션 모드로 빌드 및 실행합니다. -->

## 6. Business & Deployment Strategy (v1.0)
<!-- [KR] 6. 비즈니스 및 배포 전략 (v1.0) -->
- **BYOK (Bring Your Own Key) Model**: To eliminate recurring server costs and avoid operational overhead (e.g., handling subscriptions, fighting abusers), v1.0 completely drops central cloud databases. Users must input their own Gemini/OpenAI API key to generate content.
  <!-- [KR] BYOK 모델: 반복적인 서버 유지비를 없애고 운영 스트레스를 피하기 위해, v1.0에서는 중앙 클라우드 DB 연동(커뮤니티 공유 기능)을 과감히 포기합니다. 유저는 반드시 본인의 API 키를 입력하여 콘텐츠를 생성해야 합니다. -->
- **Zero-Backend Standalone**: The system runs purely as a local installation or standalone web app. All study guides are saved locally in the user's environment. This ensures 100% data privacy and 0 ongoing API costs for the developer.
  <!-- [KR] 완벽한 무서버 스탠드얼론: 앱은 100% 로컬 설치형 또는 스탠드얼론 웹앱으로 동작하며, 모든 학습서는 유저 환경에 저장됩니다. 이를 통해 유저의 프라이버시를 보호하고 개발자의 유지비용을 0원으로 만듭니다. -->

## 7. Personalization & Learning Methodologies (Ideation)
<!-- [KR] 7. 개인화 및 학습 방법론 (아이디에이션) -->

### 7.1 Problem Statement
- **Current State**: Most AI study guides are static, one-size-fits-all summaries. Users passively consume them, which leads to the "illusion of competence" (feeling like you know it because you read it).
- **The Goal**: Transform the study guide from a static document into an adaptive, interactive learning environment that forces active recall and proves true comprehension.

### 7.2 Explored Alternatives & Wild Ideas
1. **Reverse Feynman Simulator (역-파인만 시뮬레이터)**:
   - *Concept*: Instead of the AI explaining things to the user, the user must explain the core concepts *back* to the AI. The AI takes on a persona (e.g., a curious 10-year-old or a skeptical beginner).
   - *Mechanic*: If the user uses too much jargon or fails to connect concepts, the AI interrupts and says, "I don't get it, what does [Jargon] mean?"
2. **Dynamic Complexity Slider (동적 난이도 슬라이더)**:
   - *Concept*: A real-time UI toggle (like a volume knob) that adjusts the entire document's language and depth from 'ELI5 (Explain Like I'm 5)' up to 'Post-Doc/Academic'.
3. **The "Devil's Advocate" Mode (악마의 대변인 모드)**:
   - *Concept*: The AI identifies the most counter-intuitive point in the video/document and actively debates the user on it, forcing the user to defend the concept to prove they understand it.
4. **Spaced Repetition "Ambush" (간격 반복 기습)**:
   - *Concept*: As the user scrolls or returns to the app later, previously learned concepts are hidden or turned into mini-challenges before they can proceed.

### 7.3 Premise Challenge
- **The Tension**: Do users actually *want* the friction of deep learning, or do they just want a quick summary to save time? 
- **The Pivot**: How do we balance "fast, effortless consumption" (the hook) with "deep, challenging learning" (the value)? Could we separate these into two distinct modes: "Skim Mode" and "Feynman Mode"?

### 7.4 Market Precedents & Limitations (Not a Silver Bullet)
<!-- [KR] 7.4 시장 사례 및 한계점 (은탄환이 아닌 이유) -->
While the Reverse Feynman technique (explaining to AI) is powerful, it is not a silver bullet for personalization.

**Real-World Precedents (벤치마크 사례)**:
1. **Khanmigo (Khan Academy)**: Uses a strict Socratic tutor model. It explicitly refuses to give students the answer, forcing them to explain their reasoning step-by-step. 
   - *Result*: Educators love it because it prevents cheating. Students often find it frustrating when they are genuinely stuck.
2. **Q-Chat (Quizlet)**: Uses an AI tutor to test users via the Socratic method. It asks probing questions based on flashcards.
   - *Result*: Good for micro-learning, but user engagement drops if the session goes on too long due to high cognitive drain.
3. **Rubber Duck Debugging (Devs & ChatGPT)**: Developers instinctively use LLMs as a "rubber duck," explaining their broken code to the AI. The act of explaining often solves the problem before the AI even answers.

**Core Limitations (한계점 및 리스크)**:
1. **Extreme Cognitive Load (높은 인지적 마찰)**: Explaining concepts is exhausting. If users are forced to use Feynman mode for an entire 1-hour video, they will churn. It must be used *surgically* (only on core concepts).
2. **The Cold Start Problem (콜드 스타트 문제)**: If a user completely fails to understand the material, asking them to explain it will cause them to "rage-quit." Feynman mode requires a baseline level of comprehension. If they know 0%, they need a standard explanation, not a Socratic interrogation.
3. **Evaluation Ambiguity (평가의 모호성)**: AI can sometimes falsely reject a good explanation because it lacks specific keywords, or hallucinate and accept a fundamentally flawed explanation just because it sounds confident.

### 7.5 The "Frustration-Free" Feynman Implementation (Safety Nets)
<!-- [KR] 7.5 좌절감 없는 파인만 학습법 구현 (안전망) -->
The system explicitly rejects the "rigid wall" of traditional education and strict Socratic tutors (like Khanmigo). The Reverse Feynman mode must include built-in, frictionless safety nets to prevent learner frustration.

**Proposed Mechanisms (제안 메커니즘)**:
1. **"Yes, And..." Validation (긍정적 우회 교정)**: The AI never outright rejects the user's explanation. If the user is wrong, the AI validates their logic first ("Ah, that makes sense why you'd think that! That's true for X...") and gently guides them to the correct context ("...but what if we look at it from Y's perspective?").
2. **Scaffolded Explanations (반자동 완성형 설명)**: Instead of a blank prompt, the AI starts the sentence and the user finishes it. (e.g., AI: "So to explain it simply, gravity is like a trampoline because..." -> User: "...heavy things bend the fabric.")
3. **The "Tag Team" Mode (협력적 릴레이 설명)**: The AI and the user take turns explaining a concept to a virtual 3rd party. This reduces the burden on the user by splitting the cognitive load 50/50.
4. **Frictionless Escape Hatch (즉각적인 항복 버튼)**: A clearly visible "I'm stuck, explain it to me" button that instantly drops the Feynman challenge and provides a clear, empathetic ELI5 explanation without any penalization.

## 8. Adaptive Cognitive Routing (지능형 학습 라우팅)
<!-- [KR] 8. 적응형 인지 라우팅 체계 -->

### 8.1 The Need for an AI Content Classifier
The Feynman Technique is optimal for **Conceptual Understanding** (e.g., "Why does inflation happen?"). However, it fails completely for other cognitive domains. The system needs an `AI Content Classifier` during the initial processing phase to tag the content type and route the user to the correct UI/UX learning mode.

### 8.2 Non-Feynman Domains & Optimal Methods
1. **Math & Algorithm Proofs (Strict Logic)**
   - *Type*: Sequential, deterministic logic.
   - *Optimal Mode*: **Interactive Step-Tracer**. The system hides the outcome of a formula/code block and asks the user to predict the *next state* (e.g., "What is the value of `i` after this loop?").
2. **Simple Memorization (Facts, Dates, Vocab)**
   - *Type*: Rote data without deep causal links.
   - *Optimal Mode*: **Bizarre Mnemonic Generator & SRS**. The AI generates absurd, highly personalized memory hooks (e.g., linking a historical date to the user's favorite movie) combined with rapid-fire flashcards.
3. **Procedural & Visual Tasks (How-to, Software, Physical Skills)**
   - *Type*: Action-oriented steps.
   - *Optimal Mode*: **Blind Navigation Checklists**. The AI converts the tutorial into a strict checklist. To prove mastery, the user must recount the physical steps without looking (e.g., "First, I click the top-right gear icon...").

### 8.3 The Dynamic UI Implementation
As the LLM processes the video transcript, it embeds metadata tags (`<type:concept>`, `<type:logic>`, `<type:memory>`, `<type:procedure>`) into each chapter. The frontend dynamically swaps the interactive component based on these tags, creating a polymorphic study guide.

### 7.6 Failure Modes & Boundaries (Negative Space)
<!-- [KR] 7.6 실패 모드 및 적용 불가 영역 (바운더리) -->
The "Frustration-Free Feynman" mode is heavily guarded against contexts where it would degrade the user experience.

**Where it MUST NOT be used (적용 금지 영역)**:
1. **Strict Math/Algorithms (수학 및 알고리즘 증명)**: Precision is required. A "Yes, And..." approach to an incorrect time complexity or math formula is an educational failure.
2. **Factoids/Rote Memorization (단순 암기 및 연도/사실)**: Binary knowledge cannot be "explained." Use standard spaced-repetition flashcards instead.
3. **Procedural/Spatial Visuals (시각적/절차적 작업)**: Explaining how to tie a knot or use a 3D UI via text is agonizing.

**Architectural Guardrails (시스템 안전장치)**:
1. **The Two-Strike Rule (투 스트라이크 아웃)**: To prevent an infinite loop of patronizing AI hints ("Yes, And..." Purgatory), the frontend hardcodes a state machine. After 2 failed attempts by the user, the UI automatically triggers the Escape Hatch and reveals the answer.
2. **Gibberish Bypass Prevention**: The client-side must block low-entropy inputs (e.g., "asdf") from wasting API calls, prompting the user to either try genuinely or use the SOS button.
3. **Volatile State Protection**: If the user navigates to another tab (e.g., Transcript) to peek at the answer mid-typing, their drafted text MUST be cached (`localStorage`/Zustand) and restored upon return.

## 9. System Observability & Logging Architecture
<!-- [KR] 9. 시스템 관측성 및 로깅 아키텍처 -->
The system requires robust observability to monitor background jobs and API failures. All system logs are stored in a local SQLite database to adhere to the Zero-Setup philosophy.

### 9.1 SystemLog Schema
The `SystemLog` table explicitly defines errors and warnings. String-only logs are insufficient for debugging.
- `id`: String (Primary Key, UUID)
- `timestamp`: String (ISO 8601, Indexed for fast sorting and pruning)
- `level`: String (INFO, WARN, ERROR, CRITICAL)
- `category`: String (e.g., 'API Error', 'LLM Generation Error')
- `message`: String (Human-readable summary)
- `source`: String (Module origin, e.g., 'Backend / LLM Service')
- `event_name`: String (Specific code event, e.g., 'gemini_api_timeout')
- `details`: Text (JSON string containing stack traces, request IDs, and variables)
- `jobId`: String (Nullable)
- `statusCode`: Integer (Nullable)
- `resolved`: Boolean (Default false)

### 9.2 Zero Silent Failures & DB Contention Prevention
- **Exception-Safe Logging (Shadow Path)**: Logging must NEVER crash the primary business logic. Every database log insert is wrapped in a strict `try...except` block targeting DB exceptions (`sqlite3.OperationalError`, `sqlalchemy.exc.OperationalError`). If the DB insert fails due to lock contention, the logger falls back to standard Python `sys.stderr`.
- **Decoupled Pruning**: Log retention (default 7 days) is enforced via a periodic/probabilistic background cleanup routine, NOT via `DELETE FROM` queries on every insert, preserving SQLite write throughput.

### 9.3 Dashboard & OOM Prevention
- **Strict Pagination**: To prevent Out-Of-Memory (OOM) crashes on the FastAPI server or frontend, the `/api/admin/health` endpoint strictly enforces pagination (`limit` and `offset`) and indexed filtering.
- **Zero-Setup Migrations**: The `SystemLog` table is dynamically instantiated on FastAPI startup (e.g., via `Base.metadata.create_all(bind=engine)`), eliminating the need for manual CLI migration commands (`alembic`).

## 10. Automated AI Persona QA System (Decoupled Black-Box)
<!-- [KR] 10. AI 페르소나 기반 자동화 QA 시스템 (블랙박스 아키텍처) -->
To rigorously evaluate the pedagogical effectiveness of the Socratic Tutor (Discussion Mode) without tightly coupling testing logic to the backend codebase, the system utilizes an isolated, offline QA harness (`qa_harness/evaluate.py`).

### 10.1 Decoupled API-Driven Architecture
The QA system runs as a completely independent HTTP client. It does not import any backend modules. Instead, it interacts with the backend strictly via its public REST API, exactly simulating a frontend client.
- **Pre-flight Health Check**: Before executing tests, the QA runner pings `/api/health` to verify the backend is online, using configurable base URLs (`QA_API_BASE_URL`) rather than hardcoded localhost ports.
- **State Isolation**: Every HTTP request from the QA harness injects an `X-QA-Test-Mode: true` header. The backend detects this header to ensure test data is either kept in-memory or rolled back, preventing pollution of the production SQLite database.

### 10.2 Three-LLM Architecture
The framework utilizes three distinct LLM roles completely isolated from each other:
1. **AI Student (Gemini 3.5 Flash-Lite)**: Adopts a specific persona (defined in `qa_harness/personas.yaml`) and initiates naive or challenging questions.
2. **Socratic Tutor**: The actual production backend logic being tested via HTTP.
3. **The Judge (Gemini 3.6 Pro)**: Reads the transcript and scores the Tutor based on pedagogical rubrics.

### 10.3 Resilience and Observability
- **Asymmetric Timeouts**: To accommodate slow LLM generations on the backend, the QA HTTP client uses a strict 5-second `Connect Timeout` but a generous 120-second `Read Timeout`. Explicit exceptions (`httpx.ReadTimeout`, `httpx.ConnectError`) are caught to differentiate backend crashes from LLM bottlenecks.
- **Correlation Tracing**: The QA runner injects a unique `X-Correlation-ID` header into every request. On `httpx.HTTPStatusError` (e.g., 500 Server Error), this ID is logged to seamlessly trace the exact error trace in the backend logs.
- **Concurrency & Backoff**: Tests run with an `asyncio.Semaphore` limit to prevent self-DDoS. Exponential backoff is natively implemented for handling `429 Too Many Requests` from LLM providers.
- **JSON Parsing Safeguards**: The Judge's output relies on native Structured Outputs. The system specifically catches `pydantic.ValidationError` or `json.JSONDecodeError`, retries twice, and falls back to a `JudgeFormatError` dumping raw output.
