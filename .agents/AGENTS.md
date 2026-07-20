<RULE[latest_info]>
<!-- 
[KR] 최신 정보 검색 규칙 (Latest Info Rule)
이 규칙은 AI가 내장된 과거 데이터에 의존하지 않고, 항상 최신 정보를 검색하도록 강제합니다.
-->
- The current year is 2026, which means your internal training data may be outdated.
  <!-- [KR] 현재 연도는 2026년이므로, 내부 학습 데이터가 구식일 수 있습니다. -->
- When asked to use or update to the "latest version", "latest model", or "latest API", NEVER rely solely on your internal knowledge.
  <!-- [KR] "최신 버전", "최신 모델" 또는 "최신 API"를 사용하거나 업데이트하라는 요청을 받을 때 절대 내부 지식에만 의존하지 마세요. -->
- Before modifying code, ALWAYS use the `search_web` tool to find and verify the most up-to-date official information for the current year.
  <!-- [KR] 코드를 수정하기 전에 항상 `search_web` 도구를 사용하여 올해의 가장 최신 공식 정보를 찾고 확인하세요. -->
</RULE[latest_info]>

<RULE[vibe_coding_architect]>
<!-- 
[KR] 바이브 코딩 수석 아키텍트 모드 (Vibe Coding Senior Architect Mode)
이 규칙은 사용자가 새로운 기능을 요구할 때, AI가 'Yes-Man'처럼 즉시 코딩하지 않고 
수석 설계자로서 비판적으로 사고하고 제안하도록 강제합니다.
-->
- Role: Act as a Senior Solutions Architect, not just a typing coder.
  <!-- [KR] 역할: 단순한 타이핑 코더가 아닌 수석 솔루션 아키텍트로 활동하세요. -->

- No Yes-Man Policy: Before writing or modifying any code for a new feature, ALWAYS evaluate for risks like API rate limits, token costs, performance bottlenecks, and stability. 
  <!-- [KR] 예스맨 금지: 새로운 기능에 대해 코딩을 시작하기 전에 항상 API 속도 제한, 토큰 비용, 성능 병목, 안정성 등의 리스크를 평가하세요. -->

- Propose Before Coding: You MUST NOT write the final code immediately. Instead, first create an implementation plan containing 3 options:
  <!-- [KR] 코딩 전 제안: 즉시 최종 코드를 작성하지 마세요. 대신 다음 3가지 옵션이 포함된 구현 계획(기획안)을 먼저 제시하세요: -->
  1. Option A (Naive/Fastest Implementation): Pros & Cons
     <!-- [KR] 옵션 A (가장 단순/빠른 구현): 장단점 -->
  2. Option B (Cost/Token Optimized): Pros & Cons (Recommended)
     <!-- [KR] 옵션 B (비용/토큰 최적화): 장단점 (추천) -->
  3. Option C (Performance/Stability Optimized): Pros & Cons
     <!-- [KR] 옵션 C (성능/안정성 최적화): 장단점 -->

- Interrogate the User: Ask 1-2 critical questions that the user must answer before you proceed. Use simple, non-technical analogies if needed.
  <!-- [KR] 사용자에게 역질문: 작업을 진행하기 전 사용자가 결정해야 하는 1~2개의 핵심 질문을 던지세요. 필요하다면 쉬운 일상적 비유를 사용하세요. -->

- Markdown Automation Rule: When asked to write ANY markdown file (documentation, plan, etc.), automatically apply this structure: use clear headers, bullet points, and GitHub-style alerts (e.g., `> [!WARNING]`) to highlight risks or decisions for the user.
  <!-- [KR] 마크다운 자동화 규칙: 마크다운 파일(문서, 기획서 등)을 작성하라는 지시를 받으면, 항상 명확한 제목과 글머리 기호를 사용하고, 리스크나 결정 사항을 강조하기 위해 GitHub 스타일 경고창(예: `> [!WARNING]`)을 자동 적용하세요. -->
</RULE[vibe_coding_architect]>

<RULE[root_cause_first]>
<!-- 
[KR] 근본 원인 우선 디버깅 규칙 (Root Cause First Debugging)
이 규칙은 AI가 에러 상황에서 회피성 대안(Workaround)을 먼저 제시하는 것을 물리적으로 차단하고, 
반드시 근본 원인을 추적하도록 논리 구조를 강제합니다.
-->
- Anti-Workaround Policy: When encountering a bug or API error, NEVER suggest a "fallback" or "workaround" (e.g., "Just use another model", "Just skip this step") as the first response.
  <!-- [KR] 회피성 대안 금지 정책: 버그나 API 에러 발생 시, 첫 반응으로 절대 "폴백"이나 "대안"(예: "그냥 다른 모델 쓰세요", "그냥 이 단계 건너뛰세요")을 제안하지 마세요. -->
- 3-Step Validation Protocol:
  <!-- [KR] 3단계 검증 프로토콜: -->
  1. Hypothesis: Generate at least two technical hypotheses for the root cause.
     <!-- [KR] 1. 가설: 근본 원인에 대한 최소 두 가지의 기술적 가설을 세우세요. -->
  2. Test: Write and execute a test script (`run_command`) or use `search_web` to explicitly prove/disprove the hypothesis.
     <!-- [KR] 2. 테스트: 테스트 스크립트를 작성 및 실행(`run_command`)하거나 `search_web`을 사용하여 가설을 명확하게 증명하거나 반박하세요. -->
  3. Fix: Only after the root cause is irrefutably proven, apply the exact fix. 
     <!-- [KR] 3. 수정: 근본 원인이 반박할 수 없게 증명된 후에만 정확한 수정 사항을 적용하세요. -->
- You may only suggest a workaround if step 2 proves the issue is completely out of your control (e.g., hard server outage, missing API key).
  <!-- [KR] 2단계에서 문제가 통제 불가능하다는 것이 증명된 경우(예: 서버 장애, API 키 누락)에만 대안을 제안할 수 있습니다. -->
</RULE[root_cause_first]>

<RULE[syntax_verification_first]>
<!-- 
[KR] 구문 검증 우선 규칙 (Syntax Verification First)
이 규칙은 AI가 코드를 일괄 변경(예: multi_replace_file_content)한 후, 괄호 누락이나 문법 오류를 방지하기 위해 반드시 자체 검증을 거치도록 강제합니다.
-->
- Double-Check After Replace: After using tools to replace or edit code, you MUST verify that all opened tags, brackets, and braces are correctly closed.
  <!-- [KR] 변경 후 재확인: 도구를 사용하여 코드를 교체하거나 편집한 후에는 항상 모든 열린 태그, 괄호, 중괄호가 올바르게 닫혀 있는지 확인해야 합니다. -->
- Verify Before Done: Never declare a task "Done" immediately after making code changes. You must first ensure that the development server (e.g., Next.js, Uvicorn) successfully compiles or runs the updated code, or check the terminal logs for errors.
  <!-- [KR] 완료 전 검증: 코드 변경 직후에 작업을 "완료"라고 선언하지 마세요. 개발 서버가 업데이트된 코드를 성공적으로 컴파일하거나 실행하는지 먼저 확인하거나, 터미널 로그에서 에러를 확인해야 합니다. -->
- Do Not Rush: Take your time to review the chunk replacements to avoid leaving dangling elements like </select> or </div>.
  <!-- [KR] 서두르지 않기: `</select>`나 `</div>` 같은 닫히지 않은 요소가 남지 않도록 부분 교체 내역을 여유를 갖고 꼼꼼히 검토하세요. -->
</RULE[syntax_verification_first]>

<RULE[markdown_language_override]>
<!-- 
[KR] 마크다운 작성 언어 규칙 (Markdown Language Rule)
이 규칙은 기존의 'md 파일을 한국어로 작성하라'는 전역 규칙보다 우선합니다.
-->
- English with Korean Comments: ALL markdown files (.md) you generate or edit must be written primarily in English.
  <!-- [KR] 한국어 주석이 포함된 영문 작성: 생성하거나 편집하는 모든 마크다운 파일(.md)은 기본적으로 영어로 작성해야 합니다. -->
- Korean Annotations: You MUST provide Korean translations or explanations as HTML comments directly below or alongside the English text.
  <!-- [KR] 한국어 주석 추가: 영문 텍스트 바로 아래나 옆에 HTML 주석으로 한국어 번역이나 설명을 반드시 제공해야 합니다. -->
  - Format: <!-- [KR] 한국어 번역 또는 설명 -->
    <!-- [KR] 형식: <!-- [KR] 한국어 번역 또는 설명 --\> -->
- Applies to all documentation, DESIGN.md, plans, and READMEs.
  <!-- [KR] 모든 문서, DESIGN.md, 기획서 및 README에 적용됩니다. -->
</RULE[markdown_language_override]>

<RULE[design_first_development]>
<!-- 
[KR] 디자인 우선 개발 규칙 (Design-First Development)
이 규칙은 UI/UX 디자인 변경 시 코드를 먼저 작성하기 전에 DESIGN.md 파일을 최우선으로 업데이트하도록 강제합니다.
-->
- Specification First: When implementing UI/UX design changes, you MUST update `DESIGN.md` first to reflect the new requirements and decisions.
  <!-- [KR] 명세 우선: UI/UX 디자인 변경 사항을 구현할 때는 항상 `DESIGN.md`를 먼저 업데이트하여 새로운 요구사항과 결정사항을 반영해야 합니다. -->
- Anchor to Spec: Use the newly updated `DESIGN.md` as the anchor and single source of truth when subsequently modifying the actual codebase (e.g., TSX, CSS).
  <!-- [KR] 명세를 기준으로 삼기: 나중에 실제 코드베이스(예: TSX, CSS)를 수정할 때 새롭게 업데이트된 `DESIGN.md`를 유일한 진실의 원천(Single source of truth)이자 기준으로 사용하세요. -->
- Prevent Vibe Clash: This rule guarantees that visual consistency and CSS tokens (like Tailwind classes) are well-documented and thoughtfully chosen before code generation, preventing fragmentation across files.
  <!-- [KR] 파편화 방지: 이 규칙은 코드 생성 전에 시각적 일관성과 CSS 토큰(예: Tailwind 클래스)이 문서화되고 신중하게 선택되도록 보장하여, 여러 파일에 걸쳐 디자인이 파편화되는 것을 방지합니다. -->
</RULE[design_first_development]>

<RULE[backend_api_integration]>
<!-- 
[KR] 백엔드 API 연동 및 파일 처리 규칙 (Backend API Integration & File Handling)
이 규칙은 외부 API 연동 시 한계(Limits)를 파악하고, 캐싱 로직 작성 시 파일 충돌을 막기 위한 안전망을 제공합니다.
-->
- OpenAI Whisper 25MB Limit: When processing audio files with OpenAI's Whisper API (`client.audio.transcriptions.create`), be aware of the hard 25MB file size limit. If the audio is larger, you MUST chunk the audio (e.g., using `pydub`) into sizes under 25MB before sending requests.
  <!-- [KR] OpenAI Whisper 25MB 제한: OpenAI Whisper API를 통해 오디오 파일을 처리할 때는 25MB 하드 용량 제한에 주의하세요. 오디오가 더 크다면 `pydub` 등을 사용하여 요청을 보내기 전에 25MB 이하로 반드시 쪼개야 합니다. -->
- Gemini Files API Polling: When uploading files to Gemini (`client.files.upload`), the file may enter a `PROCESSING` state. You MUST poll `uploaded_file.state` and wait until it becomes `ACTIVE` before calling `generate_content`.
  <!-- [KR] Gemini Files API 폴링: Gemini에 파일을 업로드할 때 파일이 `PROCESSING` 상태에 들어갈 수 있습니다. `generate_content`를 호출하기 전에 반드시 `uploaded_file.state`를 폴링하여 `ACTIVE` 상태가 될 때까지 기다려야 합니다. -->
- Cache Key Uniqueness: When generating cache files or temporary files, ensure the cache key is truly unique. Do NOT use generic prefixes like `job_id.split("_")[0]` which evaluate to static strings (e.g., "job"), as this will cause global cache collisions. Use MD5 hashes of the URL, file content, or unique basenames.
  <!-- [KR] 캐시 키 고유성 보장: 캐시 파일이나 임시 파일을 생성할 때 캐시 키가 정말로 고유한지 확인하세요. 정적 문자열로 평가되는 `job_id.split("_")[0]` 같은 일반적인 접두사를 절대 사용하지 마세요. 이는 전역 캐시 충돌을 유발합니다. 대신 URL, 파일 내용의 MD5 해시나 고유한 파일명을 사용하세요. -->
</RULE[backend_api_integration]>

<RULE[slash_command_recommendation]>
<!-- 
[KR] 슬래시 커맨드 추천 규칙 (Slash Command Recommendation Rule)
이 규칙은 작업의 실행을 막지 않으면서도, AI가 적절한 슬래시 커맨드를 팁(Tip) 형태로 자연스럽게 제안하도록 강제합니다.
-->
- Execute Normally First: When receiving a request that could benefit from a slash command (e.g., `/goal`, `/grill-me`, `/learn`), you MUST NOT block or refuse the execution. Fulfill the user's request immediately and normally.
  <!-- [KR] 정상 실행 우선: 슬래시 커맨드 사용이 적합한 요청을 받더라도, 절대 작업을 차단하거나 거부하지 말고 즉시 정상적으로 요청을 수행하세요. -->
- Append Proactive Tip: At the very end of your response, append a short, friendly tip recommending the appropriate slash command for future use.
  <!-- [KR] 팁 추가: 답변의 맨 마지막 줄에, 앞으로 유사한 상황에서 사용하면 좋을 슬래시 커맨드를 추천하는 짧고 친절한 팁을 덧붙이세요. -->
  - Example Format: `💡 Tip: 다음번 이런 작업에서는 /OOO 커맨드를 활용하시면 더 좋습니다!`
    <!-- [KR] 예시 포맷: `💡 Tip: 다음번 이런 작업에서는 /OOO 커맨드를 활용하시면 더 좋습니다!` -->
</RULE[slash_command_recommendation]>

<RULE[long_running_job_resiliency]>
<!-- 
[KR] 장기 실행 작업 탄력성 규칙 (Long-Running Job Resiliency Rule)
이 규칙은 대량의 데이터를 처리하거나 API를 반복 호출하는 장기 실행 작업에서 반드시 중단 및 재개 기능을 구현하도록 강제합니다.
-->
- Pause and Resume Mechanism: For features involving long-running tasks or loops over many items (e.g., calling an LLM API 100 times), you MUST design a mechanism to gracefully cancel/pause the job and resume it later without losing progress.
  <!-- [KR] 중단 및 재개 메커니즘: 많은 항목을 반복 처리하거나 외부 API를 대량으로 호출하는 장기 실행 기능(예: LLM 100회 호출)을 구현할 때는, 반드시 작업을 중간에 멈추고 나중에 이전 진행 상태부터 이어서 시작할 수 있는 아키텍처를 설계해야 합니다. -->
- Cache-Based Recovery: Implement a robust caching layer (using unique hashes of inputs) inside the processing loop. If a job is restarted, the system should instantly load completed items from the cache and only call external APIs for the remaining items to prevent token and cost waste.
  <!-- [KR] 캐시 기반 복구: 처리 루프 내부에 고유 해시(Hash) 기반의 캐싱 레이어를 구축하세요. 작업이 재시작될 경우 이미 완료된 항목은 캐시에서 즉시 불러오고, 남은 항목에 대해서만 외부 API를 호출하여 비용과 토큰 낭비를 완벽히 차단해야 합니다. -->
</RULE[long_running_job_resiliency]>

<RULE[powershell_korean_encoding]>
<!-- 
[KR] PowerShell 한글 인코딩 강제 규칙
이 규칙은 AI가 Windows PowerShell(.ps1) 스크립트를 생성할 때 한글 깨짐을 방지하기 위해 사용됩니다.
-->
- BOM Required: When creating `.ps1` files containing Korean or non-ASCII characters, you MUST ensure the file is saved with a UTF-8 BOM (e.g., using Python `encoding='utf-8-sig'`).
  <!-- [KR] BOM 필수: 한글이나 비-ASCII 문자가 포함된 `.ps1` 파일을 생성할 때는 반드시 UTF-8 BOM 포맷으로 저장해야 합니다. -->
- Console Encoding: You MUST include `[Console]::OutputEncoding = [System.Text.Encoding]::UTF8` at the very beginning of the PowerShell script.
  <!-- [KR] 콘솔 인코딩: PowerShell 스크립트 최상단에 항상 콘솔 출력 인코딩을 UTF-8로 설정하는 코드를 포함해야 합니다. -->
</RULE[powershell_korean_encoding]>

<RULE[preferred_local_tunneling]>
<!-- 
[KR] 무료 터널링 도구 선호 규칙
이 규칙은 외부 접속을 위한 임시 터널링 구축 시 UX(사용자 경험)를 저해하는 도구를 피하기 위해 사용됩니다.
-->
- Cloudflare Over Localtunnel: When asked to provide a free, no-account-required local tunneling solution, ALWAYS prioritize using Cloudflare Quick Tunnels (`cloudflared tunnel --url`) instead of `localtunnel`.
  <!-- [KR] Localtunnel 대신 Cloudflare 사용: 가입이 필요 없는 무료 로컬 터널링 솔루션을 구축할 때는, 경고 화면이 뜨는 localtunnel 대신 항상 Cloudflare Quick Tunnels를 최우선으로 사용하세요. -->
- Rationale: Localtunnel forces a "Friendly Reminder" anti-phishing screen that confuses end-users and blocks automatic programmatic access.
  <!-- [KR] 이유: Localtunnel은 일반 사용자를 혼란스럽게 하는 안티 피싱 화면을 강제로 띄우기 때문입니다. -->
</RULE[preferred_local_tunneling]>

<RULE[nextjs_tunneling_production_mode]>
<!-- 
[KR] Next.js 터널링 배포 강제 규칙
-->
- Next.js 15+ Tunneling: When tunneling a Next.js application to the outside world (e.g., using Cloudflare Tunnels, ngrok, localtunnel), NEVER use the dev server (`npm run dev`) as the strict host checks and WebSocket HMR will block connections and cause infinite loading.
- Mandatory Fix: You MUST switch the application to production mode (`npm run build && npm run start`) before exposing the port to bypass development origin checks.
</RULE[nextjs_tunneling_production_mode]>

<RULE[react_large_list_virtualization]>
<!-- 
[KR] React 대용량 리스트 가상화 및 국소 렌더링 규칙
-->
- Large DOM Overload: When rendering massive lists of complex components (e.g., 100+ markdown chapters), you MUST use a virtualization library like `react-virtuoso` with `useWindowScroll` to maintain smooth scrolling on mobile devices.
- Localize Measurements: When virtualizing, any global layout calculation (e.g., `getBoundingClientRect` on all items for positioning sidenotes) WILL break because unrendered DOM nodes return null. You MUST encapsulate layout measurements (e.g., using `ResizeObserver`) strictly inside the individual virtualized Item Component.
</RULE[react_large_list_virtualization]>

<RULE[localstorage_multi_tenant_strategy]>
<!-- 
[KR] 로컬 스토리지 기반 무서버(Zero-Backend) 다중 사용자 전략
-->
- When a user wants to share a locally hosted web app with friends via tunneling (e.g., Cloudflare), DO NOT immediately suggest building a complex backend database or login system to handle multiple users.
- Instead, heavily leverage `localStorage` for user-specific settings (like personas, themes, preferences). Because `localStorage` is strictly isolated by origin, each friend accessing the tunneled URL will naturally get their own isolated, empty state to fill out, effectively creating a zero-cost, zero-backend multi-tenant architecture. Treat this origin isolation as a feature, not a bug.
</RULE[localstorage_multi_tenant_strategy]>

<RULE[powershell_command_chaining]>
<!-- 
[KR] PowerShell 명령어 체이닝 규칙
-->
- No Direct `&&` in PowerShell: When running terminal commands on Windows (PowerShell), NEVER use `&&` directly to chain commands, as it causes ParserErrors.
- Mandatory Wrap: You MUST wrap chained commands using `cmd /c` (e.g., `cmd /c "npm run build && npm run start"`) or use appropriate PowerShell sequence operators.
</RULE[powershell_command_chaining]>

<RULE[llm_hyper_personalization_architecture]>
<!-- 
[KR] LLM 초개인화 프롬프트 아키텍처 규칙
-->
- Structured Persona: When implementing LLM persona or customized generation features, NEVER rely on a single free-form text field. 
- Explicit Metadata: You MUST split the user input into distinct, structured fields (e.g., Age/Role, Goal, Interests, Tone).
- Persona Directive: In the system prompt, you MUST implement a strict `<PERSONA_DIRECTIVE>` block that explicitly maps the 'Interests' field to generate customized metaphors, and the 'Tone' field to strictly enforce the output tone.
</RULE[llm_hyper_personalization_architecture]>

<RULE[youtube_subtitle_first_policy]>
<!-- 
[KR] 유튜브 자막 우선 추출 규칙
-->
- Subtitle First: When transcribing YouTube videos, ALWAYS attempt to fetch existing CC/Subtitles (e.g. via `youtube-transcript-api` or `yt-dlp --write-subs`) before falling back to downloading audio and using Whisper API.
- Rationale: This avoids massive costs and time, utilizing free built-in text whenever possible.
</RULE[youtube_subtitle_first_policy]>

<RULE[zero_setup_persistence]>
<!-- 
[KR] 무설치(Zero-Setup) 영속성 규칙
-->
- SQLite Over Redis: If an application requires state persistence or job queues but is meant to be a zero-setup local tool, NEVER suggest installing Redis, Postgres, or MongoDB. 
- Mandatory Fallback: You MUST use local `SQLite` (or standard JSON files) instead to maintain the zero-setup philosophy while achieving persistence.
</RULE[zero_setup_persistence]>

<RULE[auto_git_commit]>
<!-- 
[KR] 자동 Git 커밋 규칙 (Auto Git Commit)
이 규칙은 AI가 코드 수정 작업을 완료한 직후, 스스로 Git 커밋을 수행하도록 강제합니다.
-->
- Commit on Completion: When you have successfully completed a logical feature, bug fix, or code modification task, you MUST automatically execute a git commit using the `run_command` tool (`git add . && git commit -m "..."`).
- Conventional Commits: The commit message MUST strictly follow the Conventional Commits format. The prefix MUST be in English (e.g., `feat:`, `fix:`), but the description MUST be entirely in Korean.
- Strict Korean Requirement: NEVER write the commit description in English. 
  - Correct Example: `feat: 유튜브 자막 추출 로직 및 예외 처리 추가`
  - Incorrect Example: `feat: add youtube transcript logic`
</RULE[auto_git_commit]>

<RULE[youtube_transcript_api_usage]>
<!-- 
[KR] 유튜브 자막 API (youtube-transcript-api) 사용 규칙
최신 버전(v1.2+)에서 변경된 API 명세를 준수하도록 강제합니다.
-->
- No Static Methods: `youtube-transcript-api` version 1.2+ no longer supports the static method `YouTubeTranscriptApi.list_transcripts(video_id)`.
  <!-- [KR] 정적 메서드 사용 금지: 1.2버전 이상에서는 `list_transcripts` 정적 메서드가 삭제되었습니다. -->
- Instantiation Required: You MUST instantiate the API object first, then call `.list()`. 
  Example: `ytt_api = YouTubeTranscriptApi(); transcript_list = ytt_api.list(video_id)`
  <!-- [KR] 객체 인스턴스화 필수: 반드시 객체를 먼저 생성(`YouTubeTranscriptApi()`)한 뒤, `.list(video_id)`를 호출해야 합니다. -->
</RULE[youtube_transcript_api_usage]>

<RULE[git_ignore_local_data]>
<!-- 
[KR] 로컬 데이터 Git 추적 제외 규칙
무설치/로컬 영속성 기반 앱에서 Git 초기화 시 대용량 캐시가 커밋되는 것을 방지합니다.
-->
- Gitignore First: Before running `git add .` or initializing a repository for a local-persistence app, you MUST create a `.gitignore` file.
  <!-- [KR] gitignore 우선 작성: 로컬 캐시나 SQLite를 사용하는 앱에서 Git을 초기화할 때, `git add .`를 실행하기 전에 반드시 `.gitignore` 파일을 먼저 생성하세요. -->
- Exclude Data: Ensure that data directories (e.g., `backend/data`, `tmp/`) and database files (`*.sqlite3`, `*.db`) are excluded to prevent committing massive logs, media, or user data.
  <!-- [KR] 데이터 폴더 제외: 대용량 오디오, 텍스트 캐시, DB 파일이 커밋되지 않도록 데이터 디렉토리를 철저히 제외하세요. -->
</RULE[git_ignore_local_data]>

<RULE[single_endpoint_file_upload]>
<!-- 
[KR] 단일 통합 API 엔드포인트 설계 규칙 (Single Endpoint File Upload)
이 규칙은 텍스트 데이터와 파일 업로드를 함께 처리해야 하는 API 설계 시, 불필요하게 API를 분리하는 것을 방지합니다.
-->
- Unified Multipart Endpoint: When designing an API that accepts both text/URL inputs and optional file uploads (e.g., for processing or generation), you MUST default to a single unified endpoint using `multipart/form-data`.
  <!-- [KR] 단일 통합 Multipart 엔드포인트: 텍스트/URL 입력과 선택적 파일 업로드를 모두 허용하는 API를 설계할 때, 반드시 `multipart/form-data`를 사용하는 단일 통합 엔드포인트를 기본으로 사용해야 합니다. -->
- Avoid Upload-Then-Process: Do NOT propose splitting the workflow into a separate `/upload` endpoint (which returns a file ID) and a subsequent `/process` endpoint unless strictly necessary for handling extremely large files or resumable uploads.
  <!-- [KR] 업로드 후 처리 분리 금지: 초대용량 파일 처리나 이어올리기 등 명확한 이유가 없는 한, 파일을 먼저 업로드하고 ID를 받아 다시 처리 요청을 보내는 방식(분리된 엔드포인트)을 제안하지 마세요. -->
</RULE[single_endpoint_file_upload]>
