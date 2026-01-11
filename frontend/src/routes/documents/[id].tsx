/**
 * Document detail page
 */

import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, Download, RefreshCw, Eye } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  useDocument,
  useDocumentStatus,
  useExtractionResults,
  useDocumentDownloadUrl,
} from '@/hooks/useDocuments';
import {
  getStatusColor,
  getStatusLabel,
  getDocumentTypeLabel,
  isProcessing,
} from '@/types/document';
import { formatConfidence, getConfidenceColor } from '@/types/extraction';
import { formatDateTime, formatFileSize } from '@/lib/utils';

export default function DocumentDetail() {
  const { id } = useParams<{ id: string }>();
  const { data: document, isLoading: docLoading } = useDocument(id!);
  const { data: status } = useDocumentStatus(id!, {
    enabled: !!document && isProcessing(document.status),
  });
  const { data: results, isLoading: resultsLoading } = useExtractionResults(id!);
  const { data: downloadUrl } = useDocumentDownloadUrl(id!);

  if (docLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (!document) {
    return (
      <div className="text-center py-12">
        <p className="text-muted-foreground">Document not found</p>
        <Button variant="link" asChild>
          <Link to="/documents">Back to documents</Link>
        </Button>
      </div>
    );
  }

  const currentStatus = status?.status ?? document.status;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" asChild>
            <Link to="/documents">
              <ArrowLeft className="h-5 w-5" />
            </Link>
          </Button>
          <div>
            <h1 className="text-2xl font-bold">{document.filename}</h1>
            <p className="text-muted-foreground">
              {getDocumentTypeLabel(document.document_type)} • {document.page_count} pages
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Badge className={getStatusColor(currentStatus)}>
            {getStatusLabel(currentStatus)}
          </Badge>
          {downloadUrl && (
            <Button variant="outline" asChild>
              <a href={downloadUrl} download={document.filename}>
                <Download className="mr-2 h-4 w-4" />
                Download
              </a>
            </Button>
          )}
        </div>
      </div>

      {/* Processing status */}
      {isProcessing(currentStatus) && (
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary"></div>
              <div>
                <p className="font-medium">Processing document...</p>
                <p className="text-sm text-muted-foreground">
                  {status?.current_step ?? 'Please wait'}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Document info */}
      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Document Information</CardTitle>
          </CardHeader>
          <CardContent>
            <dl className="space-y-3">
              <div className="flex justify-between">
                <dt className="text-muted-foreground">File Size</dt>
                <dd>{formatFileSize(document.file_size)}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-muted-foreground">Pages</dt>
                <dd>{document.page_count}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-muted-foreground">Uploaded</dt>
                <dd>{formatDateTime(document.created_at)}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-muted-foreground">Last Updated</dt>
                <dd>{formatDateTime(document.updated_at)}</dd>
              </div>
            </dl>
          </CardContent>
        </Card>

        {/* Extraction results */}
        {results && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                Extraction Results
                <span className={getConfidenceColor(results.overall_confidence)}>
                  {formatConfidence(results.overall_confidence)} confidence
                </span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <dl className="space-y-3">
                <div className="flex justify-between">
                  <dt className="text-muted-foreground">OCR Engines</dt>
                  <dd>{results.ocr_engines_used.join(', ')}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-muted-foreground">Processing Time</dt>
                  <dd>{results.processing_time_ms}ms</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-muted-foreground">Validation</dt>
                  <dd>
                    <Badge
                      variant={
                        results.validation_status === 'valid'
                          ? 'success'
                          : results.validation_status === 'needs_review'
                          ? 'warning'
                          : 'destructive'
                      }
                    >
                      {results.validation_status}
                    </Badge>
                  </dd>
                </div>
              </dl>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Extracted fields */}
      {results && results.fields.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Extracted Fields</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-2 px-4 font-medium">Field</th>
                    <th className="text-left py-2 px-4 font-medium">Value</th>
                    <th className="text-left py-2 px-4 font-medium">Confidence</th>
                    <th className="text-left py-2 px-4 font-medium">Source</th>
                  </tr>
                </thead>
                <tbody>
                  {results.fields.map((field, index) => (
                    <tr key={index} className="border-b">
                      <td className="py-2 px-4 font-medium">{field.field_name}</td>
                      <td className="py-2 px-4">{field.field_value}</td>
                      <td className="py-2 px-4">
                        <span className={getConfidenceColor(field.confidence)}>
                          {formatConfidence(field.confidence)}
                        </span>
                      </td>
                      <td className="py-2 px-4 text-muted-foreground">
                        {field.source_engine}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Validation errors */}
      {results && results.validation_errors.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-destructive">Validation Errors</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2">
              {results.validation_errors.map((error, index) => (
                <li key={index} className="flex items-start gap-2">
                  <span className="text-destructive">•</span>
                  <div>
                    <span className="font-medium">{error.field_name}:</span>{' '}
                    <span className="text-muted-foreground">{error.message}</span>
                  </div>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
