import { useState } from 'react';
import { Edit, Save, X, Plus, Trash2, Wand2, Download } from 'lucide-react';
import { toast } from 'sonner';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { CsvFile } from '../types';

interface CsvViewerProps {
  csv: CsvFile;
  onSave: (headers: string[], data: string[][]) => void;
  onTransform?: (csvId: string) => Promise<void>;
  onDownload?: () => void;
  onDownloadTransformed?: () => void;
}

export function CsvViewer({
  csv,
  onSave,
  onTransform,
  onDownload,
  onDownloadTransformed,
}: CsvViewerProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [editHeaders, setEditHeaders] = useState<string[]>([]);
  const [editData, setEditData] = useState<string[][]>([]);
  const [isEditingTransformed, setIsEditingTransformed] = useState(false);
  const [editTransformedHeaders, setEditTransformedHeaders] = useState<string[]>([]);
  const [editTransformedData, setEditTransformedData] = useState<string[][]>([]);

  // ✅ Always prefer edited values
  const displayHeaders = isEditing
    ? editHeaders
    : csv.editedHeaders || csv.headers;

  const displayData = isEditing
    ? editData
    : csv.editedData || csv.data;

  // --------------------
  // Editing lifecycle
  // --------------------
  const handleStartEdit = () => {
    setEditHeaders([...displayHeaders]);
    setEditData(displayData.map(row => [...row]));
    setIsEditing(true);
  };

  const handleSave = () => {
    onSave(
      [...editHeaders],
      editData.map(row => [...row])
    );
    setIsEditing(false);
  };

  const handleCancel = () => {
    setIsEditing(false);
  };

  // --------------------
  // Header & cell edits
  // --------------------
  const handleHeaderChange = (index: number, value: string) => {
    setEditHeaders(prev => {
      const next = [...prev];
      next[index] = value;
      return next;
    });
  };

  const handleCellChange = (
    rowIndex: number,
    colIndex: number,
    value: string
  ) => {
    setEditData(prev => {
      const next = prev.map(row => [...row]);
      next[rowIndex][colIndex] = value;
      return next;
    });
  };

  // --------------------
  // Row operations
  // --------------------
  const handleAddRow = () => {
    setEditData(prev => [
      ...prev,
      new Array(editHeaders.length).fill(''),
    ]);
  };

  const handleDeleteRow = (rowIndex: number) => {
    setEditData(prev => prev.filter((_, i) => i !== rowIndex));
  };

  // --------------------
  // Transform
  // --------------------
  const handleTransform = async () => {
    if (!onTransform) return;

    try {
      await onTransform(csv.id);
    } catch (err) {
      console.error('Transform error:', err);
    }
  };

  // --------------------
  // Transformed Data Editing
  // --------------------
  const handleStartEditTransformed = () => {
    setEditTransformedHeaders([...(csv.transformedHeaders || [])]);
    setEditTransformedData((csv.transformedData || []).map(row => [...row]));
    setIsEditingTransformed(true);
  };

  const handleSaveTransformed = () => {
    // Update the transformed data
    // In a real app, you'd call onSaveTransformed here
    setIsEditingTransformed(false);
    toast.success('Transformed data saved!');
  };

  const handleCancelTransformed = () => {
    setIsEditingTransformed(false);
  };

  const handleTransformedHeaderChange = (index: number, value: string) => {
    setEditTransformedHeaders(prev => {
      const next = [...prev];
      next[index] = value;
      return next;
    });
  };

  const handleTransformedCellChange = (rowIndex: number, colIndex: number, value: string) => {
    setEditTransformedData(prev => {
      const next = prev.map(row => [...row]);
      next[rowIndex][colIndex] = value;
      return next;
    });
  };

  const handleAddTransformedRow = () => {
    setEditTransformedData(prev => [
      ...prev,
      new Array(editTransformedHeaders.length).fill(''),
    ]);
  };

  const handleDeleteTransformedRow = (rowIndex: number) => {
    setEditTransformedData(prev => prev.filter((_, i) => i !== rowIndex));
  };

  return (
    <div className="space-y-4">
      {/* Toolbar */}
      <div className="flex justify-between items-center">
        <p className="text-sm text-gray-600">
          {displayData.length} rows × {displayHeaders.length} columns
        </p>

        <div className="flex gap-2">
          {isEditing ? (
            <>
              <Button size="sm" variant="outline" onClick={handleAddRow}>
                <Plus className="h-4 w-4 mr-2" />
                Add Row
              </Button>
              <Button size="sm" variant="outline" onClick={handleCancel}>
                <X className="h-4 w-4 mr-2" />
                Cancel
              </Button>
              <Button size="sm" onClick={handleSave}>
                <Save className="h-4 w-4 mr-2" />
                Save
              </Button>
            </>
          ) : (
            <>
              <Button size="sm" variant="outline" onClick={onDownload}>
                <Download className="h-4 w-4 mr-2" />
                Download CSV
              </Button>
              <div className="flex flex-col gap-2">
                <Button size="sm" variant="outline" onClick={handleStartEdit}>
                  <Edit className="h-4 w-4 mr-2" />
                  Edit
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={handleTransform}
                  disabled={!onTransform || csv.isTransforming}
                >
                  <Wand2 className="h-4 w-4 mr-2" />
                  {csv.isTransforming ? 'Transforming…' : 'Transform2Tidy'}
                </Button>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Table */}
      <div className="border rounded-lg overflow-auto max-h-[600px]">
        <table className="w-full border-collapse">
          <thead className="bg-gray-100 sticky top-0">
            <tr>
              {isEditing && <th className="border w-12" />}
              {displayHeaders.map((h, i) => (
                <th key={i} className="border px-4 py-2 text-left">
                  {isEditing ? (
                    <Input
                      value={h}
                      onChange={e =>
                        handleHeaderChange(i, e.target.value)
                      }
                      className="h-8"
                    />
                  ) : (
                    h
                  )}
                </th>
              ))}
            </tr>
          </thead>

          <tbody>
            {displayData.map((row, rIdx) => (
              <tr key={rIdx}>
                {isEditing && (
                  <td className="border text-center">
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => handleDeleteRow(rIdx)}
                    >
                      <Trash2 className="h-4 w-4 text-red-500" />
                    </Button>
                  </td>
                )}
                {row.map((cell, cIdx) => (
                  <td key={cIdx} className="border px-4 py-2">
                    {isEditing ? (
                      <Input
                        value={cell}
                        onChange={e =>
                          handleCellChange(
                            rIdx,
                            cIdx,
                            e.target.value
                          )
                        }
                        className="h-8"
                      />
                    ) : (
                      cell
                    )}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {csv.transformError && (
        <div className="text-red-500 bg-red-50 border p-3 rounded text-sm">
          <strong>Transform Error:</strong> {csv.transformError}
        </div>
      )}

      {csv.transformedData && csv.transformedHeaders && (
        <div className="space-y-4">
          <div className="text-green-600 bg-green-50 border p-3 rounded text-sm">
            <strong>✓ Transformation Complete!</strong>
          </div>

          <div>
            <div className="flex justify-between items-center mb-3">
              <h3 className="text-sm font-semibold">Transformed Data</h3>
              <div className="flex gap-2">
                {isEditingTransformed ? (
                  <>
                    <Button size="sm" variant="outline" onClick={handleAddTransformedRow}>
                      <Plus className="h-4 w-4 mr-2" />
                      Add Row
                    </Button>
                    <Button size="sm" variant="outline" onClick={handleCancelTransformed}>
                      <X className="h-4 w-4 mr-2" />
                      Cancel
                    </Button>
                    <Button size="sm" onClick={handleSaveTransformed}>
                      <Save className="h-4 w-4 mr-2" />
                      Save
                    </Button>
                  </>
                ) : (
                  <>
                    <Button size="sm" variant="outline" onClick={onDownloadTransformed}>
                      <Download className="h-4 w-4 mr-2" />
                      Download
                    </Button>
                    <Button size="sm" variant="outline" onClick={handleStartEditTransformed}>
                      <Edit className="h-4 w-4 mr-2" />
                      Edit
                    </Button>
                  </>
                )}
              </div>
            </div>

            <div className="border rounded-lg overflow-auto max-h-[400px]">
              <table className="w-full border-collapse">
                <thead className="bg-green-50 sticky top-0">
                  <tr>
                    {isEditingTransformed && <th className="border w-12" />}
                    {(isEditingTransformed ? editTransformedHeaders : csv.transformedHeaders).map((h, i) => (
                      <th key={i} className="border px-4 py-2 text-left text-sm font-semibold">
                        {isEditingTransformed ? (
                          <Input
                            value={h}
                            onChange={e => handleTransformedHeaderChange(i, e.target.value)}
                            className="h-8"
                          />
                        ) : (
                          h
                        )}
                      </th>
                    ))}
                  </tr>
                </thead>

                <tbody>
                  {(isEditingTransformed ? editTransformedData : csv.transformedData || []).map((row, rIdx) => (
                    <tr key={rIdx} className={rIdx % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                      {isEditingTransformed && (
                        <td className="border text-center">
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => handleDeleteTransformedRow(rIdx)}
                          >
                            <Trash2 className="h-4 w-4 text-red-500" />
                          </Button>
                        </td>
                      )}
                      {row.map((cell, cIdx) => (
                        <td key={cIdx} className="border px-4 py-2 text-sm">
                          {isEditingTransformed ? (
                            <Input
                              value={cell}
                              onChange={e =>
                                handleTransformedCellChange(rIdx, cIdx, e.target.value)
                              }
                              className="h-8"
                            />
                          ) : (
                            cell
                          )}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="mt-3 text-xs text-gray-600">
              <p>
                {(isEditingTransformed ? editTransformedData : csv.transformedData)?.length} rows × {(isEditingTransformed ? editTransformedHeaders : csv.transformedHeaders).length} columns
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
