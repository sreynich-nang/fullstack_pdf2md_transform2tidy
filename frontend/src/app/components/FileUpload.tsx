import { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileText, Image, Loader2 } from 'lucide-react';
import { Button } from './ui/button';
import { Card, CardContent } from './ui/card';

interface FileUploadProps {
  onUpload: (file: File) => void;
  isProcessing: boolean;
}

export function FileUpload({ onUpload, isProcessing }: FileUploadProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      const file = acceptedFiles[0];
      setSelectedFile(file);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'image/*': ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp']
    },
    maxFiles: 1,
    disabled: isProcessing
  });

  const handleUpload = () => {
    if (selectedFile) {
      onUpload(selectedFile);
      setSelectedFile(null);
    }
  };

  return (
    <Card className="w-full">
      <CardContent className="pt-6">
        <div
          {...getRootProps()}
          className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
            isDragActive
              ? 'border-primary bg-primary/5'
              : 'border-gray-300 hover:border-primary hover:bg-gray-50'
          } ${isProcessing ? 'opacity-50 cursor-not-allowed' : ''}`}
        >
          <input {...getInputProps()} />
          <div className="flex flex-col items-center gap-4">
            <div className="p-4 bg-primary/10 rounded-full">
              {isProcessing ? (
                <Loader2 className="h-8 w-8 text-primary animate-spin" />
              ) : (
                <Upload className="h-8 w-8 text-primary" />
              )}
            </div>
            <div>
              <p className="text-lg font-medium">
                {isProcessing
                  ? 'Processing...'
                  : isDragActive
                  ? 'Drop the file here'
                  : 'Drag & drop a PDF or image here'}
              </p>
              <p className="text-sm text-gray-500 mt-1">
                or click to browse files
              </p>
            </div>
            <div className="flex gap-4 text-sm text-gray-600">
              <div className="flex items-center gap-1">
                <FileText className="h-4 w-4" />
                <span>PDF</span>
              </div>
              <div className="flex items-center gap-1">
                <Image className="h-4 w-4" />
                <span>Images</span>
              </div>
            </div>
          </div>
        </div>

        {selectedFile && !isProcessing && (
          <div className="mt-4 flex items-center justify-between p-4 bg-gray-50 rounded-lg">
            <div className="flex items-center gap-3">
              {selectedFile.type.startsWith('image/') ? (
                <Image className="h-5 w-5 text-blue-500" />
              ) : (
                <FileText className="h-5 w-5 text-red-500" />
              )}
              <div>
                <p className="font-medium text-sm">{selectedFile.name}</p>
                <p className="text-xs text-gray-500">
                  {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                </p>
              </div>
            </div>
            <Button onClick={handleUpload}>Upload</Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
