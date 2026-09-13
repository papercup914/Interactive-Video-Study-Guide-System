# Interactive Video Study Guide System - 인수인계서 (Handover)

> **최종 갱신 일시**: 2026-09-13  
> **작성자**: Antigravity (AI Pair Programming Assistant)  
> **문서 목적**: 다음 세션 작업자 및 사용자를 위한 프로젝트 현황, 아키텍처, 최근 해결된 버그 히스토리 및 운영 배포 인수인계

---

## 1. 프로젝트 개요 및 배포 아키텍처

Interactive Video Study Guide System은 유튜브 영상 또는 웹 문서를 분석하여, 구조화된 인터랙티브 학습 가이드(챕터별 서술형 본문, 퀴즈, 파인만 기법, 논리 트레이서, 연상기억법 등)를 자동 생성하는 AI 학습 지원 서비스입니다.

### 1.1 인프라 구성
* **Frontend (웹 클라이언트)**:
  * **호스팅**: Vercel Production
  * **프레임워크**: Next.js 16 (App Router, Turbopack, Tailwind CSS)
  * **도메인**: `https://interactive-video-study-guide-syste.vercel.app/`
  * **저장소 브랜치**: `main` (푸시 시 Vercel 자동 빌드 및 배포)
* **Backend & Worker (AI 파이프라인)**:
  * **호스팅**: AWS EC2 (`ubuntu@13.209.73.143`)
  * **접속 키**: 프로젝트 루트 `aws/studyguide-key.pem`
  * **작업 디렉토리**: `/home/ubuntu/Interactive-Video-Study-Guide-System`
  * **컨테이너 아키텍처 (Docker Compose)**:
    * `studyguide-fastapi`: REST API 서버 (Port 8000)
    * `studyguide-celery`: 비동기 AI 파이프라인 워커 (Celery worker, 영상 다운로드/전사/목차/챕터 생성)
    * `studyguide-redis`: 메시지 브로커 및 캐시 (Port 6379)
  * **데이터베이스**: SQLite (`backend/data/jobs.db`)

---

## 2. 주요 해결 이슈 및 버그 픽스 히스토리

최근 진행된 주요 장애 해결 및 고도화 내역은 다음과 같습니다:

### 2.1 유튜브 클라우드 IP 차단 대응 및 타이틀 100% 사수
* **문제**: AWS EC2 환경에서 유튜브 봇 감지로 인해 `yt-dlp` 메타데이터 및 자막 수집이 실패하여 디폴트 텍스트 `"유튜브 학습 가이드"`로 Fallback됨.
* **해결**:
  1. 인증 없이 0.1초 만에 비디오 원제를 확보하는 **유튜브 공식 oEmbed API Fallback** 탑재 (`backend/services/video.py`).
  2. 자막 추출 불가 시 Jina Reader 기반 웹페이지 스크랩 Fallback 작동.

### 2.2 타이틀 할루시네이션 방지 (수험생 클리셰 차단)
* **문제**: 디폴트 타이틀로 인해 LLM이 수험생 공부법으로 오인하여 `[학습 가이드 필독] 공부 안 해도 점수가 오르는 마법의 학습 가이드 - 단 10분 투자로 뇌 깨우기`와 같은 소설성 제목을 생성.
* **해결**: 프롬프트 레벨에 영상 본문과 무관한 수험/공부법 클리셰 문구("공부 안 해도", "뇌 깨우기" 등) 생성 금지 **Negative Constraints** 탑재 (`backend/services/llm/profiling.py`).

### 2.3 프론트엔드 중복 챕터 헤더 제거
* **문제**: 학습 가이드 화면 상단에 작은 글씨의 `1. 도입: ...`과 바로 아래 큰 원형 뱃지 `[1] 도입: ...`가 2줄 연속 중복 출력됨.
* **해결**: 부모 컴포넌트(`frontend/src/app/guide/[jobId]/page.tsx`)의 중복 `<h2>` 태그를 제거하고, 자식 컴포넌트(`frontend/src/app/guide/[jobId]/components/ChapterItem.tsx`)의 완성형 헤더(번호 뱃지 + 속독 모드 버튼)로 단일화.

### 2.4 비상 안전망(Heuristic Fallback) IT 편향 용어 제거
* **문제**: LLM 지연/실패 시 비상 안전망 함수가 작동하면서 스타트업/인문학 영상임에도 `"시스템 아키텍처와 비즈니스 로직, 비동기 큐..."` 같은 하드코딩 개발 용어가 출력됨.
* **해결**: 특정 IT/소프트웨어 엔지니어링 편향 용어를 전면 제거하고, 모든 도메인에 부합하는 보편적이고 지적인 **핵심 맥락 및 인사이트 분석 서술문**으로 전면 개편 (`backend/services/llm/chapter.py`).

### 2.5 유튜브 웹 UI 잡음 및 영문 에러 메시지 본문 노출 방지
* **문제**: 자막 차단 시 Jina 스크랩 텍스트에 포함된 유튜브 웹 UI 에러 메시지(`An error occurred while retrieving sharing information...`, `This helps protect our community`, `......more`)가 비상 안전망에서 정상 본문으로 오인되어 삽입됨.
* **해결**:
  1. 웹페이지 UI 에러, 커뮤니티 정책 안내, 설명란 더보기 버튼 잔여물(`......more`)을 완벽히 차단하는 **정규식 필터** 탑재.
  2. 한글이 10글자 미만인 영문 원시 텍스트는 본문에 날것으로 꽂히지 않고 정제된 분석 템플릿으로 대체되는 **한국어 문장 가드레일** 적용.

### 2.6 OpenRouter 무료 모델 엔드포인트 격리 (404 원천 방지)
* **문제**: OpenRouter 무료 모델(`:free`) 호출 시 외부에서 주입된 NVIDIA `custom_base_url` 간섭으로 `integrate.api.nvidia.com` 404가 발생하여 AI 생성이 실패하던 문제.
* **해결**: `:free` 모델 또는 OpenRouter 키 사용 시 Base URL을 `https://openrouter.ai/api/v1`으로 엄격 격리 강제 (`backend/services/llm/clients.py`, `chapter.py`, `outline.py`).

### 2.7 목차 안전망의 맹탕 질문 폐기 및 본문 기계적 주어 반복 제거
* **문제**:
  1. 목차 안전망에서 대상이 누락된 `"도입: 왜 지금 이 주제에 주목해야 하는가?"`를 고정 반환.
  2. 챕터 본문에서 이 질문형 문장을 명사 주어처럼 취급하여 문단 앞머리마다 `{clean_title}의...`, `{clean_title}에 대한...`으로 조립하여 어색한 문장이 4회 이상 반복됨.
* **해결**:
  1. 원본 영상 제목(`default_title` / `raw_title`)에서 핵심 주제어를 추출하여 `"도입: [핵심 주제]의 본질과 핵심 배경"` 등 구체적 명사형 챕터명으로 생성되도록 개편 (`outline.py`, `tasks.py`).
  2. 챕터 제목을 주어로 강제 대입하는 방식을 폐기하고, 자연스러운 한국어 서술형 문장 구조로 전면 개편 (`chapter.py`).
  3. 프론트엔드 정제 로직(`frontend/src/lib/markdownProcessor.ts`)에도 구버전 캐시 데이터 서두 템플릿 자동 제거 필터 탑재.

---

## 3. Notion 버그 리포트 관리 현황

규칙(`notion_bug_reporting.md`)에 따라 모든 버그 리포트는 Notion에 공식 기록되어 관리됩니다.

| 리포트 제목 | 상태 | Notion ID / 링크 |
| :--- | :---: | :--- |
| 디스크 목차 캐시 오염 및 디폴트 타이틀로 인한 구버전 문장/할루시네이션 이슈 | **`Resolved`** ✅ | `3d7a8db0-3fbe-810b-8e5b-db770963eadb` |
| 챕터 헤더 중복 렌더링 및 비상 안전망 휴리스틱 IT 편향 문구 노출 이슈 | **`Resolved`** ✅ | `3d7a8db0-3fbe-81a9-968d-eb120af2bc3a` |
| 유튜브 웹 스크랩 UI 잡음 및 영문 에러 메시지 본문 노출 이슈 | **`Resolved`** ✅ | `3d8a8db0-3fbe-8171-8f36-da44fd79e135` |
| 목차 안전망의 맹탕 질문형 챕터명 및 본문 내 기계적 주어 반복 노출 이슈 | **`In Progress`** 🔄 | [Notion 페이지 바로가기](https://app.notion.com/p/Bug-Report-In-Progress-3d8a8db03fbe819f905cc0db1a3fee43) |

> **주의**: 노션 버그 리포트 규칙상 사용자가 명시적으로 "해결 확인/해결 완료"라고 피드백하기 전까지는 절대로 상태를 `Resolved`로 변경하지 않고 `In Progress`를 유지해야 합니다.

---

## 4. 운영 환경 배포 및 명령어 가이드

### 4.1 Git 워크플로우
* 로컬 작업 후 반드시 문법 검증 및 빌드 테스트 수행:
  * 프론트엔드: `cd frontend && npm run build`
  * 백엔드: `python -m py_compile backend/services/tasks.py backend/services/llm/outline.py backend/services/llm/chapter.py`
* 커밋 및 푸시:
  * `git add .`
  * `git commit -m "feat/fix: ..."`
  * `git push origin main` (Vercel 자동 배포 트리거)

### 4.2 AWS EC2 운영 서버 배포 명령어
```bash
# 1. EC2 접속 및 최신 코드 동기화
ssh -i "aws/studyguide-key.pem" -o StrictHostKeyChecking=no ubuntu@13.209.73.143 "cd /home/ubuntu/Interactive-Video-Study-Guide-System && git pull origin main"

# 2. 도커 컨테이너 리빌드 및 재기동
ssh -i "aws/studyguide-key.pem" -o StrictHostKeyChecking=no ubuntu@13.209.73.143 "cd /home/ubuntu/Interactive-Video-Study-Guide-System && docker compose build celery_worker fastapi && docker compose up -d celery_worker fastapi"

# 3. 실시간 컨테이너 상태 및 로그 확인
ssh -i "aws/studyguide-key.pem" -o StrictHostKeyChecking=no ubuntu@13.209.73.143 "docker compose -f /home/ubuntu/Interactive-Video-Study-Guide-System/docker-compose.yml ps"
ssh -i "aws/studyguide-key.pem" -o StrictHostKeyChecking=no ubuntu@13.209.73.143 "docker logs --tail 100 studyguide-celery"
```

---

## 5. 다음 세션 인수인계 지침 및 제안

1. **새 세션 시작 시**:
   * 본 `handover.md`를 최우선으로 검토하고 이전 작업 맥락과 현재 진행 상태를 사용자에게 브리핑한 후 작업을 개시할 것.
2. **`In Progress` 리포트 확인**:
   * 현재 `[Bug Report] 목차 안전망의 맹탕 질문형 챕터명 및 본문 내 기계적 주어 반복 노출 이슈`가 `In Progress` 상태입니다.
   * 사용자가 실제 웹 서비스에서 새로 생성된 가이드를 확인하고 피드백을 주면, 사용자의 승인에 따라 해당 노션 페이지의 상태를 `Resolved`로 업데이트할 것.
3. **코드 수정 시 필수 원칙 준수**:
   * 한국어 응답 원칙 준수.
   * 모든 수정 후 TypeScript / Python 에러 체크 필수.
   * 널/예외 처리 강화 (네트워크 단절, 외부 API 에러, 모델 파싱 실패 시 서비스 다운 방지).