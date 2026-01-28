from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

from app.core.exeception import FileNotFoundException, ProcessingException
from app.core.logger import get_logger
from app.services.transform2tidy.pipeline.execute_cleaning import execute_cleaning_scripts
from app.services.transform2tidy.pipeline.profile_raw_df import process_tables_to_profiles
from app.services.transform2tidy.pipeline.prompt1_profile import process_tables_with_prompt1
from app.services.transform2tidy.pipeline.prompt2_prompt1 import process_tables_with_prompt2
from app.services.transform2tidy.pipeline.prompt3_prompt2 import process_tables_with_prompt3
from app.services.transform2tidy.pipeline.settings import (
    CLEANED_DATA_DIR,
    EACH_TABLE_DIR,
    PROFILE_RAW_DF_DIR,
    PROMPT1_PROFILE_DIR,
    PROMPT2_PROMPT1_DIR,
    PROMPT3_PROMPT2_DIR,
    get_llm_config,
)

logger = get_logger(__name__)


def _resolve_table_csv(doc_name: str, table_id: str) -> Path:
    doc_dir = EACH_TABLE_DIR / doc_name
    if not doc_dir.exists():
        raise FileNotFoundException(f"Tables directory not found for document '{doc_name}'")

    base = table_id.replace(".csv", "")
    candidates: List[Path] = [doc_dir / base, doc_dir / f"{base}.csv"]
    for candidate in candidates:
        if candidate.exists():
            return candidate

    # Fall back to scanning the directory for a matching stem (case-insensitive)
    lowered = base.lower()
    for candidate in doc_dir.glob("*.csv"):
        if candidate.stem.lower() == lowered:
            return candidate

    raise FileNotFoundException(f"Table '{table_id}' not found for document '{doc_name}'")


def run_transform_pipeline(doc_name: str, table_id: str) -> Dict[str, Any]:
    csv_path = _resolve_table_csv(doc_name, table_id)
    logger.info("Running transform2tidy pipeline for %s/%s", doc_name, csv_path.name)

    llm_cfg = get_llm_config()

    profile_paths = process_tables_to_profiles([csv_path], PROFILE_RAW_DF_DIR, doc_name=doc_name)
    if not profile_paths:
        raise ProcessingException("profiling", "No profile JSON produced")
    profile_path = profile_paths[0]

    prompt1_paths = process_tables_with_prompt1(
        api_key=llm_cfg.api_key,
        model=llm_cfg.model,
        temperature=llm_cfg.temperature,
        max_tokens=llm_cfg.max_tokens,
        csv_paths=[csv_path],
        profile_json_paths=[profile_path],
        output_dir=PROMPT1_PROFILE_DIR,
        doc_name=doc_name,
    )
    if not prompt1_paths:
        raise ProcessingException("prompt1", "Failed to generate prompt1 output")

    prompt2_paths = process_tables_with_prompt2(
        api_key=llm_cfg.api_key,
        model=llm_cfg.model,
        temperature=llm_cfg.temperature,
        max_tokens=llm_cfg.max_tokens,
        analysis_json_paths=prompt1_paths,
        output_dir=PROMPT2_PROMPT1_DIR,
        doc_name=doc_name,
    )
    if not prompt2_paths:
        raise ProcessingException("prompt2", "Failed to generate remediation strategy")

    prompt3_paths = process_tables_with_prompt3(
        api_key=llm_cfg.api_key,
        model=llm_cfg.model,
        temperature=llm_cfg.temperature,
        max_tokens=llm_cfg.max_tokens,
        profile_json_paths=[profile_path],
        strategy_md_paths=prompt2_paths,
        output_dir=PROMPT3_PROMPT2_DIR,
        doc_name=doc_name,
    )
    if not prompt3_paths:
        raise ProcessingException("prompt3", "Failed to generate cleaning code")

    cleaned_dir = CLEANED_DATA_DIR / doc_name
    cleaned_paths = execute_cleaning_scripts([(prompt3_paths[0], csv_path)], cleaned_dir)
    if not cleaned_paths:
        raise ProcessingException("execute_cleaning", "Cleaning script did not produce output")
    cleaned_path = cleaned_paths[0]

    num_rows_original = len(pd.read_csv(csv_path))
    num_rows_cleaned = len(pd.read_csv(cleaned_path))

    log_path = cleaned_dir / f"log_{csv_path.stem}.json"

    return {
        "profile_path": profile_path,
        "prompt1_path": prompt1_paths[0],
        "prompt2_path": prompt2_paths[0],
        "prompt3_path": prompt3_paths[0],
        "cleaned_csv_path": cleaned_path,
        "num_rows_original": num_rows_original,
        "num_rows_cleaned": num_rows_cleaned,
        "summary": {
            "log_path": str(log_path) if log_path.exists() else None,
        },
    }
