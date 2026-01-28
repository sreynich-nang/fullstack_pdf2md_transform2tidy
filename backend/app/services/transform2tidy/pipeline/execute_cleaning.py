"""
Stage 6: Execute cleaning scripts on extracted tables.
=> Run the generated Python cleaning scripts on the raw CSV files to produce cleaned data.

Input: temp/prompt3_prompt2/document_name/prompt3_py1.py, prompt3_py2.py, ... + raw CSVs from temp/each_table/document_name/table1.csv, table2.csv, ...
Output: CSV files (temp/cleaned_data/document_name/cleaned_table1.csv, cleaned_table2.csv, ...)
"""
import sys
import json
import logging
import importlib.util
import pandas as pd
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional

logger = logging.getLogger(__name__)

def load_module_from_path(script_path: Path):
    try:
        module_name = script_path.stem
        spec = importlib.util.spec_from_file_location(module_name, script_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load spec for module from {script_path}")
        
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module
    except Exception as e:
        logger.error(f"Failed to load module {script_path}: {e}")
        raise

def run_cleaning_script(script_path: Path, csv_path: Path, output_dir: Path) -> Optional[Path]:
    try:
        # 1. Load Data
        logger.info(f"    Processing {csv_path.name} with {script_path.name}")
        df_raw = pd.read_csv(csv_path)
        
        # 2. Load Script
        module = load_module_from_path(script_path)
        
        if not hasattr(module, "transform2tidy_table"):
            logger.error(f"    Function 'transform2tidy_table' not found in {script_path.name}")
            return None
            
        # 3. Execute Cleaning
        try:
            # Expected return signature: df_clean, cleaning_log
            result = module.transform2tidy_table(df_raw)
            
            # Handle variable return types gracefully
            if isinstance(result, tuple) and len(result) == 2:
                df_clean, cleaning_log = result
            else:
                # If only dataframe returned
                df_clean = result
                cleaning_log = [{"step": "Unknown", "action": "Script returned only DataFrame"}]
                
        except Exception as e:
            logger.error(f"    Runtime error in cleaning script: {e}")
            return None
            
        # 4. Save Results
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Determine table number/name for output filenames
        # script name is usually prompt3_py{N}.py
        # csv name is usually table{N}.csv
        base_name = csv_path.stem # table1
        
        cleaned_csv_path = output_dir / f"cleaned_{base_name}.csv"
        log_json_path = output_dir / f"log_{base_name}.json"
        
        df_clean.to_csv(cleaned_csv_path, index=False)
        
        with open(log_json_path, 'w', encoding='utf-8') as f:
            json.dump(cleaning_log, f, indent=2, ensure_ascii=False)
            
        return cleaned_csv_path

    except Exception as e:
        logger.error(f"    Error processing pair ({script_path.name}, {csv_path.name}): {e}", exc_info=True)
        return None

def execute_cleaning_scripts(execution_pairs: List[Tuple[Path, Path]], output_dir: Path) -> List[Path]:
    successful_outputs = []
    
    if not execution_pairs:
        logger.warning("No execution pairs provided to execute_cleaning_scripts")
        return []
        
    for script_path, csv_path in execution_pairs:
        result_path = run_cleaning_script(script_path, csv_path, output_dir)
        if result_path:
            successful_outputs.append(result_path)
            
    return successful_outputs

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run a generated cleaning script on a CSV table.")
    parser.add_argument("csv_path", type=Path, help="Path to the raw CSV file")
    parser.add_argument("script_path", type=Path, help="Path to the Python cleaning script")
    
    args = parser.parse_args()
    
    print(f"Running cleaning...")
    print(f"CSV: {args.csv_path}")
    print(f"Script: {args.script_path}")
    
    # Configure logging for standalone run if not already configured
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    
    if not args.csv_path.exists():
        print(f"Error: CSV file not found: {args.csv_path}")
        sys.exit(1)
        
    if not args.script_path.exists():
        print(f"Error: Script file not found: {args.script_path}")
        sys.exit(1)

    # Automatically determine output directory based on doc name
    # e.g., temp/each_table/tidy1/table1.csv -> doc_name = tidy1
    doc_name = args.csv_path.parent.name
    output_dir = Path("temp/cleaned_data") / doc_name
    print(f"Output Directory: {output_dir}")

    result = run_cleaning_script(args.script_path, args.csv_path, output_dir)
    
    if result:
        print(f"Success! Output saved to: {result}")
    else:
        print("Execution failed.")
        sys.exit(1)
