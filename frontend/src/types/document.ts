/**
 * Document types matching backend models
 */

export type DocumentType = 'invoice' | 'insurance_claim' | 'compliance_form' | 'unknown';

export type DocumentStatus =
  | 'uploaded'
  | 'preprocessing'
  | 'ocr_processing'
  | 'extracting'
  | 'validating'
  | 'needs_review'
  | 'in_review'
  | 'completed'
  | 'failed';

export interface DocumentMetadata {
  source?: string;
  sender?: string;
  [key: string]: unknown;
}

export interface Document {
  id: string;
  filename: string;
  document_type: DocumentType;
  status: DocumentStatus;
  storage_path: string;
  page_count: number;
  file_size: number;
  metadata: DocumentMetadata;
  created_at: string;
  updated_at: string;
}

export interface DocumentUploadRequest {
  file: File;
  document_type?: DocumentType;
  metadata?: DocumentMetadata;
}

export interface DocumentUploadResponse {
  id: string;
  filename: string;
  document_type: DocumentType;
  status: DocumentStatus;
  created_at: string;
  estimated_completion?: string;
}

export interface DocumentListParams {
  page?: number;
  page_size?: number;
  document_type?: DocumentType;
  status?: DocumentStatus;
  search?: string;
  sort_by?: 'created_at' | 'filename' | 'status';
  sort_order?: 'asc' | 'desc';
}

export interface DocumentListResponse {
  items: Document[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface DocumentStatusResponse {
  id: string;
  status: DocumentStatus;
  progress?: number;
  current_step?: string;
  error_message?: string;
}

// Helper functions
export function isProcessing(status: DocumentStatus): boolean {
  return ['uploaded', 'preprocessing', 'ocr_processing', 'extracting', 'validating'].includes(status);
}

export function isTerminal(status: DocumentStatus): boolean {
  return ['completed', 'failed'].includes(status);
}

export function needsReview(status: DocumentStatus): boolean {
  return ['needs_review', 'in_review'].includes(status);
}

export function getStatusLabel(status: DocumentStatus): string {
  const labels: Record<DocumentStatus, string> = {
    uploaded: 'Uploaded',
    preprocessing: 'Preprocessing',
    ocr_processing: 'OCR Processing',
    extracting: 'Extracting',
    validating: 'Validating',
    needs_review: 'Needs Review',
    in_review: 'In Review',
    completed: 'Completed',
    failed: 'Failed',
  };
  return labels[status];
}

export function getStatusColor(status: DocumentStatus): string {
  const colors: Record<DocumentStatus, string> = {
    uploaded: 'status-uploaded',
    preprocessing: 'status-processing',
    ocr_processing: 'status-processing',
    extracting: 'status-processing',
    validating: 'status-processing',
    needs_review: 'status-needs-review',
    in_review: 'status-needs-review',
    completed: 'status-completed',
    failed: 'status-failed',
  };
  return colors[status];
}

export function getDocumentTypeLabel(type: DocumentType): string {
  const labels: Record<DocumentType, string> = {
    invoice: 'Invoice',
    insurance_claim: 'Insurance Claim',
    compliance_form: 'Compliance Form',
    unknown: 'Unknown',
  };
  return labels[type];
}
