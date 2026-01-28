# About

Automatically extract tabular data from PDF documents, clean and normalize the extracted content, and transform it into structured, tidy datasets that follow Hadley Wickham’s Tidy Data principles. The system supports reliable parsing, validation, and reshaping of complex multi-header tables into analysis-ready formats.

## Example

## Project Working-Flow
The system processes a user-uploaded file through an **API Gateway**, which routes it to a **Backend Processing Pipeline**. The pipeline transforms raw data into a **tidy format**, generates Python code to execute transformations, validates results, and optionally uses an **LLM** to explain errors or optimize transformations. The final output is returned to the user.

### Marker Backend
This is likely the initial File Upload Handler in the API Gateway Layer. It:
- Receives the uploaded file (e.g., CSV, image, document) from the user.
- Validates and temporarily stores the file.
- Triggers the next stage (Extract from Markdown2CSV or similar) for further processing.

### Extract from Markdown2CSV
This step appears to be part of the transform2tidy process, where:
- Raw data (possibly from Markdown or unstructured formats) is extracted into structured CSV format.
- Each original "wide" table is converted into separate CSV files.
- This prepares data for tidying in the next stage.

### Transform2Tidy Backend
This is the core processing pipeline that:
- Takes CSV of each wide Table (raw, untidy data).
- Converts it into a CSV of TIDY Format (normalized, structured data).

By following these steps:
1. Rule-based to generate the profile of raw dataframe, store in json
2. Ingest to Prompt1 by LLM to explain errors or refine transformations if needed by calling the External Services to support complex transformations which is Gemini-2.5-flash
3. Past to Prompt2 for suggesting the strategic from the existing raw dataframe from Prompt1
4. Ingest the result of Prompt2 + Profile-raw-dataframe to Generates Python Code for dealing on transformation
5. Auto executed that generated code, then return the cleaned_csv.csv of that specific table

## Backend Logical Flow

![logical_flow](images\backend_logical_flow.jpg)

## File-Structure

```
v1/
├── app/
│   ├── api/
│   │   ├── routes/
│   │   │   ├── extract2markdown.py
│   │   │   ├── filter2csv.py
│   │   │   └── transform2tidy.py
│   │   └── route.py
│   ├── core/
│   │   ├── config.py
│   │   ├── exeception.py
│   │   ├── file_management.py
│   │   └── logger.py
│   ├── models/
│   │   └── schemas.py
│   ├── services/
│   │   ├── extract2markdown/
│   │   │          ├── file_handler.py
│   │   │          ├── marker_runner.py
│   │   │          └── pdf_converter.py
│   │   ├── filter2csv/
│   │   │   └── table_extractor.py
│   │   ├── file_locator.py
│   │   └── transform2tidy/
│   │       ├── pipeline/
│   │       │   ├── execute_cleaning.py
│   │       │   ├── profile_raw_df.py
│   │       │   ├── prompt1_profile.py
│   │       │   ├── prompt2_prompt1.py
│   │       │   └── prompt3_prompt2.py
│   │       ├── prompts/
│   │       │   ├── prompt_1_table_error_understanding.md
│   │       │   ├── prompt_2_remediation_strategy.md
│   │       │   └── prompt_3_generate_cleaning_code.md
│   │       └── .env.transform2tidy
│   ├── utils/
│   │   ├── path_utils.py
│   │   ├── prompt_loader.py
│   │   └── timer.py
│   └── main.py
├── logs/app.log
└── temp/
     ├── each_table/  
     ├── outputs/    
     ├── pdf2image/  
     ├── transform2tidy/
     │              ├── cleaned_data/ 
     │              ├── profile_raw_df/
     │              ├── prompt1_profile/
     │              ├── prompt2_prompt1/ 
     │              └── prompt3_prompt2/ 
     └── uploads/
```

# Project Set-Up

## Docker

- Check
  - `docker --version`
  - `docker compose version`
- Clone the Repository
  - `git clone https://github.com/sreynich-nang/backend-Extract-TablefromPDF-Transfrom2Tidy.git`
  - `cd backend-Extract-TablefromPDF-Transfrom2Tidy`
- Build and Start the App
  - `docker compose up --build`
- Visit the browser
  - `http://localhost:8000`
  - or `http://localhost:8000/docs`
- Stop the App
  - `docker compose down`

# Limitation
