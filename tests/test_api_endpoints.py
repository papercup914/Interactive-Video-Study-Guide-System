import os
import sys
import unittest
from fastapi.testclient import TestClient

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.main import app
from backend.config import settings
from backend.prompts.chapter_guide import build_chapter_system_prompt

class TestApiEndpoints(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_root_health(self):
        """기본 루트 헬스체크 엔드포인트 검증"""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get("status"), "ok")

    def test_get_all_study_guides(self):
        """가이드 히스토리 목록 조회 엔드포인트 검증"""
        response = self.client.get("/api/guide/history")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)

    def test_admin_health_endpoint(self):
        """관리자 헬스체크 엔드포인트 및 is_mock / real_stats 플래그 검증"""
        response = self.client.get("/api/admin/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get("is_mock"))
        self.assertIn("real_stats", data)
        self.assertIn("summary", data)
        self.assertIn("logs", data)

    def test_config_settings_validation(self):
        """pydantic-settings 중앙 설정 객체 검증"""
        self.assertIsNotNone(settings.selected_gemini_version)
        self.assertGreater(settings.chapter_generation_concurrency, 0)
        self.assertIsNotNone(settings.database_url)

    def test_chapter_prompt_builder(self):
        """외부화된 챕터 프롬프트 빌더 동작 및 제로 인사말 지침 검증"""
        prompt = build_chapter_system_prompt(
            section_title="테스트 챕터",
            tutor_directive="당신은 튜터입니다.",
            learner_profile="대학생 개발자",
            analogy_instruction="비유 추가",
            length_instruction="상세하게"
        )
        self.assertIn("테스트 챕터", prompt)
        self.assertIn("Strict Zero-Greeting Policy", prompt)
        self.assertIn("<feynman>", prompt)
        self.assertIn("<steptracer>", prompt)

if __name__ == '__main__':
    unittest.main()
