/**
 * Document list page
 */

import { useState } from 'react';
import { Link } from 'react-router-dom';
import { FileText, Upload, Search, Filter, Trash2, RefreshCw } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useDocuments, useDeleteDocument, useReprocessDocument } from '@/hooks/useDocuments';
import {
  DocumentType,
  DocumentStatus,
  getStatusColor,
  getStatusLabel,
  getDocumentTypeLabel,
} from '@/types/document';
import { formatRelativeTime, formatFileSize } from '@/lib/utils';

export default function DocumentList() {
  const [search, setSearch] = useState('');
  const [typeFilter, setTypeFilter] = useState<DocumentType | ''>('');
  const [statusFilter, setStatusFilter] = useState<DocumentStatus | ''>('');
  const [page, setPage] = useState(1);

  const { data, isLoading, refetch } = useDocuments({
    page,
    page_size: 10,
    search: search || undefined,
    document_type: typeFilter || undefined,
    status: statusFilter || undefined,
    sort_by: 'created_at',
    sort_order: 'desc',
  });

  const deleteDocument = useDeleteDocument();
  const reprocessDocument = useReprocessDocument();

  const documents = data?.items ?? [];
  const totalPages = data?.total_pages ?? 1;

  const handleDelete = async (id: string, filename: string) => {
    if (confirm(`Are you sure you want to delete "${filename}"?`)) {
      await deleteDocument.mutateAsync(id);
    }
  };

  const handleReprocess = async (id: string) => {
    await reprocessDocument.mutateAsync(id);
  };

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Documents</h1>
          <p className="text-muted-foreground">
            Manage and view all processed documents
          </p>
        </div>
        <Button asChild>
          <Link to="/documents/upload">
            <Upload className="mr-2 h-4 w-4" />
            Upload
          </Link>
        </Button>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col sm:flex-row gap-4">
            {/* Search */}
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <input
                type="text"
                placeholder="Search documents..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border rounded-md bg-background"
              />
            </div>

            {/* Type filter */}
            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value as DocumentType | '')}
              className="px-3 py-2 border rounded-md bg-background"
            >
              <option value="">All Types</option>
              <option value="invoice">Invoice</option>
              <option value="insurance_claim">Insurance Claim</option>
              <option value="compliance_form">Compliance Form</option>
            </select>

            {/* Status filter */}
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value as DocumentStatus | '')}
              className="px-3 py-2 border rounded-md bg-background"
            >
              <option value="">All Statuses</option>
              <option value="uploaded">Uploaded</option>
              <option value="ocr_processing">Processing</option>
              <option value="completed">Completed</option>
              <option value="needs_review">Needs Review</option>
              <option value="failed">Failed</option>
            </select>

            {/* Refresh */}
            <Button variant="outline" size="icon" onClick={() => refetch()}>
              <RefreshCw className="h-4 w-4" />
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Document list */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Filter className="h-5 w-5" />
            {data?.total ?? 0} Documents
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex items-center justify-center h-32">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary"></div>
            </div>
          ) : documents.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              <FileText className="mx-auto h-12 w-12 mb-4 opacity-50" />
              <p>No documents found</p>
              {(search || typeFilter || statusFilter) && (
                <Button
                  variant="link"
                  onClick={() => {
                    setSearch('');
                    setTypeFilter('');
                    setStatusFilter('');
                  }}
                >
                  Clear filters
                </Button>
              )}
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-3 px-4 font-medium">Filename</th>
                    <th className="text-left py-3 px-4 font-medium">Type</th>
                    <th className="text-left py-3 px-4 font-medium">Status</th>
                    <th className="text-left py-3 px-4 font-medium">Size</th>
                    <th className="text-left py-3 px-4 font-medium">Created</th>
                    <th className="text-right py-3 px-4 font-medium">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {documents.map((doc) => (
                    <tr key={doc.id} className="border-b hover:bg-muted/50">
                      <td className="py-3 px-4">
                        <Link
                          to={`/documents/${doc.id}`}
                          className="flex items-center gap-2 hover:text-primary"
                        >
                          <FileText className="h-4 w-4" />
                          <span className="font-medium">{doc.filename}</span>
                        </Link>
                      </td>
                      <td className="py-3 px-4">
                        {getDocumentTypeLabel(doc.document_type)}
                      </td>
                      <td className="py-3 px-4">
                        <Badge className={getStatusColor(doc.status)}>
                          {getStatusLabel(doc.status)}
                        </Badge>
                      </td>
                      <td className="py-3 px-4 text-muted-foreground">
                        {formatFileSize(doc.file_size)}
                      </td>
                      <td className="py-3 px-4 text-muted-foreground">
                        {formatRelativeTime(doc.created_at)}
                      </td>
                      <td className="py-3 px-4 text-right">
                        <div className="flex items-center justify-end gap-2">
                          {doc.status === 'failed' && (
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => handleReprocess(doc.id)}
                              disabled={reprocessDocument.isPending}
                            >
                              <RefreshCw className="h-4 w-4" />
                            </Button>
                          )}
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => handleDelete(doc.id, doc.filename)}
                            disabled={deleteDocument.isPending}
                          >
                            <Trash2 className="h-4 w-4 text-destructive" />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-2 mt-6">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
              >
                Previous
              </Button>
              <span className="text-sm text-muted-foreground">
                Page {page} of {totalPages}
              </span>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
              >
                Next
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
