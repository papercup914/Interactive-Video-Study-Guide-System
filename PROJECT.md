# Project: Admin Health Dashboard for Interactive Video Study Guide System
<!-- [KR] 프로젝트: 인터랙티브 비디오 스터디 가이드 시스템용 관리자 헬스 대시보드 -->

## Architecture
<!-- [KR] 아키텍처 -->
- **Framework**: Next.js 16.2.10 (App Router: `src/app/`)
  <!-- [KR] 프레임워크: Next.js 16.2.10 -->
- **Language & Runtime**: TypeScript 5, React 19.2.4
  <!-- [KR] 언어 및 런타임: TypeScript 5, React 19.2.4 -->
- **Styling**: Tailwind CSS v4 (`@theme inline`, custom CSS variables)
  <!-- [KR] 스타일링: Tailwind CSS v4 -->
- **Visualization Library**: Recharts (`recharts@^3.10.1`)
  <!-- [KR] 시각화 라이브러리: Recharts -->
- **Responsive Layout**: Universal (Desktop, Tablet, Mobile full-bleed via `px-0 md:px-4`, `rounded-none md:rounded-2xl`)
  <!-- [KR] 반응형 레이아웃: 유니버설 (데스크톱, 태블릿, 모바일 풀 블리드 지원) -->
- **Dashboard Route**: `i:/Interactive Video Study Guide System/frontend/src/app/admin/health/page.tsx` (`/admin/health`)
  <!-- [KR] 대시보드 라우트 경로 -->

## Feature Inventory
<!-- [KR] 주요 기능 목록 -->
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | Chart Package Setup | Install `recharts` package without dependency conflicts and verify `npm run build` | M1 | R2, AC27 |
| 2 | Health Data Models & Hook | Define TypeScript interfaces (`src/types/adminHealth.ts`) and dynamic state hook (`src/hooks/useAdminHealth.ts`) | M1 | R1, AC31 |
| 3 | Admin Health Dashboard Route | Create `/admin/health` route returning 200 OK status code | M2 | R1, AC28 |
| 4 | Summary Health Stat Cards | Metric cards for Total Errors, Error Rate %, Active Warnings, Avg Latency with Lucide icons | M2 | R1 |
| 5 | Time-Series Error Frequency Chart | Recharts AreaChart for error frequency over time with responsive container and gradient fill | M2 | R2, AC31 |
| 6 | Error Types Breakdown Chart | Recharts Donut/PieChart for error category breakdown with custom tooltips | M2 | R2, AC31 |
| 7 | Filterable Error Log Inspector | Interactive log table with level filters (ALL, CRITICAL, ERROR, WARN), search, and stack detail modal | M2 | R1 |
| 8 | E2E & Verification Suite | E2E opaque-box test runner validating route 200 OK, dynamic state binding, build compliance | M-E2E | AC27, AC28, AC31 |

## Milestones
<!-- [KR] 마일스톤 (개발 단계) -->
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Infrastructure & Data Layer | Recharts package installation, TypeScript data models, dynamic mock generator & `useAdminHealth` hook | none | DONE |
| M2 | UI Components & Dashboard Route | `/admin/health` route implementation, Stat Cards, AreaChart, DonutChart, Log Inspector with mobile full-bleed design | M1 | DONE |
| M-E2E | E2E Testing Suite | E2E test infra, test cases (Tiers 1-5), validation runner publishing `TEST_READY.md` | M1, M2 | DONE |

## Interface Contracts
<!-- [KR] 인터페이스 계약 (타입 및 Props 정의) -->

### 1. Data Hook (`src/hooks/useAdminHealth.ts`)
<!-- [KR] 데이터 훅 정의 -->
```typescript
export interface UseAdminHealthOptions {
  timeRange?: '24h' | '7d' | '30d';
  category?: ErrorCategory | 'ALL';
  level?: LogLevel | 'ALL';
  searchQuery?: string;
  autoRefreshMs?: number;
}

export interface UseAdminHealthResult {
  data: AdminHealthData;
  loading: boolean;
  error: Error | null;
  refresh: () => void;
}
```

### 2. Dashboard Components Props
<!-- [KR] 대시보드 컴포넌트 Props -->
- `HealthStatCards`: `{ summary: SystemHealthSummary }`
- `ErrorTrendChart`: `{ data: TimeSeriesPoint[] }`
- `ErrorTypeBreakdownChart`: `{ data: CategoryBreakdown[] }`
- `ErrorLogInspector`: `{ logs: SystemLogEntry[]; onRefresh: () => void }`

## Code Layout
<!-- [KR] 코드 파일 구조 -->
- `frontend/package.json` — Recharts dependency
  <!-- [KR] Recharts 의존성 -->
- `frontend/src/types/adminHealth.ts` — Data models
  <!-- [KR] 데이터 모델 -->
- `frontend/src/hooks/useAdminHealth.ts` — Dynamic state hook & fallback mock generator
  <!-- [KR] 동적 상태 훅 및 목업 생성기 -->
- `frontend/src/components/admin/HealthStatCards.tsx` — Stat metric cards
  <!-- [KR] 통계 지표 카드 -->
- `frontend/src/components/admin/ErrorTrendChart.tsx` — AreaChart for error frequency
  <!-- [KR] 에러 빈도 AreaChart -->
- `frontend/src/components/admin/ErrorTypeBreakdownChart.tsx` — DonutChart for error categories
  <!-- [KR] 에러 카테고리 도넛 차트 -->
- `frontend/src/components/admin/ErrorLogInspector.tsx` — Filterable error table
  <!-- [KR] 필터링 가능한 에러 테이블 -->
- `frontend/src/app/admin/health/page.tsx` — Main dashboard page route
  <!-- [KR] 메인 대시보드 페이지 라우트 -->
