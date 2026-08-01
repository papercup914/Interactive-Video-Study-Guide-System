# Project Ideas

* What if we could generate personalized study guides tailored to individual learning styles, allowing everyone to progress through the same curriculum at a similar pace?
  <!-- [KR] 개개인별 성향에 따른 학습 가이드를 생성하여, 동일한 교육 과정을 비슷한 같은 속도로 학습할수있다면. -->

* What if, with the help of AI, human learning speed could accelerate proportionally to the advancement of AI itself, regardless of individual aptitude differences?
  <!-- [KR] AI 가 발전하는 속도 만큼, AI의 도움을 받아 인간의 학습속도도 개인의 능력차에 상관없이 빨라질수있다면. -->

---

# Refined Vision (After /grill-me Interview)

## 1. Mastery Learning vs. Standardized Pace
- **Initial Idea**: Everyone learns at a similar pace regardless of aptitude.
  <!-- [KR] 초기 아이디어: 개인 능력차와 무관하게 동일한 속도로 학습. -->
- **Refined Vision (Pivot)**: Time to complete may vary, but 100% comprehension is guaranteed for everyone. The AI acts as a relentless tutor that untangles bottlenecks, effectively equalizing *outcomes* rather than *time*.
  <!-- [KR] 개선된 비전(피벗): 완강 시간은 개인마다 다를 수 있지만, 100% 이해도를 보장. AI가 병목 지점을 끝까지 풀어주어 '시간'이 아닌 '성취도'를 평준화. -->

## 2. Dynamic, Content-Aware Assessment
- **Implementation Strategy**: Instead of one-size-fits-all quizzes, the AI dynamically selects the optimal assessment component based on the chapter's content type.
  <!-- [KR] 구현 전략: 모든 챕터에 똑같은 퀴즈를 넣는 대신, AI가 학습 내용의 성격에 따라 최적의 평가 컴포넌트를 동적으로 선택. -->

## 3. The Feynman Technique Component (Core Engine)
- **Roleplay Engine**: For deep, conceptual topics, the AI injects a `<feynman-chat>` component. The user must explain the concept to an "ignorant 12-year-old AI".
  <!-- [KR] 롤플레잉 엔진: 깊은 이해가 필요한 개념에는 `<feynman-chat>`을 삽입. 사용자가 '아무것도 모르는 12살 AI'에게 개념을 직접 설명하여 통과해야 함. -->
- **Hybrid Approach**: Simple factual knowledge is assessed using lightweight Multiple Choice/True-False `<quiz>` components to avoid user fatigue.
  <!-- [KR] 하이브리드 접근: 단순 사실 관계는 피로도를 줄이기 위해 가벼운 객관식/OX `<quiz>` 컴포넌트로 처리. -->

## 4. Automatic Prerequisite Mapping (Concept Map)
- **Idea**: When generating a new study guide, the AI constructs a prerequisite knowledge relationship (Concept Map), proactively informing the user, "To easily understand this video, you need to know Concept A that we summarized last week."
  <!-- [KR] 자동 선수학습 매핑: 새로운 가이드북을 생성할 때, "이 영상은 지난주에 정리한 A 개념을 알아야 이해하기 쉽습니다"라고 AI가 선수 지식 관계도(Concept Map)를 매핑하여 안내. -->

## 5. Loop Engineering (Critique & Revise)
- **Idea**: Introduce a multi-agent or self-reflection loop to drastically increase the quality and prevent hallucination. A lightweight evaluator model critiques the generated chapter against the transcript, forcing a rewrite if it fails the quality threshold. Deferred due to API cost and latency concerns.
  <!-- [KR] 루프 엔지니어링 (검열 및 재작성): 환각(Hallucination) 방지와 품질 극대화를 위해 경량 모델 기반의 검열관 AI를 도입. 생성된 챕터가 기준에 미달하면 재작성을 강제하는 루프 구조. 현재는 API 비용 및 대기 시간 증가 문제로 보류됨. -->
