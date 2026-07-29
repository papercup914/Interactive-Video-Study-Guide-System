# UI Migration & Redesign Guidelines

이 문서는 새로운 UI 시안(HTML/Tailwind 등)을 기존 코드베이스에 이식할 때, **기존의 기능, 상태(State), 숨겨진 컴포넌트(모달, 툴팁 등)가 유실되지 않도록 보장하기 위한 체크리스트이자 가이드라인**입니다. AI 에이전트 및 개발자는 프론트엔드 시안 교체 작업을 수행하기 전에 반드시 이 문서의 절차를 따라야 합니다.

## ⚠️ 목적
외형적인 디자인만 교체하다가 기존에 바인딩되어 있던 데이터, 이벤트 핸들러(`onClick`, `onChange` 등), 그리고 `hidden` 또는 `opacity-0`으로 숨겨져 있던 툴팁/팝오버 등의 UI 요소가 삭제되는 치명적인 실수를 방지합니다.

---

## 📋 핵심 절차 (Core Workflow)

디자인을 변경하거나 컴포넌트를 교체할 때 **절대 코드를 즉시 덮어쓰지 마세요.** 다음 3단계를 반드시 거쳐야 합니다.

### 1단계: 기존 컴포넌트 상태 분석 (State Analysis)
새 코드를 작성하기 전, 대상 파일(예: `page.tsx`)을 분석하여 다음 항목들의 목록을 추출하세요.
- [ ] 모든 React 훅스 (`useState`, `useEffect`, `useRef`, `useContext` 등)
- [ ] 모든 이벤트 핸들러 함수 (`handleStart`, `confirmDelete` 등)
- [ ] 라우팅 및 네비게이션 트리거 (`router.push`)

### 2단계: 숨겨진 UI 요소 및 데이터 바인딩 식별 (Hidden UI & Data)
시안에는 보이지 않더라도, 실제 동작 시 나타나는 UI 요소들을 모두 파악하세요.
- [ ] 에러 메시지나 로딩 스피너 (`isLoading`, `isSubmitting`, `isGenerating` 등)
- [ ] 조건부 렌더링 블록 (`{history.length === 0 ? (...) : (...)}`)
- [ ] 모달 / 다이얼로그 / 알럿 (`Delete Confirmation Modal` 등)
- [ ] 마우스 오버 시 나타나는 툴팁 / 팝오버 (`AI 아키텍처 안내` 툴팁, 카드 Hover 시 `Delete` 버튼 등)
- [ ] 시안의 더미 데이터(Placeholder)를 대체해야 하는 실제 동적 데이터(Variables)

### 3단계: '유실 방지 매핑 테이블' 작성 (Mapping Table)
분석이 끝나면, 기획서(Implementation Plan) 혹은 스크래치패드에 아래와 같은 형식의 **유실 방지 매핑 테이블(Mapping Table)**을 작성하여 사용자에게 컨펌을 받거나 자체 검증용으로 활용하세요.

| 기존 기능 / UI 요소 | 매핑 여부 | 새 디자인에서의 처리 방안 (구체적인 구현 위치 및 방법) |
| :--- | :---: | :--- |
| `provider` 상태 및 `AI 아키텍처 안내` 툴팁 | 🟢 | 새 디자인의 고급 설정 메뉴 우측 끝에 `group relative` 속성을 사용하여 기존 툴팁 그대로 복원 |
| `handleStart` 폼 제출 이벤트 | 🟢 | 새 디자인의 `Hero Section` 검색창 영역을 `<form onSubmit={handleStart}>`로 감싸서 Enter 키로 동작하도록 적용 |
| `deleteTarget` 확인 모달 | 🟢 | 페이지 최하단(전체 래퍼 내부)에 기존 모달 코드를 그대로 이식하되 디자인 톤(색상/테두리)만 B2B 스타일로 조정 |

---

## 🚫 금지 사항 (Anti-Patterns)
1. **Blind Copy-Paste**: 생성형 AI(예: Google Stitch, V0 등)가 만들어준 HTML을 그대로 복사해서 붙여넣고 끝내는 행위를 절대 금지합니다.
2. **Dropping Unseen Elements**: 시안에 명시적으로 그려져 있지 않다는 이유로, 기존 코드에 있던 '에러 상태 뷰', '빈 화면(Empty State)', '툴팁' 등을 임의로 삭제하지 마세요.
3. **Overwriting Logic with Dummies**: 컴포넌트의 기능 로직을 깨고, 정적인 더미 텍스트나 하드코딩된 옵션 리스트(예: AI 모델 드롭다운)로 덮어쓰지 마세요. 항상 기존의 동적 변수를 사용해야 합니다.
