import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.prompts.meeting_minutes import build_meeting_minutes_system_prompt
from backend.services.llm.meeting_minutes import _parse_meeting_sections

class TestMeetingMinutes(unittest.TestCase):
    def test_meeting_minutes_prompt_generation(self):
        """전문 회의록 시스템 프롬프트가 필수 지침 및 구조를 포함하는지 검증"""
        prompt = build_meeting_minutes_system_prompt("Q3 로드맵 및 백엔드 아키텍처 회의")
        self.assertIn("Q3 로드맵 및 백엔드 아키텍처 회의", prompt)
        self.assertIn("전문 회의록", prompt)
        self.assertIn("핵심 결정 사항", prompt)
        self.assertIn("액션 아이템", prompt)
        self.assertIn("Strict Korean Policy", prompt)
        self.assertIn("Zero-Greeting Policy", prompt)

    def test_parse_meeting_sections(self):
        """생성된 회의록 마크다운이 뷰어용 섹션 딕셔너리로 정상 파싱되고 전사 전문이 첨부되는지 검증"""
        sample_markdown = """# 🎙️ [회의록] 스프린트 계획 회의

## 1. 회의 개요 및 핵심 요약 (Executive Summary)
이번 회의는 다음 주 배포 스프린트를 조율하기 위해 진행되었습니다.

## 2. 주요 아젠다 및 논의 상세 (Key Discussions)
### API 최적화 논의
Redis 캐싱 레이어를 적용하여 응답 속도를 개선하기로 했습니다.

## 3. 핵심 결정 사항 (Key Decisions)
1. Redis 캐시 TTL을 30초로 설정.
2. Celery 워커 동시성을 3으로 유지.

## 4. 실행 과제 및 액션 아이템 (Action Items)
| 번호 | 실행 과제 | 담당 주체 | 목표 기한 | 우선순위 |
| :--- | :--- | :--- | :--- | :--- |
| 1 | Redis 캐시 테스트 | 백엔드팀 | 이번 주 금요일 | 높음 |

## 5. 리스크 요인 및 미결 과제 (Risks & Open Questions)
- Neon DB 커넥션 풀 고갈 가능성에 대한 모니터링 필요.
"""
        sample_transcript = "철수: 이번 주 배포 일정 조율합시다. 영희: Redis 캐싱을 붙이는 게 좋겠습니다."
        
        sections = _parse_meeting_sections(sample_markdown, sample_transcript)
        
        self.assertIsInstance(sections, dict)
        self.assertGreaterEqual(len(sections), 4)
        
        # 필수 섹션들이 키로 존재하는지 검증
        keys = list(sections.keys())
        self.assertTrue(any("회의 개요" in k or "Overview" in k for k in keys))
        self.assertTrue(any("주요 아젠다" in k or "Discussions" in k for k in keys))
        self.assertTrue(any("결정 사항" in k or "Decisions" in k for k in keys))
        self.assertTrue(any("액션 아이템" in k or "Action Items" in k for k in keys))
        
        # 전사 전문 첨부 확인
        self.assertIn("음성 전사 전문 (Full Transcript)", sections)
        self.assertIn(sample_transcript, sections["음성 전사 전문 (Full Transcript)"])

    def test_audio_extension_check(self):
        """오디오 확장자 목록 판별 검증"""
        audio_exts = {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg", ".wma"}
        test_files = ["meeting_record.mp3", "interview.WAV", "lecture.m4a", "document.pdf", "notes.txt"]
        
        is_audio = [os.path.splitext(f)[1].lower() in audio_exts for f in test_files]
        self.assertEqual(is_audio, [True, True, True, False, False])

if __name__ == "__main__":
    unittest.main()
