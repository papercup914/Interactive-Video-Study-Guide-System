"""
Interactive Video Study Guide System - Pydantic DTO Schemas
"""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

class StudyGuideCreateDTO(BaseModel):
    """학습 가이드 생성 및 저장용 DTO"""
    job_id: str = Field(..., description="작업 고유 ID")
    url: str = Field(default="", description="영상 또는 원본 URL")
    title: str = Field(default="", description="가이드 제목")
    image_url: str = Field(default="", description="대표 이미지 URL")
    provider: str = Field(default="youtube", description="AI 모델 또는 소스 제공자")
    document: Dict[str, Any] = Field(default_factory=dict, description="챕터별 마크다운 문서")
    learning_profile: str = Field(default="", description="학습자 프로필 JSON 문자열")
    profile_message: str = Field(default="", description="맞춤형 프로필 환영 메시지")
    generation_time_sec: int = Field(default=0, description="가이드 생성 소요 시간(초)")
    length_preset: Optional[str] = Field(default=None, description="요약 분량 프리셋")
    analogy_preset: Optional[str] = Field(default=None, description="설명 방식 프리셋")
    video_duration: Optional[str] = Field(default=None, description="영상 길이")

class StudyGuideReadDTO(BaseModel):
    """학습 가이드 조회 응답용 DTO"""
    id: str
    video_id: Optional[str] = None
    url: str = ""
    title: str = ""
    image_url: Optional[str] = None
    provider: str = ""
    document: Dict[str, Any] = Field(default_factory=dict)
    notes: List[Dict[str, Any]] = Field(default_factory=list)
    learning_profile: Optional[Dict[str, Any]] = None
    profile_message: Optional[str] = None
    generation_time_sec: int = 0
    length_preset: Optional[str] = None
    analogy_preset: Optional[str] = None
    video_duration: Optional[str] = None
    created_at: Optional[str] = None
