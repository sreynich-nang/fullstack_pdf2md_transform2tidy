// Types for the PDF extraction application
export interface ProcessedFile {
  id: string;
  name: string;
  type: 'pdf' | 'image';
  uploadedAt: Date;
  status: 'uploaded' | 'converting' | 'completed' | 'error';
  fileId?: string; // ID returned from upload endpoint
  markdown?: MarkdownFile;
  csvFiles?: CsvFile[];
  tableExtractionError?: string;
}

export interface MarkdownFile {
  content: string;
  filename: string;
  editedContent?: string;
}

export interface CsvFile {
  id: string;
  filename: string;
  tableId?: string;
  data: string[][];
  headers: string[];
  
  editedHeaders?: string[];
  editedData?: string[][];
  
  transformedData?: string[][];
  transformedHeaders?: string[];
  isTransforming?: boolean;
  transformError?: string;
}

// ...existing code...
export interface TableTransformState {
  isTransforming: boolean;
  transformedData?: string; // CSV data after transform
  error?: string;
}

// Add to existing ResultData interface
export interface ResultData {
  // ...existing fields...
  tableTransforms?: Record<number, TableTransformState>; // key is table index
}