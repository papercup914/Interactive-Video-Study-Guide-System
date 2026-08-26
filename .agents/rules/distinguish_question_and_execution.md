# Rule: Distinguish Between Questions and Execution Commands
<!-- [KR] 규칙: 질문 의도와 실행 명령 구분 -->

## Context
<!-- [KR] 컨텍스트 -->
When the user asks questions ending in terms like "How about...?", "What do you think?", "Is it possible?", or "Is there a way?", they are often seeking an opinion, discussion, or feasibility check, rather than giving a direct command to execute the action immediately.
<!-- [KR] 사용자가 "어떨까?", "어떻게 생각해?", "가능할까?", "방법이 있을까?" 등으로 질문할 때는 즉각적인 실행을 지시하기보다 의견, 토론, 또는 실현 가능성 검토를 원하는 경우가 많습니다. -->

## Protocol
<!-- [KR] 행동 프로토콜 -->
1. **Analyze Intent**: Carefully distinguish whether the user's prompt is a direct instruction to build/execute something (e.g., "Apply this", "Make this") or a theoretical/exploratory question (e.g., "How about applying this?", "Should we make this?").
<!-- [KR] 1. 의도 파악: 사용자 요청이 직접적인 실행 지시("적용해 줘", "만들어 줘" 등)인지, 아니면 이론적/탐색적 질문("적용하면 어떨까?", "만드는 게 좋을까?" 등)인지 주의 깊게 구별하십시오. -->

2. **Do Not Auto-Execute**: If the user is asking for an opinion or feasibility (a question), **DO NOT execute the action** (e.g., do not create files, modify code, or make API calls) unless the change is completely trivial and reversible without side effects.
<!-- [KR] 2. 자동 실행 금지: 의견이나 실현 가능성을 묻는 질문일 경우, 작업 내용이 부작용 없이 완전히 사소하고 복구 가능한 수준이 아니라면 **절대 작업을 강제로 실행(파일 생성, 코드 수정, API 호출 등)하지 마십시오.** -->

3. **Propose and Wait**: Instead of executing, answer the question, propose a concrete plan or how you would approach it, and explicitly ask for the user's confirmation before proceeding with the execution. (e.g., "We can construct it this way. Shall I apply it now?")
<!-- [KR] 3. 제안 및 대기: 작업을 실행하는 대신 질문에 답변하고, 구체적인 계획이나 접근 방식을 제안한 뒤, 작업을 실행하기 전에 사용자에게 명시적으로 승인을 요청하십시오. (예: "이렇게 구성할 수 있습니다. 바로 적용해 드릴까요?") -->
