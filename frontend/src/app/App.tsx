import { useState } from 'react';
import { FileUpload } from './components/FileUpload';
import { ResultsPanel } from './components/ResultsPanel';
import { Card, CardContent } from './components/ui/card';
import { Loader2 } from 'lucide-react';
import { ProcessedFile } from './types';
import { api } from './api/client';
import { toast, Toaster } from 'sonner';

function App() {
  const [currentFile, setCurrentFile] = useState<ProcessedFile | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isTransforming, setIsTransforming] = useState(false);

  const handleFileUpload = async (file: File) => {
    setIsProcessing(true);

    const processingFile: ProcessedFile = {
      id: `${Date.now()}-${Math.random().toString(36).slice(2)}`,
      name: file.name,
      type: file.type.startsWith('image/') ? 'image' : 'pdf',
      uploadedAt: new Date(),
      status: 'uploaded',
    };

    setCurrentFile(processingFile);
    toast.info('Uploading file...');

    try {
      const uploadResult = await api.uploadAndProcessFile(file);
      
      const uploadedFile: ProcessedFile = {
        ...processingFile,
        fileId: uploadResult.file_id,
      };

      setCurrentFile(uploadedFile);
      toast.success('File uploaded successfully! Click "Convert to Markdown" to continue.');
    } catch (error) {
      console.error('Upload error:', error);

      setCurrentFile({
        ...processingFile,
        status: 'error',
      });

      toast.error(
        error instanceof Error ? error.message : 'Failed to upload file'
      );
    } finally {
      setIsProcessing(false);
    }
  };

  const handleConvertMarkdown = async () => {
    if (!currentFile?.fileId) {
      toast.error('No file uploaded');
      return;
    }

    setIsProcessing(true);
    
    try {
      setCurrentFile(prev =>
        prev ? { ...prev, status: 'converting' } : prev
      );
      
      toast.info('Converting to markdown... This may take a moment.');

      const result = await api.processMarkdownAndTables(currentFile.fileId);

      const completedFile: ProcessedFile = {
        ...currentFile,
        status: 'completed',
        markdown: {
          content: result.markdown.content,
          filename: result.markdown.filename,
        },
        csvFiles: result.csv_files
          ? result.csv_files.map((csv, idx) => ({
              id: csv.table_id || `csv-${idx}`,
              filename: csv.filename,
              tableId: csv.table_id,
              data: csv.data,
              headers: csv.headers,
            }))
          : [],
        tableExtractionError: result.tableExtractionError,
      };

      setCurrentFile(completedFile);
      toast.success('Extraction completed!');
    } catch (error) {
      console.error('Conversion error:', error);

      setCurrentFile(prev =>
        prev ? { ...prev, status: 'error' } : prev
      );

      toast.error(
        error instanceof Error ? error.message : 'Failed to convert file'
      );
    } finally {
      setIsProcessing(false);
    }
  };

  const handleSaveMarkdown = (content: string) => {
    setCurrentFile(prev =>
      prev && prev.markdown
        ? {
            ...prev,
            markdown: {
              ...prev.markdown,
              editedContent: content,
            },
          }
        : prev
    );

    toast.success('Markdown saved!');
  };

  const handleSaveCsv = (csvId: string, headers: string[], data: string[][]) => {
    setCurrentFile(prev =>
      prev && prev.csvFiles
        ? {
            ...prev,
            csvFiles: prev.csvFiles.map(csv =>
              csv.id === csvId
                ? { ...csv, 
                  editedData: data.map(row => 
                    row.slice(0, csv.headers.length)), 
                    
                  editedHeaders: headers.slice(0, csv.headers.length),
                }
                : csv
            ),
          }
        : prev
    );

    toast.success('CSV saved!');
  };

  const handleTransformCsv = async (csvId: string) => {
    if (!currentFile?.fileId) {
      toast.error('No file uploaded');
      return;
    }

    const csvFile = currentFile.csvFiles?.find(csv => csv.id === csvId);
    if (!csvFile) {
      toast.error('CSV file not found');
      return;
    }

    // Create CSV content from current data
    const headers = csvFile.editedHeaders || csvFile.headers;
    const data = csvFile.editedData || csvFile.data;
    
    // Format CSV properly - simple format without quotes for now
    const csvContent = [
      headers.join(','),
      ...data.map(row => row.join(',')),
    ].join('\n');
    
    console.log('[App] CSV content to transform:', csvContent);
    console.log('[App] CSV headers:', headers);
    console.log('[App] CSV rows:', data.length);

    setCurrentFile(prev =>
      prev && prev.csvFiles
        ? {
            ...prev,
            csvFiles: prev.csvFiles.map(csv =>
              csv.id === csvId
                ? { ...csv, isTransforming: true, transformError: undefined }
                : csv
            ),
          }
        : prev
    );

    try {
      toast.info('Transforming to tidy format...');
      
      const result = await api.transform2tidy(
        csvContent,
        currentFile.fileId,
        csvFile.tableId || csvId
      );

      console.log('Transform result:', result);

      // Backend returns cleaned_csv_path - we need to fetch and parse it
      let transformedHeaders: string[] = [];
      let transformedData: string[][] = [];
      
      if (result.cleaned_csv_path) {
        try {
          console.log('[App] Fetching cleaned CSV from:', result.cleaned_csv_path);
          // The cleaned_csv_path is a file path on the server
          // We need to construct a download URL
          const downloadUrl = `${(import.meta as any).env?.VITE_API_BASE_URL || 'http://192.168.10.188:8000/api'}/transform/download/cleaned/${result.file_id}/${result.table_id}`;
          
          const csvResponse = await fetch(downloadUrl);
          if (csvResponse.ok) {
            const cleanedCsvContent = await csvResponse.text();
            console.log('[App] Cleaned CSV content length:', cleanedCsvContent.length);
            
            // Parse the CSV content
            const parsed = api.parseCsvContent(cleanedCsvContent);
            transformedHeaders = parsed.headers;
            transformedData = parsed.data;
            console.log('[App] Parsed transformed data - headers:', transformedHeaders.length, 'rows:', transformedData.length);
          } else {
            console.warn('[App] Failed to fetch cleaned CSV:', csvResponse.status);
          }
        } catch (fetchError) {
          console.error('[App] Error fetching cleaned CSV:', fetchError);
        }
      }

      setCurrentFile(prev =>
        prev && prev.csvFiles
          ? {
              ...prev,
              csvFiles: prev.csvFiles.map(csv =>
                csv.id === csvId
                  ? {
                      ...csv,
                      isTransforming: false,
                      transformedData: transformedData.length > 0 ? transformedData : (result.transformed_data || result.data),
                      transformedHeaders: transformedHeaders.length > 0 ? transformedHeaders : (result.transformed_headers || result.headers),
                    }
                  : csv
              ),
            }
          : prev
      );

      toast.success('Transformation completed!');
    } catch (error) {
      console.error('Transform error:', error);

      setCurrentFile(prev =>
        prev && prev.csvFiles
          ? {
              ...prev,
              csvFiles: prev.csvFiles.map(csv =>
                csv.id === csvId
                  ? {
                      ...csv,
                      isTransforming: false,
                      transformError: error instanceof Error ? error.message : 'Transform failed',
                    }
                  : csv
              ),
            }
          : prev
      );

      toast.error(
        error instanceof Error ? error.message : 'Failed to transform CSV'
      );
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Toaster position="top-right" />

      {/* Header */}
      <header className="bg-white border-b shadow-sm sticky top-0 z-10">
        <div className="container mx-auto px-6 py-4">
          <h1 className="text-2xl font-bold text-gray-900">
            PDF Extraction Tool
          </h1>
          <p className="text-sm text-gray-600">
            Extract and process PDF & Image documents
          </p>
        </div>
      </header>

      {/* Main */}
      <main className="container mx-auto px-6 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Upload */}
          <div className="lg:col-span-1">
            <Card>
              <CardContent className="p-6">
                <h2 className="text-lg font-semibold mb-4">
                  Upload Document
                </h2>

                <FileUpload
                  onUpload={handleFileUpload}
                  isProcessing={isProcessing}
                />

                {isProcessing && (
                  <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                    <div className="flex items-center gap-3">
                      <Loader2 className="h-5 w-5 text-blue-600 animate-spin" />
                      <div>
                        <p className="text-sm font-medium text-blue-900">
                          Processing...
                        </p>
                        <p className="text-xs text-blue-700">
                          Extracting content from your document
                        </p>
                      </div>
                    </div>
                  </div>
                )}

                {currentFile?.status === 'completed' && (
                  <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
                    <p className="text-sm font-medium text-green-900">
                      ✓ Extraction Complete
                    </p>
                    <div className="text-xs text-green-700 mt-1 space-y-1">
                      <p>
                        • Markdown: {currentFile.markdown?.filename}
                      </p>
                      <p>
                        • CSV Tables: {currentFile.csvFiles?.length}
                      </p>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Instructions */}
            <Card className="mt-6">
              <CardContent className="p-6">
                <h3 className="text-sm font-semibold mb-3">
                  How to Use :D
                </h3>
                <ol className="text-sm text-gray-600 space-y-2 list-decimal list-inside">
                  <li>Upload a PDF or image file</li>
                  <li>Click "Convert to Markdown" button</li>
                  <li>Wait for processing to complete</li>
                  <li>Edit markdown content</li>
                  <li>Edit extracted CSV tables</li>
                  <li>Download processed results</li>
                  <li>Transform to Tidy format</li>
                </ol>
              </CardContent>
            </Card>
          </div>

          {/* Results */}
          <div className="lg:col-span-2">
            <ResultsPanel
              file={currentFile}
              onSaveMarkdown={handleSaveMarkdown}
              onSaveCsv={handleSaveCsv}
              onConvertMarkdown={handleConvertMarkdown}
              onTransformCsv={handleTransformCsv}
              isProcessing={isProcessing}
            />
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t mt-12">
        <div className="container mx-auto px-6 py-4">
          <p className="text-center text-sm text-gray-600">
            API: http://192.168.10.188:8000/api
          </p>
        </div>
      </footer>
    </div>
  );
}

export default App;
