# Design System (Studygram Concept - Option E / Pattern & Pastel Engine)
<!-- [KR] 디자인 시스템 (스터디그램 컨셉 - Option E / 자체 파스텔 패턴 엔진) -->

## 1. Overview
<!-- [KR] 1. 개요 -->
This document defines the guidelines for the soft pastel-toned design system inspired by 'Studygram / Study Apps', targeting middle/high schoolers and Gen Z. The core goal is to minimize eye strain during long study sessions while creating a cute and friendly atmosphere.
<!-- [KR] 본 문서는 중·고등학생 및 Z세대를 타겟으로 한 '스터디그램(Studygram) / 스터디 앱' 감성의 부드러운 파스텔 톤 디자인 시스템의 가이드라인을 정의합니다. 장시간 학습 시 눈의 피로를 최소화하며, 귀엽고 친근한 분위기를 연출하는 것이 핵심입니다. -->
To maintain visual consistency and avoid "vibe clashes" from external photos, we use a **Deterministic Pastel Theme Engine** that generates soft geometric SVG patterns and harmonious color palettes based on the study guide's ID.
<!-- [KR] 외부 사진으로 인한 감성 충돌(Vibe Clash)을 막고 시각적 통일성을 유지하기 위해, 가이드 ID를 기반으로 부드러운 기하학적 파스텔 패턴과 조화로운 색상 팔레트를 생성하는 **결정론적 파스텔 테마 엔진**을 사용합니다. -->

## 2. Color Palette & Dynamic Themes
<!-- [KR] 2. 컬러 팔레트 및 동적 테마 -->

### 2.1. Light Mode (Default Theme)
<!-- [KR] 2.1. Light Mode (기본 테마) -->
- **Background (`--background`)**: Very light warm white or ivory base (`#fdfcf8`)
  <!-- [KR] Background (`--background`): 매우 밝은 웜 화이트 또는 아이보리 계열 (`#fdfcf8`) -->
- **Card (`--card`)**: Pure white (`#ffffff`)
  <!-- [KR] Card (`--card`): 순백색 (`#ffffff`) -->
- **Primary (`--primary`)**: Soft pastel lavender/soft blue (`#93a5cf` ~ `#e4efe9` gradient base) - used as an accent color
  <!-- [KR] Primary (`--primary`): 부드러운 파스텔 라벤더/소프트 블루 (`#93a5cf` ~ `#e4efe9` 그라데이션 베이스) - 포인트 컬러로 사용 -->
- **Primary Foreground (`--primary-foreground`)**: White (`#ffffff`)
  <!-- [KR] Primary Foreground (`--primary-foreground`): 흰색 (`#ffffff`) -->
- **Muted (`--muted`)**: Very pale peach/gray (`#f7f5f2`)
  <!-- [KR] Muted (`--muted`): 아주 연한 피치/그레이 (`#f7f5f2`) -->
- **Muted Foreground (`--muted-foreground`)**: Soft charcoal gray (`#64748b`)
  <!-- [KR] Muted Foreground (`--muted-foreground`): 부드러운 차콜 그레이 (`#64748b`) -->
- **Border (`--border`)**: Very light and soft beige/gray (`#f0eae4`)
  <!-- [KR] Border (`--border`): 매우 옅고 부드러운 베이지/회색 (`#f0eae4`) -->
- **Foreground (Text) (`--foreground`)**: Dark gray (`#334155`) -> Avoid pure black (`#000`) to prevent glare
  <!-- [KR] Foreground (Text) (`--foreground`): 먹색/다크 그레이 (`#334155`) -> 완전한 블랙(`#000`)은 피하여 눈부심 방지 -->
- **Destructive**: Pastel red/coral (`#ffa0a0`)
  <!-- [KR] Destructive: 파스텔 레드/코랄 (`#ffa0a0`) -->

### 2.2. Deterministic Theme Engine (lib/theme.ts)
<!-- [KR] 2.2. 결정론적 테마 엔진 -->
Each guide is assigned a unique theme based on its ID. The body of the guide page inherits the `lightBgColor` to create a cohesive reading environment.
<!-- [KR] 각 가이드는 ID에 따라 고유한 테마를 부여받습니다. 가이드 열람 페이지의 전체 배경은 이 테마의 `lightBgColor`를 상속받아 일체감 있는 읽기 환경을 제공합니다. -->
- **Lavender**: `primaryColor` (bg-indigo-300), `lightBgColor` (bg-indigo-50), `gradient` (from-indigo-200 to-purple-200)
- **Peach**: `primaryColor` (bg-rose-300), `lightBgColor` (bg-rose-50), `gradient` (from-rose-200 to-pink-200)
- **Mint**: `primaryColor` (bg-teal-300), `lightBgColor` (bg-teal-50), `gradient` (from-teal-200 to-emerald-200)
- **Sky**: `primaryColor` (bg-sky-300), `lightBgColor` (bg-sky-50), `gradient` (from-sky-200 to-blue-200)
- **Butter**: `primaryColor` (bg-amber-300), `lightBgColor` (bg-amber-50), `gradient` (from-amber-200 to-yellow-200)

## 3. UI Components & Imagery
<!-- [KR] 3. UI 요소 및 이미지 -->
- **Thumbnails & Banners**: 
  <!-- [KR] 썸네일 및 배너: -->
  - Do not use external photos (Unsplash, etc.) as they may break the soft aesthetic.
    <!-- [KR] 외부 사진(Unsplash 등)은 부드러운 감성을 깰 수 있으므로 사용하지 않습니다. -->
  - Use dynamically generated geometric CSS/SVG patterns (Polka dots, checks, diagonal lines) layered with `mix-blend-overlay` over pastel gradients **ONLY** for thumbnail cards.
    <!-- [KR] 파스텔 그라데이션 위에 `mix-blend-overlay`로 합성된 동적 기하학 CSS/SVG 패턴(도트, 체크, 사선)은 **오직 썸네일 카드**에만 사용합니다. -->
  - **Guide Viewer Rule**: The actual guide viewing pages (`guide/[jobId]`) MUST remain completely minimal (no large banners, no tinted backgrounds) to ensure 100% readability across Light/Dark/E-ink modes. Only small thematic elements (e.g., a tiny theme emoji next to the title) are permitted.
    <!-- [KR] **가이드 뷰어 규칙**: 실제 가이드를 읽는 본문 페이지(`guide/[jobId]`)는 라이트/다크/E-ink 모드에서 100% 가독성을 확보하기 위해 거대한 배너나 틴팅된 배경색을 절대 사용하지 않습니다. 제목 옆에 작게 붙는 테마 이모지 등 최소한의 요소만 허용됩니다. -->
- **Contextual Marginalia (맥락형 우측 여백 노트)**:
  <!-- [KR] 맥락형 우측 여백 노트: -->
  - When users request an AI explanation for highlighted text, the response should appear as a sticky note card on the right margin, anchored to the text block.
    <!-- [KR] 텍스트 하이라이트 후 AI 설명 요청 시, 해당 텍스트 블록 우측 여백에 포스트잇(Sticky note) 형태의 카드로 답변이 표시되어야 합니다. -->
  - Use `bg-muted/50` or `bg-primary/5` for the note background to differentiate it from the main content.
    <!-- [KR] 본문과 구별되도록 노트 배경은 `bg-muted/50` 또는 `bg-primary/5`를 사용합니다. -->
- **Border Radius**:
  <!-- [KR] 둥근 모서리: -->
  - Cards, modals, large areas: `rounded-3xl` (Very rounded)
    <!-- [KR] 카드, 모달, 큰 영역: `rounded-3xl` (매우 둥글게) -->
  - Buttons, inputs, badges: `rounded-full` (Pill shape)
    <!-- [KR] 버튼, 입력창, 뱃지: `rounded-full` (완전한 알약 형태) -->
- **Shadows**:
  <!-- [KR] 그림자: -->
  - Soft, diffused pastel-toned floating shadows (e.g., `shadow-2xl shadow-primary/10`) to create a plush, elevated feel.
    <!-- [KR] 카드가 푹신하게 떠오른 듯한 느낌을 주기 위해 부드럽고 퍼지는 파스텔 톤 그림자(`shadow-2xl shadow-primary/10`)를 사용합니다. -->
- **Micro Interactions**:
  <!-- [KR] 마이크로 애니메이션: -->
  - Smooth transition speed (`transition-all duration-500 ease-out`) for hover effects on thumbnails.
    <!-- [KR] 썸네일 호버 시 부드러운 전환 속도(`transition-all duration-500 ease-out`). -->
  - Jelly-like bouncy click feel using `active:scale-95` on buttons
    <!-- [KR] 버튼 클릭 시 `active:scale-95` 적용으로 젤리 같은 쫀득한 클릭감 제공 -->

### 5.4. Sidenotes (Mobile)
<!-- [KR] 5.4. 사이드노트 (모바일) -->
- On mobile devices (`max-width: 768px`), sidenotes collapse into an inline button (💬) with a background matching the highlight color.
  <!-- [KR] 모바일(`max-width: 768px`)에서는 사이드노트가 하이라이트 색상과 동일한 배경을 가진 인라인 버튼(💬)으로 축소됩니다. -->
- Tapping the button expands the sidenote block inline beneath the paragraph using a smooth accordion animation (`height 0 -> auto`).
  <!-- [KR] 버튼을 탭하면 부드러운 아코디언 애니메이션(`height 0 -> auto`)을 통해 문단 바로 아래에 사이드노트 블록이 인라인으로 확장됩니다. -->

## 6. UI Components & Patterns
<!-- [KR] 6. UI 컴포넌트 및 패턴 -->

### 6.1. Info Tooltips (Tailwind CSS)
<!-- [KR] 6.1. 정보 툴팁 (Tailwind CSS) -->
- For dense informational text (like the AI Architecture summary), use a clean CSS-only hover tooltip instead of cluttering the UI.
  <!-- [KR] AI 아키텍처 안내와 같이 정보가 많은 텍스트는 UI를 복잡하게 만들지 않도록 순수 CSS 기반 호버 툴팁을 사용합니다. -->
- Structure: A container with `group relative` containing the trigger text/icon, and an absolute positioned tooltip box with `opacity-0 group-hover:opacity-100 transition-opacity absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-max max-w-xs z-50`.
  <!-- [KR] 구조: `group relative` 컨테이너 안에 트리거 텍스트/아이콘과, `opacity-0 group-hover:opacity-100` 등을 적용한 절대 위치 툴팁 박스(`absolute bottom-full ... z-50`)를 배치합니다. -->

## 4. Typography
<!-- [KR] 4. 타이포그래피 -->
- **Primary Font**: Prioritize rounded fonts on `font-sans` to mimic a rounded Gothic feel.
  <!-- [KR] 기본 폰트: 둥근 고딕 느낌을 내기 위해 `font-sans`에 라운드 폰트 우선 적용. -->
- **Characteristics**:
  <!-- [KR] 특징: -->
  - Headings are rounded and bold to emphasize friendliness.
    <!-- [KR] 제목(Heading)은 둥글고 두껍게 처리하여 친근함을 강조합니다. -->
  - Body text uses `leading-relaxed` (1.6 line height) and generous letter spacing to improve readability.
    <!-- [KR] 본문(Body)은 `leading-relaxed` (줄간격 1.6) 및 넉넉한 글자 간격을 사용하여 가독성을 높입니다. -->

## 7. Admin Health Dashboard UI Specification (/admin/health)
<!-- [KR] 7. 관리자 헬스 대시보드 UI 명세 (/admin/health) -->

### 7.1. Responsive Design Trio Strategy (PC, Tablet, Mobile)
<!-- [KR] 7.1. 3종 반응형 디자인 전략 (PC, 태블릿, 모바일) -->
- **Desktop (PC)**: 4-column summary metric card grid (`grid-cols-4`), 2-column chart grid (`grid-cols-1 lg:grid-cols-2`), full log table with stack trace detail drawer/modal.
  <!-- [KR] 데스크톱: 4열 메트릭 카드 그리드, 2열 차트 그리드 (시계열 에러 추이 + 에러 카테고리 도넛 차트), 스택 트레이스 상세보기 모달이 포함된 로그 테이블. -->
- **Tablet**: 2-column summary metric card grid (`grid-cols-2`), stacked full-width charts, compact table rows.
  <!-- [KR] 태블릿: 2열 메트릭 카드 그리드, 세로로 중첩된 1열 차트 레이아웃. -->
- **Mobile**: Enforce **Full-Bleed Text UI** (`px-0 md:px-4`, `rounded-none md:rounded-2xl`, `border-x-0 md:border`). Single-column card stack, horizontally scrollable filter tabs, touch-friendly search input, modal bottom-sheet drawer for stack traces.
  <!-- [KR] 모바일: 모바일 텍스트 꽉 찬 UI 규칙 적용 (px-0 md:px-4, rounded-none md:rounded-2xl). 1열 카드 스택, 가로 스크롤 가능한 레벨 필터 탭, 바텀시트 모달 드로어. -->

### 7.2. Component Architecture
<!-- [KR] 7.2. 컴포넌트 아키텍처 -->
1. **`HealthStatCards.tsx`**: Displays Total Errors, Error Rate %, Active Warnings, Avg Latency (ms), and System Status badge (Healthy / Degraded / Critical) using Lucide icons (`AlertTriangle`, `Activity`, `CheckCircle2`, `Clock`, `ShieldAlert`).
   <!-- [KR] HealthStatCards.tsx: 요약 지표 카드 4종 및 시스템 상태 뱃지 표시 -->
2. **`ErrorTrendChart.tsx`**: Client-guarded (`'use client';` + `mounted` state) Recharts `<AreaChart>` displaying error/warning counts over time with gradient fill and dark tooltips (`w-full h-64 sm:h-80`).
   <!-- [KR] ErrorTrendChart.tsx: 하이드레이션 오류 없는 Client Component 기반 시계열 면적 차트 -->
3. **`ErrorTypeBreakdownChart.tsx`**: Client-guarded Recharts `<PieChart>` with `innerRadius={50}` displaying category breakdown with color-coded slices and legend (`w-full h-64 sm:h-80`).
   <!-- [KR] ErrorTypeBreakdownChart.tsx: 카테고리별 에러 비중 도넛 차트 -->
4. **`ErrorLogInspector.tsx`**: Filterable log inspector component with level tabs (`ALL`, `CRITICAL`, `ERROR`, `WARN`), live search input, full-bleed mobile container, and expandable stack trace modal/drawer.
   <!-- [KR] ErrorLogInspector.tsx: 에러 필터링, 실시간 검색, 스택 트레이스 모달을 지원하는 로그 탐색기 -->
5. **`src/app/admin/health/page.tsx`**: Page route integrating header, time range selector (`24h`, `7d`, `30d`), manual refresh button, and dynamic state binding via `useAdminHealth`.
   <!-- [KR] page.tsx: 시간 범위 선택기 및 새로고침 버튼이 탑재된 관리자 대시보드 메인 라우트 -->

