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
