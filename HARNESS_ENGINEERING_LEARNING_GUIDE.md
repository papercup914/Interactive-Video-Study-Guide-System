# Harness Engineering 학습 가이드 & 미성년자 학습 도구 피벗 전략

> **생성일**: 2026-08-04  
> **출처**: Hermes Agent 대화 세션 2건 종합  
> **프로젝트**: Interactive Video Study Guide System

---

## 📚 Part 1: Harness Engineering 완전 학습 가이드

### 1. 이론-코드 1:1 매핑: 체크포인팅 (토큰/시간 증발 방지)

#### 이론 (HARNESS_ARCHITECTURE.md:13-18)
> **Solution**: Intermediate checkpointing (SQLite) saves completed chapters instantly, ensuring the process resumes exactly where it failed.

#### 실제 구현 코드 (3개 파일 연동)

**1️⃣ DB 모델** (`backend/data/models.py:18-24`)
```python
class JobCheckpoint(Base):
    __tablename__ = "job_checkpoints"
    job_id = Column(String, primary_key=True)
    section_title = Column(String, primary_key=True)
    content = Column(Text)
    created_at = Column(String, default=lambda: datetime.now().isoformat())
```

**2️⃣ 저장/조회 함수** (`backend/services/job_manager.py:109-122`)
```python
def save_chapter_checkpoint(job_id: str, section_title: str, content: str) -> None:
    with SessionLocal() as db:
        checkpoint = db.query(JobCheckpoint).filter(
            JobCheckpoint.job_id == job_id, 
            JobCheckpoint.section_title == section_title
        ).first()
        if checkpoint:
            checkpoint.content = content
        else:
            checkpoint = JobCheckpoint(job_id=job_id, section_title=section_title, content=content)
            db.add(checkpoint)
        db.commit()  # 즉시 커밋

def get_completed_chapters(job_id: str) -> Dict[str, str]:
    with SessionLocal() as db:
        checkpoints = db.query(JobCheckpoint).filter(
            JobCheckpoint.job_id == job_id
        ).all()
        return {cp.section_title: cp.content for cp in checkpoints}
```

**3️⃣ 파이프라인 활용** (`backend/services/tasks.py:112-138`)
```python
async def process_section(idx: int, section_title: str):
    # 체크포인트 확인 - 이미 했으면 API 호출 안 함!
    if section_title in completed_chapters:
        print(f"[Harness] Checkpoint loaded for {section_title}, skipping API call.")
        document[section_title] = completed_chapters[section_title]
        return
    
    content = await async_generate_chapter_content(...)
    if content:
        document[section_title] = content
        save_chapter_checkpoint(job_id, section_title, content)  # 즉시 저장
```

#### 동작 시나리오
```
10개 챕터 중 7번째에서 프로세스 강제 종료 → 재시작 시
→ Chapter 1~6: DB에서 로드, API 호출 0회, 토큰 0원
→ Chapter 7~10: 정상 생성
```

---

### 2. 이론-코드 1:1 매핑: Defensive Parsing (방어적 파싱)

#### 이론 (HARNESS_ARCHITECTURE.md:20-25, 92-104)
> LLMs do not always follow instructions perfectly. They may drop closing tags, output malformed JSON, or inject hallucinated text.
> **Solution**: Defensive Parsing and React ErrorBoundaries at the frontend layer to sanitize and isolate corrupted outputs.

#### 실제 구현: `getProcessedMarkdown()` 5단계 방어 로직 (`frontend/src/app/guide/[jobId]/page.tsx:640-727`)

**1️⃣ 한국어 조사 붙은 마크다운 마커 보정**
```typescript
processed = processed.replace(/(\*\*|__|\*|_)(?=[가-힣])/g, '$1<!-- -->');
// **내용 → **<!-- -->내용
```

**2️⃣ 커스텀 태그 공백 정규화**
```typescript
tagsToProcess.forEach(tag => {
    processed = processed.replace(new RegExp(`<\\s*${tag}\\s*>`, 'gi'), `<${tag}>`);
    processed = processed.replace(new RegExp(`</\\s*${tag}\\s*>`, 'gi'), `</${tag}>`);
});
// < feynman > → <feynman>
```

**3️⃣ 닫히지 않은 태그 강제 닫기**
```typescript
tagsToProcess.forEach(tag => {
    if (processed.includes(`<${tag}>`) && !processed.includes(`</${tag}>`)) {
        processed += `\n</${tag}>`;
    }
});
```

**4️⃣ 태그 내부 JSON 문법 보정**
```typescript
jsonContent = jsonContent.replace(/,\s*([\]}])/g, '$1');  // trailing comma 제거
if (tag === 'quiz' && !jsonContent.startsWith('[') && jsonContent.includes('{')) {
    jsonContent = `[${jsonContent}]`;  // 객체→배열 강제 변환
}
```

**5️⃣ 사용자 노트(<mark>) 안전한 주입 (XSS 방지)**
```typescript
processed = processed.replace(/<\/?mark[^>]*>/gi, '');  // 기존 mark 제거
const escaped = note.selected_text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
// 이스케이프 후 안전한 <mark> 주입
```

#### 복구 전후 비교
```
LLM 출력 (깨짐)                    →  복구 후 (렌더링 가능)
< feynman >                       →  <feynman>
{ "key": "value", }               →  { "key": "value" }
<quiz>{...}</quiz>                →  <quiz>[{...}]</quiz>
**내용                            →  **<!-- -->내용
```

---

### 3. Harness 3계층 아키텍처 요약

| 계층 | 컴포넌트 | 핵심 역할 |
|------|----------|----------|
| **Frontend** | ErrorBoundary | 컴포넌트 트리 격리, 전체 화면 죽음 방지 |
| **Frontend** | LocalStorage 캐싱 | Stale-While-Revalidate, 즉시 로드 |
| **Frontend** | Defensive Parsing | 깨진 HTML/JSON 강제 수리 |
| **Backend** | SQLite Checkpointing | 챕터 단위 영구 저장, 재개 지원 |
| **Backend** | Tenacity Retry | 지수 백오프(4s→8s→16s→30s) 자동 재시도 |
| **Backend** | Fallback Router | Gemini 실패 시 GPT-4o로 투명 전환 |
| **Backend** | Pydantic Structured Output | JSON Schema 강제, 출력 검증 자동화 |
| **External** | Context Caching (Gemini) | 대용량 문서 토큰 75% 절감 |
| **External** | Map-Reduce | 20K자 이상 자동 청크 병렬 요약 |

---

### 4. 복잡도 분담표: "한 번만 생각하고 시스템에 박아넣기"

| 영역 | 누가 생각함? | 빈도 |
|------|-------------|------|
| JSON Schema 설계 | 백엔드 개발자 | 프로젝트당 1~2회 |
| 프롬프트 출력 규칙 | 프롬프트 엔지니어 | 태그 타입당 1회 |
| Defensive Parser 작성 | 프론트엔드 개발자 | **프로젝트당 1회** |
| 새 태그 추가 시 | 담당 개발자 | `tagsToProcess`에 문자열 1개 추가 (10초) |
| 실행 시 매번 | **시스템 (자동)** | 0초 생각 |

---

## 🎯 Part 2: 미성년자 학습 보조 도구 피벗 전략

### 1. 타겟 재정의 (현실적)

| 구분 | 기존(과대) | 변경(현실) |
|------|-----------|-----------|
| **주 사용자** | 초등 4학년~박사 | **초등 고학년~고등학생(보호자/교사 동반)** |
| **역할** | 단독 교사 대체 | **보조 교재 + 학습 코치 + 진단 도구** |
| **목표** | 박사학위 도달 | **교과/자율학습 효율화, 자기주도학습 습관 형성** |
| **필수 조건** | 없음 | **보호자/교사 모니터링 계정 필수** |

---

### 2. 미성년자 특화 적용 가능 학습법 7가지

| # | 학습법 | 이론적 기반 | 적합성 | 구현 난이도 |
|---|--------|------------|--------|------------|
| **1** | **스캐폴딩(Scaffolding)** | 비고츠키 ZPD | ⭐⭐⭐⭐⭐ | 중 |
| **2** | **마스터리 러닝(Mastery Learning)** | 블룸 완전학습 | ⭐⭐⭐⭐⭐ | 중하 |
| **3** | **간격 반복(Spaced Repetition)** | 에빙하우스 망각곡선 | ⭐⭐⭐⭐⭐ | 중 |
| **4** | **게이미피케이션 + SDT** | 자기결정성이론 | ⭐⭐⭐⭐ | 중 |
| **5** | **듀얼 코딩(Dual Coding)** | 파비오 | ⭐⭐⭐⭐ | 중상 |
| **6** | **Thinking Aloud + 메타인지** | 플라벨 | ⭐⭐⭐⭐ | 중 |
| **7** | **프로젝트 기반 학습(PBL)** | 듀이/현대 PBL | ⭐⭐⭐ | 상 |

---

### 3. 아키텍처 추가 요구사항

#### 3.1 계정/권한 시스템 (필수)
```python
# backend/models.py 추가
class User(Base):
    id = Column(String, primary_key=True)
    role = Column(Enum('student', 'parent', 'teacher'))
    parent_id = Column(String, ForeignKey('users.id'), nullable=True)
    grade_level = Column(Integer)
    learning_profile = Column(JSON)

class LearningSession(Base):
    student_id = Column(String, ForeignKey('users.id'))
    guide_id = Column(String)
    mastery_scores = Column(JSON)
    interaction_log = Column(JSON)  # 클릭, 체류시간, 힌트 사용
```

#### 3.2 보호자/교사 대시보드 (신규 페이지)
```
기능:
├── 실시간 진행률 (챕터 완료, 퀴즈 정답률)
├── 약점 분석 (오답 패턴, 소요 시간 과다 구간)
├── 학습 습관 리포트 (주간/월간)
├── 개입 알림 (3일 미접속, 정답률 50% 미만, 힌트 과다)
└── 목표 설정/보상 승인
```

#### 3.3 적응형 난이도 엔진
```python
# backend/services/adaptive_engine.py
class AdaptiveEngine:
    difficulty_levels = ['scaffolded', 'guided', 'independent', 'challenge']
    
    def get_next_difficulty(self, student_id: str, concept_id: str) -> str:
        # IRT 기반 능력치 추정 → ZPD 내 난이도 반환
        pass
    
    def generate_scaffolded_content(self, base_content: str, level: str) -> str:
        templates = {
            'scaffolded': "단계별 힌트, 핵심 용어 볼드, 예시 3개+",
            'guided': "생각 질문 2-3개, 부분 풀이",
            'independent': "원본 콘텐츠",
            'challenge': "심화 문제, 역질문, 적용 과제"
        }
        # LLM으로 변환
        pass
```

#### 3.4 마스터리 루프 + 간격 반복
```python
# backend/services/mastery_loop.py
class MasteryLoop:
    MASTERY_THRESHOLD = 0.85
    SPACED_INTERVALS = [1, 3, 7, 14, 30]  # FSRS 기반
    
    async def process_interaction(self, student_id: str, concept_id: str, 
                                   interaction: Interaction) -> NextAction:
        mastery = self.update_mastery(student_id, concept_id, interaction)
        
        if mastery >= self.MASTERY_THRESHOLD:
            await self.schedule_reviews(student_id, concept_id, self.SPACED_INTERVALS)
            return NextAction.NEXT_CONCEPT
        
        if interaction.hint_used > 2 or interaction.time_exceeded:
            return NextAction.INCREASE_SCAFFOLDING
        
        return NextAction.RETRY_SAME_LEVEL
```

#### 3.5 게이미피케이션: SDT 기반 설계
| 심리적 욕구 | 구현 요소 |
|------------|----------|
| **자율성** | 학습 경로 선택, 난이도 자율 조절, 목표 직접 설정 |
| **유능감** | 마스터리 뱃지, 실시간 피드백, 성장 그래프 |
| **관계성** | 보호자 응원 메시지, 또래 그룹(익명), 선생님 코멘트 |

---

### 4. 필요 기술 스택 추가

| 영역 | 기술 | 용도 |
|------|------|------|
| **인증/권한** | NextAuth.js / Clerk / Supabase Auth | RBAC |
| **실시간** | Socket.io / Supabase Realtime | 보호자 알림, 동시 세션 |
| **분석/리포트** | Apache ECharts / Recharts + puppeteer | 주간 리포트 PDF 자동 생성 |
| **스케줄러** | Celery Beat / APScheduler | 복습 알림, 주간 리포트 발송 |
| **TTS/STT** | Web Speech API / ElevenLabs / Whisper | 저학년 읽기 지원, 음성 답변 |
| **지식 그래프** | NetworkX / Neo4j (나중) | 개념 선행 관계, 학습 경로 추천 |
| **IRT/심리측정** | `pyirt` / 맞춤 구현 | 숙달도 정밀 추정, 문항 난이도 보정 |

---

### 5. 단계적 구현 로드맵 (6개월)

| 단계 | 기간 | 핵심 구현 | 산출물 |
|------|------|-----------|--------|
| **1단계: 기반** | 1-2개월 | 계정 시스템(RBAC), 보호자 연결, 세션 로깅 | 보호자 대시보드 MVP |
| **2단계: 적응형** | 2-3개월 | 난이도 조절 엔진, 스캐폴딩 템플릿, 마스터리 루프 | "내 수준에 맞춤" 체감 |
| **3단계: 진단/복습** | 3-4개월 | 진단 평가, 간격 반복 스케줄러, 약점 분석 | "구멍 메우기" 자동화 |
| **4단계: 동기/사회** | 4-5개월 | 뱃지/보상, 보호자 응원, 주간 리포트 PDF | 지속률 ↑, 재방문 ↑ |
| **5단계: 접근성** | 5-6개월 | TTS, 음성 입력, 큰 글자/고대비 모드 | 저학년/장애학생 지원 |
| **6단계: 고도화** | 6개월+ | 지식 그래프 경로 추천, IRT 정밀화, PBL 템플릿 | "진짜 튜터" 수준 |

---

### 6. 꼭 피해야 할 함정 (미성년자 대상)

| 함정 | 위험성 | 대안 |
|------|--------|------|
| **"AI가 다 가르쳐줌" 마케팅** | 보호자 방임 유도 | **"보조 도구" 명시, 보호자 가이드 필수** |
| **데이터 수집 과다** | 아동 개인정보보호법 위반 | **최소 수집, 보호자 동의 필수, 익명화** |
| **게이미피케이션 과도** | 외적 동기만 강화 → 내재 동기 훼손 | **보상은 '인정/성장' 중심, 물질 보상 최소화** |
| **난이도 자동 낮춤만 함** | 도전 회피 학습 | **ZPD 내 '적절한 어려움' 유지, 도전 모드 별도** |
| **콘텐츠 필터링 없음** | 부적절 출력, 편향, 환각 노출 | **출력 전 필터링 레이어, 보호자 신고 기능** |

---

## 💡 한 줄 요약

> **"초등 4학년이 혼자 박사 되는 도구" → "보호자/교사와 함께 쓰는, 진단·적응·복습·동기까지 갖춘 스마트 보조교재"**

**핵심 피벗 포인트 2가지:**
1. **"혼자 하게 두지 않는다"** - 보호자/교사 루프 필수화
2. **"진단→처방→복습 루프 자동화"** - 마스터리 러닝 + 간격 반복 + 적응형 난이도

---

## 📎 참고: 현재 프로젝트 강점 (그대로 활용 가능)

- ✅ Harness Engineering 아키텍처 (체크포인트, 폴백, 구조화 출력)
- ✅ Pydantic + JSON Schema 강제 출력 검증
- ✅ Gemini Context Caching + Map-Reduce 비용 최적화
- ✅ 인지 라우팅 태그 (<feynman>, <steptracer>, <mnemonic>, <procedure>)
- ✅ Defensive Parsing + ErrorBoundary 프론트엔드 방어막
- ✅ LLM Wiki / 에이전트 협업 인프라

> 이 인프라 위에 **"계정 시스템 + 보호자 대시보드 + 적응형 엔진 + 진단/복습 루프"**만 얹으면 미성년자 대상 제품으로 즉시 출시 가능합니다.