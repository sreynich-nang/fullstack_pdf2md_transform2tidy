You are a Remediation strategic, Given the Auditor's Diagnosis (<PROMPT1_ERROR_DIAGNOSIS_JSON>), provide a transformation strategy to move from Messy Spreadsheet to Relational Tidy Table by follow the Hadley Wickham’s Tidy Data rules

Please provide a transformation matrix:

1. Header Resolution: Map the current multi-level structure to a single flat header row.
2. Denormalization of Metadata: Identify "Implicit Variables" (values only found in titles or headers) and explain how to inject them as new columns for every observation.
3. Row-Level Filtering: List the keywords or patterns (e.g., "Total*", "Grand Total") that indicate rows to be deleted.
4. The Unpivot Strategy:
- Which columns are Identities (Primary Keys/Dimensions)?
- Which columns are Measures (to be collapsed into a single column)?
 
Explain your reasoning based on the errors flagged in the JSON.

Key Improvements Made:
- Added "Forward Filling" Logic: Messy data often has a "Year" in one cell that applies to the next 50 rows. The improved prompts ask the LLM to address this (Implicit Variables).
- Double-Counting Prevention: Specifically asks how to handle "Total" rows, which is a common pitfall in data transformation.
- Technical Terminology: Included terms like id_vars, value_vars, forward-fill, concatenate, and atomic values to guide the LLM toward professional solutions.