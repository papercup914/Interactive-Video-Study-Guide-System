# Interactive Video Study Guide System — 전체 코드 리뷰

**리뷰 일시**: 2026-09-03  
**브랜치**: main  
**커밋**: 54affd9 (fix: prioritize video metadata, prevent junk transcript, and add chronological outline guardrail)

---

## 아키텍처 개요
- **Backend**: FastAPI + Celery + Redis + SQLAlchemy (SQLite/PostgreSQL)
- **Frontend**: Next.js 16 + React 19 + Tailwind CSS 4 + TypeScript
- **주요 기능**: YouTube/문서 → 9종 프리셋(3×3) 학습 가이드 자동 생성, 인터랙티브 위젯(파인만/퀴즈/단계추적/연상/절차), 배치 사전 생성, 동기화

---

## 🔴 Critical Issues (즉시 수정 필요)

### 1. `backend/services/llm.py` — Gemini Context Caching 버그 (Line 106-124)
```python
def get_or_create_document_cache(file_name: str, model_id: str):
    # ...
    uploaded_file = client.files.get(name=file_name)  # ❌ 파일이 없을 때 예외 처리 없음
```
- **문제**: 업로드되지 않은 파일에 `files.get()` 호출 시 404 발생 → 전체 파이프라인 중단
- **수정**: `try/except`로 감싸고 없으면 업로드하거나 캐시 생성을 건너뛰도록 처리

### 2. `backend/services/video.py` — 하드코딩된 API 키 (Line 189)
```python
api_key="***"  # ❌ 실제 키가 아닌 플레이스홀더
```
- **문제**: `INNERTUBE_API_KEY` 추출 실패 시 무효 키로 요청 → 400 에러
- **수정**: 기본 키 제거하고 추출 실패 시 바로 다음 클라이언트로 폴백

### 3. `frontend/src/app/guide/[jobId]/page.tsx` — 중복 로컬스토리지 쓰기 (Line 732-733)
```typescript
localStorage.setItem(`harness_guide_${jobId}`, JSON.stringify(data))
localStorage.setItem(`harness_guide_${jobId}`, JSON.stringify(data))  // ❌ 중복
```

### 4. `backend/services/tasks.py` — `profile_result` 스코프 버그 (Line 244)
```python
pm = profile_result.get("profile_message", "") if 'profile_result' in locals() else ""
```
- **문제**: `is_document=True` 분기에서는 `profile_result` 정의되지 않음 → `locals()` 체크로 우회하지만 논리적 결함
- **수정**: 분기 바깥에서 `profile_result = {}`로 초기화

### 5. `backend/services/llm.py` — `clean_invalid_cached_chapters` 시작 시 호출 비용 (main.py Line 55-63)
- **문제**: 앱 시작마다 전체 캐시 디렉토리 스캔 → 지연 시간 증가
- **수정**: 비동기 백그라운드 태스크로 이관하거나 주기적 크론으로 이동

---

## 🟠 High Priority Issues

### 6. `backend/services/llm.py` — `generate_outline` 비디오 챕터 번역 프롬프트 문제 (Line 363-364)
```python
context_data = "이 영상의 스크립트 내용은 위의 챕터 제목을 번역하기 위한 컨텍스트입니다."
```
- **문제**: 실제 스크립트를 버리고 가짜 컨텍스트 전달 → 챕터 제목 번역 품질 저하
- **수정**: 원본 스크립트 일부(처음 5000자 등)를 컨텍스트로 전달

### 7. `backend/services/batch_generator.py` — Rate Limit 방지용 고정 슬립 (Line 287)
```python
await asyncio.sleep(2.0)
```
- **문제**: 비디오 수 × 2초 = 최대 60초 지연, 실제 API 한도에 맞지 않음
- **수정**: 토큰 버킷/슬라이딩 윈도우 기반 동적 백오프 구현

### 8. `frontend/src/app/guide/[jobId]/page.tsx` — `getProcessedMarkdown` 중복/과도한 정규식 (Line 1026-1154)
- 100줄 넘는 정규식 처리가 매 렌더마다 실행 → 대용량 가이드에서 렉 유발
- **수정**: 메모이제이션(`useMemo`) 적용 및 파싱 로직을 워커/별도 유틸로 분리

### 9. `backend/services/video.py` — `_fetch_innertube_captions` 과도한 중첩 try/except (Line 173-308)
- 4개 클라이언트 × 3단계 폴백 = 12단계 중첩 → 디버깅/유지보수 어려움
- **수정**: 파이프라인 패턴으로 리팩토링 (`for client in clients: for strategy in strategies:`)

### 10. `backend/routers/admin.py` — 하드코딩된 모의 데이터 (Line 20-142)
- **문제**: 운영 대시보드에 실제 로그 대신 시드 데이터 반환
- **수정**: 실제 DB/로그 집계 쿼리로 교체 또는 명확히 `mock` 플래그 추가

---

## 🟡 Medium Priority Issues

### 11. `backend/services/llm.py` — 프롬프트 템플릿 하드코딩 (Line 704-790)
- 100줄 넘는 시스템 프롬프트가 함수 내에 인라인으로 존재 → 수정/테스트 어려움
- **권장**: 별도 `.txt`/`jinja2` 템플릿 파일로 분리

### 12. `frontend/src/app/page.tsx` — `GroupedGuideCard` 내부 상태 과다 (Line 222-224)
```typescript
const [selectedLength, setSelectedLength] = useState<string>("아주 상세하게");
const [selectedAnalogy, setSelectedAnalogy] = useState<string>("풍부한 비유");
const [showMatrix, setShowMatrix] = useState<boolean>(false);
```
- 각 카드마다 독립 상태 → 10개 카드면 30개 상태 객체, 리렌더링 낭비
- **수정**: 부모에서 단일 상태 관리 후 props 전달

### 13. `backend/services/job_manager.py` — `get_all_presets_for_video` N+1 쿼리 (Line 487-516)
```python
guides = db.query(StudyGuide).all()  # ❌ 전체 로드 후 파이썬 필터링
```
- **수정**: SQLAlchemy 필터(`extract_video_id` 함수 인덱스 또는 `video_id` 컬럼 추가)로 DB 단에서 필터링

### 14. `backend/data/models.py` — `created_at` String 타입 (Line 16, 38, 66, 83)
- **문제**: 정렬/범위 쿼리 시 문자열 비교 → ISO 포맷 의존, 타임존 문제
- **수정**: `DateTime(timezone=True)` 타입 사용

### 15. `frontend/src/components/markdown/` — 위젯 컴포넌트 간 중복 로직
- `MDXFeynman`, `MDXStepTracer`, `MDXMnemonic`, `MDXProcedure` 모두 유사한 JSON 파싱/에러 바운더리 패턴 반복
- **수정**: 공통 베이스 컴포넌트(`MDXInteractiveBase`) 추출

### 16. `requirements.txt` vs `backend/requirements.txt` 의존성 불일치
- 루트: `streamlit`, `aiosqlite` / 백엔드: `fastapi`, `celery`, `sqlalchemy` 등
- **수정**: 루트 requirements 제거하거나 `backend/` 단일 진입점으로 통일

---

## 🟢 Low Priority / 개선 사항

### 17. 타입 힌트 부족
- `backend/services/llm.py`: `async_generate_chapter_content` 반환 타입 미지정
- `backend/services/video.py`: 여러 함수가 `str | None` 반환하지만 타입 힌트 불일치

### 18. 에러 메시지 한국어/영어 혼용
- 백엔드 로그는 한국어, 프론트엔드 에러는 영어/한국어 혼용 → 일관성 확보 필요

### 19. 테스트 커버리지
- `tests/test_narrative_structure.py`만 존재 → API 라우터, 배치 파이프라인, 동기화 로직 테스트 부재

### 20. 환경변수 검증 누락
- `GEMINI_API_KEY`, `SUPABASE_JWT_SECRET`, `REDIS_URL` 등 필수 변수 미설정 시 런타임 에러
- **권장**: `pydantic-settings`로 설정 검증 레이어 추가

### 21. 프론트엔드 번들 크기
- `lucide-react` 전체 import (Tree-shaking 의존) → 필요한 아이콘만 개별 import 권장
- `react-virtuoso` 무거운 의존성 → 가벼운 대안 검토

### 22. `backend/services/tasks.py` — 동시성 제한 하드코딩 (Line 169)
```python
concurrency_limit = 3
```
- **수정**: 환경변수/설정으로 외부화

---

## 📋 권장 액션 플랜

| 우선순위 | 작업 | 예상 소요 |
|-----------|------|-----------|
| **P0** | Gemini Context Caching 버그 수정 (`get_or_create_document_cache`) | 30분 |
| **P0** | 하드코딩된 Innertube API 키 제거 | 15분 |
| **P0** | `profile_result` 스코프 버그 수정 | 10분 |
| **P1** | 비디오 챕터 번역 컨텍스트 복원 | 30분 |
| **P1** | `getProcessedMarkdown` 메모이제이션 적용 | 1시간 |
| **P1** | 배치 Rate Limit 동적 백오프 구현 | 2시간 |
| **P2** | 프롬프트 템플릿 외부화 (jinja2) | 2시간 |
| **P2** | `get_all_presets_for_video` DB 필터링 최적화 | 1시간 |
| **P2** | `created_at` DateTime 타입 마이그레이션 | 1시간 |
| **P3** | 위젯 베이스 컴포넌트 추출 | 3시간 |
| **P3** | 설정 검증 레이어(`pydantic-settings`) 추가 | 2시간 |
| **P3** | 테스트 커버리지 확대 (API, 배치, 동기화) | 4시간 |

---

## ✅ 긍정적인 점 (유지/확장 권장)

1. **엄격한 서술형 검증 파이프라인** (`validate_chapter_narrative`, `sanitize_chapter_narrative`) — 품질 보장에 탁월
2. **자동 재시도/폴백 메커니즘** (Gemini ↔ OpenAI, 다중 자막 소스) — 운영 안정성 높음
3. **9종 프리셋 매트릭스 UX** — 사용자 선택권 극대화, 프론트엔드 구현 완성도 높음
4. **배치 사전 생성 + 동기화 아키텍처** — 로컬/운영 서버 분리 배포에 적합
5. **인터랙티브 위젯 4종** (Feynman/StepTracer/Mnemonic/Procedure) — 학습 효과 검증된 패턴
6. **캐시 무효화/자동 정리** (`clean_invalid_cached_chapters`) — 기술 부채 방지