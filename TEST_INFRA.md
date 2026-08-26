# Automated Opaque-Box Test Strategy & Test Infrastructure Specifications
<!-- [KR] 자동화 블랙박스(Opaque-Box) 테스트 전략 및 테스트 인프라 명세서 -->

## 1. Executive Summary & Strategy Overview
<!-- [KR] 1. 개요 및 테스트 전략 요약 -->
This document defines the automated opaque-box test strategy and testing framework for the Interactive Video Study Guide System's Admin Health Dashboard (`/admin/health`). 

The test strategy treats the application and dashboard route as an opaque box—validating observable external behaviors, build output, HTTP response status codes, interface data contracts, dynamic state transitions, and edge-case resilience without assuming internal implementation details.

```
+-----------------------------------------------------------------------------------+
|                           4-TIER TEST ARCHITECTURE                                |
+-----------------------------------------------------------------------------------+
| Tier 1: Build Validation & Route Accessibility (npm run build, GET 200 OK)      |
| Tier 2: Boundary & Edge Case Testing (Empty filters, 30d max, special chars)      |
| Tier 3: Dynamic State Binding & Interaction (Severity/category filter, refresh)  |
| Tier 4: Real-World Workload & Error Scenarios (Spikes, latency, degraded state)  |
+-----------------------------------------------------------------------------------+
```

---

## 2. Feature Coverage Checklist
<!-- [KR] 2. 기능 테스트 커버리지 체크리스트 -->

| Ref ID | Feature | Specification Target | Test Tier | Status |
|--------|---------|-----------------------|-----------|--------|
| `COV-01` | Package Build & Setup | Next.js build succeeds (`npm run build`), `recharts` package installed | Tier 1 | Mandatory |
| `COV-02` | Route Accessibility | GET `/admin/health` responds with HTTP status 200 OK | Tier 1 | Mandatory |
| `COV-03` | Stat Summary Cards Data | `totalLogs`, `errorRate`, `totalErrors`, `totalWarnings`, `avgLatencyMs` dynamic binding | Tier 3 | Mandatory |
| `COV-04` | Time-Series Error Chart Data | Recharts AreaChart dataset formatting (timestamps, count per interval) | Tier 3 | Mandatory |
| `COV-05` | Category Breakdown Data | DonutChart category breakdown aggregation & percentage calculation | Tier 3 | Mandatory |
| `COV-06` | Log Inspector Filtering | Filter logs by severity level (`info`, `warning`, `error`, `critical`, `ALL`) | Tier 3 | Mandatory |
| `COV-07` | Log Category Filtering | Filter logs by category (`API Error`, `LLM Generation Error`, etc.) | Tier 3 | Mandatory |
| `COV-08` | Search Query Filtering | Live search input matching message, source, details, or jobId | Tier 3 | Mandatory |
| `COV-09` | Timestamp Auto-Refresh | Interactive refresh action updates `lastUpdated` ISO timestamp | Tier 3 | Mandatory |
| `COV-10` | Boundary: Empty Log Result | Valid search/filter returning 0 logs handled gracefully without crash | Tier 2 | Mandatory |
| `COV-11` | Boundary: Max Range 30d | Time range filter boundary (`24h`, `7d`, `30d`) validation | Tier 2 | Mandatory |
| `COV-12` | Boundary: Special Characters | Search query containing XSS scripts (`<script>`), SQL syntax (`' OR '1'='1`), symbols | Tier 2 | Mandatory |
| `COV-13` | Real-World: Critical Spike | Simulation of high-density critical error burst state | Tier 4 | Mandatory |
| `COV-14` | Real-World: Degraded Latency | Simulation of high backend API latency (> 1000ms) degraded status | Tier 4 | Mandatory |
| `COV-15` | Real-World: Zero-Error State | All-clear healthy system state with zero errors and 0% error rate | Tier 4 | Mandatory |

---

## 3. 4-Tier Test Case Methodology
<!-- [KR] 3. 4단계 테스트 케이스 방법론 -->

### Tier 1: Build & Route Accessibility Validation
<!-- [KR] Tier 1: 빌드 및 라우트 접근성 검증 -->
- **Objective**: Ensure the Next.js frontend compiles cleanly without bundle or dependency errors, and the `/admin/health` dashboard route returns HTTP status 200.
- **Methodology**:
  - `T1.1`: Package verification — checks `package.json` contains `recharts` and required UI libraries.
  - `T1.2`: Route file structural integrity — verifies `src/app/admin/health/page.tsx` exists and exports standard React page component.
  - `T1.3`: Next.js static build execution — executes `npm run build` command and validates exit code 0.
  - `T1.4`: Server HTTP accessibility test — spins up local production/dev server and performs HTTP GET `/admin/health`, expecting 200 OK.

### Tier 2: Boundary & Edge Case Testing (Category-Partition, BVA, Pairwise)
<!-- [KR] Tier 2: 경계값 및 엣지 케이스 테스트 (카테고리-파티셔닝, BVA, 페어와이즈) -->
- **Objective**: Verify robustness against extreme, unexpected, or empty input data combinations.
- **Methodology**:
  - **Category-Partitioning**:
    - Log Severity: `{ ALL, info, warning, error, critical }`
    - Category: `{ ALL, 'API Error', 'Network Error', 'Auth Error', 'Render Warning', 'LLM Generation Error', 'Audio Processing Error', 'PDF Parse Warning' }`
    - Time Range: `{ 24h, 7d, 30d }`
  - **Boundary Value Analysis (BVA)**:
    - `T2.1`: Search for non-existent string (`XYZ_NONEXISTENT_QUERY_9999`) -> returns exactly 0 matching logs without throwing uncaught exceptions.
    - `T2.2`: Time range selection boundary (`24h` vs `30d`) -> ensures time-series data interval range correctly scales without out-of-bounds array access.
    - `T2.3`: Special character search query (`<script>alert('xss')</script>`, `' OR 1=1 --`, `!@#$%^&*()_+`) -> handles escaping cleanly without HTML injection or syntax crashes.

### Tier 3: Dynamic State Binding & Interaction Tests
<!-- [KR] Tier 3: 동적 상태 바인딩 및 상호작용 테스트 -->
- **Objective**: Validate state changes, data binding logic, calculation integrity, and interactive user trigger handlers.
- **Methodology**:
  - `T3.1`: Severity Filter State — applying level filter `error` reduces visible dataset strictly to logs with `level === 'error'`.
  - `T3.2`: Category Filter State — applying category filter `LLM Generation Error` reduces visible dataset strictly to logs with matching category.
  - `T3.3`: Combined Search & Filter — selecting `warning` level AND searching for `Audio` matches only intersecting log entries.
  - `T3.4`: Summary Stat Consistency — validates mathematical relation:
    $$\text{totalLogs} = \text{totalErrors} + \text{totalWarnings} + \text{infoLogs}$$
    $$\text{errorRate} = \left(\frac{\text{totalErrors}}{\text{totalLogs}}\right) \times 100$$
  - `T3.5`: Interactive Refresh Action — triggering `refresh()` updates `lastUpdated` timestamp string to current time and regenerates dynamic state.

### Tier 4: Real-World Workload & Error Visualization Scenarios
<!-- [KR] Tier 4: 실제 환경 워크로드 및 에러 시각화 시나리오 -->
- **Objective**: Simulate operational production conditions, system failures, and heavy log volume visualizations.
- **Methodology**:
  - `T4.1`: Critical Error Spike Scenario — high-volume error burst where > 50% of logs are `critical` / `error`; verifies system status resolves to `Critical` and stat cards update error rate.
  - `T4.2`: High-Latency Degraded Scenario — system latency > 1200ms with active background processing jobs; verifies system status resolves to `Degraded`.
  - `T4.3`: Zero-Error Ideal State Scenario — clean operational state with 0 errors and 0 warnings; verifies system status resolves to `Healthy` and error rate displays 0.00%.
  - `T4.4`: End-to-End Route HTTP Server Verification — executes full HTTP request pipeline against Next.js production server.

---

## 4. Test Execution & Reporting Framework
<!-- [KR] 4. 테스트 실행 및 리포팅 프레임워크 -->
All automated tests are bundled into the custom test runner located at:
`frontend/src/tests/run-admin-tests.ts`

### Execution Command
```bash
# Executable from frontend root directory
npx tsx src/tests/run-admin-tests.ts
```

### Result Artifacts
- Terminal Console: Color-coded pass/fail summary per tier and overall execution score.
- `TEST_READY.md`: Automated test readiness publication summary file.
