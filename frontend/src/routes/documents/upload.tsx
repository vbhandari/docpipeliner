/**
 * Document upload page
 */

import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDropzone } from 'react-dropzone';
import { Upload, FileText, X, CheckCircle, AlertCircle } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { useUploadDocument } from '@/hooks/useDocuments';
import { DocumentType, getDocumentTypeLabel } from '@/types/document';
import { formatFileSize } from '@/lib/utils';

interface UploadFile {
  file: File;
  id: string;
  status: 'pending' | 'uploading' | 'success' | 'error';
  error?: string;
  documentId?: string;
}

export default function DocumentUpload() {
  const navigate = useNavigate();
  const [files, setFiles] = useState<UploadFile[]>([]);
  const [documentType, setDocumentType] = useState<DocumentType | 'auto'>('auto');
  const uploadDocument = useUploadDocument();

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const newFiles: UploadFile[] = acceptedFiles.map((file) => ({
      file,
      id: Math.random().toString(36).substring(7),
      status: 'pending',
    }));
    setFiles((prev) => [...prev, ...newFiles]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
    },
    maxSize: 50 * 1024 * 1024, // 50MB
  });

  const removeFile = (id: string) => {
    setFiles((prev) => prev.filter((f) => f.id !== id));
  };

  const uploadAll = async () => {
    const pendingFiles = files.filter((f) => f.status === 'pending');

    for (const uploadFile of pendingFiles) {
      setFiles((prev) =>
        prev.map((f) =>
          f.id === uploadFile.id ? { ...f, status: 'uploading' } : f
        )
      );

      try {
        const result = await uploadDocument.mutateAsync({
          file: uploadFile.file,
          documentType: documentType === 'auto' ? undefined : documentType,
        });

        setFiles((prev) =>
          prev.map((f) =>
            f.id === uploadFile.id
              ? { ...f, status: 'success', documentId: result.id }
              : f
          )
        );
      } catch (error) {
        setFiles((prev) =>
          prev.map((f) =>
            f.id === uploadFile.id
              ? {
                  ...f,
                  status: 'error',
                  error: error instanceof Error ? error.message : 'Upload failed',
                }
              : f
          )
        );
      }
    }
  };

  const pendingCount = files.filter((f) => f.status === 'pending').length;
  const successCount = files.filter((f) => f.status === 'success').length;
  const allDone = files.length > 0 && pendingCount === 0;

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Upload Documents</h1>
        <p className="text-muted-foreground">
          Upload PDF documents for processing
        </p>
      </div>

      {/* Upload area */}
      <Card>
        <CardContent className="pt-6">
          <div
            {...getRootProps()}
            className={`
              border-2 border-dashed rounded-lg p-12 text-center cursor-pointer
              transition-colors
              ${isDragActive ? 'border-primary bg-primary/5' : 'border-muted-foreground/25 hover:border-primary/50'}
            `}
          >
            <input {...getInputProps()} />
            <Upload className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
            {isDragActive ? (
              <p className="text-lg font-medium">Drop files here...</p>
            ) : (
              <>
                <p className="text-lg font-medium">
                  Drag and drop PDF files here
                </p>
                <p className="text-sm text-muted-foreground mt-1">
                  or click to browse
                </p>
                <p className="text-xs text-muted-foreground mt-4">
                  Supported: PDF up to 50MB
                </p>
              </>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Document type selector */}
      <Card>
        <CardHeader>
          <CardTitle>Document Type</CardTitle>
        </CardHeader>
        <CardContent>
          <select
            value={documentType}
            onChange={(e) => setDocumentType(e.target.value as DocumentType | 'auto')}
            className="w-full px-3 py-2 border rounded-md bg-background"
          >
            <option value="auto">Auto-detect</option>
            <option value="invoice">Invoice</option>
            <option value="insurance_claim">Insurance Claim</option>
            <option value="compliance_form">Compliance Form</option>
          </select>
          <p className="text-sm text-muted-foreground mt-2">
            Select the document type or let the system auto-detect it
          </p>
        </CardContent>
      </Card>

      {/* File list */}
      {files.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Upload Queue ({files.length} files)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {files.map((uploadFile) => (
                <div
                  key={uploadFile.id}
                  className="flex items-center justify-between p-3 border rounded-lg"
                >
                  <div className="flex items-center gap-3">
                    <FileText className="h-5 w-5 text-muted-foreground" />
                    <div>
                      <p className="font-medium">{uploadFile.file.name}</p>
                      <p className="text-sm text-muted-foreground">
                        {formatFileSize(uploadFile.file.size)}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {uploadFile.status === 'pending' && (
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => removeFile(uploadFile.id)}
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    )}
                    {uploadFile.status === 'uploading' && (
                      <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-primary"></div>
                    )}
                    {uploadFile.status === 'success' && (
                      <CheckCircle className="h-5 w-5 text-green-500" />
                    )}
                    {uploadFile.status === 'error' && (
                      <div className="flex items-center gap-2 text-destructive">
                        <AlertCircle className="h-5 w-5" />
                        <span className="text-sm">{uploadFile.error}</span>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>

            {/* Actions */}
            <div className="flex items-center justify-between mt-6">
              <Button
                variant="outline"
                onClick={() => setFiles([])}
                disabled={uploadDocument.isPending}
              >
                Clear All
              </Button>
              <div className="flex items-center gap-4">
                {allDone && successCount > 0 && (
                  <Button variant="outline" onClick={() => navigate('/documents')}>
                    View Documents
                  </Button>
                )}
                <Button
                  onClick={uploadAll}
                  disabled={pendingCount === 0 || uploadDocument.isPending}
                >
                  {uploadDocument.isPending ? 'Uploading...' : `Upload ${pendingCount} Files`}
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
