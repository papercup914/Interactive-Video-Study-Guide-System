# Interactive Video Study Guide System - 인수인계서 (Handover)

> **최종 갱신 일시**: 2026-09-13 (21:55 KST)  
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

## 2. 최근 주요 작업 및 버그 픽스 히스토리

### 2.1 [공식 문서화] 유튜브 영상 기반 AI 학습 가이드 생성 파이프라인 & 프롬프트 총괄 명세서
* **내용**: 원활한 유지보수 및 확장을 위해, 원본 유튜브 영상을 학습 가이드로 생성하는 100% 모든 메커니즘, 관련된 17개 코드 파일 위치 및 역할, 모든 프롬프트 원문 전문, 5단계 자막 수집 및 장애 대응 안전망을 집대성하여 Notion 공식 문서로 발행.
* **Notion 페이지**: [시스템 아키텍처 명세서 바로가기](https://app.notion.com/p/AI-3daa8db03fbe81be8ac8e186fb21c874)

### 2.2 [P0 버그 픽스] Fallback 합성 가드레일 내 IT 편향 용어 완전 제거
* **문제**: LLM이 서술형 본문 없이 XML 태그나 원시 JSON으로 바로 시작했을 때 작동하는 보정 가드레일(`chapter.py:463-477`)에 `"시스템과 알고리즘"`, `"전체 아키텍처 관점"`, `"성능 최적화와 예외 처리 패턴"` 등 IT 편향 하드코딩 용어가 잔류하여, 인문/철학/비즈니스 영상 요약 시 문맥이 왜곡될 위험이 있었음.
* **해결**: `chapter.py` 내의 Fallback 템플릿을 모든 도메인에 부합하는 보편적 지적 탐구 서술문(`"본질과 맥락의 유기적 결합"`, `"현장의 실제 맥락과 조건에 유연하게 응용"`)으로 전면 개편.

### 2.3 [P0 고도화] 목차 및 챕터 생성 시 영상 원제(`raw_title` / `default_title`) 컨텍스트 주입
* **문제**:
  1. 공식 챕터 각색 및 스크립트 목차 생성 시 영상의 원본 제목이 프롬프트에 주입되지 않아, 공식 챕터명이 `Intro`, `Part 1` 등 추상적일 때 맥락을 살리지 못할 위험이 있었음.
  2. 챕터 본문 비동기 생성(`chapter.py`) 시에도 원본 영상 제목이 전달되지 않아 개별 챕터가 전체 대주제 맥락을 놓칠 수 있었음.
* **해결**:
  1. `outline.py:104-137`: 공식 챕터 각색 프롬프트 및 스크립트 기반 목차 생성 프롬프트에 `[영상 원본 제목/주제]: "{default_title}"` 컨텍스트를 명시적 주입.
  2. `tasks.py` ➡️ `chapter.py` ➡️ `backend/prompts/chapter_guide.py`: `raw_title` 매개변수를 신설하여 시스템 프롬프트 상단에 `[영상 전체 주제/제목]: "{raw_title}"`을 주입함으로써 모든 챕터가 영상의 대주제와 일관성을 유지하도록 개선.

### 2.4 [P1 품질 강화] 한국어 서술 검증 기준(`validate_chapter_narrative`) 대폭 강화
* **문제**: 기존 한글 150자 미만 검사 기준이 너무 관대하여, 본문의 대부분이 영문으로 작성되고 끝에 인사이트 박스 몇 줄만 한글인 경우에도 합격 처리될 위험이 존재.
* **해결**:
  1. 한글 최소 절대 글자 수를 150자 ➡️ **250자 미만 시 즉시 탈락**으로 상향.
  2. **한글/영문 알파벳 비율 검증 신설**: 본문에 영문 알파벳이 100자 이상 포함된 경우, **한글 비율이 40% 미만이면 즉시 탈락** 처리하고 100% 한국어 번역 에스컬레이션 재시도를 트리거하도록 강화 (`validators.py`).

### 2.5 비판적 코드 리뷰 검토 및 오판 규명 (Fact-Check)
* **캐시 정화 백그라운드 태스크 (`_bg_cache_cleanup`) 미구현 주장 해명**:
  * 리뷰어가 `main.py`를 확인하지 못해 미구현으로 추정하였으나, 실제 `main.py:54-70`의 `@app.on_event("startup")` 내에서 `clean_invalid_cached_chapters`와 `clean_invalid_cached_outlines`가 비동기 백그라운드 태스크로 완벽히 작동 중임을 확인.
* **에스컬레이션 프롬프트 3배 누적 팽창 주장 해명**:
  * 원본 불변 객체인 `base_system_prompt`에 당회차 `escalation`만 결합하므로 재시도가 발생해도 프롬프트가 3배로 불어나지 않음을 규명.

---

## 3. Notion 버그 리포트 관리 현황

규칙(`notion_bug_reporting.md`)에 따라 모든 버그 리포트는 Notion에 공식 기록되어 관리됩니다.

| 리포트 제목 | 상태 | Notion ID / 링크 |
| :--- | :--- | :--- |
| 디스크 목차 캐시 오염 및 디폴트 타이틀로 인한 구버전 문장/할루시네이션 이슈 | **`Resolved`** ✅ | `3d7a8db0-3fbe-810b-8e5b-db770963eadb` |
| 챕터 헤더 중복 렌더링 및 비상 안전망 휴리스틱 IT 편향 문구 노출 이슈 | **`Resolved`** ✅ | `3d7a8db0-3fbe-81a9-968d-eb120af2bc3a` |
| 유튜브 웹 스크랩 UI 잡음 및 영문 에러 메시지 본문 노출 이슈 | **`Resolved`** ✅ | `3d8a8db0-3fbe-8171-8f36-da44fd79e135` |
| 목차 안전망의 맹탕 질문형 챕터명 및 본문 내 기계적 주어 반복 노출 이슈 | **`In Progress`** 🔄 | [Notion 페이지 바로가기](https://app.notion.com/p/Bug-Report-In-Progress-3d8a8db03fbe819f905cc0db1a3fee43) |

> **주의**: 노션 버그 리포트 규칙상 사용자가 명시적으로 "해결 확인/해결 완료"라고 피드백하기 전까지는 절대로 상태를 `Resolved`로 변경하지 않고 `In Progress`를 유지해야 합니다.

---

## 4. 운영 환경 배포 및 명령어 가이드

### 4.1 로컬 검증 완료 상태
* **백엔드 컴파일 검증 완료**: `tasks.py`, `chapter.py`, `outline.py`, `validators.py`, `chapter_guide.py` (Exit code 0)
* **프론트엔드 Turbopack 빌드 완료**: `cd frontend && npm run build` (Exit code 0)

### 4.2 Git 커밋 및 Vercel 자동 배포
```bash
git add .
git commit -m "fix(pipeline): remove IT bias in fallback synthesis, inject raw_title to outline/chapter prompts, strengthen korean validation"
git push origin main
```

### 4.3 AWS EC2 운영 서버 배포 명령어
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

## 5. 다음 세션 인수인계 지침

1. **새 세션 시작 시**:
   * 본 `handover.md`를 최우선으로 검토하고 이전 작업 맥락과 현재 진행 상태를 사용자에게 브리핑한 후 작업을 개시할 것.
2. **`In Progress` 리포트 확인**:
   * 현재 `[Bug Report] 목차 안전망의 맹탕 질문형 챕터명 및 본문 내 기계적 주어 반복 노출 이슈`가 `In Progress` 상태입니다.
   * 사용자가 실제 웹 서비스에서 새로 생성된 가이드를 확인하고 피드백을 주면, 사용자의 승인에 따라 해당 노션 페이지의 상태를 `Resolved`로 업데이트할 것.
3. **코드 수정 시 필수 원칙 준수**:
   * 한국어 응답 원칙 준수.
   * 모든 수정 후 TypeScript / Python 에러 체크 필수.
   * 널/예외 처리 강화 (네트워크 단절, 외부 API 에러, 모델 파싱 실패 시 서비스 다운 방지).