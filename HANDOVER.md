# Interactive Video Study Guide System - 인수인계서 (Handover)

> **최종 갱신 일시**: 2026-09-14 (15:15 KST)  
> **작성자**: Antigravity (AI Pair Programming Assistant)  
> **문서 목적**: 다음 세션 작업자 및 사용자를 위한 프로젝트 현황, 아키텍처, 최근 해결된 버그 히스토리 및 운영 배포 인수인계

---

## 1. 프로젝트 개요 및 배포 아키텍처

Interactive Video Study Guide System은 유튜브 영상 또는 웹 문서를 분석하여, 구조화된 인터랙티브 학습 가이드(챕터별 서술형 본문, 퀴즈, 파인만 기법, 논리 트레이서, 연상기억법 등)를 자동 생성하는 AI 학습 지원 서비스입니다.

### 1.1 인프라 및 클라이언트 구성
* **Frontend (웹 클라이언트)**:
  * **호스팅**: Vercel Production
  * **프레임워크**: Next.js 16 (App Router, Turbopack, Tailwind CSS)
  * **도메인**: `https://interactive-video-study-guide-syste.vercel.app/`
  * **저장소 브랜치**: `main` (푸시 시 Vercel 자동 빌드 및 배포)
* **Mobile (안드로이드 네이티브 클라이언트)**:
  * **프로젝트 위치**: `android/`
  * **프레임워크**: Jetpack Compose, Kotlin 2.3.20, Android SDK 36 (`minSdk 24`)
  * **CI/CD 파이프라인**: GitHub Actions (`.github/workflows/android-build.yml`)
  * **생성 아티팩트**: `app-debug.apk` (약 11.9 MB)
  * **로컬 보관 위치**: `apk_output/studyguide-debug-apk/app-debug.apk`
* **Backend & Worker (AI 파이프라인)**:
  * **호스팅**: AWS EC2 (`ubuntu@13.209.73.143`)
  * **접속 키**: 프로젝트 루트 `aws/studyguide-key.pem`
  * **작업 디렉토리**: `/home/ubuntu/Interactive-Video-Study-Guide-System`
  * **컨테이너 아키텍처 (Docker Compose)**:
    * `studyguide-fastapi`: REST API 서버 (Port 8000)
    * `studyguide-celery`: 비동기 AI 파이프라인 워커 (Celery worker, 영상 다운로드/전사/목차/챕터 생성)
    * `studyguide-redis`: 메시지 브로커 및 캐시 (Port 6379)
  * **데이터베이스**: Neon Tech 클라우드 PostgreSQL (`ep-divine-frost-axkzt83r...aws.neon.tech/neondb`)

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

### 2.6 [P0 운영 배포] 관리자 대시보드(/admin) 활성화 및 EC2 백엔드 실시간 동기화
* **문제 증상**:
  1. 관리자 통합 대시보드(`https://interactive-video-study-guide-syste.vercel.app/admin`) 접속 시 404 발생.
  2. UI 진입 후 콘솔에서 `/api/admin/overview`, `/api/admin/jobs`, `/api/admin/guides` 404 에러 발생 및 PWA `manifest.json` 파싱 실패(Line 1 Syntax error) 발생.
* **원인 규명**:
  1. `frontend/src/app/admin/page.tsx` 및 `layout.tsx`가 로컬에만 존재하고 Untracked 상태여서 Vercel 배포 누락.
  2. EC2 인스턴스(`13.209.73.143`)에서 신규 추가된 `backend/routers/admin.py` 코드가 미반영되어 Docker 컨테이너가 이전 이미지로 기동 중이었음.
  3. `backend/routers/admin.py` 상단에 `Header`, `HTTPException`, `Depends`, `timezone`, `os` import 누락으로 인한 런타임 NameError.
  4. Supabase 미들웨어에서 `/manifest.json`이 미인증 사용자로 간주되어 `/login`으로 307 리다이렉트되어 HTML이 JSON 매니페스트로 전달됨.
* **해결 조치**:
  1. Git 추적 추가 및 커밋(`f62eb46`, `125f0c2`, `1f2b307`)을 통해 Vercel 및 EC2에 최신 코드 반영.
  2. EC2 SSH 원격 접속 후 `git pull origin main` 및 `./scripts/deploy_backend.sh` 실행하여 `studyguide-backend:latest` 재빌드 및 컨테이너 재가동 완료.
  3. `frontend/src/utils/supabase/middleware.ts`에 `manifest.json`, `favicon.ico`, `/icons/` 정적 자산 및 `/admin` 바이패스 추가.
  4. 실측 검증: `/api/admin/overview` 호출 시 Neon PostgreSQL(`connected`), Redis(`connected`), Celery(`active 1 worker`), Job 총 105건 데이터 정상 반환 확인.

### 2.7 [Track A 완수] Neon PostgreSQL 전환, 쿼터 배지, YouTube 싱크, 내보내기, PWA, 운영 배포 (전체 5단계 완수)
* **배경 및 목적**:
  * 기존 SQLite 단일 파일(`jobs.db`)의 동시성 락 충돌과 미인증/무제한 생성으로 인한 서버 API 키 비용 폭사 위험을 영구 차단하고, 스토어 규격(Store-Ready)과 학습자 생산성(내보내기/싱크)을 완비하기 위함.
* **작업 내용**:
  1. **Neon PostgreSQL 클라우드 DB 전환**: `docker-compose.yml`에서 SQLite 강제 설정을 제거하고 `.env`의 **Neon PostgreSQL**(`postgresql://neondb_owner:...`)을 최우선 적용.
  2. **`user_id` 모델링 및 마이그레이션**: `Job`, `StudyGuide`에 `user_id` 추가, DB 기동 시 자동 스키마 마이그레이션 적용.
  3. **일일 3회 쿼터 시스템 (`UserUsage`)**: 1인당 1일 3회 제한 (`check_and_increment_quota`), 4회차 시 `HTTP 429` 차단, BYOK 입력 시 무제한 허용.
  4. **프론트엔드 잔여 쿼터 배지 & Auth 연동**: 메인 화면 Hero 섹션에 `"오늘 무료 생성 한도: 2/3회 남음"` 배지 렌더링, `fetch("/api/guide/start")`에 Supabase JWT 토큰 연동.
  5. **상단 YouTube Player 타임스탬프 싱크 (`seekToTime`)**: HTML5 postMessage 프로토콜로 외부 라이브러리 없이 가이드 내 타임스탬프(`[02:15]`) 클릭 시 영상 해당 위치로 즉시 점프 및 재생. 구글 플레이 스토어 ToS 규정 완벽 준수.
  6. **지식 내보내기 (Export)**: 가이드 뷰어 상단에 **[MD 다운로드]** 및 **[Notion 복사]** 버튼 추가 (클릭 시 마크다운 파일 다운로드 또는 노션 최적화 클립보드 복사).
  7. **모바일 PWA 패키징**: `manifest.json`, 512x512 벡터 앱 아이콘(`icons/icon.svg`), `layout.tsx` 메타 태그 완비 (스마트폰 홈 화면 추가 시 네이티브 앱처럼 실행).
  8. **AWS EC2 운영 서버 배포 완료**: Git 푸시 ➔ EC2 원격 동기화 ➔ Docker Compose 컨테이너 리빌드 완료 (`FastAPI 200 OK`, `Celery Ready`).

### 2.7 [안드로이드 네이티브 앱] Jetpack Compose WebView 래퍼 & GitHub Actions APK 빌드 파이프라인 구축
* **배경**: 스마트폰 기기에서 웹 브라우저 주소창 없이 네이티브 앱 환경으로 학습하고, 하드웨어 뒤로가기 제어 및 마크다운 파일 다운로드를 지원하기 위함.
* **구현 내용**:
  1. **네이티브 안드로이드 프로젝트 신설 (`android/`)**:
     * Jetpack Compose + 최신 Android SDK 36 (`minSdk 24`, `namespace: com.example.studyguide`).
     * `MainActivity.kt`: 프로덕션급 WebView 래퍼 구현 (하드웨어 뒤로가기 `BackHandler`, 상단 로딩 프로그레스바 `LinearProgressIndicator`, 쿠키 및 로컬스토리지 완벽 유지).
     * **안드로이드 시스템 다운로드 매니저(`DownloadManager`) 연동**: 가이드 뷰어의 [MD 다운로드] 버튼 클릭 시 모바일 기기 내부 `Download/` 폴더에 즉시 파일 저장.
     * **네트워크 권한**: `AndroidManifest.xml`에 `INTERNET`, `ACCESS_NETWORK_STATE` 선언.
  2. **GitHub Actions 클라우드 APK 빌드 자동화 (`.github/workflows/android-build.yml`)**:
     * 코드 푸시 시 `ubuntu-latest`, Temurin JDK 17, `setup-android` 환경에서 `./gradlew assembleDebug` 자동 실행.
     * 빌드 성공 시 `studyguide-debug-apk` 아티팩트(`app-debug.apk`) 자동 생성 및 즉시 다운로드 제공.
  3. **컴파일 에러 해결 및 빌드 완수**:
     * `CookieManager.setAcceptThirdPartyCookies` 매개변수 불일치 오류 픽스 (`b8df306`).
     * GitHub Actions 클라우드 빌드 성공 (Build #34767765608).
     * 로컬 테스트용 APK 파일 수령 완료: `apk_output/studyguide-debug-apk/app-debug.apk` (약 11.9 MB).
     * `.gitignore`에 APK 및 빌드 캐시 디렉토리 등록 (`684aa31`).

### 2.8 [개발자용 관리 페이지 C안] 통합 관리자 대시보드 허브(`/admin`) 구축 및 패스코드(A안) 보안 가드 완비
* **배경**:
  * 기존 `/admin/batch`(일괄 생성)와 `/admin/health`(로그 모니터링)로 분산되어 있던 관리 도구를 일원화하고, 비인가자의 DB 임의 조작 방지를 위한 보안 인증 및 실시간 Celery/쿼터 제어 포털 구축.
* **구현 내용**:
  1. **A안 패스코드(Secret Key) 인증 가드 (`/admin/layout.tsx`)**:
     * 비인가 접근 차단 모달, 로컬스토리지 보관 및 모든 API 헤더(`X-Admin-Secret`) 자동 주입.
     * 상단 네비게이션에 [대시보드 허브], [일괄 생성], [시스템 헬스], [잠금/로그아웃] 일관 적용.
  2. **메인 관리자 대시보드 허브 (`/admin/page.tsx`)**:
     * **인프라 헬스 실시간 Ping**: Neon PostgreSQL, Redis, Celery Worker 상태 감지.
     * **핵심 지표 요약**: 총 가이드 수, 오늘 생성 요청 수, 실시간 대기 작업, 실패율.
     * **작업 & 큐 탭 (`jobs`)**: 실시간 Job 목록, 상태별 필터링, 실패 작업 [1-Click 재시도], 진행 중 작업 [강제 취소], [삭제], 에러 스택 트레이스 모달.
     * **사용자 쿼터 탭 (`quota`)**: 당일 사용자별 사용량(`UserUsage`) 실시간 조회 및 [⚡ 0회로 초기화(Reset)] 지원.
     * **학습 가이드 DB 탭 (`guides`)**: 저장된 가이드 검색, [뷰어로 열기], [삭제].
  3. **백엔드 관리자 API 신설 (`routers/admin.py`, `job_manager.py`)**:
     * `verify`, `overview`, `jobs(list/retry/cancel/delete)`, `users/usage`, `reset-quota`, `guides(list/delete)` 완비.
* **검증 결과**:
  * 백엔드 단위 테스트 `tests/test_admin_c_plan.py` (3개 테스트 전체 통과, Exit code 0).
  * 프론트엔드 Next.js 프로덕션 빌드 (`npm run build`) 무결점 성공 (Exit code 0).

### 2.9 [관리자 포털] 학습 가이드 생성 매커니즘 제어 포털(/admin/generation-config) 구축 완비
* **배경 및 목적**:
  * 기존에는 AI 모델, 목차 생성 알고리즘, 서술형 본문 지침, 4대 위젯, 한글 검증 임계치 등의 파라미터가 소스 코드에 고정되어 있어, 수정 시마다 재배포가 필요했던 한계를 영구 해결하고, 관리자가 웹 UI에서 모든 매커니즘을 실시간 제어할 수 있도록 구축.
* **구현 내용**:
  1. **Neon PostgreSQL DB 영속화 (`models.py`, `pipeline_config.py`)**:
     * `SystemConfig` 모델 신설 및 자동 테이블 마이그레이션 (`_ensure_table`).
     * AI 모델(Gemini/GPT/Groq), 목차 규칙, 본문 서술 지침, 4대 위젯, 품질 검증 가드레일, 자막 수집 파이프라인의 통합 스키마 관리.
     * 3대 추천 프리셋 시스템 (🎯 표준 균형 모드, ⚡ 초고속 경량 모드, 🔬 학술/심화 연구 모드).
     * 인메모리 캐시(TTL 30초) + DB Fallback 안전망으로 무중단 서비스 보장.
  2. **관리자 REST API 신설 (`backend/routers/admin.py`)**:
     * `GET /api/admin/pipeline/config`: 설정 및 프리셋 조회
     * `PUT /api/admin/pipeline/config`: 실시간 설정 저장 및 DB 반영
     * `POST /api/admin/pipeline/reset`: 표준 기본값으로 1-Click 리셋
     * `POST /api/admin/pipeline/apply-preset`: 추천 프리셋 즉시 적용
     * `POST /api/admin/pipeline/test-simulate`: 관리자용 실시간 샌드박스 시뮬레이터 API
  3. **프론트엔드 전용 제어 센터 (`/admin/generation-config/page.tsx`)**:
     * 상단 헤더 네비게이션에 [생성 매커니즘 제어] 탭 연동 (`layout.tsx`).
     * 관리자 대시보드 허브에 퀵 배너 연동 (`admin/page.tsx`).
     * 6대 탭 인터페이스:
       * 🤖 **AI 모델 & 엔진**: Primary LLM, Concurrency(1~8), Temperature, Max Tokens, Timeout, Retries
       * 📑 **목차 설계 규칙**: 공식 챕터 파싱 토글, 각색 스타일(호기심/인사이트/직역), 시간 순서 엄격 강제, 스마트 슬라이싱 윈도우
       * ✍️ **본문 서술 & 프롬프트**: 제로-인사말 강제 토글, 100% 한국어 서술 토글, 금지어 에디터, 튜터 페르소나
       * 🧩 **인터랙티브 위젯**: 4대 위젯(파인만, 논리트레이서, 연상기억, 절차) 스위치, 부착 방식(AI 자동 1개 / 전체 / 끔)
       * 🛡️ **품질 검증 가드레일**: 최소 글자 수, 한글/영문 비율 임계치, 에스컬레이션 재시도 토글 및 프롬프트 편집기
       * 🧪 **실시간 테스트 랩 (Playground)**: 목차 추출 및 단일 챕터 생성을 즉석 테스트하고 소요 시간 및 가드레일 통과 여부 확인
* **검증 결과**:
  * 백엔드 단위 테스트 `tests/test_pipeline_config.py` (6개 테스트 100% 통과, Exit code 0).
  * 기존 관리자 테스트 `tests/test_admin_c_plan.py` 회귀 테스트 통과 (Exit code 0).
  * Next.js 프로덕션 빌드 (`npm run build`) 무결점 성공 (Exit code 0).

### 2.10 [음성 파일 지원 & 회의록 생성 파이프라인] 사운드 파일(MP3/WAV/M4A 등) 업로드 및 전문 비즈니스 회의록 생성 메커니즘 구축
* **배경 및 목적**:
  * 기존 유튜브 영상/웹 문서 중심의 파이프라인에서 확장하여, 사용자가 직접 녹음한 음성 파일(회의, 통화, 인터뷰, 세미나 등)을 업로드하고 텍스트로 변환 및 요약할 수 있는 기능을 요청받음.
  * 사운드 파일의 경우 챕터 퀴즈나 파인만 기법 위주의 학습 가이드가 부적합하므로, 핵심 결정 사항(Key Decisions)과 액션 아이템(Action Items Table & Checklist), 원문 전사본을 포함하는 **전문 비즈니스 회의록(Meeting Minutes)** 생성 메커니즘을 신설.
* **구현 내용**:
  1. **전문 회의록 시스템 프롬프트 (`backend/prompts/meeting_minutes.py`)**:
     * 100% 한국어 비즈니스 어조, 인사말/서두/결미 멘트 100% 배제.
     * 5단계 구조화 출력 규격 강제:
       - `## 1. 회의 개요 및 핵심 요약 (Executive Summary)`: 일시, 안건/주제, 3줄 핵심 요약.
       - `## 2. 주요 논의 내용 (Key Discussions)`: 안건별 핵심 논의 및 쟁점 사항.
       - `## 3. 핵심 결정 사항 (Key Decisions)`: 합의된 사항 및 보류/기각 사항.
       - `## 4. 실행 과제 및 액션 아이템 (Action Items)`: 담당자, 기한, 마크다운 체크리스트 및 요약 테이블.
       - `## 5. 주요 위험 요소 및 이슈 (Risks & Open Questions)`: 잠재적 리스크 및 후속 확인 필요 항목.
  2. **회의록 LLM 생성 및 파싱 서비스 (`backend/services/llm/meeting_minutes.py`)**:
     * `generate_meeting_minutes_content`: LLM 호출 후 마크다운 섹션을 파싱하여 가이드 뷰어 호환 문서(`document`) 딕셔너리로 변환.
     * 원문 전사 전문(`Full Transcript`)을 마지막 섹션에 첨부하여 회의 참가자 발언 원문 대조 지원.
  3. **비동기 태스크 파이프라인 오디오 분기 (`backend/services/tasks.py`)**:
     * `AUDIO_EXTENSIONS` (`.mp3`, `.wav`, `.m4a`, `.aac`, `.flac`, `.ogg`, `.wma`) 감지 로직 추가.
     * 오디오 파일인 경우 `process_audio`로 Whisper STT(Gemini STT 폴백) 수행 후, `generate_meeting_minutes_content`를 거쳐 즉시 완료 처리(`save_study_guide(length_preset="전문 회의록", analogy_preset="비즈니스 액션 플랜", ...)`).
  4. **프론트엔드 업로드 UI 및 회의록 모드 감지 (`frontend/src/app/page.tsx`)**:
     * 파일 입력 `accept` 속성에 `.mp3,.wav,.m4a,.aac,.flac,.ogg,.wma` 확장자 추가.
     * 오디오 파일 감지 시 `🎙️ {filename}` 노란색 배지 렌더링 및 "회의 녹음 파일이 감지되었습니다. 전문 회의록 및 액션 아이템 모드로 생성됩니다" 안내 배너 출력.
     * 생성 버튼 텍스트가 "회의록 생성 시작"으로 자동 전환.
* **검증 결과**:
  * 백엔드 단위 테스트 `tests/test_meeting_minutes.py` (프롬프트 구성, 마크다운 파싱, 오디오 확장자 감지 3개 테스트 100% 통과).
  * 프론트엔드 프로덕션 빌드 (`npm run build`) 무결점 성공 (Exit code 0).
  * AWS EC2(`13.209.73.143`) 백엔드 Docker 컨테이너 무중단 재빌드 및 배포 완료 (`FastAPI 200 OK`, `Celery Ready`).

### 2.11 [P0 버그 픽스] 대용량 오디오 업로드 413 Payload Too Large 해결 (청크 분할 업로드 시스템 구축)
* **문제 증상**:
  * 메인 화면에서 대용량 음성 녹음 파일(MP3 등)을 첨부하고 생성을 요청했을 때 `생성 요청 실패: 서버 응답 오류 (상태 코드: 413)` 팝업 발생.
* **원인 규명**:
  * Next.js 프론트엔드가 호스팅된 Vercel Production의 Serverless/Rewrites 프록시에는 **단일 HTTP 요청 바디 4.5 MB 제한(Hard Limit)**이 존재함.
  * 브라우저가 수십 MB 오디오 파일을 `/api/guide/start`로 직접 전송하면서 백엔드(FastAPI) 도달 전 Vercel 엣지 인프라에서 `413 FUNCTION_PAYLOAD_TOO_LARGE`로 요청을 즉시 차단함.
* **해결 조치**:
  1. **백엔드 청크 수신 및 결합 엔드포인트 신설 (`backend/routers/guide.py`)**:
     * `POST /api/guide/upload-chunk`: 3MB 단위로 분할된 조각 바이너리를 `backend/tmp/chunks/{upload_id}/`에 저장하고, 마지막 청크 수신 시 단일 파일로 결합하여 `file_path` 반환.
     * `POST /api/guide/start`: `uploaded_file_paths` 수신 지원. 이미 결합된 파일 경로를 Celery 작업 큐로 즉시 전달하여 메인 요청 바디를 수백 바이트(JSON)로 경량화.
  2. **프론트엔드 브라우저 청크 분할 전송 모듈 (`frontend/src/app/page.tsx`)**:
     * `uploadFileInChunks`: `Blob.slice()`를 이용하여 3MB 조각 단위로 순차 전송.
     * 실시간 업로드 진행률(0% ~ 100%) 및 청크 조각 번호 표시 프로그레스 바 UI 렌더링.
* **검증 결과**:
  * 청크 업로드 및 무결점 결합 단위 테스트 `tests/test_chunked_upload.py` 통과 (`Ran 1 test in 0.173s, OK`).
  * 프론트엔드 빌드(`npm run build`) 무결점 성공 (Exit code 0).
  * AWS EC2(`13.209.73.143`) 백엔드 Docker 재빌드 및 무중단 배포 완료 (`FastAPI 200 OK`).

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

### 4.1 로컬 및 운영 검증 완료 상태
* **백엔드 컴파일 검증 완료**: `tasks.py`, `chapter.py`, `outline.py`, `validators.py`, `models.py`, `job_manager.py`, `auth.py`, `guide.py` (Exit code 0)
* **PostgreSQL 및 쿼터 단위 테스트 완료**: `python tests/test_track_a_neon_and_quota.py` (5개 테스트 전체 통과, Exit code 0)
* **프론트엔드 Turbopack 빌드 완료**: `cd frontend && npm run build` (Exit code 0)
* **안드로이드 클라우드 APK 빌드 완료**: GitHub Actions Build #34767765608 성공 (`app-debug.apk`, 11.9MB 생성 및 로컬 다운로드 완료)
* **AWS EC2 운영 서버 배포 완료**: FastAPI 및 Celery 컨테이너 리빌드/재기동 확인 (`13.209.73.143:8000/health` 200 OK)
* **Vercel Production 배포 완료**: `main` 브랜치 자동 배포

### 4.2 Git 배포 내역
* **최신 커밋**: `0b0efa6` (`docs(handover): update HANDOVER.md with admin dashboard and EC2 backend hotfix`)
* **관리자 및 핫픽스 관련 커밋**:
  * `1f2b307`: `fix(admin): add missing imports in admin router`
  * `125f0c2`: `fix(middleware): bypass manifest.json and static metadata to prevent PWA syntax error`
  * `f62eb46`: `fix(admin): track admin layout and main dashboard page on vercel`
  * `7f43d07`: `fix(vercel): remove cleanUrls from vercel.json to resolve /admin 404 routing conflict`
  * `5865331`: `fix(auth): allow /admin routes to bypass Supabase consumer login in middleware`
* **안드로이드 관련 커밋**:
  * `9f3575c`: `docs(handover): update handover document with Android client and APK CI pipeline`
  * `684aa31`: `chore: update .gitignore for apk_output and android build cache`
  * `b8df306`: `fix(android): resolve CookieManager webView parameter mismatch`
  * `c879637`: `feat(android): add native Android WebView wrapper and APK build workflow`
* **인프라 고도화 커밋**: `8273188` (`feat(track-a): complete store-ready infrastructure with Neon DB, quota badge, YouTube sync, Markdown export and PWA`)


---

## 5. 다음 세션 인수인계 지침

1. **새 세션 시작 시 (Track B 전담)**:
   * 본 `HANDOVER.md`를 최우선으로 검토하고 이전 작업 맥락(Track A 전체 완수 및 EC2 배포 완료)과 현재 진행 상태를 사용자에게 브리핑한 후 작업을 개시할 것.
2. **Track B 핵심 과제 착수**:
   * 현재 `In Progress` 상태인 `[Bug Report] 목차 안전망의 맹탕 질문형 챕터명 및 본문 내 기계적 주어 반복 노출 이슈`를 해결할 것.
   * `backend/services/outline.py`의 휴리스틱 질문형 목차 폴백 로직을 도메인 맞춤형 서술식 챕터명으로 전면 개편.
   * `backend/prompts/chapter_guide.py`에 `"이 영상은~"`, `"화자는~"` 등 기계적 3인칭 주어 반복 금지 가드레일 주입 및 검증.
3. **코드 수정 시 필수 원칙 준수**:
   * 한국어 응답 원칙 준수.
   * 모든 수정 후 TypeScript / Python 에러 체크 필수.
   * 널/예외 처리 강화 (네트워크 단절, 외부 API 에러, 모델 파싱 실패 시 서비스 다운 방지).