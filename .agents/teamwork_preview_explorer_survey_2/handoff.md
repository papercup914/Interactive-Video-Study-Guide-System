# Handoff Report: Survey Explorer 2 — Admin Health Dashboard Data Modeling & Logging Survey

> **작성 일시**: 2026-08-03T15:24:00+09:00  
> **작성자**: Survey Explorer 2 (Teamwork Explorer)  
> **작업 디렉토리**: `i:/Interactive Video Study Guide System/.agents/teamwork_preview_explorer_survey_2`  
> **대상 코드베이스**: `i:/Interactive Video Study Guide System/frontend` 및 관련 백엔드 패스  

---

## 1. Observation (관측 사항)

### 1.1. 프론트엔드 환경 및 종속성 (`frontend/package.json`)
- **Next.js & React**: Next.js `16.2.10` (App Router), React `19.2.4`, TypeScript `5`.
- **UI 및 차트 관련 패키지 현황**: `lucide-react` (^1.27.0), `framer-motion` (^12.42.2), `tailwindcss` (^4), `react-virtuoso` (^4.18.11), `react-markdown` (^10.1.0) 등이 설치되어 있음. 현재 Recharts 또는 Chart.js 등 전용 차트 시각화 라이브러리는 아직 `package.json`에 포함되지 않은 상태임.
- **라우팅 규칙**: Next.js App Router (`src/app/`) 구조를 채택하고 있으며, 신규 대시보드는 `src/app/admin/health/page.tsx` 라우트로 구축되어야 함.

### 1.2. 기존 에러 핸들링 및 상태 관리 관측
1. **React 렌더링 에러 (`src/components/ErrorBoundary.tsx`)**:
   - `componentDidCatch(error: Error, errorInfo: ErrorInfo)` (Line 26~28):
     `console.error('[ErrorBoundary] Caught error in chapter: ...', error, errorInfo)` 형태로 클라이언트 렌더링 에러를 콘솔에만 출력 중.
2. **비동기 Polling 및 작업 상태 에러 (`src/app/contexts/TaskContext.tsx`)**:
   - `TaskContext.tsx` Line 30~67: `/api/guide/status/${jobId}` Polling 수행 중 `res.ok`가 아닐 때 `err.detail === "Job not found"` 경고 처리 및 `console.error("Polling error", e)` 출력.
   - 작업 취소 실패 시 Line 96 `console.error("Cancel failed", e)` 처리.
3. **메인 페이지 가이드 작업 연동 (`src/app/page.tsx`)**:
   - Line 60~62, 99~101, 123~125: History 패치 실패, 가이드 생성 시작 오류, 삭제 오류 발생 시 `console.error` 및 기본 HTML `alert()` 경고 창으로 사용자 알림.

### 1.3. 백엔드 API 및 프록시 설정 (`frontend/next.config.ts` 및 `backend/routers/guide.py`)
- **Next.js Proxy (`next.config.ts`)**: Line 7~10에서 `/api/:path*` 요청을 `http://127.0.0.1:8000/api/:path*`로 백엔드 프록시 설정 중.
- **백엔드 예외 처리 (`backend/routers/guide.py`)**:
  - Line 193~197: 특정 챕터 생성 실패 시 `Warning: Section X failed completely despite retries: ...` 출력 후 마크다운 경고 블록(`> [!WARNING]`) 삽입.
  - Line 223~226: 전체 가이드 생성 프로세스 예외 발생 시 `fail_job(job_id, error_msg)` 호출 후 스택 트레이스(`traceback.format_exc()`) 기록.

---

## 2. Logic Chain (논리 체인)

1. **에러 수집의 체계화 필요성**:
   - 기존 코드베이스는 클라이언트(React ErrorBoundary, TaskContext, fetch) 및 백엔드(LLM 처리, PDF 파싱, 오디오 추출) 전반에서 발생하는 에러를 단지 `console.error` 또는 in-memory `fail_job`으로 처리하고 있어, 관리자가 통합적으로 상태를 점검할 수 있는 중앙 로그 저장/조회 메커니즘이 부재함.
2. **관리자 헬스 대시보드 (`/admin/health`) 역할 정의**:
   - R1/R2 및 AC 기준에 따라 관리자 대시보드는 단순 정적 라우트가 아니라 **(1) 시스템 종합 헬스 메트릭, (2) 시간대별 에러/경고 발생 빈도 (시계열 차트), (3) 카테고리/타입별 에러 분포 (분포 차트), (4) 실시간 필터링 가능한 필터블 로그 리스트**를 제공해야 함.
3. **타입 안전성(Type Safety) 중심의 데이터 모델링**:
   - TypeScript 환경에서 에러 로그, 시계열 집계 데이터, 카테고리 분포 데이터를 엄격하게 타입 정의(`src/types/adminHealth.ts`)함으로써 차트 컴포넌트(Recharts 등)와 실시간 데이터 바인딩 시 null exception 방지 및 정적 타입 검사를 보장함.
4. **동적 데이터 바인딩 및 Mock/Fetch 이중화 전략**:
   - 정적 HTML 바인딩을 금지하는 요구사항(AC31)을 충족하기 위해, Custom React Hook (`useAdminHealth`)을 통해 backend API (`/api/admin/health`) 호환 데이터 패치를 시도하고, 백엔드가 미가동 중이거나 개발 환경인 경우 시계열 분포를 포함한 동적 Mock 데이터 생성기(`generateMockHealthData`)로 실시간 상태(State)를 업데이트하도록 설계함.

---

## 3. Caveats (주의사항 및 한계)

1. **백엔드 영구 로그 데이터베이스 부재**:
   - 현재 백엔드는 `backend/data/saved_guides.json`에 학습 가이드 완료 이력만 저장하고 있음. 따라서 에러 로그 중앙 수집 백엔드가 구현되기 전까지는 클라이언트 측 동적 Mock 데이터 생성기 및 LocalStorage/Session state 기반 억셉턴스를 활용해야 함.
2. **차트 라이브러리 미설치 상태**:
   - 현재 `package.json`에는 Recharts 등 차트 시각화 라이브러리가 포함되어 있지 않으므로, Implementer 단계에서 `recharts` (또는 `chart.js` / `react-chartjs-2`) 패키지 설치가 필수적임.

---

## 4. Conclusion & Concrete Specifications (결론 및 구체적 명세)

### 4.1. TypeScript 구체적 데이터 구조 명세 (`src/types/adminHealth.ts`)

```typescript
/**
 * 로그 중요도 (Log Severity Level)
 */
export type LogLevel = 'info' | 'warning' | 'error' | 'critical';

/**
 * 에러 카테고리 분류 (Error Category / Type)
 */
export type ErrorCategory =
  | 'API Error'               // 백엔드 API 응답 에러 (500, 404, 429 등)
  | 'Network Error'           // 네트워크 연결 실패, 타임아웃, CORS
  | 'Auth Error'              // 인증/인가 실패, API 키 누락
  | 'Render Warning'          // React 컴포넌트, ErrorBoundary, MDX 파싱 경고
  | 'LLM Generation Error'    // AI 모델 호출 실패, 토큰 초과, 파싱 에러
  | 'Audio Processing Error'  // Whisper 오디오 추출, 25MB 용량 초과
  | 'PDF Parse Warning';       // PyMuPDF / pymupdf4llm 파싱 오류 및 대체 fallback

/**
 * 로그 발생 모듈 (Log Source)
 */
export type LogSource =
  | 'Frontend / React Render'
  | 'Frontend / API Client'
  | 'Backend / FastAPI Router'
  | 'Backend / LLM Service'
  | 'Backend / Audio Transcriber'
  | 'Backend / PDF Parser'
  | 'System / Health Monitor';

/**
 * 1. 단일 에러/경고 로그 데이터 모델 (SystemLogEntry)
 */
export interface SystemLogEntry {
  id: string;                 // 고유 log ID (e.g. log_9b1deb4d)
  timestamp: string;          // ISO 8601 string (예: "2026-08-03T15:30:00.000Z")
  level: LogLevel;            // Log level ('info' | 'warning' | 'error' | 'critical')
  category: ErrorCategory;    // 에러 타입 카테고리
  message: string;            // 사용자 및 개발자용 요약 메시지
  source: LogSource;          // 발생 출처
  details?: string | null;    // Stack trace, 원본 에러 응답 객체
  jobId?: string | null;      // 연관 백그라운드 가이드 생성 작업 ID
  statusCode?: number | null; // HTTP Status Code (API 에러 시)
  resolved?: boolean;         // 관리자 처리 완료 여부
}

/**
 * 2. 시간대별 시계열 집계 모델 (TimeSeriesPoint)
 * - Hourly / Daily 빈도 시각화 차트 (Line / Area / Bar Chart 바인딩용)
 */
export interface TimeSeriesPoint {
  timestamp: string;          // ISO 타임스탬프 또는 날짜 기준
  formattedTime: string;      // 차트 X축 레이블 (예: "14:00", "08/03")
  errorCount: number;         // 에러 수 (error + critical)
  warningCount: number;       // 경고 수 (warning)
  infoCount: number;          // 정보 수 (info)
  totalCount: number;         // 총 발생 수
}

/**
 * 3. 카테고리별 에러 분포 모델 (CategoryBreakdown)
 * - 에러 타입별 비율 파이 / 도넛 차트 바인딩용
 */
export interface CategoryBreakdown {
  category: ErrorCategory;    // 에러 카테고리 명칭
  count: number;              // 해당 카테고리 발생 건수
  percentage: number;         // 전체 에러 대비 비율 (%)
  color: string;              // 차트 파스텔 UI 매핑 색상 (Tailwind / Hex)
}

/**
 * 4. 시스템 종합 헬스 요약 데이터 (SystemHealthSummary)
 */
export interface SystemHealthSummary {
  systemStatus: 'Healthy' | 'Degraded' | 'Critical';
  totalLogs: number;
  errorRate: number;            // 실패율 (%)
  totalErrors: number;
  totalWarnings: number;
  avgLatencyMs: number;         // 평균 API 응답 지연 (ms)
  activeJobs: number;           // 백그라운드 진행 작업 수
  lastUpdated: string;          // 최종 갱신 시간 (ISO string)
}

/**
 * 5. 대시보드 전체 바인딩 데이터 구조 (AdminHealthData)
 */
export interface AdminHealthData {
  summary: SystemHealthSummary;
  timeSeries: TimeSeriesPoint[];
  categoryBreakdown: CategoryBreakdown[];
  logs: SystemLogEntry[];
}
```

### 4.2. 데이터 패치 및 동적 State 바인딩 / Mock 생성 전략

1. **Custom Hook 아키텍처 (`src/hooks/useAdminHealth.ts`)**:
   - `timeRange` ('24h' | '7d' | '30d'), `selectedCategory`, `selectedLevel`, `searchQuery` 등의 state를 관리함.
   - API 패치 기능: 백엔드 `/api/admin/health` 호출 시도.
   - Fallback 및 Dynamic Generator: API 호출 실패 또는 개발 모드일 경우 `generateMockHealthData(options)`를 실행하여 real-time 데이터 세트를 동적 계산.
   - Polling / Auto-refresh: 5초/10초 단위 자동 갱신 지원.
2. **동적 데이터 바인딩 구조**:
   - `/admin/health` 페이지는 단순 static Markup이 아닌 `useAdminHealth` Hook에서 반환되는 `data` state를 바인딩하여 Recharts 차트 및 Log Table 컴포넌트를 반응형으로 렌더링.

---

## 5. Verification Method (독립 검증 방법)

1. **타입 파일 존재 및 구문 검증**:
   - `src/types/adminHealth.ts` 생성이 완료되었는지 확인하고 TypeScript 빌드 검증:
     ```bash
     npx tsc --noEmit
     ```
2. **동적 state 바인딩 및 라우트 OK 검증**:
   - Next.js 빌드 시 `/admin/health` 라우트가 200 OK로 성공적으로 빌드되는지 확인:
     ```bash
     npm run build
     ```
3. **Browser / API 접근성 검증**:
   - 개발 서버 가동 후 `http://localhost:3000/admin/health` 페이지 접근 시 200 OK 응답 및 차트/상태 바인딩 확인.
