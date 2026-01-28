"""
Application Configuration
"""
from pydantic_settings import BaseSettings
from pathlib import Path
from typing import List


class Settings(BaseSettings):
    """Application settings"""
    
    # Application Info
    APP_NAME: str = "DocumentProcessingPipeline"
    APP_VERSION: str = "5.0.0"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    
    # API Settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    # File Upload Settings
    MAX_UPLOAD_SIZE: int = 50000000  # 50MB
    ALLOWED_EXTENSIONS: str = "pdf,png,jpg,jpeg"
    
    # Directory Settings
    TEMP_DIR: str = "temp"
    UPLOADS_DIR: str = "temp/uploads"
    OUTPUTS_DIR: str = "temp/outputs"
    PDF2IMAGE_DIR: str = "temp/pdf2image"
    EACH_TABLE_DIR: str = "temp/each_table"
    TRANSFORM_DIR: str = "temp/transform2tidy"
    LOGS_DIR: str = "logs"
    
    # Transform2Tidy Subdirectories
    CLEANED_DATA_DIR: str = "temp/transform2tidy/cleaned_data"
    PROFILE_RAW_DF_DIR: str = "temp/transform2tidy/profile_raw_df"
    PROMPT1_PROFILE_DIR: str = "temp/transform2tidy/prompt1_profile"
    PROMPT2_PROMPT1_DIR: str = "temp/transform2tidy/prompt2_prompt1"
    PROMPT3_PROMPT2_DIR: str = "temp/transform2tidy/prompt3_prompt2"
    
    # # Anthropic API Settings
    # ANTHROPIC_API_KEY: str = ""
    # TRANSFORM_MODEL: str = "claude-sonnet-4-20250514"
    TRANSFORM_MAX_TOKENS: int = 4000
    TRANSFORM_TEMPERATURE: float = 0.0
    
    @property
    def allowed_extensions_list(self) -> List[str]:
        """Get list of allowed file extensions"""
        return [ext.strip() for ext in self.ALLOWED_EXTENSIONS.split(",")]
    
    @property
    def base_dir(self) -> Path:
        """Get base directory"""
        return Path(__file__).parent.parent.parent
    
    def get_path(self, path_str: str) -> Path:
        """Get absolute path from relative path string"""
        return self.base_dir / path_str
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()