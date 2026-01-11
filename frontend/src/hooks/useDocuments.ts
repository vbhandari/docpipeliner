/**
 * React Query hooks for document operations
 */

import {
  useQuery,
  useMutation,
  useQueryClient,
  type UseQueryOptions,
} from '@tanstack/react-query';
import * as documentsApi from '@/services/documents';
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
import { isTerminal } from '@/types';

// Query keys
export const documentKeys = {
  all: ['documents'] as const,
  lists: () => [...documentKeys.all, 'list'] as const,
  list: (params: DocumentListParams) => [...documentKeys.lists(), params] as const,
  details: () => [...documentKeys.all, 'detail'] as const,
  detail: (id: string) => [...documentKeys.details(), id] as const,
  status: (id: string) => [...documentKeys.detail(id), 'status'] as const,
  results: (id: string) => [...documentKeys.detail(id), 'results'] as const,
};

/**
 * Hook to fetch paginated document list
 */
export function useDocuments(
  params: DocumentListParams = {},
  options?: Omit<UseQueryOptions<DocumentListResponse>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: documentKeys.list(params),
    queryFn: () => documentsApi.listDocuments(params),
    staleTime: 30_000, // 30 seconds
    ...options,
  });
}

/**
 * Hook to fetch a single document
 */
export function useDocument(
  id: string,
  options?: Omit<UseQueryOptions<Document>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: documentKeys.detail(id),
    queryFn: () => documentsApi.getDocument(id),
    enabled: !!id,
    ...options,
  });
}

/**
 * Hook to poll document status during processing
 */
export function useDocumentStatus(
  id: string,
  options?: {
    enabled?: boolean;
    refetchInterval?: number | false;
  }
) {
  const { enabled = true, refetchInterval } = options || {};

  return useQuery({
    queryKey: documentKeys.status(id),
    queryFn: () => documentsApi.getDocumentStatus(id),
    enabled: enabled && !!id,
    refetchInterval: refetchInterval ?? ((data: DocumentStatusResponse | undefined) => {
      // Stop polling when document reaches terminal state
      if (data && isTerminal(data.status)) {
        return false;
      }
      return 2000; // Poll every 2 seconds
    }),
  });
}

/**
 * Hook to fetch extraction results
 */
export function useExtractionResults(
  id: string,
  options?: Omit<UseQueryOptions<ExtractionResult>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: documentKeys.results(id),
    queryFn: () => documentsApi.getExtractionResults(id),
    enabled: !!id,
    ...options,
  });
}

/**
 * Hook to upload a document
 */
export function useUploadDocument() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      file,
      documentType,
      metadata,
    }: {
      file: File;
      documentType?: DocumentType;
      metadata?: DocumentMetadata;
    }) => documentsApi.uploadDocument(file, documentType, metadata),
    onSuccess: () => {
      // Invalidate document list to show new document
      queryClient.invalidateQueries({ queryKey: documentKeys.lists() });
    },
  });
}

/**
 * Hook to delete a document
 */
export function useDeleteDocument() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => documentsApi.deleteDocument(id),
    onSuccess: (_data, id) => {
      // Remove from cache and invalidate list
      queryClient.removeQueries({ queryKey: documentKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: documentKeys.lists() });
    },
  });
}

/**
 * Hook to reprocess a document
 */
export function useReprocessDocument() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => documentsApi.reprocessDocument(id),
    onSuccess: (_data, id) => {
      // Invalidate document data
      queryClient.invalidateQueries({ queryKey: documentKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: documentKeys.lists() });
    },
  });
}

/**
 * Hook to request manual review
 */
export function useRequestReview() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => documentsApi.requestReview(id),
    onSuccess: (_data, id) => {
      queryClient.invalidateQueries({ queryKey: documentKeys.detail(id) });
    },
  });
}

/**
 * Hook to get document download URL
 */
export function useDocumentDownloadUrl(id: string) {
  return useQuery({
    queryKey: [...documentKeys.detail(id), 'download-url'],
    queryFn: () => documentsApi.getDocumentDownloadUrl(id),
    enabled: !!id,
    staleTime: 5 * 60 * 1000, // 5 minutes (presigned URLs typically valid for 15 min)
  });
}
