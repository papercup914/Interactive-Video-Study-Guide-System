import os
import sys
import unittest
import json
from unittest.mock import patch, MagicMock

# 프로젝트 루트를 sys.path에 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.services.pipeline_config import (
    get_pipeline_config,
    update_pipeline_config,
    reset_pipeline_config_to_defaults,
    apply_pipeline_preset,
    get_all_presets_meta,
    DEFAULT_PIPELINE_CONFIG,
    PRESETS
)

class TestPipelineConfig(unittest.TestCase):
    def setUp(self):
        # 테스트 전 기본값으로 리셋
        reset_pipeline_config_to_defaults()

    def test_default_config_structure(self):
        """기본 설정 스키마의 필수 키들이 완벽하게 존재하는지 검증"""
        cfg = get_pipeline_config()
        self.assertIn("llm", cfg)
        self.assertIn("outline", cfg)
        self.assertIn("chapter", cfg)
        self.assertIn("widgets", cfg)
        self.assertIn("guardrails", cfg)
        self.assertIn("sources", cfg)
        
        # LLM 세부 항목 확인
        self.assertIn("primary_model", cfg["llm"])
        self.assertIn("concurrency", cfg["llm"])
        self.assertIn("temperature", cfg["llm"])
        
        # Guardrails 세부 항목 확인
        self.assertGreaterEqual(cfg["guardrails"]["min_korean_chars"], 50)
        self.assertGreaterEqual(cfg["guardrails"]["min_korean_ratio_percent"], 10.0)

    def test_update_config(self):
        """설정 부분 업데이트 및 영속화 검증"""
        patch_data = {
            "llm": {
                "temperature": 0.4,
                "concurrency": 5
            },
            "guardrails": {
                "min_korean_chars": 300
            }
        }
        updated = update_pipeline_config(patch_data)
        self.assertEqual(updated["llm"]["temperature"], 0.4)
        self.assertEqual(updated["llm"]["concurrency"], 5)
        self.assertEqual(updated["guardrails"]["min_korean_chars"], 300)
        
        # 캐시 재조회 시에도 유지되는지 확인
        fetched = get_pipeline_config()
        self.assertEqual(fetched["llm"]["temperature"], 0.4)
        self.assertEqual(fetched["llm"]["concurrency"], 5)

    def test_invalid_values_sanitization(self):
        """비정상 값 입력 시 가드레일에 의해 자동 보정되는지 검증"""
        patch_data = {
            "llm": {
                "temperature": 99.9,  # 비정상
                "concurrency": -5     # 비정상
            },
            "guardrails": {
                "min_korean_chars": 5  # 너무 낮음
            }
        }
        updated = update_pipeline_config(patch_data)
        self.assertEqual(updated["llm"]["temperature"], 0.2)
        self.assertEqual(updated["llm"]["concurrency"], 3)
        self.assertEqual(updated["guardrails"]["min_korean_chars"], 50)

    def test_apply_presets(self):
        """프리셋(초고속, 표준, 심화) 적용 검증"""
        # 1. 초고속 모드 적용
        fast_cfg = apply_pipeline_preset("fast_lite")
        self.assertEqual(fast_cfg["llm"]["primary_model"], "gemini-2.5-flash-lite")
        self.assertEqual(fast_cfg["llm"]["concurrency"], 5)
        
        # 2. 학술/심화 연구 모드 적용
        deep_cfg = apply_pipeline_preset("deep_research")
        self.assertEqual(deep_cfg["llm"]["primary_model"], "gemini-1.5-pro")
        self.assertEqual(deep_cfg["llm"]["concurrency"], 2)

        # 3. 잘못된 프리셋 예외 처리
        with self.assertRaises(ValueError):
            apply_pipeline_preset("non_existent_preset")

    def test_reset_to_defaults(self):
        """기본값 리셋 동작 검증"""
        # 먼저 값 변경
        update_pipeline_config({"llm": {"concurrency": 8}})
        self.assertEqual(get_pipeline_config()["llm"]["concurrency"], 8)
        
        # 리셋 실행
        reset_cfg = reset_pipeline_config_to_defaults()
        self.assertEqual(reset_cfg["llm"]["concurrency"], 3)
        self.assertEqual(reset_cfg["llm"]["primary_model"], DEFAULT_PIPELINE_CONFIG["llm"]["primary_model"])

    def test_presets_meta(self):
        """프리셋 메타데이터 목록 형식 검증"""
        meta = get_all_presets_meta()
        self.assertIn("standard_balanced", meta)
        self.assertIn("fast_lite", meta)
        self.assertIn("deep_research", meta)
        self.assertIn("name", meta["standard_balanced"])
        self.assertIn("description", meta["standard_balanced"])

if __name__ == "__main__":
    unittest.main()
