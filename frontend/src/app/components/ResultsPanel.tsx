import { useState, useEffect } from 'react';
import { FileText, Table, Download } from 'lucide-react';
import { Button } from './ui/button';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { ProcessedFile } from '../types';
import { MarkdownViewer } from './MarkdownViewer';
import { CsvViewer } from './CsvViewer';

interface ResultsPanelProps {
  file: ProcessedFile | null;
  onSaveMarkdown: (content: string) => void;
  onSaveCsv: (
    csvId: string,
    headers: string[],
    data: string[][]
  ) => void;
  onTransformCsv?: (csvId: string) => Promise<void>;
  onConvertMarkdown?: () => Promise<void>;
  isProcessing?: boolean;
}

export function ResultsPanel({
  file,
  onSaveMarkdown,
  onSaveCsv,
  onTransformCsv,
  onConvertMarkdown,
  isProcessing = false,
}: ResultsPanelProps) {
  const [activeView, setActiveView] =
    useState<'markdown' | 'csv'>('markdown');
  const [selectedCsvId, setSelectedCsvId] = useState('');
  const [csvVersion, setCsvVersion] = useState(0);

  // ✅ SAFE csvFiles access
  const csvFiles = file?.csvFiles ?? [];

  useEffect(() => {
    if (csvFiles.length && !selectedCsvId) {
      setSelectedCsvId(csvFiles[0].id);
    }
  }, [csvFiles, selectedCsvId]);

  const handleSaveCsv = (
    csvId: string,
    headers: string[],
    data: string[][]
  ) => {
    onSaveCsv(csvId, headers, data);
    setCsvVersion(v => v + 1);
  };

  const handleDownloadCsv = (csvId: string) => {
    const csv = csvFiles.find(c => c.id === csvId);
    if (!csv) return;

    const headers = csv.editedHeaders || csv.headers;
    const data = csv.editedData || csv.data;

    const content = [headers, ...data]
      .map(r => r.join(','))
      .join('\n');

    const blob = new Blob([content], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = csv.filename;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleDownloadTransformedCsv = (csvId: string) => {
    const csv = csvFiles.find(c => c.id === csvId);
    if (!csv || !csv.transformedHeaders || !csv.transformedData) return;

    const headers = csv.transformedHeaders;
    const data = csv.transformedData;

    const content = [headers, ...data]
      .map(r => r.join(','))
      .join('\n');

    const blob = new Blob([content], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `transformed_${csv.filename}`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Show message when file is uploaded but not yet converted
  if (!file || (file.status !== 'completed' && file.status !== 'uploaded' && file.status !== 'converting')) {
    return (
      <Card className="w-full">
        <CardContent className="p-12 text-center text-gray-400">
          <FileText className="h-16 w-16 mx-auto mb-4" />
          No processed files yet
        </CardContent>
      </Card>
    );
  }

  // Show "Convert to Markdown" button when file is uploaded but not yet converted
  if (file.status === 'uploaded') {
    return (
      <Card className="w-full">
        <CardHeader>
          <CardTitle>File Ready for Processing</CardTitle>
          <p className="text-sm text-gray-500">{file.name}</p>
        </CardHeader>
        <CardContent className="text-center py-12">
          <FileText className="h-16 w-16 mx-auto mb-4 text-blue-500" />
          <p className="text-gray-600 mb-4">
            File uploaded successfully. Click below to convert to Markdown and extract tables.
          </p>
          <Button 
            onClick={onConvertMarkdown}
            disabled={isProcessing}
            size="lg"
          >
            {isProcessing ? 'Converting...' : 'Convert to Markdown'}
          </Button>
        </CardContent>
      </Card>
    );
  }

  // Show converting state
  if (file.status === 'converting') {
    return (
      <Card className="w-full">
        <CardHeader>
          <CardTitle>Converting to Markdown</CardTitle>
          <p className="text-sm text-gray-500">{file.name}</p>
        </CardHeader>
        <CardContent className="text-center py-12">
          <div className="flex justify-center mb-4">
            <div className="animate-spin h-12 w-12 border-4 border-blue-500 border-t-transparent rounded-full"></div>
          </div>
          <p className="text-gray-600">
            Processing your document... This may take a moment.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>Extraction Results</CardTitle>
        <p className="text-sm text-gray-500">{file.name}</p>
      </CardHeader>

      <CardContent>
        <Tabs
          value={activeView}
          onValueChange={v =>
            setActiveView(v as 'markdown' | 'csv')
          }
        >
          <TabsList className="grid grid-cols-2 mb-4">
            <TabsTrigger value="markdown">
              <FileText className="h-4 w-4 mr-2" />
              Markdown
            </TabsTrigger>
            <TabsTrigger
              value="csv"
            >
              <Table className="h-4 w-4 mr-2" />
              CSV Tables ({csvFiles.length})
            </TabsTrigger>
          </TabsList>

          <TabsContent value="markdown">
            {file.markdown && (
              <MarkdownViewer
                markdown={file.markdown}
                onSave={onSaveMarkdown}
              />
            )}
          </TabsContent>

          <TabsContent value="csv">
            <div className="space-y-4">
              {csvFiles.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <Table className="h-12 w-12 mx-auto mb-3 opacity-50" />
                  <p>No tables found in the extracted markdown.</p>
                  <p className="text-sm">The document may not contain any structured tables.</p>
                  {file?.tableExtractionError && (
                    <div className="text-xs text-red-600 mt-3 bg-red-50 p-2 rounded border border-red-200">
                      <strong>Debug Info:</strong> {file.tableExtractionError}
                    </div>
                  )}
                  <p className="text-xs text-red-500 mt-2">
                    📋 Check the browser console (F12) to see detailed API logs.
                  </p>
                </div>
              ) : (
                <>
                  <div className="flex gap-2 flex-wrap">
                    {csvFiles.map(csv => (
                      <Button
                        key={csv.id}
                        size="sm"
                        variant={
                          csv.id === selectedCsvId
                            ? 'default'
                            : 'outline'
                        }
                        onClick={() => setSelectedCsvId(csv.id)}
                      >
                        {csv.filename}
                      </Button>
                    ))}
                  </div>

                  {selectedCsvId && (
                    <CsvViewer
                      key={`${selectedCsvId}-v${csvVersion}`}
                      csv={csvFiles.find(c => c.id === selectedCsvId)!}
                      onSave={(headers, data) =>
                        handleSaveCsv(selectedCsvId, headers, data)
                      }
                      onTransform={onTransformCsv}
                      onDownload={() =>
                        handleDownloadCsv(selectedCsvId)
                      }
                      onDownloadTransformed={() =>
                        handleDownloadTransformedCsv(selectedCsvId)
                      }
                    />
                  )}
                </>
              )}
            </div>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}
