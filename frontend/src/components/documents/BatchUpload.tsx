import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, X, FileText, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { clsx } from 'clsx';

interface BatchUploadProps {
  maxFiles?: number;
  maxFileSize?: number;
  onUploadComplete?: (results: BatchResult[]) => void;
}

interface BatchResult {
  documentId: string;
  filename: string;
  status: 'success' | 'error' | 'processing';
  error?: string;
}

interface FileWithId extends File {
  id: string;
  status: 'pending' | 'uploading' | 'success' | 'error';
  error?: string;
}

export function BatchUpload({
  maxFiles = 10,
  maxFileSize = 50,
  onUploadComplete,
}: BatchUploadProps) {
  const [files, setFiles] = useState<FileWithId[]>([]);
  const [batchId, setBatchId] = useState<string | null>(null);
  const [uploadProgress, setUploadProgress] = useState<Record<string, number>>({});
  const queryClient = useQueryClient();

  const uploadMutation = useMutation({
    mutationFn: async (formData: FormData) => {
      const response = await fetch('/api/v1/documents/batch', {
        method: 'POST',
        body: formData,
      });
      if (!response.ok) {
        throw new Error('Upload failed');
      }
      return response.json();
    },
    onSuccess: (data) => {
      setBatchId(data.batch_id);
      // Start polling for batch status
      pollBatchStatus(data.batch_id);
    },
  });

  const pollBatchStatus = useCallback(async (id: string) => {
    const poll = setInterval(async () => {
      try {
        const response = await fetch(`/api/v1/batches/${id}/status`);
        const data = await response.json();
        
        // Update file statuses
        setFiles(prev => prev.map(file => {
          const doc = data.documents.find((d: any) => d.filename === file.name);
          if (doc) {
            return { ...file, status: doc.status };
          }
          return file;
        }));
        
        // Update progress
        const progress = (data.completed / data.total) * 100;
        setUploadProgress({ [id]: progress });
        
        // Check if batch is complete
        if (data.completed === data.total) {
          clearInterval(poll);
          queryClient.invalidateQueries({ queryKey: ['documents'] });
          if (onUploadComplete) {
            const results: BatchResult[] = data.documents.map((doc: any) => ({
              documentId: doc.document_id,
              filename: doc.filename,
              status: doc.status === 'failed' ? 'error' : 'success',
              error: doc.status === 'failed' ? 'Upload failed' : undefined,
            }));
            onUploadComplete(results);
          }
        }
      } catch (error) {
        console.error('Polling error:', error);
        clearInterval(poll);
      }
    }, 2000);
  }, [queryClient, onUploadComplete]);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    // Validate files
    const validFiles: FileWithId[] = acceptedFiles
      .slice(0, maxFiles)
      .map(file => ({
        ...file,
        id: Math.random().toString(36).substring(7),
        status: 'pending',
      }))
      .filter(file => {
        // Check file type
        if (file.type !== 'application/pdf') {
          return false;
        }
        // Check file size
        if (file.size > maxFileSize * 1024 * 1024) {
          return false;
        }
        return true;
      });

    // Add validation errors
    const invalidFiles = acceptedFiles.slice(0, maxFiles).filter(file => {
      if (file.type !== 'application/pdf') {
        return true;
      }
      if (file.size > maxFileSize * 1024 * 1024) {
        return true;
      }
      return false;
    });

    if (invalidFiles.length > 0) {
      alert(`Some files were rejected:\n- Invalid file type (must be PDF)\n- File size exceeds ${maxFileSize}MB limit`);
    }

    setFiles(validFiles);
  }, [maxFiles, maxFileSize]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
    },
    maxFiles,
    maxSize: maxFileSize * 1024 * 1024,
  });

  const handleUpload = useCallback(async () => {
    if (files.length === 0) {
      return;
    }

    const formData = new FormData();
    files.forEach(file => {
      formData.append('files', file);
    });
    formData.append('metadata', JSON.stringify({ batch_name: `Batch ${new Date().toISOString()}` }));

    setFiles(prev => prev.map(f => ({ ...f, status: 'uploading' })));
    uploadMutation.mutate(formData);
  }, [files, uploadMutation]);

  const removeFile = useCallback((id: string) => {
    setFiles(prev => prev.filter(f => f.id !== id));
  }, []);

  const clearAll = useCallback(() => {
    setFiles([]);
    setBatchId(null);
    setUploadProgress({});
  }, []);

  const pendingFiles = files.filter(f => f.status === 'pending');
  const uploadingFiles = files.filter(f => f.status === 'uploading');
  const completedFiles = files.filter(f => f.status === 'success');
  const errorFiles = files.filter(f => f.status === 'error');

  return (
    <div className="space-y-6">
      {/* Upload Area */}
      <div
        {...getRootProps()}
        className={clsx(
          'border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-colors',
          isDragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-gray-400'
        )}
      >
        <input {...getInputProps()} className="hidden" />
        <Upload className="mx-auto h-12 w-12 text-gray-400 mb-4" />
        <p className="text-lg font-medium text-gray-700 mb-2">
          {isDragActive ? 'Drop files here' : 'Drag & drop PDF files here'}
        </p>
        <p className="text-sm text-gray-500 mb-4">
          or click to browse
        </p>
        <p className="text-xs text-gray-400">
          Max {maxFiles} files, {maxFileSize}MB each
        </p>
      </div>

      {/* File List */}
      {files.length > 0 && (
        <div className="mt-6 border rounded-lg overflow-hidden">
          <div className="bg-gray-50 px-4 py-3 border-b flex justify-between items-center">
            <h3 className="font-semibold text-gray-900">
              Files to Upload ({files.length})
            </h3>
            <button
              onClick={clearAll}
              className="text-sm text-red-600 hover:text-red-700"
            >
              Clear All
            </button>
          </div>
          
          <div className="divide-y max-h-96 overflow-y-auto">
            {files.map(file => (
              <div
                key={file.id}
                className="flex items-center justify-between px-4 py-3 hover:bg-gray-50"
              >
                <div className="flex items-center space-x-3 flex-1">
                  <FileText className="h-5 w-5 text-gray-400" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {file.name}
                    </p>
                    <p className="text-xs text-gray-500">
                      {(file.size / 1024 / 1024).toFixed(2)} MB
                    </p>
                  </div>
                </div>
                
                <div className="flex items-center space-x-2">
                  {file.status === 'pending' && (
                    <button
                      onClick={() => removeFile(file.id)}
                      className="p-1 text-gray-400 hover:text-gray-600"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  )}
                  
                  {file.status === 'uploading' && (
                    <Loader2 className="h-5 w-5 text-blue-500 animate-spin" />
                  )}
                  
                  {file.status === 'success' && (
                    <CheckCircle className="h-5 w-5 text-green-500" />
                  )}
                  
                  {file.status === 'error' && (
                    <AlertCircle className="h-5 w-5 text-red-500" />
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Upload Progress */}
      {batchId && (
        <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <h3 className="font-semibold text-blue-900">Uploading Documents</h3>
            <span className="text-sm text-blue-700">
              {uploadProgress[batchId] || 0}%
            </span>
          </div>
          <div className="w-full bg-blue-200 rounded-full h-2">
            <div
              className="bg-blue-500 h-2 rounded-full transition-all duration-300"
              style={{ width: `${uploadProgress[batchId] || 0}%` }}
            />
          </div>
          <p className="text-xs text-blue-600 mt-2">
            {uploadingFiles.length} uploading, {completedFiles.length} completed, {errorFiles.length} failed
          </p>
        </div>
      )}

      {/* Upload Button */}
      {pendingFiles.length > 0 && (
        <button
          onClick={handleUpload}
          disabled={uploadMutation.isPending}
          className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg font-medium hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
        >
          {uploadMutation.isPending ? (
            <span className="flex items-center justify-center">
              <Loader2 className="mr-2 h-5 w-5 animate-spin" />
              Uploading...
            </span>
          ) : (
            `Upload ${pendingFiles.length} File${pendingFiles.length > 1 ? 's' : ''}`
          )}
        </button>
      )}

      {/* Error Messages */}
      {uploadMutation.error && (
        <div className="mt-4 bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center">
            <AlertCircle className="h-5 w-5 text-red-500 mr-2" />
            <p className="text-sm text-red-700">
              Upload failed: {uploadMutation.error.message}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
