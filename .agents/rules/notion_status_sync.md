# Rule: Notion SSOT Status Board Sync
<!-- [KR] 규칙: Notion 프로젝트 현황(SSOT) 보드 동기화 -->

## Description
<!-- [KR] 설명 -->
This project uses a Single Source of Truth (SSOT) progress board in Notion. The AI must interact with it to maintain an up-to-date project status.
<!-- [KR] 이 프로젝트는 단일 진실 공급원(SSOT) 방식으로 Notion 진척도 보드를 사용합니다. AI는 항상 프로젝트 현황을 최신 상태로 유지하기 위해 보드와 상호작용해야 합니다. -->

## Target Page
<!-- [KR] 대상 페이지 -->
- **Page Name**: 📊 프로젝트 현황 보드 (STATUS)
  <!-- [KR] 페이지 이름 -->
- **Page ID**: `3b4a8db03fbe81478777da31c6f859eb`
  <!-- [KR] 페이지 ID -->

## Protocol
<!-- [KR] 행동 프로토콜 -->
1. **When starting a new conversation or significant task**:
<!-- [KR] 1. 새로운 대화나 중요한 작업을 시작할 때: -->
   - Always read the Status Board using `API-retrieve-page-markdown` on `3b4a8db03fbe81478777da31c6f859eb` to regain context of what was last done, current focus, and what is pending in the roadmap.
   <!-- [KR] 새 작업을 시작할 때는 항상 `API-retrieve-page-markdown`을 사용해 Status Board를 읽어들여, 최근 완료된 작업과 현재 포커스, 대기 중인 로드맵 맥락을 파악해야 합니다. -->

2. **When completing a significant milestone or at the end of the day**:
<!-- [KR] 2. 중요한 마일스톤을 달성하거나 하루 일과를 마칠 때: -->
   - Update the Status Board using `API-update-page-markdown` (with `replace_content`) to reflect the newly completed work in the "📅 Changelog / Completed" section.
   <!-- [KR] `API-update-page-markdown`(`replace_content` 모드)을 사용하여 "📅 Changelog / Completed" 섹션에 새롭게 완료한 내역을 반영하십시오. -->
   - Update or clear the "🚀 Current Focus" section.
   <!-- [KR] "🚀 Current Focus" 섹션을 업데이트하거나 비우십시오. -->
   - Move completed items out of "💡 Backlog / Roadmap" if they were listed there.
   <!-- [KR] 완료된 항목이 "💡 Backlog / Roadmap"에 기재되어 있었다면 목록에서 제거하십시오. -->

3. **Format**:
<!-- [KR] 3. 양식: -->
   - Always maintain the existing 4-section markdown structure (Current Focus, Changelog, Backlog, Known Issues).
   <!-- [KR] 기존의 4가지 섹션 마크다운 구조(Current Focus, Changelog, Backlog, Known Issues)를 항상 유지하십시오. -->
