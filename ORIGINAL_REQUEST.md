# Original User Request

## 2026-08-03T06:20:36Z

<USER_REQUEST>
# Teamwork Project Prompt — Draft

> Status: Launched
> Goal: Execute the teamwork project based on the following requirements

Next.js 프론트엔드 내에 숨겨진 관리자용 웹 대시보드 라우트(`/admin/health` 등)를 구축하여, 발생한 에러 로그 및 시스템 경고 목록을 시각화하여 점검합니다.

Working directory: i:/Interactive Video Study Guide System/frontend
Integrity mode: development

## Requirements

### R1. 에러 및 경고 로그 수집 대시보드
새로운 Next.js 라우트를 생성하고, 백엔드 또는 로컬에 쌓인 에러 로그 및 시스템 경고 데이터를 가져와(또는 Mock 데이터를 활용하여) 대시보드 형태로 구성해야 합니다.

### R2. 시각화 라이브러리 도입
Recharts, Chart.js 등 오픈소스 UI 컴포넌트 라이브러리를 설치하여, 시간대별 에러 발생 빈도나 에러 타입별 비율 등을 직관적으로 시각화하는 차트를 포함해야 합니다.

## Acceptance Criteria

### 차트 및 UI 렌더링 검증
- [ ] Next.js 환경에서 선택한 시각화 라이브러리 패키지가 충돌 없이 설치되고 빌드(`npm run build`)를 통과해야 함.
- [ ] 브라우저 에이전트(Browser Subagent) 또는 스크립트 접근 시 해당 관리자 라우트 페이지가 정상적으로 200 OK 상태 코드를 반환해야 함.

### 데이터 연동 검증
- [ ] 대시보드가 하드코딩된 정적 HTML이 아니라, 컴포넌트 렌더링 시점에 데이터를 Fetch하거나 상태(State)로 관리하여 차트에 바인딩하는 구조여야 함.
</USER_REQUEST>
