/**
 * Document API service
 */

import { api, uploadFile } from './api';
import type {
  Document,
  DocumentListParams,
  DocumentListResponse,
  DocumentStatusResponse,
  DocumentUploadResponse,
  DocumentType,
  DocumentMetadata,
} from '@/types';
import type { ExtractionResult } from '@/types';

/**
 * Upload a new document
 */
export async function uploadDocument(
  file: File,
  documentType?: DocumentType,
  metadata?: DocumentMetadata
): Promise<DocumentUploadResponse> {
  const additionalData: Record<string, string> = {};

  if (documentType) {
    additionalData.document_type = documentType;
  }

  if (metadata) {
    additionalData.metadata = JSON.stringify(metadata);
  }

  const response = await uploadFile('documents', file, additionalData);
  return response.json();
}

/**
 * List documents with optional filters
 */
export async function listDocuments(
  params: DocumentListParams = {}
): Promise<DocumentListResponse> {
  const searchParams = new URLSearchParams();

  if (params.page) searchParams.set('page', params.page.toString());
  if (params.page_size) searchParams.set('page_size', params.page_size.toString());
  if (params.document_type) searchParams.set('document_type', params.document_type);
  if (params.status) searchParams.set('status', params.status);
  if (params.search) searchParams.set('search', params.search);
  if (params.sort_by) searchParams.set('sort_by', params.sort_by);
  if (params.sort_order) searchParams.set('sort_order', params.sort_order);

  const response = await api.get('documents', { searchParams });
  return response.json();
}

/**
 * Get a single document by ID
 */
export async function getDocument(id: string): Promise<Document> {
  const response = await api.get(`documents/${id}`);
  return response.json();
}

/**
 * Get document processing status
 */
export async function getDocumentStatus(id: string): Promise<DocumentStatusResponse> {
  const response = await api.get(`documents/${id}/status`);
  return response.json();
}

/**
 * Get extraction results for a document
 */
export async function getExtractionResults(id: string): Promise<ExtractionResult> {
  const response = await api.get(`documents/${id}/results`);
  return response.json();
}

/**
 * Delete a document
 */
export async function deleteDocument(id: string): Promise<void> {
  await api.delete(`documents/${id}`);
}

/**
 * Reprocess a document
 */
export async function reprocessDocument(id: string): Promise<DocumentUploadResponse> {
  const response = await api.post(`documents/${id}/reprocess`);
  return response.json();
}

/**
 * Request manual review for a document
 */
export async function requestReview(id: string): Promise<void> {
  await api.post(`documents/${id}/request-review`);
}

/**
 * Get presigned URL for document download
 */
export async function getDocumentDownloadUrl(id: string): Promise<string> {
  const response = await api.get(`documents/${id}/download-url`);
  const data = await response.json() as { url: string };
  return data.url;
}

/**
 * Get presigned URL for document preview (page images)
 */
export async function getPagePreviewUrl(
  documentId: string,
  pageNumber: number
): Promise<string> {
  const response = await api.get(`documents/${documentId}/pages/${pageNumber}/preview-url`);
  const data = await response.json() as { url: string };
  return data.url;
}
