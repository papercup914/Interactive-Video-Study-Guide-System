---
name: Project Governance & Safety Rules
description: Mandatory rules enforcing Approval-Gated Execution, Git manual verification, and QA review for all AI actions.
---

# Project Governance & Safety Rules

이 프로젝트(Interactive Video Study Guide System)의 리스크 관리를 위해, AI 에이전트는 아래의 거버넌스 및 안전 규칙을 예외 없이 **최우선**으로 준수해야 합니다.

## 1. 결재 기반 실행 강제화 (Approval-Gated Execution)
에이전트는 사용자의 명시적인 허가 없이 시스템의 상태를 변경하는 어떠한 도구(`write_to_file`, `replace_file_content`, `multi_replace_file_content`, `run_command`를 통한 패키지 설치 등)도 **즉시 실행해서는 안 됩니다.**

**[변경 작업 프로세스]**
1. 변경이 필요하다고 판단되면, 아래 양식에 맞추어 사용자에게 **'사전 보고'**를 먼저 텍스트로 출력합니다.
   - **이유 (Why):** 왜 이 파일/설정을 변경해야 하는가?
   - **대상 (Where):** 변경할 정확한 파일 경로 (예: `frontend/src/app/page.tsx`)
   - **내용 (What):** 어떤 코드를 추가/삭제/수정할 것인가? (Diff 요약)
2. 보고서 끝에 **"진행할까요?"**라고 물어봅니다.
3. 사용자가 "진행해", "승인(Proceed)", "OK" 등으로 명시적으로 허락한 이후에만 실제 쓰기 도구(Write Tool)를 호출합니다.
*(단, 단순 조회성 터미널 명령어, `view_file`, `grep_search` 등 읽기 전용 작업은 허가 없이 즉시 실행 가능합니다.)*

## 2. Git을 활용한 수동 검증 (Git Manual Verification)
에이전트는 코드를 수정할 권한은 가지지만, **절대 `git commit`이나 `git push` 등 코드를 영구적으로 반영하는 명령어를 스스로 실행해서는 안 됩니다.**

**[작업 후 리뷰 프로세스]**
1. 에이전트가 코드 수정을 완료하면, 사용자에게 작업 완료를 알리고 "VS Code 등의 Git 툴을 열어 변경 사항(Diff)을 확인해 주세요"라고 안내합니다.
2. 사용자가 Git Diff를 눈으로 직접 확인하고, 문제가 없다면 사용자가 **직접(수동으로)** Commit과 Merge를 수행합니다.
3. 만약 사용자가 수정을 요구하거나 코드를 되돌렸다면(Discard), 에이전트는 피드백을 받아 다시 '사전 보고' 단계부터 시작합니다.

## 3. QA 및 빌드 검증 (Automated & Visual QA)
- 코드 수정을 마친 후에는 반드시 스스로 `npm run lint`, `npm run build` 등을 백그라운드에서 돌려 에러가 없는지 체크합니다.
- UI/CSS가 변경된 경우, `browser` 서브 에이전트를 통해 `http://localhost:3000` 화면이 깨지지 않았는지 스스로 검증한 뒤 사용자에게 보고합니다.
