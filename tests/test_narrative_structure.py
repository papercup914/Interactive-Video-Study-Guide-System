import os
import sys
import unittest
import tempfile
import shutil
import asyncio
from unittest.mock import patch, MagicMock

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.services.llm import (
    validate_chapter_narrative,
    clean_invalid_cached_chapters,
    async_generate_chapter_content
)

SAMPLE_RICH_NARRATIVE_FEYNMAN = """# 대형 언어 모델(LLM)의 핵심 아키텍처와 트랜스포머의 동작 원리

현대 생성형 AI의 중추적인 기둥이자 모든 대형 언어 모델(LLM)의 핵심 아키텍처인 '트랜스포머(Transformer)'의 핵심 메커니즘과 동작 원리를 심층적으로 분석합니다. 

인공지능 연구에서 과거 순환 신경망(RNN)이나 LSTM 모델들이 가졌던 가장 큰 한계는 긴 텍스트 문맥을 처리할 때 과거의 정보를 쉽게 잊어버리는 '기울기 소실(Vanishing Gradient)' 문제와 시계열 순차 처리로 인한 병렬 연산의 불가능함이었습니다. 2017년 구글의 연구진이 발표한 "Attention Is All You Need" 논문은 이러한 인공 신경망의 오랜 한계를 완전히 뒤바꾸어 놓았습니다.

### 1. 셀프 어텐션(Self-Attention): 문맥을 엮어내는 마법의 렌즈
트랜스포머의 심장부는 바로 셀프 어텐션 메커니즘입니다. 문장 내의 모든 단어가 다른 모든 단어와의 상호 연관성을 계산하여, 문맥에 따라 단어의 의미 임베딩을 유기적으로 변형시킵니다.
예를 들어 "은행에 가서 돈을 찾았다"에서의 '은행'과 "강가 은행나무 아래서 쉬었다"에서의 '은행'은 전혀 다른 의미를 지닙니다. 셀프 어텐션은 주변 단어들('돈', '강가')의 쿼리(Query), 키(Key), 밸류(Value) 벡터 간의 내적 연산을 통해 적절한 가중치를 부여함으로써 단어의 진정한 의미를 찾아냅니다.

> **💡 핵심 인사이트**
> 트랜스포머 모델의 본질은 '단어들의 동적 관계망 형성'입니다. 고정된 단어 사전의 의미가 아니라, 문맥 속에서 끊임없이 변형되는 동적 관계성을 수십억 개의 파라미터로 학습합니다.

### 2. 멀티 헤드 어텐션과 포지셔널 인코딩
하나의 어텐션만으로는 문맥의 다양한 측면(문법적 관계, 의미론적 관계, 수식 관계 등)을 동시에 포착하기 어렵습니다. 따라서 트랜스포머는 여러 개의 어텐션 헤드를 병렬로 배치하여 문장의 다양한 뉘앙스를 다각도로 분석합니다. 또한 순서 정보가 없는 행렬 연산의 특성을 보완하기 위해 사인(Sine)과 코사인(Cosine) 주기 함수를 이용한 '포지셔널 인코딩(Positional Encoding)'을 벡터에 더해줍니다.

### 3. 실무 엔지니어링 팁 & 주의사항
실제 프로덕션 환경에서 LLM 파이프라인을 구축할 때 주의할 점은 다음과 같습니다:
1. **KV 캐싱(Key-Value Caching)**: 추론 단계에서 매 토큰 생성 시 이전 계산 결과를 캐싱하여 계산 복잡도를 $O(N^2)$에서 $O(N)$으로 획기적으로 낮출 수 있습니다.
2. **컨텍스트 윈도우 관리**: 어텐션 연산은 입력 시퀀스 길이에 따라 메모리가 2차 함수($N^2$)로 급증하므로 플래시 어텐션(FlashAttention)과 같은 하드웨어 가속 알고리즘을 필히 고려해야 합니다.

<feynman>
{
  "tag_team_scenario": "당신과 제가 한 팀이 되어, 트랜스포머의 어텐션 메커니즘을 처음 접하는 컴퓨터공학과 1학년 학생에게 설명하는 상황입니다.",
  "target_persona": "기초 코딩은 알지만 인공지능 행렬 연산은 처음인 대학 신입생",
  "initial_ai_message": "자, 학생에게 어텐션을 도서관 사서에 빗대어 설명해볼까요? 사서가 책을 찾을 때 필요한 세 가지 요소가 있는데...",
  "concept_summary": "어텐션은 질문에 가장 잘 들어맞는 책의 라벨을 찾아 그 책의 실제 내용을 가져오는 검색 과정과 같습니다."
}
</feynman>"""

SAMPLE_RICH_NARRATIVE_STEPTRACER = r"""# 순전파 및 역전파 알고리즘의 단계별 연산 흐름

딥러닝의 핵심 학습 메커니즘은 입력 데이터를 받아 예측값을 계산하는 순전파(Forward Propagation)와 예측 오차를 줄이기 위해 가중치를 갱신하는 역전파(Backpropagation)의 순환 과정으로 이루어져 있습니다.

이 챕터에서는 연쇄 법칙(Chain Rule)을 기반으로 한 기울기 계산 과정을 수학적 및 코드 관점에서 단계별로 분해하여 설명합니다. 모델의 가중치 $W$와 편향 $b$가 주어졌을 때, 선형 결합 $z = Wx + b$를 거쳐 활성화 함수 $a = \sigma(z)$를 통과하는 기초 신경망 단위(Neuron)의 미분 유도 과정을 체계적으로 이해하는 것이 본 학습의 목표입니다.

과거 신경망 연구 초창기에는 다층 퍼셉트론(MLP)의 가중치를 갱신할 효율적인 수학적 해법을 찾지 못해 인공지능의 첫 번째 빙하기를 겪었습니다. 그러나 제프리 힌튼(Geoffrey Hinton)을 비롯한 연구진들이 연쇄 법칙을 바탕으로 한 오차 역전파법을 재발견하면서 딥러닝 혁명의 기틀이 마련되었습니다.

### 1. 순전파(Forward Propagation): 입력에서 예측값까지의 연산 흐름
순전파는 입력 벡터가 각 레이어의 가중치 행렬과 곱해지고 편향이 더해진 뒤, 비선형 활성화 함수를 통과하여 최종 출력층에 도달하는 과정입니다.
- **선형 변환**: $z^{[l]} = W^{[l]} a^{[l-1]} + b^{[l]}$
- **비선형 활성화**: $a^{[l]} = g^{[l]}(z^{[l]})$
- **손실 계산**: 예측값 $\hat{y}$과 실제 정답 라벨 $y$ 사이의 오차를 정의하는 손실 함수 $L(\hat{y}, y)$를 계산합니다.

> **💡 핵심 인사이트**
> 역전파는 복잡한 다층 신경망 전체의 미분을 국소적(Local) 미분들의 곱으로 쪼개어 계산하는 동적 프로그래밍 기법입니다. 전체 연산 그래프를 거꾸로 순회하며 그래디언트를 역전파합니다.

### 2. 역전파(Backpropagation) 계산의 핵심 단계
1. **손실 함수 정의**: 회귀에서는 평균 제곱 오차(MSE), 분류에서는 교차 엔트로피(Cross-Entropy)를 계산합니다.
2. **출력층 기울기 계산**: $\frac{\partial L}{\partial a^{[L]}}$ 및 $\frac{\partial L}{\partial z^{[L]}}$를 구합니다.
3. **은닉층 오차 전파**: 연쇄 법칙을 적용하여 이전 레이어로 오차 신호를 전달합니다: $\frac{\partial L}{\partial z^{[l]}} = \frac{\partial L}{\partial a^{[l]}} \odot g'^{[l]}(z^{[l]})$
4. **가중치 및 편향 기울기 도출**: $\frac{\partial L}{\partial W^{[l]}} = \frac{\partial L}{\partial z^{[l]}} (a^{[l-1]})^T$
5. **가중치 업데이트**: 계산된 그래디언트에 학습률(Learning Rate)을 곱해 경사하강법을 수행합니다.

### 3. 실무 엔지니어링 팁 & 주의사항
실무에서는 PyTorch와 같은 자동 미분(Autograd) 라이브러리를 사용하지만, 내부 계산 그래프(Computation Graph)의 생명주기와 메모리 점유 방식을 이해해야 대규모 모델 훈련 시 OOM(Out of Memory) 문제를 예방할 수 있습니다. 
특히 `torch.no_grad()`를 추론 시에 필수적으로 사용하여 불필요한 중간 활성화 값의 메모리 저장을 방지해야 합니다.

<steptracer>
{
  "scenario": "단일 뉴런에서 선형 변환 z = 2x + 1 및 손실 L = (y_pred - y_true)^2 의 역전파 계산",
  "steps": [
    {"question": "x=3, y_true=10일 때 순전파 출력 z의 값은 무엇인가요?", "answer": "z = 2*3 + 1 = 7 입니다."},
    {"question": "손실 L의 값과 z에 대한 손실의 기울기 dL/dz는 얼마인가요?", "answer": "L = (7 - 10)^2 = 9이며, dL/dz = 2*(7 - 10) = -6 입니다."}
  ]
}
</steptracer>"""

SAMPLE_TAG_ONLY = """<feynman>
{
  "tag_team_scenario": "초보자에게 설명하는 시나리오",
  "target_persona": "비전공자",
  "initial_ai_message": "설명을 시작합니다.",
  "concept_summary": "개념 요약입니다."
}
</feynman>"""

SAMPLE_SHORT_NARRATIVE = """# 대형 언어 모델 개요
LLM은 대량의 텍스트 데이터를 학습하여 자연어를 생성하는 인공지능 모델입니다.
<feynman>
{
  "tag_team_scenario": "초보자 설명",
  "target_persona": "초보자",
  "initial_ai_message": "시작",
  "concept_summary": "요약"
}
</feynman>"""

SAMPLE_RICH_NARRATIVE_MNEMONIC = r"""# 신경망 활성화 함수(Activation Functions)의 특성과 암기법

딥러닝 모델의 비선형성(Non-linearity)을 부여하는 핵심 요소는 활성화 함수(Activation Function)입니다. 만약 활성화 함수 없이 선형 결합($Wx+b$)만을 연속하여 쌓는다면, 아무리 레이어가 깊어져도 결국 하나의 거대한 선형 변환과 수학적으로 동일해지기 때문에 비선형 복잡도를 학습할 수 없습니다.

인공 신경망이 복잡한 현실 세계의 고차원 데이터(이미지, 자연어, 오디오 등)를 표현하고 학습할 수 있는 비결은 바로 각 층마다 비선형 활성화 함수를 배치하여 의사결정 경계를 구부리고 비틀 수 있기 때문입니다.

### 1. 주요 활성화 함수 비교 분석
대표적인 활성화 함수들의 특징과 장단점은 다음과 같습니다:
1. **시그모이드(Sigmoid)**: 출력을 0과 1 사이로 압축하여 확률 해석에 용이하지만, 입력값이 극단적일 때 기울기가 0에 수렴하는 '기울기 소실(Vanishing Gradient)' 문제가 발생합니다.
2. **하이퍼볼릭 탄젠트(Tanh)**: 출력이 -1과 1 사이이며 원점 중심(Zero-centered)이지만, 시그모이드와 마찬가지로 양 끝단에서 기울기 소실이 발생합니다.
3. **ReLU(Rectified Linear Unit)**: 입력이 0보다 크면 기울기가 1로 유지되어 역전파 연산이 매우 빠르고 효율적이나, 음수 영역에서 뉴런이 죽어버리는 'Dying ReLU' 현상이 나타납니다.
4. **Leaky ReLU / PReLU**: 음수 영역에서도 작은 기울기를 허용하여 Dying ReLU 문제를 완화합니다.
5. **GELU / Swish**: 최신 트랜스포머 아키텍처에서 주로 사용되며, 입력의 확률적 게이팅을 통해 더 부드러운 그래디언트 흐름을 제공합니다.

> **💡 핵심 인사이트**
> 활성화 함수 선택의 핵심은 '기울기 전파의 안정성'과 '연산 효율성' 간의 균형입니다. 현대 LLM들은 음수 영역에서도 약간의 비선형성을 허용하는 GELU 계열을 표준으로 채택하고 있습니다.

### 2. 실무 엔지니어링 팁 & 주의사항
- 모델의 초기 레이어에서 학습이 진행되지 않는다면 활성화 함수의 포화(Saturation) 상태를 점검하십시오.
- ReLU 사용 시 가중치 초기화는 반드시 He 초기화(Kaiming Normal)를 사용하여 출력 분산을 보존해야 합니다.
- 시그모이드나 Tanh를 사용할 때는 Xavier(Glorot) 초기화를 선택해야 층을 거듭해도 그래디언트가 소멸하거나 폭발하지 않습니다.

<mnemonic>
{
  "story": "시골 마을(Sigmoid) 사서가 책을 0~1권만 빌려주다 지쳐 쓰러졌고(소실), 탄산(Tanh) 음료는 -1도에서 얼었으며, 레고(ReLU) 블록은 0 이하를 부러뜨렸지만 게릴라(GELU) 전술로 승리했다!",
  "flashcards": [
    {"q": "Sigmoid의 대표적인 한계점은?", "a": "양 끝단에서 기울기가 0으로 수렴하는 기울기 소실(Vanishing Gradient)"},
    {"q": "현대 트랜스포머/LLM에서 주로 채택하는 활성화 함수는?", "a": "GELU (Gaussian Error Linear Unit)"}
  ]
}
</mnemonic>"""

SAMPLE_RICH_NARRATIVE_PROCEDURE = r"""# PyTorch 분산 학습(DDP: Distributed Data Parallel) 파이프라인 구축 절차

단일 GPU의 VRAM 용량을 초과하는 대형 모델을 학습하거나 대규모 데이터셋을 고속으로 처리하기 위해서는 다중 GPU 분산 학습(Distributed Training) 파이프라인이 필수적입니다.

PyTorch의 `DistributedDataParallel`(DDP)은 각 GPU 프로세스마다 독립적인 파이썬 인터프리터를 구동하고, 백엔드 통신 라이브러리(NCCL)를 통해 역전파 시 그래디언트의 All-Reduce 동기화 연산을 수행하는 가장 안정적이고 효율적인 분산 프레임워크입니다.

### 1. DDP 구축의 핵심 3대 원칙
1. **프로세스 그룹 초기화(init_process_group)**: 환경 변수(RANK, WORLD_SIZE, MASTER_ADDR, MASTER_PORT)를 기반으로 GPU 간 통신 링(Ring)을 구성합니다.
2. **분산 샘플러(DistributedSampler)**: 데이터셋이 여러 GPU에 중복 없이 분할 공급되도록 에포크마다 시드를 셔플합니다.
3. **그래디언트 동기화 최적화**: `gradient_accumulation_steps`와 혼합 정밀도(AMP: Automatic Mixed Precision)를 결합하여 통신 오버헤드를 최소화합니다.

> **💡 핵심 인사이트**
> DataParallel(DP)과 달리 DDP는 파이썬 GIL(Global Interpreter Lock)의 병목을 완전히 우회하여 선형에 가까운 멀티 GPU 확장 성능을 보장합니다.

### 2. DDP 실무 엔지니어링 체크포인트
- NCCL 통신 시 프로세스 간 데드락(Deadlock)을 방지하기 위해 모든 조건 분기(if-else)에서 동일한 All-Reduce 호출 순서를 보장하십시오.
- 메인 프로세스(Rank 0)에서만 모델 체크포인트를 저장하고 로깅을 수행해야 파일 쓰기 충돌 및 디스크 I/O 병목을 방지할 수 있습니다.
- 옵티마이저 스텝 이전에 `torch.nn.utils.clip_grad_norm_`을 적용하여 대규모 배치에서의 그래디언트 폭발을 제어하십시오.

<procedure>
{
  "checklists": [
    {"step": 1, "action": "torchrun 또는 torch.distributed.launch로 런타임 환경 설정", "hint": "WORLD_SIZE 및 LOCAL_RANK 환경변수 확인"},
    {"step": 2, "action": "dist.init_process_group(backend='nccl') 호출", "hint": "GPU 간 통신 초기화"},
    {"step": 3, "action": "모델을 DDP(model, device_ids=[local_rank])로 래핑", "hint": "각 프로세스 디바이스에 모델 할당"},
    {"step": 4, "action": "학습 루프 시작 전 sampler.set_epoch(epoch) 호출", "hint": "에포크별 데이터 셔플링 보장"}
  ]
}
</procedure>"""


class TestNarrativeStructureValidation(unittest.TestCase):
    def test_validate_rich_narrative_feynman_passes(self):
        """충분한 길이의 서술형 본문과 하단 feynman 태그를 가진 정상 출력 검증 통과"""
        is_valid, reason = validate_chapter_narrative(SAMPLE_RICH_NARRATIVE_FEYNMAN, min_chars=1000, min_narrative_chars=800)
        self.assertTrue(is_valid)
        self.assertEqual(reason, "유효한 서술형 본문 및 2단계 구조입니다.")

    def test_validate_rich_narrative_steptracer_passes(self):
        """충분한 길이의 서술형 본문과 하단 steptracer 태그를 가진 정상 출력 검증 통과"""
        is_valid, reason = validate_chapter_narrative(SAMPLE_RICH_NARRATIVE_STEPTRACER, min_chars=1000, min_narrative_chars=800)
        self.assertTrue(is_valid)
        self.assertEqual(reason, "유효한 서술형 본문 및 2단계 구조입니다.")

    def test_validate_rich_narrative_mnemonic_passes(self):
        """충분한 길이의 서술형 본문과 하단 mnemonic 태그를 가진 정상 출력 검증 통과"""
        is_valid, reason = validate_chapter_narrative(SAMPLE_RICH_NARRATIVE_MNEMONIC, min_chars=1000, min_narrative_chars=800)
        self.assertTrue(is_valid)
        self.assertEqual(reason, "유효한 서술형 본문 및 2단계 구조입니다.")

    def test_validate_rich_narrative_procedure_passes(self):
        """충분한 길이의 서술형 본문과 하단 procedure 태그를 가진 정상 출력 검증 통과"""
        is_valid, reason = validate_chapter_narrative(SAMPLE_RICH_NARRATIVE_PROCEDURE, min_chars=1000, min_narrative_chars=800)
        self.assertTrue(is_valid)
        self.assertEqual(reason, "유효한 서술형 본문 및 2단계 구조입니다.")

    def test_validate_tag_only_rejected(self):
        """태그로 바로 시작하는 tag-only 출력 거부"""
        is_valid, reason = validate_chapter_narrative(SAMPLE_TAG_ONLY, min_chars=1000, min_narrative_chars=800)
        self.assertFalse(is_valid)
        self.assertIn("인터랙티브 태그", reason)

    def test_validate_all_forbidden_tag_starts_rejected(self):
        """모든 위젯 태그(<feynman>, <steptracer>, <mnemonic>, <procedure>)로 시작하는 불량 출력 거부 검증"""
        tags = ["<feynman>", "<steptracer>", "<mnemonic>", "<procedure>", "<quiz>", "<discussion>"]
        for tag in tags:
            sample = f"{tag}\n{{\"test\": 123}}\n{tag.replace('<', '</')}"
            is_valid, reason = validate_chapter_narrative(sample)
            self.assertFalse(is_valid, f"Failed to reject starting with {tag}")
            self.assertIn("인터랙티브 태그", reason)

    def test_validate_markdown_wrapped_tag_start_rejected(self):
        """```xml 로 감싸져 시작하는 태그 단독 출력 거부"""
        sample = "```xml\n<feynman>\n{\"tag_team_scenario\": \"test\"}\n</feynman>\n```"
        is_valid, reason = validate_chapter_narrative(sample)
        self.assertFalse(is_valid)

    def test_validate_code_fenced_named_tag_start_rejected(self):
        """```feynman 또는 ```steptracer 로 시작하는 태그 단독 코드 블록 거부"""
        sample = "```feynman\n{\n  \"tag_team_scenario\": \"test scenario\"\n}\n```"
        is_valid, reason = validate_chapter_narrative(sample)
        self.assertFalse(is_valid)

    def test_validate_code_fenced_raw_json_rejected(self):
        """```json 으로 감싸진 순수 JSON 구조 시작 출력 거부"""
        long_json = "```json\n{\n  \"chapter\": \"딥러닝 개요\",\n  \"content\": \"" + "상세 설명 " * 200 + "\"\n}\n```"
        is_valid, reason = validate_chapter_narrative(long_json)
        self.assertFalse(is_valid)
        self.assertIn("원시 데이터 블록", reason)

    def test_validate_code_fenced_raw_array_rejected(self):
        """```json 으로 감싸진 순수 JSON 배열 시작 출력 거부"""
        long_array = "```json\n[\n  {\"step\": 1, \"content\": \"" + "데이터 처리 " * 200 + "\"}\n]\n```"
        is_valid, reason = validate_chapter_narrative(long_array)
        self.assertFalse(is_valid)
        self.assertIn("원시 데이터 블록", reason)

    def test_validate_forbidden_xml_root_tags_rejected(self):
        """<chapter>, <response>, <root>, <widget> 등 비정상 XML 루트로 시작하는 출력 거부"""
        for root_tag in ["<chapter>", "<response>", "<root>", "<interactive>", "<widget>"]:
            sample = f"{root_tag}\n# 제목\n" + "내용 " * 200 + f"\n{root_tag.replace('<', '</')}"
            is_valid, reason = validate_chapter_narrative(sample)
            self.assertFalse(is_valid, f"Failed to reject starting with {root_tag}")

    def test_validate_raw_json_rejected(self):
        """마크다운 본문 없이 순수 JSON으로 시작하는 출력 거부"""
        sample = '{\n  "introduction": "hello",\n  "principles": "world"\n}'
        is_valid, reason = validate_chapter_narrative(sample)
        self.assertFalse(is_valid)
        self.assertIn("원시 JSON 구조", reason)

    def test_validate_arbitrary_code_fenced_and_comment_starts_rejected(self):
        """임의의 언어 태그(markdown, text, bash 등) 코드 펜스나 HTML 주석으로 시작하는 불량 출력 거부"""
        bad_starts = [
            "```markdown\n{\n  \"test\": 123\n}\n```",
            "```text\n<feynman>\n{\"tag_team_scenario\": \"test\"}\n</feynman>\n```",
            "```bash\n[\n  {\"step\": 1}\n]\n```",
            "<!-- LLM Output -->\n<feynman>\n{\"tag_team_scenario\": \"test\"}\n</feynman>",
            "```step_tracer\n{\"scenario\": \"test\"}\n```",
            "<guide>\n# 제목\n" + "내용 " * 200 + "\n</guide>",
            "<section>\n# 제목\n" + "내용 " * 200 + "\n</section>",
            "<output>\n# 제목\n" + "내용 " * 200 + "\n</output>",
            "<data>\n# 제목\n" + "내용 " * 200 + "\n</data>",
            "<xml>\n<feynman>test</feynman>\n</xml>"
        ]
        for sample in bad_starts:
            is_valid, reason = validate_chapter_narrative(sample)
            self.assertFalse(is_valid, f"Failed to reject sample starting with: {sample[:30]}...")

    def test_validate_empty_or_none(self):
        """빈 값 또는 None 입력 시 거부"""
        is_valid, _ = validate_chapter_narrative("")
        self.assertFalse(is_valid)
        is_valid, _ = validate_chapter_narrative(None)
        self.assertFalse(is_valid)
        is_valid, _ = validate_chapter_narrative(12345)
        self.assertFalse(is_valid)


class TestCacheAutoInvalidation(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_clean_invalid_cached_chapters(self):
        """불량 캐시 파일(1000자 미만, 태그 단독 등)만 자동 삭제하고 정상 캐시는 보존"""
        valid_path = os.path.join(self.temp_dir, "valid_chapter.txt")
        with open(valid_path, "w", encoding="utf-8") as f:
            f.write(SAMPLE_RICH_NARRATIVE_FEYNMAN)

        invalid_tag_only_path = os.path.join(self.temp_dir, "invalid_tag_only.txt")
        with open(invalid_tag_only_path, "w", encoding="utf-8") as f:
            f.write(SAMPLE_TAG_ONLY)

        invalid_short_path = os.path.join(self.temp_dir, "invalid_short.txt")
        with open(invalid_short_path, "w", encoding="utf-8") as f:
            f.write(SAMPLE_SHORT_NARRATIVE)

        removed = clean_invalid_cached_chapters(data_dir=self.temp_dir)
        self.assertEqual(removed, 2)

        self.assertTrue(os.path.exists(valid_path), "정상 캐시 파일은 보존되어야 함")
        self.assertFalse(os.path.exists(invalid_tag_only_path), "태그 단독 캐시 파일은 삭제되어야 함")
        self.assertFalse(os.path.exists(invalid_short_path), "길이 미달 캐시 파일은 삭제되어야 함")


class TestChapterGenerationPipeline(unittest.IsolatedAsyncioTestCase):
    @patch("backend.services.llm.safe_gemini_generate_content")
    @patch("backend.services.llm.get_gemini_client")
    @patch("backend.services.llm._get_cache_dir")
    async def test_auto_retry_recovers_from_tag_only_output(self, mock_cache_dir, mock_get_client, mock_generate):
        """1차 시도에서 tag-only가 나오면 자동 재시도하여 정상 서술형 본문으로 복구 및 캐시 저장"""
        temp_cache_dir = tempfile.mkdtemp()
        mock_cache_dir.return_value = temp_cache_dir

        try:
            # 1차 응답: tag-only 불량 출력, 2차 응답: 정상 서술형 본문
            mock_resp_fail = MagicMock()
            mock_resp_fail.text = SAMPLE_TAG_ONLY
            mock_resp_success = MagicMock()
            mock_resp_success.text = SAMPLE_RICH_NARRATIVE_FEYNMAN

            mock_generate.side_effect = [mock_resp_fail, mock_resp_success]

            result = await async_generate_chapter_content(
                section_title="트랜스포머의 핵심 아키텍처",
                context_data="트랜스포머는 어텐션 메커니즘을 사용합니다...",
                provider="Google Gemini",
                chunk_index=0,
                total_chunks=1,
                length_preset="아주 상세하게",
                force_refresh=True
            )

            self.assertGreaterEqual(len(result), 1500)
            self.assertFalse(result.startswith("<feynman>"))
            self.assertIn("현대 생성형 AI의 중추적인 기둥", result)
            self.assertIn("<feynman>", result)

            # 캐시 파일이 생성되었는지 확인
            cache_files = os.listdir(temp_cache_dir)
            self.assertEqual(len(cache_files), 1)
            with open(os.path.join(temp_cache_dir, cache_files[0]), "r", encoding="utf-8") as f:
                saved_cache = f.read()
            self.assertEqual(saved_cache, SAMPLE_RICH_NARRATIVE_FEYNMAN)
        finally:
            shutil.rmtree(temp_cache_dir, ignore_errors=True)

    @patch("backend.services.llm.safe_gemini_generate_content")
    @patch("backend.services.llm.get_gemini_client")
    @patch("backend.services.llm._get_cache_dir")
    async def test_auto_retry_recovers_from_code_fenced_json(self, mock_cache_dir, mock_get_client, mock_generate):
        """1차 시도에서 code-fenced json이 나오면 자동 재시도하여 정상 서술형 본문으로 복구"""
        temp_cache_dir = tempfile.mkdtemp()
        mock_cache_dir.return_value = temp_cache_dir

        try:
            mock_resp_fail = MagicMock()
            mock_resp_fail.text = "```json\n{\n  \"chapter\": \"LLM 개요\",\n  \"content\": \"" + "설명 " * 200 + "\"\n}\n```"
            mock_resp_success = MagicMock()
            mock_resp_success.text = SAMPLE_RICH_NARRATIVE_STEPTRACER

            mock_generate.side_effect = [mock_resp_fail, mock_resp_success]

            result = await async_generate_chapter_content(
                section_title="순전파 및 역전파 알고리즘",
                context_data="역전파는 연쇄 법칙을 사용합니다...",
                provider="Google Gemini",
                chunk_index=0,
                total_chunks=1,
                length_preset="아주 상세하게",
                force_refresh=True
            )

            self.assertGreaterEqual(len(result), 1500)
            self.assertFalse(result.startswith("```json"))
            self.assertIn("순전파 및 역전파 알고리즘", result)
            self.assertIn("<steptracer>", result)
        finally:
            shutil.rmtree(temp_cache_dir, ignore_errors=True)

    @patch("backend.services.llm.safe_gemini_generate_content")
    @patch("backend.services.llm.get_gemini_client")
    @patch("backend.services.llm._get_cache_dir")
    async def test_multi_chapter_karpathy_simulation(self, mock_cache_dir, mock_get_client, mock_generate):
        """Karpathy 2시간 강의 시뮬레이션: 전 챕터가 1,500자 이상 서술형 본문을 포함하며 태그로 시작하지 않음 검증"""
        temp_cache_dir = tempfile.mkdtemp()
        mock_cache_dir.return_value = temp_cache_dir

        try:
            mock_resp = MagicMock()
            mock_resp.text = SAMPLE_RICH_NARRATIVE_FEYNMAN
            mock_generate.return_value = mock_resp

            chapters = [
                "1. 거대 언어 모델의 탄생과 사전 학습(Pre-training)",
                "2. 토크나이저와 어텐션 메커니즘",
                "3. 파인튜닝과 정렬(Alignment / RLHF)",
                "4. 모델 추론 최적화 및 미래 전망"
            ]

            results = {}
            for idx, ch in enumerate(chapters):
                content = await async_generate_chapter_content(
                    section_title=ch,
                    context_data="Karpathy LLM tutorial transcript context...",
                    provider="Google Gemini",
                    chunk_index=idx,
                    total_chunks=len(chapters),
                    length_preset="아주 상세하게",
                    force_refresh=True
                )
                results[ch] = content

            # Acceptance Criteria 검증
            self.assertEqual(len(results), 4)
            for ch, content in results.items():
                self.assertGreaterEqual(len(content), 1500, f"Chapter {ch} is less than 1500 chars")
                self.assertFalse(content.strip().startswith("<feynman>"), f"Chapter {ch} starts with feynman")
                self.assertFalse(content.strip().startswith("<steptracer>"), f"Chapter {ch} starts with steptracer")
                self.assertFalse(content.strip().startswith("<mnemonic>"), f"Chapter {ch} starts with mnemonic")
                self.assertFalse(content.strip().startswith("<procedure>"), f"Chapter {ch} starts with procedure")
                
                # 인터랙티브 태그 이전 서술형 본문 검증
                tag_pos = content.find("<feynman>")
                self.assertGreater(tag_pos, 1000, f"Narrative prose in {ch} is too short prior to tag")
        finally:
            shutil.rmtree(temp_cache_dir, ignore_errors=True)

    @patch("backend.services.llm.safe_gemini_generate_content")
    @patch("backend.services.llm.get_gemini_client")
    @patch("backend.services.llm._get_cache_dir")
    async def test_detailed_preset_invalidates_short_summary_cache(self, mock_cache_dir, mock_get_client, mock_generate):
        """'아주 상세하게' 프리셋 요청 시 1,000~1,499자의 부족한 캐시 파일은 무효화하고 1,500자 이상으로 재성성 검증"""
        import hashlib
        temp_cache_dir = tempfile.mkdtemp()
        mock_cache_dir.return_value = temp_cache_dir

        try:
            section = "어텐션 메커니즘 개요"
            provider = "Google Gemini"
            length_preset = "아주 상세하게"
            analogy_preset = "풍부한 비유"
            learner_profile = ""
            url_hash = "test_hash"

            # 1,100자 짜리 짧은 요약 캐시 파일 사전 생성
            cache_key_raw = f"{url_hash}_{section}_{provider}_{length_preset}_{analogy_preset}_{learner_profile}"
            cache_hash = hashlib.md5(cache_key_raw.encode('utf-8')).hexdigest()
            cache_file = os.path.join(temp_cache_dir, f"{cache_hash}.txt")

            short_content = "# 어텐션 메커니즘 개요\n\n" + "이 챕터는 트랜스포머 어텐션 메커니즘을 요약 설명합니다. " * 35 + "\n\n<feynman>\n{\"tag_team_scenario\":\"s\",\"target_persona\":\"p\",\"initial_ai_message\":\"m\",\"concept_summary\":\"c\"}\n</feynman>"
            self.assertGreater(len(short_content), 1000)
            self.assertLess(len(short_content), 1500)

            with open(cache_file, "w", encoding="utf-8") as f:
                f.write(short_content)

            # LLM mock response (> 1500 chars)
            mock_resp = MagicMock()
            mock_resp.text = SAMPLE_RICH_NARRATIVE_FEYNMAN
            mock_generate.return_value = mock_resp

            result = await async_generate_chapter_content(
                section_title=section,
                context_data="어텐션 context...",
                provider=provider,
                chunk_index=0,
                total_chunks=1,
                length_preset=length_preset,
                analogy_preset=analogy_preset,
                learner_profile=learner_profile,
                url_hash=url_hash,
                force_refresh=False
            )

            # 기존 1100자 캐시가 아닌 1500자 이상의 새로운 상세 내용이 반환되어야 함
            self.assertGreaterEqual(len(result), 1500)
            self.assertEqual(result, SAMPLE_RICH_NARRATIVE_FEYNMAN)
            mock_generate.assert_called()
        finally:
            shutil.rmtree(temp_cache_dir, ignore_errors=True)

    @patch("backend.services.llm.safe_gemini_generate_content")
    @patch("backend.services.llm.get_gemini_client")
    @patch("backend.services.llm._get_cache_dir")
    async def test_persistent_tag_only_output_fallback_synthesis(self, mock_cache_dir, mock_get_client, mock_generate):
        """3회 재시도 모두 tag-only로 실패하더라도 최종 결과물이 마크다운 서술형 본문으로 안전하게 합성되어 반환됨을 검증 (AC: Zero chapters start with tags)"""
        temp_cache_dir = tempfile.mkdtemp()
        mock_cache_dir.return_value = temp_cache_dir

        try:
            # 모든 재시도 응답이 tag-only 불량 출력인 극단적 상황 모킹
            mock_resp_fail = MagicMock()
            mock_resp_fail.text = SAMPLE_TAG_ONLY
            mock_generate.return_value = mock_resp_fail

            result = await async_generate_chapter_content(
                section_title="어텐션 메커니즘의 수학적 원리",
                context_data="어텐션 메커니즘 context...",
                provider="Google Gemini",
                chunk_index=0,
                total_chunks=1,
                length_preset="아주 상세하게",
                force_refresh=True
            )

            # 검증: 절대 <feynman>으로 시작하지 않고 마크다운 대제목 및 서술형 본문으로 시작해야 함
            self.assertFalse(result.strip().startswith("<feynman>"), "출력이 <feynman>으로 시작해서는 안 됨")
            self.assertTrue("어텐션 메커니즘" in result.strip()[:100], "출력 서두가 어텐션 메커니즘 서술형 본문으로 시작해야 함")
            self.assertIn("핵심 인사이트", result)
            self.assertIn("실무 활용 팁", result)
            self.assertIn("<feynman>", result)
            self.assertTrue(result.strip().endswith("</feynman>"), "인터랙티브 태그가 최하단에 위치해야 함")
        finally:
            shutil.rmtree(temp_cache_dir, ignore_errors=True)

    @patch("backend.services.llm.safe_gemini_generate_content")
    @patch("backend.services.llm.get_gemini_client")
    @patch("backend.services.llm._get_cache_dir")
    async def test_multilingual_transcript_prompt_directive(self, mock_cache_dir, mock_get_client, mock_generate):
        """영어/외국어 스크립트 전달 시 프롬프트에 100% 한국어 번역 및 서술형 가이드 지침이 포함되는지 검증"""
        temp_cache_dir = tempfile.mkdtemp()
        mock_cache_dir.return_value = temp_cache_dir

        try:
            mock_resp = MagicMock()
            mock_resp.text = SAMPLE_RICH_NARRATIVE_FEYNMAN
            mock_generate.return_value = mock_resp

            await async_generate_chapter_content(
                section_title="Transformer Architecture Overview",
                context_data="Attention is all you need. In this lecture by Andrej Karpathy, we build GPT from scratch in PyTorch...",
                provider="Google Gemini",
                chunk_index=0,
                total_chunks=1,
                length_preset="아주 상세하게",
                force_refresh=True
            )

            # Gemini 호출 시 전달된 contents 인자 검증
            call_args = mock_generate.call_args
            contents_arg = call_args[1].get("contents") or call_args[0][2]
            prompt_str = " ".join([str(c) for c in contents_arg])
            self.assertIn("한국어로 번역", prompt_str)
            self.assertIn("2단계 엄격 출력 구조", prompt_str)
        finally:
            shutil.rmtree(temp_cache_dir, ignore_errors=True)


class TestNarrativeBoundaryValueAnalysis(unittest.TestCase):
    def test_exact_character_count_boundaries_summary_preset(self):
        """핵심 요약 프리셋 경계값 테스트: 999자 거부 vs 1000자 통과"""
        header = "# 요약 제목\n\n"
        tag = "\n\n<feynman>\n{\"tag_team_scenario\":\"s\",\"target_persona\":\"p\",\"initial_ai_message\":\"m\",\"concept_summary\":\"c\"}\n</feynman>"
        
        # 본문 길이를 조절하여 전체 길이 999자 생성 (tag 길이 포함)
        filler_len_999 = 999 - len(header) - len(tag)
        body_999 = header + ("가" * filler_len_999) + tag
        self.assertEqual(len(body_999), 999)
        is_valid_999, _ = validate_chapter_narrative(body_999, min_chars=1000, min_narrative_chars=800)
        self.assertFalse(is_valid_999, "999자는 1000자 최소 기준에 미달하므로 거부되어야 함")

        # 본문 길이를 조절하여 전체 길이 1000자 생성 (narrative 분량 850자 이상)
        filler_len_1000 = 1000 - len(header) - len(tag)
        body_1000 = header + ("가" * filler_len_1000) + tag
        self.assertEqual(len(body_1000), 1000)
        is_valid_1000, _ = validate_chapter_narrative(body_1000, min_chars=1000, min_narrative_chars=800)
        self.assertTrue(is_valid_1000, "1000자는 1000자 최소 기준을 만족하므로 통과해야 함")

    def test_exact_character_count_boundaries_detailed_preset(self):
        """상세 프리셋 경계값 테스트: 1499자 거부 vs 1500자 통과"""
        header = "# 상세 제목\n\n"
        tag = "\n\n<feynman>\n{\"tag_team_scenario\":\"s\",\"target_persona\":\"p\",\"initial_ai_message\":\"m\",\"concept_summary\":\"c\"}\n</feynman>"
        
        filler_len_1499 = 1499 - len(header) - len(tag)
        body_1499 = header + ("가" * filler_len_1499) + tag
        self.assertEqual(len(body_1499), 1499)
        is_valid_1499, _ = validate_chapter_narrative(body_1499, min_chars=1500, min_narrative_chars=1200)
        self.assertFalse(is_valid_1499, "1499자는 1500자 최소 기준에 미달하므로 거부되어야 함")

        filler_len_1500 = 1500 - len(header) - len(tag)
        body_1500 = header + ("가" * filler_len_1500) + tag
        self.assertEqual(len(body_1500), 1500)
        is_valid_1500, _ = validate_chapter_narrative(body_1500, min_chars=1500, min_narrative_chars=1200)
        self.assertTrue(is_valid_1500, "1500자는 1500자 최소 기준을 만족하므로 통과해야 함")


if __name__ == "__main__":
    unittest.main()
