# Rule: Terminology Sync in Notion
<!-- [KR] 용어 정의서 동기화 규칙 -->

When modifying, removing, or adding a new terminology in this project, you must not only update the code or UI but also **always update the following Notion "Terminology Definition" page**.
<!-- [KR] 이 프로젝트에서 용어를 변경, 삭제, 또는 새로 추가할 경우에는, 코드나 UI만 수정하는 것에 그치지 않고 항상 다음 Notion "용어 정의서" 페이지에 접속하여 해당 내용을 업데이트해야 합니다. -->

- **Notion URL**: https://app.notion.com/p/UI-UX-UI-3b3a8db03fbe8101905fc2a2619edd43?source=copy_link
- **Notion Page ID**: `3b3a8db03fbe8101905fc2a2619edd43`
- **Tool to Use**: `notion-mcp-server` APIs (e.g., `API-retrieve-page-markdown`, `API-update-page-markdown`)
  <!-- [KR] 사용 도구: notion-mcp-server의 API -->

## When does this rule apply?
<!-- [KR] 언제 이 규칙이 적용되나요? -->
- When the user requests a change to UI text, feature names, database column names, or specific concepts/terms in business logic.
  <!-- [KR] 사용자가 UI 텍스트, 기능명, 데이터베이스 컬럼명, 또는 비즈니스 로직 상의 특정 개념이나 용어를 변경해달라고 요청할 때. -->
- When a new domain concept/term is added.
  <!-- [KR] 새로운 도메인 개념/용어가 추가될 때. -->
- When discarding or replacing an existing terminology.
  <!-- [KR] 기존 용어를 폐기하거나 다른 용어로 대체할 때. -->

## Action Guidelines
<!-- [KR] 행동 지침 -->
Whenever a terminology-related change occurs, immediately use the Notion MCP server to read the markdown of the Notion page, reflect the modified/added/removed items, and update (Patch/Update) the page.
<!-- [KR] 용어에 관련된 수정 작업이 발생하면, 즉시 Notion MCP 서버를 활용해 Notion 페이지의 마크다운을 읽어오고, 변경/추가/삭제된 사항을 반영한 뒤 페이지를 업데이트(Patch/Update)하십시오. -->
