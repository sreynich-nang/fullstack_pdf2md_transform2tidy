from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from app.core.config import settings as app_settings

TRANSFORM_ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = TRANSFORM_ROOT / ".env.transform2tidy"


def _load_env_file() -> None:
    """Populate os.environ with key/value pairs from the optional .env file."""
    if not ENV_FILE.exists():
        return

    for raw_line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.split("#", 1)[0].strip().strip('"').strip("'")
        if key and value and key not in os.environ:
            os.environ[key] = value


_load_env_file()


@dataclass(frozen=True)
class LLMConfig:
    api_key: str
    model: str
    temperature: float
    max_tokens: int


def get_llm_config() -> LLMConfig:
    api_key = os.environ.get("LLM_API_KEY")
    if not api_key:
        raise RuntimeError(
            "LLM_API_KEY is not set. Update .env.transform2tidy or export the variable first."
        )

    return LLMConfig(
        api_key=api_key,
        model=os.environ.get("LLM_MODEL", "gemini-2.5-flash"),
        temperature=float(os.environ.get("LLM_TEMPERATURE", "0.7")),
        max_tokens=int(os.environ.get("LLM_MAX_TOKENS", "4096")),
    )


EACH_TABLE_DIR = app_settings.get_path(app_settings.EACH_TABLE_DIR)
PROFILE_RAW_DF_DIR = app_settings.get_path(app_settings.PROFILE_RAW_DF_DIR)
PROMPT1_PROFILE_DIR = app_settings.get_path(app_settings.PROMPT1_PROFILE_DIR)
PROMPT2_PROMPT1_DIR = app_settings.get_path(app_settings.PROMPT2_PROMPT1_DIR)
PROMPT3_PROMPT2_DIR = app_settings.get_path(app_settings.PROMPT3_PROMPT2_DIR)
CLEANED_DATA_DIR = app_settings.get_path(app_settings.CLEANED_DATA_DIR)
TRANSFORM_TEMP_DIR = app_settings.get_path(app_settings.TRANSFORM_DIR)


def ensure_directories(directories: Iterable[Path]) -> None:
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


ensure_directories(
    [
        EACH_TABLE_DIR,
        PROFILE_RAW_DF_DIR,
        PROMPT1_PROFILE_DIR,
        PROMPT2_PROMPT1_DIR,
        PROMPT3_PROMPT2_DIR,
        CLEANED_DATA_DIR,
        TRANSFORM_TEMP_DIR,
    ]
)
