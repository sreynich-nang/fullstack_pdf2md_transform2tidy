// Access Vite environment variables - with fallback to alternative server
const API_BASE_URL = (import.meta as any).env?.VITE_API_BASE_URL || 'http://192.168.10.188:8000/api';

// Log the API URL for debugging
console.log('[API Client] Using API URL:', API_BASE_URL);

// Response interfaces
export interface UploadResponse {
  status: string;
  file_id: string;
  filename: string;
  processing_time_seconds?: number;
}

export interface MarkdownResponse {
  status: string;
  file_id: string;
  markdown_content: string;
  processing_time_seconds?: number;
}

export interface TableExtractionResponse {
  status?: string;
  file_id: string;
  tables?: Array<{
    table_id: string;
    csv_path?: string;
    num_rows?: number;
    num_columns?: number;
  }>;
  table_files?: Array<{
    table_id: string;
    filename: string;
  }>;
  tables_count?: number;
  total_tables?: number;
  processing_time?: number;
  message?: string;
}

export interface CsvFileData {
  filename: string;
  data: string[][];
  headers: string[];
  table_id?: string;
}

export interface ExtractionResult {
  markdown: {
    content: string;
    filename: string;
  };
  csv_files?: CsvFileData[];
  file_id: string;
  tableExtractionError?: string;
}

// Type for table object (from API)
type TableFile = { table_id: string; filename?: string };

export const apiClient = {
  uploadFile: async (file: File): Promise<UploadResponse> => {
    if (!API_BASE_URL) throw new Error('API_BASE_URL is not configured.');

    console.log('[API Client] Uploading file:', file.name);
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE_URL}/extract/upload`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Upload failed');
    }

    const result = await response.json();
    console.log('[API Client] Upload response:', result);
    return result;
  },

  convertToMarkdown: async (fileId: string): Promise<MarkdownResponse> => {
    if (!API_BASE_URL) throw new Error('API_BASE_URL is not configured.');

    console.log('[API Client] Converting to markdown for file_id:', fileId);
    const response = await fetch(`${API_BASE_URL}/extract/markdown/${encodeURIComponent(fileId)}`, {
      method: 'POST',
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Markdown conversion failed');
    }

    const result = await response.json();
    console.log('[API Client] Markdown conversion response:', result);
    return result;
  },

  downloadMarkdown: async (fileId: string): Promise<string> => {
    if (!API_BASE_URL) throw new Error('API_BASE_URL is not configured.');

    console.log('[API Client] Downloading markdown for file_id:', fileId);
    const response = await fetch(`${API_BASE_URL}/extract/download/markdown/${encodeURIComponent(fileId)}`);

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Download failed');
    }

    return response.text();
  },

  filterTables: async (fileId: string): Promise<TableExtractionResponse> => {
    if (!API_BASE_URL) throw new Error('API_BASE_URL is not configured.');

    console.log('[API Client] Extracting tables for file_id:', fileId);
    const url = `${API_BASE_URL}/filter/tables/${encodeURIComponent(fileId)}`;
    const response = await fetch(url, { method: 'POST' });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      console.error('[API Client] filterTables error:', errorData);
      throw new Error(errorData.detail || `Table extraction failed (${response.status})`);
    }

    const result = await response.json();
    console.log('[API Client] filterTables response:', JSON.stringify(result, null, 2));
    return result;
  },

  downloadTable: async (fileId: string, tableId: string): Promise<string> => {
    if (!API_BASE_URL) throw new Error('API_BASE_URL is not configured.');

    const url = `${API_BASE_URL}/filter/download/table/${encodeURIComponent(fileId)}/${encodeURIComponent(tableId)}`;
    const response = await fetch(url);

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `CSV download failed (${response.status})`);
    }

    return response.text();
  },

  parseCsvContent: (csvContent: string): { headers: string[]; data: string[][] } => {
    const lines = csvContent.trim().split('\n').filter(line => line.trim());
    if (lines.length === 0) return { headers: [], data: [] };

    const parseRow = (line: string): string[] => {
      const result: string[] = [];
      let current = '';
      let inQuotes = false;

      for (let i = 0; i < line.length; i++) {
        const char = line[i];
        if (char === '"') inQuotes = !inQuotes;
        else if (char === ',' && !inQuotes) {
          result.push(current.trim());
          current = '';
        } else {
          current += char;
        }
      }
      result.push(current.trim());
      return result;
    };

    const headers = parseRow(lines[0]);
    const data = lines.slice(1).map(parseRow);
    return { headers, data };
  },

  uploadAndProcessFile: async (file: File): Promise<UploadResponse> => {
    console.log('[API Client] Starting uploadAndProcessFile for:', file.name);
    return apiClient.uploadFile(file);
  },

  processMarkdownAndTables: async (fileId: string): Promise<ExtractionResult> => {
    console.log('[API Client] Starting processMarkdownAndTables for file_id:', fileId);

    await apiClient.convertToMarkdown(fileId);
    const markdownContent = await apiClient.downloadMarkdown(fileId);

    let csvFiles: CsvFileData[] = [];
    let tableExtractionError: string | undefined = undefined;

    try {
      const tableResult = await apiClient.filterTables(fileId);
      const tablesCount = tableResult.total_tables ?? tableResult.tables_count ?? 0;
      const tablesToProcess: TableFile[] = tableResult.tables || tableResult.table_files || [];

      if (tablesToProcess.length > 0) {
        const csvResults: (CsvFileData | null)[] = await Promise.all(
          tablesToProcess.map(async (tableFile: TableFile): Promise<CsvFileData | null> => {
            try {
              const tableId = tableFile.table_id;
              const filename = tableFile.filename || `${tableId}.csv`;

              const csvContent = await apiClient.downloadTable(fileId, tableId);
              if (!csvContent || csvContent.trim().length === 0) return null;

              const parsed = apiClient.parseCsvContent(csvContent);
              return { filename, headers: parsed.headers, data: parsed.data, table_id: tableId };
            } catch (error) {
              console.error('[API Client] Failed table download/parse:', tableFile.table_id, error);
              return null;
            }
          })
        );

        // Filter out nulls with type guard
        csvFiles = csvResults.filter((f): f is CsvFileData => f !== null);

        if (csvFiles.length === 0 && tablesToProcess.length > 0) {
          tableExtractionError = `Failed to download all ${tablesToProcess.length} table(s)`;
        }
      } else {
        tableExtractionError = tablesCount === 0 ? 'No tables found in markdown' : `Expected ${tablesCount} tables but none found`;
      }
    } catch (error) {
      console.error('[API Client] Table extraction failed:', error);
      tableExtractionError = error instanceof Error ? error.message : 'Unknown error during table extraction';
    }

    return {
      markdown: { content: markdownContent, filename: 'document.md' },
      csv_files: csvFiles,
      file_id: fileId,
      tableExtractionError,
    };
  },

  transform2tidy: async (csvContent: string, fileId: string, tableId: string) => {
    if (!API_BASE_URL) throw new Error('API_BASE_URL is not configured.');

    console.log('[API Client] Transform2Tidy request:');
    console.log('[API Client] File ID:', fileId);
    console.log('[API Client] Table ID:', tableId);
    console.log('[API Client] CSV Content length:', csvContent.length);
    console.log('[API Client] CSV Content preview:', csvContent.substring(0, 200));

    const url = `${API_BASE_URL}/transform/tidy`;
    const requestBody = { csv_data: csvContent, file_id: fileId, table_id: tableId };
    
    console.log('[API Client] Request body:', JSON.stringify(requestBody, null, 2));

    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(requestBody),
    });

    console.log('[API Client] Transform response status:', response.status);

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      console.error('[API Client] Transform error response:', errorData);
      const errorMessage = errorData.detail || errorData.error || errorData.message || `Transform failed (${response.status})`;
      throw new Error(errorMessage);
    }

    const result = await response.json();
    console.log('[API Client] Transform success:', result);
    return result;
  },

  downloadCleanedCsv: async (fileId: string, tableId: string): Promise<string> => {
    if (!API_BASE_URL) throw new Error('API_BASE_URL is not configured.');

    const url = `${API_BASE_URL}/transform/download/cleaned/${encodeURIComponent(fileId)}/${encodeURIComponent(tableId)}`;
    const response = await fetch(url);

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Cleaned CSV download failed (${response.status})`);
    }

    return response.text();
  },
};

// Export the API client
export const api = apiClient;
