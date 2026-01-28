"""
Stage 3: Reasoning - Analyze table errors using prompt1 and profile data.
LLM-based analysis: Use Gemini to understand and explain table issues.

Input: prompt1 template + profile_raw_df JSON
Output: JSON files (document_name/prompt1_table1.json, prompt1_table2.json, ...)
"""

import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List

import google.generativeai as genai

PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.services.transform2tidy.pipeline.settings import (
    EACH_TABLE_DIR,
    PROMPT1_PROFILE_DIR,
    get_llm_config,
)
from app.utils.prompt_loader import load_prompt, render_prompt


logger = logging.getLogger(__name__)
PROMPT1_TEMPLATE = load_prompt("prompt_1_table_error_understanding.md")


def analyze_table_errors(
    api_key: str,
    model: str,
    temperature: float,
    max_tokens: int,
    table_profile: Dict[str, Any],
    csv_path: Path
) -> Dict[str, Any]:
    
    # Configure Gemini
    genai.configure(api_key=api_key)
    
    # Load and read CSV for context
    import pandas as pd
    df = pd.read_csv(csv_path, encoding="utf-8")
    
    # CORE TASK: Prepare flexible variables and render prompt with profile JSON
    # Profile JSON is the main variable from temp/profile_raw_df/{doc_name}/profile_table{N}.json
    variables = {
        "PROFILE_JSON": table_profile,      # Main variable: Profile JSON data
        "table_preview": df.head(10).to_string(),
        "column_info": list(df.columns),
        "row_count": len(df),
        "column_count": len(df.columns)
    }
    
    # Render prompt: render_prompt(PROMPT_1_FILE_content, profile_raw_df_json + other variables)
    try:
        rendered_prompt = render_prompt(PROMPT1_TEMPLATE, variables, strict=False)
    except Exception:
        logger.warning("Falling back to raw prompt template for %s", csv_path.name)
        rendered_prompt = PROMPT1_TEMPLATE
    
    # Call Gemini API with rendered prompt
    model_obj = genai.GenerativeModel(model)
    response = model_obj.generate_content(
        rendered_prompt,
        generation_config={
            "temperature": temperature,
            "max_output_tokens": max_tokens,
        }
    )
    
    # Parse response
    analysis_result = {
        "status": "success",
        "model": model,
        "analysis": response.text,
        "table_profile": table_profile,
        "csv_path": str(csv_path)
    }
    
    return analysis_result


def save_analysis_as_json(
    analysis: Dict[str, Any],
    output_dir: Path,
    doc_name: str,
    table_num: int
) -> Path:
    
    doc_subdir = output_dir / doc_name
    doc_subdir.mkdir(parents=True, exist_ok=True)
    
    json_path = doc_subdir / f"prompt1_table{table_num}.json"
    
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False)
    
    return json_path


def process_tables_with_prompt1(
    api_key: str,
    model: str,
    temperature: float,
    max_tokens: int,
    csv_paths: List[Path],
    profile_json_paths: List[Path],
    output_dir: Path,
    doc_name: str
) -> List[Path]:
    
    result_paths = []
    import re
    
    for csv_path, profile_path in zip(csv_paths, profile_json_paths):
        # Extract table number from filename (e.g., profile_table11 -> 11)
        table_num = len(result_paths) + 1
        
        # Robust extraction of table number: looks for 'table' followed by digits
        # This handles profile_table11.json, table11_profile.json, and table11.json
        match = re.search(r"table(\d+)", profile_path.stem)
        if match:
            table_num = int(match.group(1))

        # Load profile JSON from temp/profile_raw_df/{doc_name}/profile_table{N}.json
        with open(profile_path, "r", encoding="utf-8") as f:
            profile = json.load(f)
        
        # Core task: Analyze table using render_prompt() with PROMPT_1_FILE and profile JSON
        analysis = analyze_table_errors(
            api_key=api_key,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            table_profile=profile,  # Flexible variable: profile JSON from temp/profile_raw_df/
            csv_path=csv_path
        )
        
        # Save result to temp/prompt1_profile/{doc_name}/prompt1_table{N}.json
        result_path = save_analysis_as_json(analysis, output_dir, doc_name, table_num)
        result_paths.append(result_path)
    
    return result_paths

if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    parser = argparse.ArgumentParser(description="Analyze table errors using prompt1.")
    parser.add_argument("input_profiles", nargs="+", type=Path, help="Input profile JSON files")
    parser.add_argument("--output-dir", type=Path, default=PROMPT1_PROFILE_DIR, help="Output directory for analysis JSONs")

    args = parser.parse_args()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    llm_cfg = get_llm_config()

    csv_paths: List[Path] = []
    profile_paths: List[Path] = []
    doc_name = None

    for profile_path in args.input_profiles:
        if not profile_path.exists():
            logger.warning("Profile not found: %s", profile_path)
            continue

        current_doc_name = profile_path.parent.name
        if doc_name is None:
            doc_name = current_doc_name
        elif doc_name != current_doc_name:
            logger.warning("Mixed documents detected. Using %s for output grouping.", doc_name)

        filename = profile_path.stem
        if filename.startswith("profile_"):
            table_name = filename.replace("profile_", "")
        elif filename.endswith("_profile"):
            table_name = filename[:-8]
        else:
            table_name = filename

        csv_path = EACH_TABLE_DIR / current_doc_name / f"{table_name}.csv"
        if not csv_path.exists():
            logger.error("Corresponding CSV not found for %s", profile_path)
            logger.error("Expected at: %s", csv_path)
            continue

        csv_paths.append(csv_path)
        profile_paths.append(profile_path)

    if not csv_paths or doc_name is None:
        logger.error("No valid input pairs found.")
        sys.exit(1)

    logger.info("Processing %s tables for document '%s'...", len(csv_paths), doc_name)

    output_paths = process_tables_with_prompt1(
        api_key=llm_cfg.api_key,
        model=llm_cfg.model,
        temperature=llm_cfg.temperature,
        max_tokens=llm_cfg.max_tokens,
        csv_paths=csv_paths,
        profile_json_paths=profile_paths,
        output_dir=output_dir,
        doc_name=doc_name,
    )

    logger.info("Generated %s analyses in %s", len(output_paths), output_dir / doc_name)
