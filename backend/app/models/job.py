from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
import uuid


class Language(str, Enum):
    HINDI = "hi-IN"
    TAMIL = "ta-IN"
    BENGALI = "bn-IN"
    GUJARATI = "gu-IN"
    KANNADA = "kn-IN"
    MALAYALAM = "ml-IN"
    MARATHI = "mr-IN"
    ODIA = "od-IN"
    PUNJABI = "pa-IN"
    TELUGU = "te-IN"
    URDU = "ur-IN"


LANGUAGE_NAMES = {
    Language.HINDI: "Hindi",
    Language.TAMIL: "Tamil",
    Language.BENGALI: "Bengali",
    Language.GUJARATI: "Gujarati",
    Language.KANNADA: "Kannada",
    Language.MALAYALAM: "Malayalam",
    Language.MARATHI: "Marathi",
    Language.ODIA: "Odia",
    Language.PUNJABI: "Punjabi",
    Language.TELUGU: "Telugu",
    Language.URDU: "Urdu",
}


class ProcessingTier(str, Enum):
    STARTER = "starter"       # Subtitles (SRT) only — ₹150/min/lang
    STANDARD = "standard"     # Subtitles + AI dubbing — ₹350-500/min/lang
    PREMIUM = "premium"       # Dubbing + Lip Sync + Review — ₹700-1000/min/lang


class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    AWAITING_REVIEW = "awaiting_review"
    REVIEW_APPROVED = "review_approved"
    COMPLETED = "completed"
    FAILED = "failed"


class StageStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    SKIPPED = "skipped"
    ERROR = "error"


class PipelineStage(BaseModel):
    name: str
    status: StageStatus = StageStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    meta: Dict[str, Any] = Field(default_factory=dict)


class TranscriptSegment(BaseModel):
    id: int
    start: float   # seconds
    end: float
    text: str
    speaker: Optional[str] = None


class TranslatedSegment(BaseModel):
    id: int
    start: float
    end: float
    source_text: str
    translated_text: str
    language: Language
    reviewer_approved: bool = False
    reviewer_edited: Optional[str] = None
    qa_flags: List[str] = Field(default_factory=list)


class JobCreateRequest(BaseModel):
    title: str
    source_language: str = "en-IN"
    target_languages: List[Language]
    tier: ProcessingTier = ProcessingTier.STANDARD
    client_name: Optional[str] = None
    notes: Optional[str] = None


class Job(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    source_language: str = "en-IN"
    target_languages: List[Language]
    tier: ProcessingTier
    status: JobStatus = JobStatus.PENDING
    client_name: Optional[str] = None
    notes: Optional[str] = None

    # File paths
    input_video_path: Optional[str] = None
    extracted_audio_path: Optional[str] = None
    output_paths: Dict[str, str] = Field(default_factory=dict)  # lang -> output path

    # Pipeline progress
    stages: List[PipelineStage] = Field(default_factory=list)
    progress_pct: int = 0

    # Transcript
    transcript: List[TranscriptSegment] = Field(default_factory=list)
    translations: Dict[str, List[TranslatedSegment]] = Field(default_factory=dict)  # lang -> segments

    # Metadata
    duration_seconds: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    error: Optional[str] = None

    def update_stage(self, stage_name: str, status: StageStatus, error: str = None, meta: dict = None):
        for stage in self.stages:
            if stage.name == stage_name:
                stage.status = status
                if status == StageStatus.RUNNING:
                    stage.started_at = datetime.utcnow()
                elif status in (StageStatus.DONE, StageStatus.ERROR, StageStatus.SKIPPED):
                    stage.completed_at = datetime.utcnow()
                if error:
                    stage.error = error
                if meta:
                    stage.meta.update(meta)
                return
        # Stage not found — create it
        new_stage = PipelineStage(name=stage_name, status=status)
        if meta:
            new_stage.meta = meta
        self.stages.append(new_stage)
