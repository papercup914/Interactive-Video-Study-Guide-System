"""
Interactive Video Study Guide System - 파이프라인 동적 설정 관리 모듈
관리자가 웹 대시보드(/admin/generation-config)에서 실시간으로 수정하는
모든 생성 매커니즘(AI 모델, 목차 규칙, 서술 지침, 위젯 규칙, 가드레일, 자막 수집)을
DB(Neon PostgreSQL)에 영속화하고, 안전한 인메모리 캐시 및 Fallback을 제공합니다.
"""

import os
import json
import copy
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from backend.data.database import SessionLocal
from backend.data.models import SystemConfig

CONFIG_KEY = "generation_pipeline_v1"

# 1. 시스템 표준 기본 설정 (Factory Default)
DEFAULT_PIPELINE_CONFIG: Dict[str, Any] = {
    # 1) AI 모델 및 런타임 엔진
    "llm": {
        "primary_model": "gemini-2.5-flash",
        "fallback_models": [
            "gemini-2.5-flash-lite",
            "gemini-1.5-pro",
            "openai/gpt-4o",
            "llama-3.3-70b-versatile"
        ],
        "temperature": 0.2,
        "max_tokens": 8192,
        "concurrency": 3,
        "timeout_seconds": 60,
        "max_retries": 3,
        "retry_multiplier": 1.5
    },
    
    # 2) 목차(Outline) 생성 매커니즘
    "outline": {
        "use_official_chapters": True,
        "official_adaptation_style": "curiosity_hook",  # curiosity_hook, direct_insight, literal_korean
        "min_chapters": 4,
        "max_chapters": 15,
        "target_chunk_size": 2500,
        "strict_time_sequence": True,
        "smart_slicing_window": 4500,
        "clean_noise_tags": True,
        "fallback_templates": {
            "business": [
                "도입: {clean_topic}의 본질과 핵심 배경",
                "{clean_topic}을 둘러싼 오해와 주요 실패 요인",
                "{clean_topic}의 성공을 가르는 결정적 조건과 통찰",
                "실전 적용: {clean_topic}을 위한 핵심 실천 전략"
            ],
            "technical": [
                "도입: {clean_topic}의 배경과 시스템 아키텍처",
                "{clean_topic}의 핵심 동작 원리와 데이터 흐름",
                "{clean_topic}의 실무 구현 전략과 장애 방지 가이드",
                "최종 점검: {clean_topic} 최적화 체크리스트"
            ],
            "general": [
                "도입: {clean_topic}의 핵심 배경과 질문",
                "{clean_topic}에 대한 심층 분석과 새로운 시각",
                "{clean_topic}이 주는 일상과 실무의 시사점",
                "핵심 요약: {clean_topic}의 미래 통찰"
            ]
        }
    },
    
    # 3) 챕터 본문 서술 매커니즘 & 프롬프트
    "chapter": {
        "zero_greeting_policy": True,
        "strict_korean_policy": True,
        "default_persona_role": "지식 큐레이션 및 학습 코치",
        "default_persona_tone": "친절하면서도 핵심을 꿰뚫는 명쾌한 어조",
        "default_focus_areas": "개념의 본질적 이유(Why)와 실전 응용(How)",
        "forbidden_greeting_words": [
            "안녕하세요", "반갑습니다", "여러분의 튜터입니다",
            "이번 시간에는", "이번 챕터에서는", "환영합니다"
        ],
        "narrative_sections": [
            "도입 및 핵심 문제 제기 (훅 & 핵심 요약 중심)",
            "상세 원리 및 비유 설명",
            "핵심 인사이트 박스 (💡)",
            "실무 활용 팁 / 주의사항"
        ]
    },
    
    # 4) 인터랙티브 학습 위젯 규칙
    "widgets": {
        "feynman_enabled": True,
        "steptracer_enabled": True,
        "mnemonic_enabled": True,
        "procedure_enabled": True,
        "attachment_mode": "auto_one",  # auto_one (적합한 1개 자동 선택), all, disabled
        "require_strict_json": True
    },
    
    # 5) 품질 검증 가드레일 임계치
    "guardrails": {
        "min_total_chars_summary": 1000,
        "min_total_chars_detailed": 1500,
        "min_narrative_chars_summary": 800,
        "min_narrative_chars_detailed": 1200,
        "min_korean_chars": 250,
        "min_korean_ratio_percent": 40.0,
        "english_char_threshold_for_ratio_check": 100,
        "enable_auto_escalation_retry": True,
        "escalation_prompt": (
            "\n[긴급 시정 명령]: 이전 생성 결과가 한국어 분량 미달이거나 서술문 없이 태그만 출력되었습니다. "
            "반드시 1,500자 이상의 유려하고 상세한 한국어 서술형 본문을 먼저 완전하게 작성한 후, "
            "맨 아래에 위젯 태그를 덧붙이십시오. 인사말은 절대 금지합니다."
        )
    },
    
    # 6) 데이터 소스 및 자막 수집 파이프라인
    "sources": {
        "transcript_priority": ["youtube_transcript_api", "ytdlp_subtitles", "whisper_asr"],
        "whisper_model_size": "base",  # tiny, base, small, medium
        "clean_jina_scraped_noise": True,
        "enable_gemini_context_caching": True,
        "max_script_chars_for_caching": 12000
    }
}

# 2. 추천 프리셋 모음
PRESETS: Dict[str, Dict[str, Any]] = {
    "standard_balanced": {
        "name": "🎯 표준 균형 모드 (기본값)",
        "description": "최적의 품질과 속도를 제공하는 프로덕션 표준 설정입니다.",
        "config_patch": {
            "llm": {
                "primary_model": "gemini-2.5-flash",
                "temperature": 0.2,
                "concurrency": 3,
                "max_tokens": 8192
            },
            "guardrails": {
                "min_total_chars_detailed": 1500,
                "min_korean_chars": 250,
                "min_korean_ratio_percent": 40.0
            }
        }
    },
    "fast_lite": {
        "name": "⚡ 초고속 경량 모드",
        "description": "응답 속도를 최우선으로 하여 빠른 미리보기 및 대량 처리에 적합합니다.",
        "config_patch": {
            "llm": {
                "primary_model": "gemini-2.5-flash-lite",
                "temperature": 0.1,
                "concurrency": 5,
                "max_tokens": 4096
            },
            "outline": {
                "min_chapters": 3,
                "max_chapters": 8
            },
            "guardrails": {
                "min_total_chars_detailed": 1000,
                "min_narrative_chars_detailed": 700,
                "min_korean_chars": 180
            }
        }
    },
    "deep_research": {
        "name": "🔬 학술/심화 연구 모드",
        "description": "최고 사양 모델로 깊이 있는 통찰과 긴 분량의 고품질 가이드를 생성합니다.",
        "config_patch": {
            "llm": {
                "primary_model": "gemini-1.5-pro",
                "temperature": 0.3,
                "concurrency": 2,
                "max_tokens": 12000
            },
            "outline": {
                "min_chapters": 6,
                "max_chapters": 18
            },
            "guardrails": {
                "min_total_chars_detailed": 2200,
                "min_narrative_chars_detailed": 1800,
                "min_korean_chars": 400,
                "min_korean_ratio_percent": 50.0
            }
        }
    }
}

# 인메모리 캐시 (DB 부하 방지 및 초고속 참조)
_CACHED_CONFIG: Optional[Dict[str, Any]] = None
_LAST_CACHE_TIME: float = 0.0
CACHE_TTL_SECONDS = 30.0  # 30초마다 필요시 DB와 갱신


def _deep_merge(target: dict, patch: dict) -> dict:
    """중첩 딕셔너리를 재귀적으로 안전하게 병합합니다."""
    result = copy.deepcopy(target)
    for key, value in patch.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


_table_checked = False

def _ensure_table():
    global _table_checked
    if _table_checked:
        return
    try:
        from backend.data.database import engine
        from backend.data.models import Base
        Base.metadata.create_all(bind=engine, tables=[SystemConfig.__table__])
        _table_checked = True
    except Exception as e:
        print(f"[PipelineConfig Table Check] {e}")


def get_pipeline_config(force_db_reload: bool = False) -> Dict[str, Any]:
    """
    현재 학습 가이드 생성 파이프라인 설정을 반환합니다.
    인메모리 캐시를 우선 확인하며, 캐시 만료 시 DB에서 로드합니다.
    DB 접속 오류 시에도 항상 안전한 기본값(DEFAULT_PIPELINE_CONFIG)을 반환합니다.
    """
    global _CACHED_CONFIG, _LAST_CACHE_TIME
    import time
    now = time.time()
    
    if not force_db_reload and _CACHED_CONFIG is not None and (now - _LAST_CACHE_TIME < CACHE_TTL_SECONDS):
        return _CACHED_CONFIG

    _ensure_table()

    try:
        with SessionLocal() as db:
            row = db.query(SystemConfig).filter(SystemConfig.key == CONFIG_KEY).first()
            if row and row.value:
                try:
                    loaded_data = json.loads(row.value)
                    if isinstance(loaded_data, dict):
                        # 기본 스키마와 병합하여 신규 필드 누락 방지
                        merged = _deep_merge(DEFAULT_PIPELINE_CONFIG, loaded_data)
                        _CACHED_CONFIG = merged
                        _LAST_CACHE_TIME = now
                        return _CACHED_CONFIG
                except Exception as parse_err:
                    print(f"[PipelineConfig Warning] JSON decode error: {parse_err}. Falling back to default.")
            
            # DB에 설정이 없으면 최초 1회 기본값 영속화
            try:
                new_row = SystemConfig(
                    key=CONFIG_KEY,
                    value=json.dumps(DEFAULT_PIPELINE_CONFIG, ensure_ascii=False),
                    description="학습 가이드 생성 파이프라인 통합 설정",
                    updated_at=datetime.now(timezone.utc)
                )
                db.add(new_row)
                db.commit()
            except Exception as insert_err:
                db.rollback()
                print(f"[PipelineConfig] Could not seed default config to DB: {insert_err}")
                
    except Exception as db_err:
        print(f"[PipelineConfig Warning] DB access failed: {db_err}. Returning fallback config.")

    # DB 접근 실패 시 인메모리 기본값 유지
    _CACHED_CONFIG = copy.deepcopy(DEFAULT_PIPELINE_CONFIG)
    _LAST_CACHE_TIME = now
    return _CACHED_CONFIG


def update_pipeline_config(updates: Dict[str, Any]) -> Dict[str, Any]:
    """
    관리자가 제출한 새로운 파이프라인 설정을 검증하고 DB에 영속화하며 캐시를 즉시 갱신합니다.
    """
    global _CACHED_CONFIG, _LAST_CACHE_TIME
    import time
    
    _ensure_table()
    current = get_pipeline_config()
    merged = _deep_merge(current, updates)
    
    # 런타임 유효성 검사
    llm = merged.get("llm", {})
    if llm.get("temperature", 0.2) < 0.0 or llm.get("temperature", 0.2) > 1.5:
        llm["temperature"] = 0.2
    if llm.get("concurrency", 3) < 1 or llm.get("concurrency", 3) > 10:
        llm["concurrency"] = 3
        
    guardrails = merged.get("guardrails", {})
    if guardrails.get("min_korean_chars", 250) < 50:
        guardrails["min_korean_chars"] = 50
    if guardrails.get("min_korean_ratio_percent", 40.0) < 10.0:
        guardrails["min_korean_ratio_percent"] = 10.0

    try:
        with SessionLocal() as db:
            row = db.query(SystemConfig).filter(SystemConfig.key == CONFIG_KEY).first()
            json_str = json.dumps(merged, ensure_ascii=False, indent=2)
            if row:
                row.value = json_str
                row.updated_at = datetime.now(timezone.utc)
            else:
                row = SystemConfig(
                    key=CONFIG_KEY,
                    value=json_str,
                    description="학습 가이드 생성 파이프라인 통합 설정",
                    updated_at=datetime.now(timezone.utc)
                )
                db.add(row)
            db.commit()
    except Exception as e:
        print(f"[PipelineConfig Error] Failed to update config in DB: {e}")
        raise RuntimeError(f"설정 저장 중 데이터베이스 오류가 발생했습니다: {str(e)}")

    _CACHED_CONFIG = merged
    _LAST_CACHE_TIME = time.time()
    return _CACHED_CONFIG


def reset_pipeline_config_to_defaults() -> Dict[str, Any]:
    """
    모든 설정을 시스템 초기 표준값(Factory Defaults)으로 리셋합니다.
    """
    return update_pipeline_config(copy.deepcopy(DEFAULT_PIPELINE_CONFIG))


def apply_pipeline_preset(preset_key: str) -> Dict[str, Any]:
    """
    특정 사전 정의 프리셋(초고속, 표준, 심화)을 현재 설정에 적용합니다.
    """
    if preset_key not in PRESETS:
        raise ValueError(f"알 수 없는 프리셋 키입니다: {preset_key}")
        
    preset_data = PRESETS[preset_key]
    patch = preset_data.get("config_patch", {})
    return update_pipeline_config(patch)


def get_all_presets_meta() -> Dict[str, Any]:
    """프론트엔드 프리셋 선택 UI를 위한 메타 정보 목록을 반환합니다."""
    return {
        key: {
            "name": val["name"],
            "description": val["description"]
        }
        for key, val in PRESETS.items()
    }
