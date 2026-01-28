import { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Eye, Edit, Save, X, Download } from 'lucide-react';
import { Button } from './ui/button';
import { Textarea } from './ui/textarea';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { MarkdownFile } from '../types';

interface MarkdownViewerProps {
  markdown: MarkdownFile;
  onSave: (content: string) => void;
}

export function MarkdownViewer({ markdown, onSave }: MarkdownViewerProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [editContent, setEditContent] = useState(markdown.editedContent || markdown.content);
  const [viewMode, setViewMode] = useState<'preview' | 'source'>('preview');

  // Update editContent when markdown prop changes
  useEffect(() => {
    setEditContent(markdown.editedContent || markdown.content);
  }, [markdown.content, markdown.editedContent]);

    const handleDownload = () => {
      const content = markdown.editedContent || markdown.content;
      const blob = new Blob([content], { type: 'text/markdown' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${markdown.filename || 'document'}.md`;
      a.click();
      URL.revokeObjectURL(url);
  };

  const handleSave = () => {
    onSave(editContent);
    setIsEditing(false);
  };

  const handleCancel = () => {
    setEditContent(markdown.editedContent || markdown.content);
    setIsEditing(false);
  };

  const handleEdit = () => {
    setIsEditing(true);
    setViewMode('source'); // Switch to source view when editing
  };

  const displayContent = markdown.editedContent || markdown.content;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <Tabs value={viewMode} onValueChange={(v) => setViewMode(v as 'preview' | 'source')}>
          <TabsList>
            <TabsTrigger value="preview">
              <Eye className="h-4 w-4 mr-2" />
              Preview
            </TabsTrigger>
            <TabsTrigger value="source">
              <Edit className="h-4 w-4 mr-2" />
              Source
            </TabsTrigger>
          </TabsList>
        </Tabs>

        <div className="flex gap-2">
          {isEditing ? (
            <>
              <Button size="sm" variant="outline" onClick={handleCancel}>
                <X className="h-4 w-4 mr-2" />
                Cancel
              </Button>
              <Button size="sm" onClick={handleSave}>
                <Save className="h-4 w-4 mr-2" />
                Save
              </Button>
            </>
      //     ) : (
      //       <Button size="sm" variant="outline" onClick={handleEdit}>
      //         <Edit className="h-4 w-4 mr-2" />
      //         Edit
      //       </Button>
      //     )}
      //   </div>
      // </div>
        ) : (
              <>
                <Button size="sm" variant="outline" onClick={handleDownload}>
                  <Download className="h-4 w-4 mr-2" />
                  Download
                </Button>
                <Button size="sm" variant="outline" onClick={handleEdit}>
                  <Edit className="h-4 w-4 mr-2" />
                  Edit
                </Button>
              </>
            )}
          </div>
        </div>

      {viewMode === 'preview' ? (
        <div className="prose prose-table:border-collapse max-w-none p-6 bg-white border rounded-lg max-h-[600px] overflow-auto
          [&_table]:w-full [&_table]:border-collapse [&_table]:border [&_table]:border-gray-300
          [&_th]:border [&_th]:border-gray-300 [&_th]:bg-gray-100 [&_th]:px-4 [&_th]:py-2 [&_th]:text-left [&_th]:font-semibold
          [&_td]:border [&_td]:border-gray-300 [&_td]:px-4 [&_td]:py-2
          [&_tr:nth-child(even)]:bg-gray-50
        ">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {displayContent}
          </ReactMarkdown>
        </div>
      ) : (
        <div className="border rounded-lg overflow-hidden">
          <Textarea
            value={isEditing ? editContent : displayContent}
            onChange={(e) => setEditContent(e.target.value)}
            readOnly={!isEditing}
            className={`font-mono text-sm min-h-[600px] border-0 focus-visible:ring-0 ${
              !isEditing ? 'bg-gray-50 cursor-default' : 'bg-white'
            }`}
            placeholder="Enter markdown content..."
          />
        </div>
      )}
    </div>
  );
}
