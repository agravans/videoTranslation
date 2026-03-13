from pydantic_settings import BaseSettings
from pathlib import Path
from typing import Optional


class Settings(BaseSettings):
    # Sarvam AI
    sarvam_api_key: str = ""
    sarvam_base_url: str = "https://api.sarvam.ai"

    # Anthropic
    anthropic_api_key: str = ""

    # OpenAI (Whisper API fallback)
    openai_api_key: str = ""

    # ElevenLabs
    elevenlabs_api_key: str = ""

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # AWS S3
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_region: str = "ap-south-1"
    s3_bucket: str = ""

    # App
    app_env: str = "development"
    debug: bool = True
    max_video_size_mb: int = 500
    upload_dir: str = "./uploads"
    output_dir: str = "./outputs"
    log_level: str = "INFO"

    # Whisper
    whisper_model: str = "base"

    # Mock modes for testing without API keys
    mock_sarvam: bool = False
    mock_claude: bool = False

    class Config:
        env_file = ".env"
        extra = "ignore"

    def ensure_dirs(self):
        Path(self.upload_dir).mkdir(parents=True, exist_ok=True)
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.ensure_dirs()
