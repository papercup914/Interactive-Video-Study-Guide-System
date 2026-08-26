# Handoff Report — Dashboard Visualization & Frontend Architecture Analysis

<!-- [KR] 대시보드 시각화 및 프론트엔드 아키텍처 분석 전달 보고서 -->

## 1. Observation
<!-- [KR] 1. 관찰 내용 (직접 확인한 파일, 버전, 명령어 및 결과) -->

*   **Target Codebase Path**: `i:/Interactive Video Study Guide System/frontend`
*   **Environment & Dependencies (`package.json`)**:
    *   Next.js: `16.2.10` (App Router architecture enabled)
    *   React / React DOM: `19.2.4`
    *   Tailwind CSS: `^4.0.0` (with `@tailwindcss/postcss`, `@tailwindcss/typography`, `@tailwindcss/forms`)
    *   Icon & Animation Libraries: `lucide-react@^1.27.0`, `framer-motion@^12.42.2`
    *   Virtualization: `react-virtuoso@^4.18.11`
*   **NPM Dry-Run Installation Results**:
    *   `recharts`: Executed `npm install --dry-run recharts`. Succeeded with exit code `0`. Resolved `recharts@3.10.1` cleanly with React 19.2.4 without peer dependency errors or legacy flags.
    *   `react-chartjs-2` + `chart.js`: Executed `npm install --dry-run react-chartjs-2 chart.js`. Succeeded with exit code `0`. Resolved `react-chartjs-2@5.3.1` and `chart.js@4.5.1` cleanly.
*   **Web Search & Technical Findings (2026 Ecosystem Status)**:
    *   **Recharts**: Version `3.10.x` / `2.15+` has native support for React 19. Depends on DOM APIs (`window`, `document`, SVG `getBoundingClientRect`), requiring Client Component isolation (`'use client'`).
    *   **Chart.js / react-chartjs-2**: Version `5.3.0+` supports React 19. Uses HTML5 Canvas rendering. Requires manual registration of Chart.js modules (`ChartJS.register(...)`) and `'use client'`.
    *   **Tremor (`@tremor/react`)**: Monolithic `@tremor/react` package is legacy in 2026 and causes peer dependency conflicts with React 19. Official Tremor recommendation is Tremor Raw (copying Tailwind UI component patterns + Recharts).
*   **UI Guidelines & Responsive Rules (`RULE[mobile_fullbleed_text_ui]`)**:
    *   Mobile viewport (`< sm`): Must enforce full-bleed layouts (`px-0 md:px-4`, `p-3 md:p-6`, `rounded-none md:rounded-2xl`, `border-x-0 md:border-x-2`) to maximize density and readability for text and chart data.

---

## 2. Logic Chain
<!-- [KR] 2. 논리 체인 (관찰 사실로부터 결론까지의 단계적 추론) -->

1.  **Library Selection Rationale (Recharts vs Alternatives)**:
    *   *Observation*: Both `recharts@3.10.1` and `react-chartjs-2@5.3.1` install cleanly with React 19.2.4.
    *   *Deduction*: Recharts components are declarative SVG React components, allowing direct styling with Tailwind CSS design tokens (`var(--color-primary)`), rich custom React tooltips (`content={<CustomTooltip />}`), and seamless responsive scaling via `<ResponsiveContainer>`. Chart.js uses Canvas pixel rendering, making custom UI tooltip overlays harder to style with Tailwind. `@tremor/react` is deprecated in favor of Tremor Raw (Tailwind + Recharts).
    *   *Step Conclusion*: **Recharts (`recharts`)** is the superior visualization choice for the `/admin/health` dashboard.

2.  **SSR vs Client Component Requirements in Next.js App Router**:
    *   *Observation*: Next.js 16 App Router renders components on the server by default. Recharts calculates element coordinates via browser DOM APIs (`getBoundingClientRect`).
    *   *Deduction*: Rendering Recharts on the server during initial SSR causes hydration warnings (`width=0, height=0` mismatch between server string and browser client mount).
    *   *Step Conclusion*: All chart files must be marked with `'use client';`. To prevent SSR hydration warnings, charts should be dynamically imported with `{ ssr: false }` or guarded with a client-mounting state check (`useEffect` setting `mounted = true`). Containers must declare explicit height (`h-64 sm:h-80 w-full`).

3.  **UI Design Guidelines & Responsive Strategy (3 Environments)**:
    *   *Observation*: Project rules mandate responsive optimization for Desktop, Tablet, and Mobile (`mobile_fullbleed_text_ui`).
    *   *Deduction*:
        *   **Desktop (`lg:` / `xl:`)**: 4-column metric grid (`grid-cols-4`), 2-column split chart view (AreaChart on left, DonutChart on right), full interactive tabular log inspector.
        *   **Tablet (`md:`)**: 2-column metric grid (`grid-cols-2`), stacked single-column charts, compact log rows.
        *   **Mobile (`< sm`)**: 1-column layout, full-bleed containers (`px-0 md:px-4`, `rounded-none md:rounded-2xl`, `border-x-0 md:border`), scrollable or card-stack error logs.

4.  **Dashboard Chart Types & Component Architecture**:
    *   **System Health Summary Metrics (Stat Cards)**: Total Errors (24h), Error Rate %, Active Alerts Count, Avg Latency. Rendered via Lucide icons (`AlertTriangle`, `Activity`, `CheckCircle2`, `Clock`).
    *   **Error Frequency Over Time (AreaChart)**: Gradient-filled `<AreaChart>` displaying error volume trends over time, color-coded with primary brand variables.
    *   **Error Types Breakdown (DonutChart / PieChart)**: `<PieChart>` with `innerRadius={60}` displaying proportions of error categories (`API_TIMEOUT`, `LLM_RATE_LIMIT`, `WHISPER_PAYLOAD_TOO_LARGE`, `MDX_PARSE_ERROR`, `AUTH_FAILURE`).
    *   **Recent Error Logs Table / Inspector**: Interactive table/list with severity filter tabs (`ALL`, `CRITICAL`, `ERROR`, `WARN`), search bar, timestamps, and expandable drawer/modal for error stack trace inspection.

---

## 3. Caveats
<!-- [KR] 3. 주의사항 및 가정 (미조사 영역, 전제조건, 대안 해석) -->

*   **SSR Hydration Mismatch Risk**: Importing Recharts directly without a mounting guard or dynamic import with `{ ssr: false }` will trigger browser console warnings in Next.js App Router (`Warning: Text content did not match`).
*   **Tailwind v4 Integration**: Frontend uses Tailwind CSS v4 (`@theme inline`). Custom chart tooltips and fills should reference CSS variables (e.g., `var(--color-primary)` or `#3525cd`).
*   **Data Binding Requirements**: Acceptance criteria require dynamic state/fetch binding (not hardcoded static HTML). The implementer should implement structured mock log state with client fetch hooks so `/admin/health` functions standalone without external service dependency.

---

## 4. Conclusion
<!-- [KR] 4. 최종 결론 (추천 라이브러리, 컴포넌트 구조, 아키텍처) -->

*   **Recommended Visualization Library**: **Recharts (`recharts@^3.10.1`)**
*   **SSR Architecture**: Client Component (`'use client'`) with `next/dynamic` (`{ ssr: false }`) or client mounting state guard.
*   **Layout Compliance**: Enforce 3-environment responsive design with `mobile_fullbleed_text_ui` on mobile (`px-0 md:px-4`, `rounded-none md:rounded-2xl`, `border-x-0 md:border`).
*   **Dashboard Module Breakdown**:
    1. `HealthStatCards.tsx` (Summary metrics grid)
    2. `ErrorTrendChart.tsx` (Recharts AreaChart for error frequency over time)
    3. `ErrorTypeBreakdownChart.tsx` (Recharts DonutChart for error categories)
    4. `ErrorLogInspector.tsx` (Interactive filterable error log table/list with full-bleed mobile UI)

---

## 5. Verification Method
<!-- [KR] 5. 검증 방법 (독립적 검증을 위한 명령어 및 테스트 절차) -->

1.  **Install Recharts**:
    ```bash
    cd "i:/Interactive Video Study Guide System/frontend"
    npm install recharts
    ```
2.  **Build Verification**:
    ```bash
    npm run build
    ```
    Confirm Next.js 16 compilation succeeds without TypeScript or peer dependency errors.
3.  **Runtime & Responsive Verification**:
    *   Run `npm run dev` and navigate to `/admin/health`.
    *   Verify 200 OK status code.
    *   Inspect browser developer console to verify zero SSR hydration errors.
    *   Test viewport widths: Desktop (>1024px), Tablet (768px-1023px), Mobile (<640px) to verify full-bleed mobile layout (`px-0 md:px-4`).
