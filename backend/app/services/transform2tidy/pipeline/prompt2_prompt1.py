"""
Stage 4: Strategic - Generate remediation strategy using prompt2.
LLM-based strategy generation: Use Gemini to create cleaning strategies.

Input: prompt2 template + prompt1 analysis
Output: Markdown files (document_name/prompt2_table1.md, prompt2_table2.md, ...)

# Core workflow flow:
analysis_json (from temp/prompt1_profile/)
    ↓
parse_str2json(analysis_text)  # Convert LLM text to JSON
    ↓
<PROMPT1_ERROR_DIAGNOSIS_JSON> variable
    ↓
render_prompt(PROMPT_2_FILE, variables)  # Core task
    ↓
Gemini API
    ↓
Save to temp/prompt2_prompt1/{doc_name}/
"""


import json
import logging
import re
import sys
from pathlib import Path
from typing import List

import google.generativeai as genai

PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.services.transform2tidy.pipeline.settings import (
    PROMPT2_PROMPT1_DIR,
    get_llm_config,
)
from app.utils.prompt_loader import load_prompt, render_prompt


logger = logging.getLogger(__name__)
PROMPT2_TEMPLATE = load_prompt("prompt_2_remediation_strategy.md")


def parse_str2json(text: str) -> dict:
    """
    Safely parse JSON returned by an LLM.
    Handles markdown code fences and JSON formatting issues.
    
    Args:
        text: LLM response text (may contain ```json code fences)
        
    Returns:
        Parsed JSON dictionary
    """
    text = text.strip()
    
    # Remove ```json or ``` fences
    text = re.sub(r"^```(?:json)?", "", text)
    text = re.sub(r"```$", "", text)
    text = text.strip()
    
    return json.loads(text)


def generate_remediation_strategy(
    api_key: str,
    model: str,
    temperature: float,
    max_tokens: int,
    analysis_json: dict
) -> str:
    
    # Configure Gemini
    genai.configure(api_key=api_key)
    
    # Parse prompt1 result: Extract analysis text and convert to JSON
    # analysis_json has: {"status": "success", "analysis": "<LLM_text>", ...}
    analysis_text = analysis_json.get("analysis", "{}")
    
    # Try to parse the analysis text as JSON (it may contain JSON from prompt1)
    try:
        prompt1_error_diagnosis = parse_str2json(analysis_text)
    except (json.JSONDecodeError, ValueError):
        # If parsing fails, use the raw text as is
        prompt1_error_diagnosis = {"raw_analysis": analysis_text}
    
    # CORE TASK: Prepare flexible variables and render prompt with parsed prompt1 JSON
    variables = {
        "PROMPT1_ERROR_DIAGNOSIS_JSON": prompt1_error_diagnosis,  # Main variable: parsed prompt1 result
        "analysis": analysis_text,
        "table_profile": analysis_json.get("table_profile", {}),
    }
    
    # Render prompt: render_prompt(PROMPT_2_FILE, prompt1_error_diagnosis_json + other variables)
    try:
        rendered_prompt = render_prompt(PROMPT2_TEMPLATE, variables, strict=False)
    except Exception:
        logger.warning("Falling back to raw prompt2 template for %s", analysis_json.get("csv_path"))
        rendered_prompt = PROMPT2_TEMPLATE
    
    # Call Gemini API with rendered prompt
    model_obj = genai.GenerativeModel(model)
    response = model_obj.generate_content(
        rendered_prompt,
        generation_config={
            "temperature": temperature,
            "max_output_tokens": max_tokens,
        }
    )
    
    return response.text

def save_strategy_as_markdown(
    strategy: str,
    output_dir: Path,
    doc_name: str,
    table_num: int
) -> Path:
    
    doc_subdir = output_dir / doc_name
    doc_subdir.mkdir(parents=True, exist_ok=True)
    
    md_path = doc_subdir / f"prompt2_table{table_num}.md"
    
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(strategy)
    
    return md_path


def process_tables_with_prompt2(
    api_key: str,
    model: str,
    temperature: float,
    max_tokens: int,
    analysis_json_paths: List[Path],
    output_dir: Path,
    doc_name: str
) -> List[Path]:
    
    import re

    result_paths = []
    
    for analysis_path in analysis_json_paths:
        # Extract table number from filename (e.g., prompt1_table11 -> 11)
        # Default fallback
        table_num = len(result_paths) + 1
        
        # Robust regex extraction to handle prompt1_table5.json -> 5
        match = re.search(r"table(\d+)", analysis_path.stem)
        if match:
            table_num = int(match.group(1))

        # Load analysis JSON from temp/prompt1_profile/{doc_name}/prompt1_table{N}.json
        with open(analysis_path, "r", encoding="utf-8") as f:
            analysis_json = json.load(f)
        
        # Core task: Generate strategy using render_prompt() with PROMPT_2_FILE and parsed prompt1 JSON
        strategy = generate_remediation_strategy(
            api_key=api_key,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            analysis_json=analysis_json  # Flexible variable: prompt1 analysis from temp/prompt1_profile/
        )
        
        # Save strategy to temp/prompt2_prompt1/{doc_name}/prompt2_table{N}.md
        result_path = save_strategy_as_markdown(strategy, output_dir, doc_name, table_num)
        result_paths.append(result_path)
    
    return result_paths

if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    parser = argparse.ArgumentParser(description="Generate remediation strategies using prompt2.")
    parser.add_argument("input_analyses", nargs="+", type=Path, help="Input prompt1 analysis JSON files")
    parser.add_argument("--output-dir", type=Path, default=PROMPT2_PROMPT1_DIR, help="Output directory for strategy MD files")

    args = parser.parse_args()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    llm_cfg = get_llm_config()

    analysis_paths: List[Path] = []
    doc_name = None

    for analysis_path in args.input_analyses:
        if not analysis_path.exists():
            logger.warning("Analysis file not found: %s", analysis_path)
            continue

        current_doc_name = analysis_path.parent.name
        if doc_name is None:
            doc_name = current_doc_name
        elif doc_name != current_doc_name:
            logger.warning("Mixed documents detected. Using %s for output grouping.", doc_name)

        analysis_paths.append(analysis_path)

    if not analysis_paths or doc_name is None:
        logger.error("No valid input files found.")
        sys.exit(1)

    logger.info("Processing %s analyses for document '%s'...", len(analysis_paths), doc_name)

    output_paths = process_tables_with_prompt2(
        api_key=llm_cfg.api_key,
        model=llm_cfg.model,
        temperature=llm_cfg.temperature,
        max_tokens=llm_cfg.max_tokens,
        analysis_json_paths=analysis_paths,
        output_dir=output_dir,
        doc_name=doc_name,
    )

    logger.info("Generated %s strategies in %s", len(output_paths), output_dir / doc_name)
