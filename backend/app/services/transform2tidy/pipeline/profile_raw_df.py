"""
Stage 2: Profile raw dataframes extracted from markdown tables.
=> Primary goal is to compress and summarize the raw CSV daata into a format that LLM can undestand. Due to LLM have token limits, given the whole dataframe is not an ideal, that giving only the profile is a choice. The following are the steps:
  - Table shape (rows, columns)
  - Column types
  - Column roles (dimension, measure)
  - Missingness
  - Cadinality
  - Sample values
  - Presence of total rows

Input: CSV file (table1.csv, table2.csv, ...)
Output: JSON files (temp/profile_raw_df/document_name/profile_table1.json, profile_table2.json, ...)
"""
import argparse
import json
from pathlib import Path
import pandas as pd
import numpy as np
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def convert_np_types(obj):
    if isinstance(obj, dict):
        return {k: convert_np_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_np_types(v) for v in obj]
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    else:
        return obj

def profile_dataframe(df: pd.DataFrame):
    profile = {
        "shape": {"rows": df.shape[0], "columns": df.shape[1]},
        "columns": [],
        "suspected_totals_rows": [],
        "header_samples": [df.columns.tolist()]
    }

    suspected_total_labels = ["Total", "Grand Total", "Subtotal"]
    profile["suspected_totals_rows"] = df.index[df.iloc[:, 0].astype(str).str.strip().isin(suspected_total_labels)].tolist()

    for col in df.columns:
        series = df[col]
        col_profile = {
            "name": col,
            "dtype": str(series.dtype),
            "semantic_type": "numeric" if pd.api.types.is_numeric_dtype(series) else "categorical",
            "role": "measure" if pd.api.types.is_numeric_dtype(series) else "dimension",
            "null_ratio": float(series.isnull().mean()),
            "unique_ratio": float(series.nunique(dropna=True) / len(series)) if len(series) > 0 else 0.0,
            "sample_values": series.dropna().head(5).tolist(),
            "contains_total_labels": bool(series.astype(str).str.strip().isin(suspected_total_labels).any())
        }
        profile["columns"].append(col_profile)

    return convert_np_types(profile)

def process_table_file(file_path: Path, base_output_dir: Path, base_input_dir: Path):
    """
    base_input_dir: the root folder of CSVs (e.g., temp/each_table)
    base_output_dir: root folder for profiles (e.g., temp/profile_raw_df)
    """
    logger.info(f"Profiling {file_path}...")
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        logger.error(f"Failed to read CSV {file_path}: {e}")
        return

    profile = profile_dataframe(df)

    # Compute relative path from base input
    relative_path = file_path.relative_to(base_input_dir).parent  # e.g., tidy1
    output_dir = base_output_dir / relative_path
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / f"{file_path.stem}_profile.json"
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(profile, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved profile to {output_file}")
    except Exception as e:
        logger.error(f"Error dumping JSON profile: {e}")
def process_tables_to_profiles(csv_paths, output_dir, doc_name=None):
    """
    Wrapper function to process a list of CSV paths.
    Compatible with main.py pipeline call.
    """
    logger.info(f"Processing {len(csv_paths)} tables for profiling...")
    result_paths = []
    
    # We need to determine the 'base_input_dir' for process_table_file relative calculation
    # Typically this is 'temp/each_table'
    # We can infer it from the first CSV path
    if not csv_paths:
        return []
        
    # Assuming csv_paths[0] is like .../temp/each_table/doc_name/table1.csv
    # We want base_input_dir to be .../temp/each_table
    base_input_dir = csv_paths[0].parent.parent
    
    for csv_path in csv_paths:
        process_table_file(csv_path, output_dir, base_input_dir)
        
        # Calculate expected output path to add to results
        # process_table_file saves as {csv_stem}_profile.json in output_dir/doc_name/
        relative_path = csv_path.relative_to(base_input_dir).parent # doc_name
        json_path = output_dir / relative_path / f"{csv_path.stem}_profile.json"
        if json_path.exists():
            result_paths.append(json_path)
            
    return result_paths


def main():
    parser = argparse.ArgumentParser(description="Profile raw CSV table to JSON")
    parser.add_argument("input_path", type=str, help="Path to CSV file or folder")
    parser.add_argument("--output-dir", type=str, default="temp/profile_raw_df", help="Directory to save JSON profiles")
    args = parser.parse_args()

    input_path = Path(args.input_path).resolve()
    output_dir = Path(args.output_dir).resolve()

    if input_path.is_file():
        # Determine base input folder as parent of CSV
        base_input_dir = input_path.parent.parent  # e.g., temp/each_table
        process_table_file(input_path, output_dir, base_input_dir)
    elif input_path.is_dir():
        # Assume folder contains subfolders like tidy1, tidy2...
        base_input_dir = input_path.resolve()
        csv_files = list(input_path.rglob("*.csv"))
        logger.info(f"Processing {len(csv_files)} CSV files...")
        for csv_file in csv_files:
            process_table_file(csv_file, output_dir, base_input_dir)
    else:
        logger.error(f"Input path {input_path} is neither a file nor a directory")

if __name__ == "__main__":
    main()

