# LLM Wiki (AI Context Index)
<!-- [KR] AI 컨텍스트 인덱스 (토큰 최적화 위키) -->

> [!IMPORTANT]
> This file is a strictly compressed index for AI Agents (Antigravity). Do NOT duplicate detailed documentation here. Use this file to locate the exact path of the required knowledge and read it only when necessary using `view_file` to save context tokens.
> <!-- [KR] 이 파일은 AI 에이전트를 위한 초압축 인덱스입니다. 이곳에 상세 문서를 중복 작성하지 마세요. 컨텍스트 토큰을 절약하기 위해 이 파일에서 필요한 지식의 정확한 경로를 찾고, 필요할 때만 `view_file`로 읽으세요. -->

## 1. System Architecture & UI/UX
<!-- [KR] 1. 시스템 아키텍처 및 UI/UX -->
- **Core Architecture & Tech Stack**: Includes details on Next.js 16+, FastAPI, TailwindCSS pastel glass aesthetic, and Cloudflare tunneling.
  <!-- [KR] 핵심 아키텍처 및 기술 스택: Next.js 16+, FastAPI, 파스텔 글래스 미학, 터널링 설정 등 -->
* **Architecture & Philosophy**: [DESIGN.md](file:///i:/Interactive%20Video%20Study%20Guide%20System/DESIGN.md) (Look here for UI/UX strategy, backend tech stack, and BYOK v1.0 deployment model).
* **Terminology & Variables**: [GLOSSARY.md](file:///i:/Interactive%20Video%20Study%20Guide%20System/GLOSSARY.md) (Look here for UI terms vs Code variable mapping, e.g., '가이드북' -> `guide`).

## 2. Core Generation Pipeline
<!-- [KR] 2. 핵심 생성 파이프라인 -->
- **Video to Text Logic (6 Steps)**: Explains the exact flow from Youtube URL -> Whisper/Jina -> MapReduce -> Persona Injection -> Checkpointing.
  <!-- [KR] 비디오 -> 텍스트 로직 (6단계): URL 입력부터 속성 분석, 페르소나 주입, 체크포인팅까지의 전체 흐름 -->
  - 👉 [PIPELINE_DETAILS.md](file:///C:/Users/radia/.gemini/antigravity/brain/264415c3-6b4e-4d37-b860-4582a8dc633e/PIPELINE_DETAILS.md)

## 3. Strict AI Rules & Behaviors
<!-- [KR] 3. 엄격한 AI 규칙 및 행동 지침 -->
- **Mandatory User Rules**: Contains critical rules like Vibe Coding Architect mode, Latest Info forcing (2026), Next.js tunneling fixes, and Powershell encoding. **ALWAYS active in context.**
  <!-- [KR] 필수 사용자 규칙: Vibe Coding 수석 아키텍트 모드, 최신 정보(2026) 강제, Next.js 터널링 픽스 등. 시스템 컨텍스트에 항상 주입됨. -->
  - 👉 [.agents/AGENTS.md](file:///i:/Interactive%20Video%20Study%20Guide%20System/.agents/AGENTS.md)

## 4. User Operations & Backlog
<!-- [KR] 4. 사용자 운영 및 백로그 -->
- **Bug Reporting Pipeline**: Standardized format for user bug reports using `[요청]` instead of `[기대]`.
  <!-- [KR] 버그 리포팅 파이프라인: `[기대]` 대신 `[요청]`을 사용하는 규격화된 제보 포맷 -->
  - 👉 [issue_reporting_pipeline.md](file:///C:/Users/radia/.gemini/antigravity/brain/264415c3-6b4e-4d37-b860-4582a8dc633e/issue_reporting_pipeline.md)
- **Feature Ideas & Backlog**: Holds upcoming ideas like the "Automatic Prerequisite Concept Map".
  <!-- [KR] 기능 아이디어 및 백로그: '자동 선수학습 개념도' 같은 향후 개발 예정 아이디어 보관소 -->
  - 👉 [IDEAS.md](file:///i:/Interactive%20Video%20Study%20Guide%20System/IDEAS.md)

---
*Tip for AI: When updating a subsystem, read ONLY the linked file relevant to your task.*
<!-- [KR] AI 팁: 서브시스템을 업데이트할 때, 전체를 읽지 말고 관련된 파일 하나만 읽으세요. -->
