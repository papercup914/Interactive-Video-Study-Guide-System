# [시스템 아키텍처] 유튜브 영상 기반 AI 학습 가이드 자동 생성 파이프라인 & 프롬프트 총괄 명세서

# [시스템 아키텍처] 유튜브 영상 기반 AI 학습 가이드 자동 생성 파이프라인 & 프롬프트 총괄 명세서

> **최종 갱신 일시**: 2026-09-13
> 

> **문서 목적**: 유튜브 영상 URL로부터 구조화된 인터랙티브 학습 가이드(챕터별 서술형 본문, 퀴즈, 파인만 기법, 논리 트레이서, 연상기억법 등)를 자동 생성하는 전체 백엔드 AI 파이프라인 매커니즘, 관련 코드 파일 위치, 모든 프롬프트 전문 및 장애 대응 안전망을 100% 명세하여 원활한 유지보수를 보장함.
> 

---

## 1. 전체 아키텍처 및 엔드-투-엔드(End-to-End) 워크플로우

학습 가이드 생성 시스템은 사용자로부터 유튜브 URL을 입력받아 **메타데이터 수집 → 자막 다중 추출(또는 STT/웹스크랩) → AI 프로파일링 → 목차 설계 → 챕터별 비동기 병렬 생성 → 3중 가드레일 검증 → BZCF 스타일 타이틀 번역 → DB 영속화**에 이르는 완전 자동화 파이프라인으로 구동됩니다.

```
[사용자 요청 (Next.js 웹 클라이언트)]
       │
       ▼ POST /api/guide/start
[FastAPI 라우터 (backend/routers/guide.py)]
       │ (작업 ID 발급 & Celery 작업 발행)
       ▼
[Redis 메시지 브로커] ───► [Celery 비동기 워커 (backend/services/tasks.py)]
                                  │
      ┌───────────────────────────┴───────────────────────────┐
      ▼                                                       ▼
[Step 1 & 2: 메타데이터 & 자막 수집]                [Step 3: AI 프로파일링]
  - yt-dlp 메타데이터 확인                            - transcript 전반 5,000자 분석
  - 실패 시 oEmbed API Fallback                      - 분량/비유 프리셋 & 튜터 페르소나 산출
  - Innertube 모바일 API (0차)
  - 쿠키 세션 / 기본 세션 (1, 2차)
  - yt-dlp 자막 파싱 (3차)
  - Whisper/Gemini 오디오 전사 (4차)
  - Jina Reader 웹 스크랩 (5차 우회)
      │
      ▼
[Step 4: Gemini Context Caching] ──► 긴 텍스트 파일 업로드 및 캐시 핸들 획득
      │
      ▼
[Step 5: 목차(Outline) 설계] (backend/services/llm/outline.py)
  - 공식 챕터 존재 시: BZCF 스타일 질문형/통찰형 챕터명으로 각색
  - 공식 챕터 부재 시: 시간 순서(Time Sequence) 엄격 유지 목차 생성
  - 실패 시: 도메인별 4대 표준 챕터 휴리스틱 안전망 작동
      │
      ▼
[Step 6 & 7: 챕터별 비동기 병렬 생성] (backend/services/llm/chapter.py)
  - asyncio.Semaphore(기본 3병렬) 동시성 제어
  - 12,000자 초과 스크립트 시 현재 챕터 기준 스마트 슬라이싱
  - 2단계 엄격 출력 구조 강제 (마크다운 서술형 본문 + 인터랙티브 위젯 1종)
      │
      ▼
[Step 8: 3중 품질 가드레일 및 자동 복구]
  - 1차: sanitize_chapter_narrative (인사말/메타텍스트/중복제목 제거)
  - 2차: validate_chapter_narrative (글자수/한국어 150자/2단계 구조 검증)
  - 검증 실패 시 에스컬레이션 프롬프트로 최대 3회 자동 재생성
  - 최종 실패 시: 도메인 중립적 비상 안전망(_build_heuristic_chapter) 합성
      │
      ▼
[Step 9: 가이드 대표 제목 번역 및 영속화]
  - translate_title: BZCF 스타일 [타깃 뱃지] + 직관적 훅 제목 - 부제
  - SQLite(jobs.db)에 최종 가이드 문서 및 체크포인트 영속화
  - 클라이언트 폴링(GET /api/guide/poll/{job_id})으로 완료 전달
```

---

## 2. 관련된 모든 소스 코드 파일 맵 (Codebase Map)

학습 가이드 생성 파이프라인과 직접 연관된 모든 백엔드 코드 파일의 위치와 핵심 역할입니다:

| 구분 | 파일 경로 (File Path) | 핵심 역할 및 책임 |
| --- | --- | --- |
| **진입점 & 서버** | `backend/main.py` | FastAPI 앱 초기화, CORS 설정, 백그라운드 캐시 무결성 검증/정리(`_bg_cache_cleanup`) |
| **비동기 브로커** | `backend/celery_app.py` | Celery 인스턴스 설정 및 Redis 브로커/백엔드 연동 |
| **환경 설정** | `backend/config.py` | 모델 버전, API 키(OpenAI, Gemini, OpenRouter, Groq 등), CORS, 시스템 설정 로드 |
| **API 라우터** | `backend/routers/guide.py` | `/start` (가이드 생성 요청), `/check` (중복 조회), `/presets` (변환 매트릭스), `/poll/{job_id}` (진행률 조회) |
| **태스크 총괄** | `backend/services/tasks.py` | `async_generate_guide` 오케스트레이션 함수 (메타데이터/자막 추출, 프로파일링, 목차, 챕터 생성 병렬 제어, 완료 처리) |
| **영상 처리** | `backend/services/video.py` | `extract_video_id`, `get_video_metadata` (yt-dlp + oEmbed), `get_youtube_transcript` (Innertube/쿠키/yt-dlp), `download_audio` |
| **외부 소스** | `backend/services/source.py` | `extract_text_from_web` (Jina Reader 유튜브/웹페이지 스크랩 Fallback), `extract_text_from_pdf`, `upload_pdf_to_gemini` |
| **작업/DB 관리** | `backend/services/job_manager.py` | SQLite(`backend/data/jobs.db`) 작업 상태 갱신, 체크포인트 저장(`save_chapter_checkpoint`), 가이드 저장/조회 |
| **LLM 파사드** | `backend/services/llm.py` | 하위 호환성을 위해 `backend/services/llm/` 모듈들의 함수를 재익스포트하는 파사드 모듈 |
| **LLM 클라이언트** | `backend/services/llm/clients.py` | Gemini/OpenAI/OpenRouter/Groq 클라이언트 팩토리, OpenRouter 무료 모델 엔드포인트 격리 라우팅, 지수 백오프 재시도 설정 |
| **목차 생성** | `backend/services/llm/outline.py` | `generate_outline` (공식 챕터 각색 및 시간순 목차 생성, 디스크 캐싱, `_build_heuristic_sections` 안전망) |
| **챕터 생성** | `backend/services/llm/chapter.py` | `async_generate_chapter_content` (2단계 구조 강제, 스마트 슬라이싱, 자동 재시도 루프, `_build_heuristic_chapter` 비상 안전망) |
| **프롬프트 빌더** | `backend/prompts/chapter_guide.py` | `build_chapter_system_prompt` (4대 절대 준수 규칙, 4종 인터랙티브 위젯 JSON 스키마 정의) |
| **프로파일링/번역** | `backend/services/llm/profiling.py` | `profile_content` (콘텐츠 성격 분석 및 페르소나 계산), `translate_title` (BZCF 스타일 제목 번역), `extract_image_keyword`, `generate_answer` |
| **검증 및 살균** | `backend/services/llm/validators.py` | `sanitize_chapter_narrative` (인사말/메타텍스트/중복제목 정규식 제거), `validate_chapter_narrative` (글자수/한국어/2단계 구조 검증) |
| **오디오 STT** | `backend/services/llm/audio.py` | `process_audio` (Whisper API 전사 + 실패 시 Gemini 멀티모달 오디오 변환 Fallback, 20MB 청킹) |
| **캐시 관리** | `backend/services/llm/cache.py` | Gemini Context Caching(`get_or_create_document_cache`), 챕터/목차 로컬 디스크 캐시 오염 자동 감지 및 퍼지 |
| **프리셋 상수** | `backend/constants/presets.py` | 분량(`아주 상세하게`, `적당한 설명`, `핵심 요약`) 및 비유(`풍부한 비유`, `적절한 비유 추가`, `비유 없이 담백하게`) 정규화 로직 |

---

## 3. 학습 가이드 자동 생성 10단계 메커니즘 심층 분석

### [Step 1] 클라이언트 요청 접수 및 비동기 작업 큐 발행

- **코드 위치**: `backend/routers/guide.py` (`start_guide_generation`)
- 사용자가 유튜브 URL, AI 제공자(Provider), 분량 프리셋, 비유 프리셋, 학습자 프로필(페르소나)을 전송합니다.
- 고유한 작업 ID(`job_{uuid}`)를 발급하고 SQLite DB에 `status="processing"`으로 등록합니다.
- 무거운 AI 연산이 FastAPI 이벤트 루프를 블로킹하지 않도록 Celery 비동기 작업(`celery_generate_guide_task.delay(job_id, request_data, file_paths)`)으로 위임하고 즉시 200 OK와 `job_id`를 반환합니다.

### [Step 2] 영상 메타데이터 및 원본 제목 100% 사수

- **코드 위치**: `backend/services/video.py` (`get_video_metadata`), `backend/services/tasks.py`
- AWS EC2 등 클라우드 IP 환경에서 유튜브 봇 감지로 인해 메타데이터 추출이 차단되는 현상을 방어하기 위해 **2중 메타데이터 수집 전략**을 가동합니다:
    1. `yt-dlp` 메타데이터 추출 (`extract_flat=True`, 다중 클라이언트 `mweb, web, android, ios` 적용): 영상 제목, 전체 재생 시간(초), 등록된 타임스탬프 챕터 수집.
    2. `oEmbed API Fallback` (`https://www.youtube.com/oembed?url={canonical_url}&format=json`): 인증이나 세션 없이 0.1초 만에 비디오 원본 제목을 100% 반환하는 유튜브 공식 공개 엔드포인트. 메타데이터가 `"제목 알 수 없음"`으로 떨어질 경우 즉시 작동하여 올바른 원제 확보.

### [Step 3] 영상 자막(Transcript) 5단계 다중 수집 파이프라인

- **코드 위치**: `backend/services/video.py` (`get_youtube_transcript`, `_fetch_innertube_captions`), `backend/services/tasks.py`
- 영상 자막은 AI 학습 가이드의 원천 재료입니다. 어떠한 네트워크/IP 차단 환경에서도 텍스트를 확보할 수 있도록 5단계 Fallback 체계를 구축했습니다:
    - **0차 (Innertube 모바일 API)**: YouTube의 내부 모바일 API(`ANDROID`, `IOS`, `WEB_EMBEDDED_PLAYER`)를 통해 자막 트랙 XML을 직접 호출. 한국어 자막이 없을 경우 실시간 번역(`&tlang=ko`) 파라미터를 결합하여 초고속 한글 자막 획득.
    - **1차 (쿠키 세션 YouTubeTranscriptApi)**: 서버 내 `cookies.txt`가 존재할 경우 Netscape 쿠키를 주입한 세션으로 자막 추출.
    - **2차 (기본 세션 YouTubeTranscriptApi)**: 쿠키 만료 또는 비로그인 환경에서 표준 세션으로 자막 추출.
    - **3차 (yt-dlp 내장 자막 추출기)**: `writesubtitles=True`, `writeautomaticsub=True` 옵션으로 `json3` / `vtt` 트랙 다운로드 및 파싱.
    - **4차 (오디오 다운로드 및 AI STT)**: 자막이 전혀 없는 영상의 경우 `download_audio`로 MP3 추출 후 `process_audio` 가동. OpenAI Whisper-1 우선 시도 → 실패 시 Google Gemini 멀티모달 파일 업로드로 자동 전사.
    - **5차 (Jina Reader 웹 분석 우회)**: 클라우드 IP가 완전히 차단되어 오디오 다운로드까지 실패할 경우, Jina Reader(`https://r.jina.ai/{url}`)를 통해 웹페이지 마크다운 스크랩 수행. `clean_youtube_scraped_text`로 웹 UI 잔여물/조회수/추천영상 잡음을 제거하고, 본문 텍스트 내 타임스탬프가 있으면 `extract_chapters_from_scraped_text`로 공식 챕터 정보까지 복원.

### [Step 4] AI 콘텐츠 프로파일링 및 튜터 페르소나 설정

- **코드 위치**: `backend/services/llm/profiling.py` (`profile_content`)
- 스크립트 전반부 최대 5,000자를 LLM에 전달하여 콘텐츠의 성격, 정보 밀도, 대상 독자를 분석합니다.
- 만약 사용자가 분량/비유를 "Auto"로 설정했다면 영상 난이도에 맞추어 `length_preset`과 `analogy_preset`을 자동 결정합니다.
- 영상 주제에 가장 부합하는 **맞춤형 AI 튜터 페르소나**(역할: 예 `IT 시니어 아키텍트`, 어조: 예 `전문적이고 냉철하게`, 집중 영역: 예 `실무 아키텍처와 장애 방지`)를 도출하여 후속 챕터 작성 지침에 주입합니다.

### [Step 5] 대용량 컨텍스트 처리 & Gemini Context Caching

- **코드 위치**: `backend/services/tasks.py`, `backend/services/llm/cache.py`
- 긴 영상의 전체 스크립트를 여러 챕터 생성 시 반복 전송하면 막대한 토큰 비용과 지연이 발생합니다.
- 제공자가 Gemini인 경우 스크립트를 로컬 파일로 저장한 뒤 Google Files API로 업로드하여 캐시를 활성화하고, `GEMINI_FILE_URI::{uploaded_file.name}` 참조를 유지하여 챕터 생성 시 초고속 저비용 참조를 수행합니다.

### [Step 6] 목차(Outline) 설계 및 시간순 정렬

- **코드 위치**: `backend/services/llm/outline.py` (`generate_outline`)
- **A. 공식 챕터가 존재하는 경우**: 원작자의 타임스탬프 챕터 제목들을 입력받아, BZCF 스타일의 감칠맛 나는 한국어 질문형/통찰형 챕터 제목(Why/How)으로 번역 및 각색합니다. 원본 챕터의 개수와 시간적 순서(Time Sequence)는 100% 동일하게 유지합니다.
- **B. 공식 챕터가 없는 경우**: 스크립트 글자 수에 비례하여 적정 챕터 수(요약: 3~5개, 적당: 5~12개, 상세: 7~20개)를 계산하고, 영상의 도입부부터 중간, 결론에 이르는 **시간 흐름(Time Sequence)을 엄격하게 준수**하는 한국어 목차를 생성합니다.
- **C. AI API 호출 실패 시 휴리스틱 안전망 (`_build_heuristic_sections`)**:
    - 원본 영상 제목과 스크립트 서두를 분석하여 도메인(비즈니스/스타트업, 기술/개발, 일반교양/인문)을 자동 판별.
    - 영상의 실제 핵심 키워드를 반영한 4대 표준 서술형 챕터를 즉시 구성하여 파이프라인 중단을 원천 방지합니다.

### [Step 7] 챕터별 비동기 병렬 생성 및 스마트 청킹 (Smart Slicing)

- **코드 위치**: `backend/services/llm/chapter.py` (`async_generate_chapter_content`), `backend/services/tasks.py`
- `asyncio.Semaphore(3)`를 적용하여 최대 3개 챕터를 동시에 비동기 병렬 생성합니다.
- **체크포인트 캐싱**: `save_chapter_checkpoint`를 통해 이미 유효하게 생성된 챕터는 디스크/DB에서 즉시 복원하여 중복 API 호출을 방지합니다.
- **스마트 슬라이싱 (Smart Slicing)**: 12,000자를 초과하는 초대형 스크립트의 경우, 현재 생성하려는 챕터의 위치(청크 인덱스)를 기준으로 전후 4,500자(총 9,000자 윈도우)를 지능적으로 슬라이싱하여 LLM에 전달합니다. 이를 통해 LLM 컨텍스트 낭비와 타임아웃을 방지하고 해당 챕터 본문에 대한 집중도를 극대화합니다.

### [Step 8] 2단계 엄격 출력 구조와 4종 인터랙티브 위젯

- **코드 위치**: `backend/prompts/chapter_guide.py` (`build_chapter_system_prompt`)
- 모든 챕터는 다음의 2단계 구조를 엄격하게 지켜야 합니다:
    1. **파트 1: 상세 마크다운 서술형 본문** (최소 1,000~2,000자 이상)
        - `## {section_title}`
        - 도입 및 핵심 문제 제기 (훅 & 질문)
        - 상세 원리 및 비유 설명
        - `> **💡 핵심 인사이트**` 강조 박스
        - 실무 활용 팁 / 주의사항
    2. **파트 2: 인터랙티브 학습 장치 위젯 (맨 끝에 1개 태그만 부착)**
        - `<feynman>`: 개념 이해 및 원리 파악을 위한 1:1 파인만 대화 시나리오
        - `<steptracer>`: 알고리즘, 코드 흐름, 수학적 도출을 위한 단계별 트레이서
        - `<mnemonic>`: 용어 정의 및 핵심 사실 암기를 위한 연상기억 스토리 & 플래시카드
        - `<procedure>`: 실무 도구 조작 및 행동 지침을 위한 체크리스트

### [Step 9] 3중 품질 가드레일 (살균, 검증, 자동 재시도, 비상 안전망)

- **코드 위치**: `backend/services/llm/validators.py`, `backend/services/llm/chapter.py`
    1. **1차 살균 (`sanitize_chapter_narrative`)**: LLM이 무의식적으로 출력한 인사말("안녕하세요", "여러분의 튜터입니다"), 메타 텍스트("[파트 1: ...]"), 서두의 중복 챕터 제목 라인을 정규식으로 완벽 제거.
    2. **2차 검증 (`validate_chapter_narrative`)**:
        - 원시 JSON이나 태그로 바로 시작하는지 여부 검사
        - 서두에 인사말이나 메타텍스트가 잔류했는지 검사
        - 태그 앞의 순수 서술형 본문 분량(최소 800~1,200자) 충족 여부 검사
        - 한국어 글자 수가 150자 이상인지(영어 원문 미번역 방지) 검사
    3. **자동 에스컬레이션 재시도 (최대 3회)**: 검증 탈락 시 탈락 사유(예: 한글 미번역, 본문 분량 부족, 태그로 시작 등)를 에스컬레이션 지시문에 실시간으로 결합하여 모델에 재요청.
    4. **최종 비상 안전망 (`_build_heuristic_chapter`)**: 모든 API가 실패하거나 타임아웃될 경우, 웹 잡음 정규식 필터와 10글자 이상 한글 문장 가드레일을 통과한 실제 스크립트 문장을 조립하여 완성도 높은 4단락 서술문과 `<quiz>` 위젯을 합성.

### [Step 10] BZCF 스타일 타이틀 번역 및 최종 영속화

- **코드 위치**: `backend/services/llm/profiling.py` (`translate_title`), `backend/services/job_manager.py`
- 원본 영상 제목과 본문 스크립트를 종합하여 100만 지식 채널(BZCF) 스타일의 직관적인 제목을 생성합니다:
    - 형태: `[타깃 뱃지] 직관적 훅 제목 - 부제` (예: `[예비 창업가 필독] 돈이 아닌 '이것'에 미친 사람만 창업해야 하는 이유 - 폴 그레이엄의 위대한 창업가론`)
    - **Negative Constraint 적용**: 영상 맥락과 무관한 수험생 클리셰("공부 안 해도 점수 오르는", "뇌 깨우기" 등) 생성 금지.
- 최종 완성된 전체 챕터 딕셔너리와 메타데이터를 SQLite DB(`jobs.db`)에 영속화하고 작업 완료(`completed`) 상태로 마감합니다.

---

## 4. 모든 관련 프롬프트 전문 (100% Full Prompt Reference)

파이프라인에서 실제 LLM에 전달되는 모든 프롬프트의 원문 전문입니다.

### 4.1 챕터 시스템 프롬프트 (`backend/prompts/chapter_guide.py`)

```python
def build_chapter_system_prompt(
    section_title: str,
    tutor_directive: str,
    learner_profile: str,
    analogy_instruction: str,
    length_instruction: str
) -> str:
    profile_text = learner_profile if learner_profile else "일반적인 성인 학습자"
    
    return f"""{tutor_directive}

제공된 [전체 스크립트]를 분석하여 챕터 제목 '{section_title}'에 해당하는 내용으로 상세한 챕터 학습 가이드 본문을 작성하십시오.

<PERSONA_DIRECTIVE>
[학습자 프로필]
{profile_text}
1. 튜터 페르소나의 '어조'와 학습자 프로필의 '원하는 튜터 어조'를 조화롭게 섞어 본문 전체에 걸쳐 철저하게 유지하십시오.
2. 비유 강제: 어려운 개념을 설명할 때는 프로필의 '주요 관심사'와 관련된 메타포(비유)를 하나 이상 들어 설명하십시오. 
3. 눈높이 강제: '학습 목표'와 '연령대/직업'에 맞추어 전문 용어의 수준을 조절하십시오.
4. 번역 강제: 외국어 영상이더라도 100% 자연스러운 한국어로 번역 및 해설하십시오.
</PERSONA_DIRECTIVE>

======================================================================
[🚨 초강력 절대 준수 1: 100% 자연스러운 한국어 번역 및 해설 서술 (Strict Korean Output Policy)]
- 분석 대상 원본 영상의 스크립트가 영어, 일본어 등 어떠한 외국어이더라도, **모든 본문 서술(도입 훅, 상세 설명, 비유, 핵심 인사이트 박스, 실무 팁)과 위젯 태그 내부 텍스트는 예외 없이 100% 자연스럽고 유창한 한국어로 번역 및 해설하여 작성**해야 합니다.
- 영문 고유명사(예: Docker, API, Git, PromptQL, Python 등 필수 기술 용어)를 제외한 모든 설명 문장은 유려한 한국어 문장(~합니다, ~입니다)으로 번역하여 서술하십시오.
- 절대로 영어나 외국어로 본문을 작성하지 마십시오. 영문 본문 출력은 시스템 품질 검증에서 즉시 탈락(Reject) 처리됩니다.
======================================================================
[🚨 초강력 절대 준수 2: 인사말/자기소개 완전 영구 금지 (Strict Zero-Greeting Policy)]
"안녕하세요", "여러분의 튜터입니다", "이번 시간에는...", "반갑습니다" 등의 인사말이나 챗봇식 자기소개를 **일절 단 한 글자도 출력하지 마십시오.**
어떠한 페르소나가 주어지더라도 인사말은 허용되지 않습니다.
본문 서두는 반드시 이 챕터에서 해결하고자 하는 핵심 질문(Why/What)이나 흥미로운 실무/기술적 배경 한 줄(Hook)로 즉시 시작하십시오!
======================================================================
[🚨 초강력 절대 준수 3: 메타 텍스트 출력 금지]
출력 결과에 "[파트 1: 상세 챕터 서술형 학습 본문]", "---", "### [파트 2...]" 와 같은 안내용 구분선이나 구조 텍스트를 절대 출력하지 마십시오.
오직 마크다운 포맷(`## {section_title}`)의 실제 본문 내용부터 바로 시작해야 합니다.
======================================================================
[🚨 초강력 절대 준수 4: 2단계 엄격 출력 구조 (모두 한국어로 작성)]
당신의 출력은 반드시 아래 2단계 순서를 완벽히 지켜야 하며, 메타 안내 텍스트 없이 100% 한국어 내용만 출력하십시오.

(본문 시작 부분)
## {section_title}
1. **도입 및 핵심 문제 제기 (훅 & 핵심 요약 중심)**: 
   - 인사말 없이 즉시 시작하여 한국어로 학습자의 호기심 자극.
2. **상세 원리 및 비유 설명**: 
   - 100% 자연스러운 한국어로 깊이 있게 풀어서 설명.
   - {analogy_instruction}
3. **핵심 인사이트 박스**: `> **💡 핵심 인사이트**` 형태의 한국어 Markdown 인용구를 활용.
4. **실무 활용 팁 / 주의사항**: 한국어로 실생활/업무 활용 꿀팁 안내.
5. **분량 지침**: {length_instruction}

(본문이 끝난 직후 아래 태그 중 1개만 부착 - 메타 텍스트 없이 태그만, JSON 내부 값도 100% 한국어)

[주의사항]
- 반드시 여는 태그와 닫는 태그(예: `<feynman>` ... `</feynman>`)로 전체 JSON을 감싸야 합니다.
- 본문 서술 없이 태그만 출력하면 안 되며, 100% 한국어 서술형 본문 맨 아래에 부록으로 들어가야 합니다.
- JSON 내부의 모든 설명 및 질문/답변 텍스트도 100% 자연스러운 한국어로 작성하십시오.

1. 개념 이해 (CONCEPT): 원리, 이유, 복잡한 메커니즘을 다루는 챕터.
<feynman>
{{
  "tag_team_scenario": "학습자와 AI가 한 팀이 되어 관련 지식이 전혀 없는 초보자에게 이 개념을 쉽게 설명하는 흥미로운 상황 제시",
  "target_persona": "설명을 들을 가상의 초보자 특징 (예: '중력을 처음 배우는 초등학생')",
  "initial_ai_message": "AI가 먼저 사고 실험 파트너로서 대화를 시작하며 반자동 완성을 유도하는 문장",
  "concept_summary": "사용자가 도저히 모를 때(SOS) 즉시 보여줄 아주 쉽고 완벽한 1문단짜리 비유적 정답 요약"
}}
</feynman>

2. 논리/수학/알고리즘 (LOGIC): 단계별 증명, 코드의 흐름, 수학적 도출을 다루는 챕터.
<steptracer>
{{
  "scenario": "풀어야 할 문제 상황이나 코드 스니펫",
  "steps": [
    {{"question": "이 루프를 한 번 돌고 나면 변수 x의 값은 무엇이 될까요?", "answer": "x는 5가 됩니다. 왜냐하면..."}},
    {{"question": "다음 단계는?", "answer": "..."}}
  ]
}}
</steptracer>

3. 단순 암기 (MEMORY): 연도, 사실관계, 용어의 정의 등 논리적 설명보다 단순 기억이 필요한 챕터.
<mnemonic>
{{
  "story": "학습자의 관심사나 아주 기상천외한 요소를 활용하여 이 사실을 평생 잊지 않게 만들어주는 짧고 강렬한 연상기억법 스토리",
  "flashcards": [
    {{"q": "앞면 질문", "a": "뒷면 정답"}},
    {{"q": "앞면 질문", "a": "뒷면 정답"}}
  ]
}}
</mnemonic>

4. 절차적/시각적 작업 (PROCEDURE): 툴 사용법, 요리 순서 등 행동 지침이 필요한 챕터.
<procedure>
{{
  "checklists": [
    {{"step": 1, "action": "작업 1단계 수행", "hint": "도움말 및 팁"}},
    {{"step": 2, "action": "작업 2단계 수행", "hint": "도움말 및 팁"}}
  ]
}}
</procedure>

반드시 4가지 중 현재 챕터에 가장 적합한 1가지만 골라 정확한 JSON 구조로 본문 맨 끝에 덧붙여 출력하세요."""
```

---

### 4.2 챕터 생성 사용자 프롬프트 & 재시도 에스컬레이션 (`backend/services/llm/chapter.py`)

```python
user_instruction = (
    f"[🚨 최우선 필수 지침: 100% 자연스러운 한국어로 번역 및 해설 서술 (Strict Korean Policy)]\n"
    f"원본 영상 스크립트가 영어, 일본어 등 외국어이더라도, 출력되는 모든 마크다운 서술형 본문과 인터랙티브 태그 내용은 100% 자연스럽고 유창한 한국어로 번역 및 풀어서 작성하십시오. 필수 기술 용어(Docker, API, PromptQL 등)를 제외하고 영문 문장을 출력하면 시스템 검증에서 즉시 탈락(Reject)됩니다.\n\n"
    f"다음은 분석할 원본 영상 전체 스크립트입니다:\n\n{chunked_context}\n\n"
    f"=======================================================\n"
    f"[작성 지시: 챕터 '{section_title}']\n"
    f"위 스크립트를 분석하여 '{section_title}'에 대한 마크다운 서술형 학습 본문을 100% 자연스러운 한국어로 먼저 풍부하게 작성({target_min_chars}자 이상)하고, 맨 마지막에 인터랙티브 학습 장치 태그 1개를 부착하세요.\n"
    f"- [100% 한국어 서술]: 본문의 모든 설명, 비유, 인사이트, 팁은 100% 자연스러운 한국어로 번역 및 작성하십시오.\n"
    f"- [도입부 인삿말/자기소개 완전 금지]: '안녕하세요', '여러분의 튜터입니다' 등 의례적인 인사말/자기소개를 절대 쓰지 말고, 챕터의 핵심 질문(Why/What) 또는 흥미로운 실무 배경 한 줄로 곧바로 시작하십시오.\n"
    f"- [메타 텍스트 금지]: '[파트 1...]', '[파트 2...]' 같은 안내용 텍스트를 절대 출력하지 마십시오.\n"
    f"- 절대로 XML 태그나 JSON으로 바로 시작하지 마십시오. 반드시 마크다운 대제목(## {section_title})과 핵심 문제 제기 본문부터 시작하십시오!"
)

# [검증 실패 시 에스컬레이션 주입 지시문]
korean_extra = (
    "🚨 [경고: 외국어 미번역 감지!] 이전 출력이 한국어가 아닌 외국어(영어 등)로 작성되었습니다.\n"
    "지금 즉시 본문의 모든 설명과 문장을 100% 유창하고 자연스러운 한국어로 번역 및 해설하여 작성하십시오!\n"
    "고유 기술 명칭(예: Docker, API, PromptQL 등) 외에 영문 문장이 단 하나라도 포함되어서는 안 됩니다!\n"
) if "한국어" in reason else ""

escalation = (
    f"\n\n[🚨 치명적 오류 수정 지시: 지침 위반 ({reason})]\n"
    f"{korean_extra}"
    f"이전 출력에서 서술형 학습 본문이 누락되거나 분량이 부족했거나, 인사말/메타텍스트가 포함되었거나, 한국어로 번역되지 않았습니다.\n"
    f"절대로 인사말(안녕하세요, 반갑습니다, 여러분의 튜터입니다 등)이나 메타 태그([파트 1...])를 출력하지 마십시오!\n"
    f"반드시 마크다운 대제목(## {section_title})으로 시작하여, 최소 {target_min_chars}자 이상의 깊이 있는 100% 한국어 서술형 본문(도입 훅, 상세 원리 및 비유, 핵심 인사이트 박스, 실무 팁)을 먼저 완벽히 작성한 뒤, 맨 마지막에만 1개의 인터랙티브 태그를 부착하십시오!\n"
    f"절대로 XML 태그로 바로 시작하거나 본문 없이 태그만 출력하지 마십시오!\n"
)
```

---

### 4.3 목차(Outline) 생성 프롬프트 (`backend/services/llm/outline.py`)

#### A. 유튜브 공식 챕터가 존재하는 경우

```
당신은 100만 지식 큐레이션 채널(예: BZCF 등)의 수석 콘텐츠 기획자입니다.
유튜브 영상의 원작자가 등록한 공식 챕터 정보가 주어집니다.
이 공식 챕터들을 독자가 흥미를 느끼고 핵심 교훈(Benefit)을 직관적으로 파악할 수 있도록
감칠맛 나는 한국어 질문형/통찰형 챕터 제목으로 번역 및 각색해주세요.

[작성 규칙]
- 단순한 직역 대신, 시청자가 해당 파트에서 얻어갈 수 있는 '핵심 질문(Why/How)'이나 '인사이트'가 드러나도록 매력적으로 작성하세요.
  (예: "Why Today's Startups Are More Ambitious" -> "왜 지금 세대의 스타트업은 더 거대해졌는가?")
  (예: "What Actually Motivates Founders" -> "돈이 아닌 '이것'에 미친 사람만 창업해야 하는 이유")
- 원래의 챕터 개수와 시간적 순서(Time Sequence)를 100% 엄격하게 동일하게 유지해야 합니다.
- 각 목차 항목은 번호나 기호 없이 새로운 줄에 순수 한국어 제목만 하나씩 작성해줘.

공식 챕터 제목:
{chapter_text}
```

#### B. 유튜브 공식 챕터가 없는 경우 (스크립트 분석)

```
당신은 100만 지식 큐레이션 채널(예: BZCF 등)의 수석 콘텐츠 기획자입니다.
주어진 내용(오디오 또는 스크립트)을 분석하여 학습용 목차(Outline)를 작성해줘.
{outline_instruction}
- [🚨 최우선 절대 준수: 시간 순서(Time Sequence) 엄격 유지]
  반드시 영상의 시작(도입/배경)부터 중간(핵심 내용/원리/실습), 끝(결론/마무리/전망) 순서대로 시간 흐름에 맞게 나열해야 합니다.
  절대로 '결론'이나 '마무리'가 1번이나 앞부분에 오거나, '도입'이나 '개요'가 뒷부분에 오는 역순(Inversion)으로 작성하지 마십시오!
- [직관적 훅 챕터 지침]:
  '핵심 원리와 메커니즘 분석', '시스템 아키텍처' 같은 무미건조한 공학적 표현을 일괄 적용하지 마십시오.
  영상의 성격(비즈니스, 스타트업, 인문, 라이프, 기술 등)에 완벽히 맞추어, 
  독자의 지적 호기심을 자극하고 실질적 통찰을 제공하는 생생한 질문형/메시지형 챕터 제목을 작성하세요.
  (예: "비즈니스 모델의 3대 성공 공식", "위대한 파운더를 만드는 단 1가지 조건", "실전에 즉시 적용하는 4단계 액션 플랜")
- [중요] 원본 스크립트가 외국어(영어 등)이더라도, 각 목차 항목의 제목은 반드시 자연스럽고 명확한 한국어로 번역하여 작성하세요.
- 각 목차 항목은 번호나 기호 없이 새로운 줄에 순수 한국어 제목만 하나씩 작성해줘.
```

---

### 4.4 AI 콘텐츠 프로파일링 프롬프트 (`backend/services/llm/profiling.py`)

```
You are an expert AI content profiler. Analyze the following transcript sample and determine its content type, information density, and target audience.
Based on your analysis, choose the most appropriate settings for generating a study guide.

Output MUST be a valid JSON object without any markdown formatting. Use this EXACT schema:
{
    "length_preset": "핵심 요약" | "적당한 설명" | "아주 상세하게",
    "analogy_preset": "비유 없이 담백하게" | "적절한 비유 추가" | "풍부한 비유",
    "profile_message": "A short, friendly Korean message explaining your decision (e.g., '💡 AI가 전문적인 IT 강의로 인식하여 비유 없이 상세하게 정리합니다.')",
    "tutor_persona": {
        "role": "The specific role the AI should take (e.g., '문학 평론가', 'IT 시니어 개발자', '열정적인 동기부여 강사', '중립적인 토론 진행자')",
        "tone": "The tone of voice (e.g., '전문적이고 냉철하게', '친절하고 비유를 섞어서', '학술적이고 객관적으로')",
        "focus_areas": "What to focus on based on content type (e.g., '핵심 쟁점과 논거 분석', '실무 적용 가능한 코드 스니펫', '저자의 의도와 문맥 해석')"
    }
}

Transcript Sample:
{sample_text}
```

---

### 4.5 BZCF 스타일 타이틀 번역/각색 프롬프트 (`backend/services/llm/profiling.py`)

```
당신은 100만 구독자를 보유한 탑티어 지식 큐레이션 채널(예: BZCF 등)의 메인 에디터이자 베스트셀러 출판 기획자입니다.
주어진 유튜브 영상의 제목과 맥락(자막/설명 발췌)을 면밀히 분석하여, 학습자가 당장 열어보고 싶도록 직관적이고 매력적인 한국어 학습 가이드 대표 제목을 작성해주세요.

[🚨 절대 금지 규칙 - 엄격 준수]
1. 영상의 실제 본문 내용과 무관한 일반적인 수험/공부법 어그로 문구(예: "공부 안 해도 점수 오르는", "마법의 학습 가이드", "10분 투자로 뇌 깨우기", "성적 향상 비법" 등)를 절대 창작하지 마십시오!
2. [타깃 뱃지]에 [학습 가이드 필독]이나 [영상 필독]처럼 아무런 의미가 없는 일반 명사를 절대 쓰지 마십시오. 반드시 영상의 실제 도메인과 타깃(예: [예비 창업가 필독], [초기 창업자 필독], [스타트업 대표 필수], [개발자 필독], [AI 연구자 추천] 등)을 정확히 지정하십시오.
3. 만약 원본 제목이 일반적이거나 불명확하더라도, 반드시 아래 '영상 내용/설명 발췌'에서 핵심 인물(예: 폴 그레이엄, YC 등)과 핵심 사건/주제(스타트업, 야망, AI, 투자 등)를 찾아내어 제목을 작성하십시오.

[작성 규칙]
1. [타깃 뱃지]: 영상의 핵심 내용을 가장 필요로 하는 실제 대상 독자를 맨 앞에 대괄호로 지정.
2. 직관적 훅 제목: 영상의 본질적 통찰과 질문을 정조준하는 직관적이고 강력한 제목(예: "사업하고 싶으면 이거 끝까지 봐야함", "진짜 창업가를 움직이는 힘은 돈이 아니다", "위대한 아이디어가 처음엔 두려워 보이는 이유").
3. 명확한 부제: 하이픈(-) 뒤에 영상의 핵심 인물이나 핵심 주제(예: "폴 그레이엄의 위대한 창업가론").
4. 최종 출력 형태는 오직 다음 한 줄만 출력해야 합니다:
   [타깃 뱃지] 직관적 훅 제목 - 부제
5. 따옴표나 기타 설명, 서론 없이 오직 최종 제목 한 줄만 출력하세요.

원본 제목: "{title}"{context_snippet}
```

---

### 4.6 1:1 사고 확장 파트너 Q&A 프롬프트 (`backend/services/llm/profiling.py`)

```
당신은 학습자의 질문에 답하는 1:1 맞춤형 사고 확장 파트너입니다.
사용자가 문서 학습 중 특정 단어나 문장을 선택하여 질문을 남겼습니다.

[전체 문맥 (배경 지식 참고용)]: 
{context}

[사용자가 선택한 텍스트 (집중 분석 대상)]: 
"{selected_text}"

[사용자의 질문]: 
{question}

<PERSONA_DIRECTIVE>
당신은 무미건조한 AI가 아닙니다. 아래의 [학습자 프로필]에 100% 빙의하여 답변하십시오.

[학습자 프로필]
{learner_profile if learner_profile else "일반적인 성인 학습자"}

1. 어조 강제: 명시된 '원하는 어조'를 철저하게 유지하십시오.
2. 비유 강제: 이해를 돕기 위해 반드시 프로필의 '주요 관심사'에 빗대어 찰떡같은 비유를 하나 들어주세요.
3. 눈높이 강제: '학습 목표'와 '연령대/직업'에 맞추어 어휘를 선택하십시오.
</PERSONA_DIRECTIVE>

지시사항:
1. 전체 문맥을 요약하지 마세요. 사용자의 질문은 오직 **[사용자가 선택한 텍스트]**에 관한 것입니다.
2. 선택된 단어/문장의 정의, 역할, 이유 등을 전체 문맥에 비추어 정확하게 설명하세요.
3. **(중요)** "안녕하세요", "좋은 질문입니다" 같은 인사말이나 불필요한 서론을 절대 쓰지 마세요. 곧바로 답변(본론)부터 시작하세요.
```

---

### 4.7 배경 이미지 키워드 추출 & 오디오 전사 프롬프트

- **Unsplash 키워드 추출 (`extract_image_keyword`)**:
    
    ```
    You are an expert image researcher. Analyze the following video title and output EXACTLY ONE OR TWO English keywords that best represent its visual theme.
    These keywords will be used to search Unsplash for a high-quality background photo.
    Do not output anything else, no explanations, no quotes. Just the keywords in English.
    
    Video Title: "{title}"
    ```
    
- **Gemini 오디오 전사 STT (`process_audio`)**:
    
    ```
    Please provide a complete and highly accurate transcription of this audio in its original language. Do not summarize, format, or skip any parts. Return ONLY the transcribed text.
    ```
    

---

## 5. 장애 대응 및 비상 안전망(Fail-Safe) 아키텍처

| 위험 요소 | 발생 상황 | 극복 및 대응 안전망 매커니즘 |
| --- | --- | --- |
| **유튜브 봇 감지 (429/Sign-in)** | AWS EC2 등 클라우드 IP에서 자막 및 오디오 다운로드 차단 | 1) `oEmbed API`로 원제 100% 사수
2) `Innertube` 모바일 다중 클라이언트 호출
3) `Jina Reader` 웹 스크랩 우회 + 잡음 정규식 필터링 |
| **타이틀 할루시네이션** | 디폴트 제목으로 인해 수험생 공부법으로 오인 생성 | `translate_title`에 공부법 어그로 문구 생성 금지 Negative Constraints 적용, 원본 스크립트 인물/주제 강제 주입 |
| **목차 안전망 맹탕 제목** | 모든 AI 호출 실패 시 목차 안전망 가동 | `clean_topic`을 원본 비디오 제목에서 동적으로 추출하여 `"도입: [주제]의 본질과 핵심 배경"` 등 명사형 문장으로 조립 |
| **비상 안전망 IT 편향** | AI 챕터 생성 타임아웃/실패 시 비상 챕터 합성 | 하드코딩 개발 용어(아키텍처, 비동기 큐 등) 완전 배제, 보편적 지적 탐구 템플릿과 10자 이상 한글 문장 가드레일 적용 |
| **영문 날것 본문 노출** | 자막 차단 시 영문 웹 UI 에러 메시지가 본문에 삽입 | 영문 에러 정규식 필터 탑재 + 한글 150자 미만 시 자동 탈락 및 재시도 에스컬레이션 |
| **OpenRouter 404 장애** | `:free` 모델 호출 시 외부 `custom_base_url` 간섭 발생 | `:free` 또는 OpenRouter 키 감지 시 Base URL을 `https://openrouter.ai/api/v1`으로 강제 격리 |
| **디스크 캐시 오염** | 과거 버그로 손상된 챕터/목차가 디스크에 영구 잔류 | FastAPI 서버 시작(`backend/main.py`) 시 백그라운드 자동 살균기(`_bg_cache_cleanup`)가 오염된 캐시 자동 삭제 |

---

## 6. 유지보수 및 운영 배포 가이드

### 6.1 로컬 문법 및 빌드 검증

```bash
# 프론트엔드 빌드 검증
cd frontend && npm run build

# 백엔드 핵심 파이프라인 문법 검증
python -m py_compile backend/services/tasks.py backend/services/llm/outline.py backend/services/llm/chapter.py backend/services/llm/profiling.py
```

### 6.2 AWS EC2 운영 서버 무중단 배포

```bash
# 1. EC2 접속 및 최신 main 브랜치 동기화
ssh -i "aws/studyguide-key.pem" -o StrictHostKeyChecking=no ubuntu@13.209.73.143 "cd /home/ubuntu/Interactive-Video-Study-Guide-System && git pull origin main"

# 2. Celery 워커 및 FastAPI 도커 컨테이너 리빌드 및 재기동
ssh -i "aws/studyguide-key.pem" -o StrictHostKeyChecking=no ubuntu@13.209.73.143 "cd /home/ubuntu/Interactive-Video-Study-Guide-System && docker compose build celery_worker fastapi && docker compose up -d celery_worker fastapi"

# 3. 실시간 워커 로그 확인
ssh -i "aws/studyguide-key.pem" -o StrictHostKeyChecking=no ubuntu@13.209.73.143 "docker logs --tail 100 studyguide-celery"
```