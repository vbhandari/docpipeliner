/**
 * React Query hooks for review operations
 */

import {
  useQuery,
  useMutation,
  useQueryClient,
  type UseQueryOptions,
} from '@tanstack/react-query';
import * as reviewsApi from '@/services/reviews';
import type {
  ReviewTask,
  ReviewListParams,
  ReviewListResponse,
  ReviewSubmission,
  ReviewStats,
} from '@/types';
import { documentKeys } from './useDocuments';

// Query keys
export const reviewKeys = {
  all: ['reviews'] as const,
  lists: () => [...reviewKeys.all, 'list'] as const,
  list: (params: ReviewListParams) => [...reviewKeys.lists(), params] as const,
  details: () => [...reviewKeys.all, 'detail'] as const,
  detail: (id: string) => [...reviewKeys.details(), id] as const,
  stats: () => [...reviewKeys.all, 'stats'] as const,
  next: () => [...reviewKeys.all, 'next'] as const,
};

/**
 * Hook to fetch paginated review list
 */
export function useReviews(
  params: ReviewListParams = {},
  options?: Omit<UseQueryOptions<ReviewListResponse>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: reviewKeys.list(params),
    queryFn: () => reviewsApi.listReviews(params),
    staleTime: 10_000, // 10 seconds - reviews change more frequently
    ...options,
  });
}

/**
 * Hook to fetch a single review task
 */
export function useReview(
  id: string,
  options?: Omit<UseQueryOptions<ReviewTask>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: reviewKeys.detail(id),
    queryFn: () => reviewsApi.getReview(id),
    enabled: !!id,
    ...options,
  });
}

/**
 * Hook to fetch review statistics
 */
export function useReviewStats(
  options?: Omit<UseQueryOptions<ReviewStats>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: reviewKeys.stats(),
    queryFn: () => reviewsApi.getReviewStats(),
    staleTime: 30_000, // 30 seconds
    ...options,
  });
}

/**
 * Hook to get the next review in queue
 */
export function useNextReview(
  options?: Omit<UseQueryOptions<ReviewTask | null>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: reviewKeys.next(),
    queryFn: () => reviewsApi.getNextReview(),
    staleTime: 5_000, // 5 seconds
    ...options,
  });
}

/**
 * Hook to submit corrections for a review
 */
export function useSubmitCorrections() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, submission }: { id: string; submission: ReviewSubmission }) =>
      reviewsApi.submitCorrections(id, submission),
    onSuccess: (data: ReviewTask) => {
      // Update the review in cache
      queryClient.setQueryData(reviewKeys.detail(data.id), data);
      // Invalidate lists and stats
      queryClient.invalidateQueries({ queryKey: reviewKeys.lists() });
      queryClient.invalidateQueries({ queryKey: reviewKeys.stats() });
      // Also invalidate the related document
      queryClient.invalidateQueries({ queryKey: documentKeys.detail(data.document_id) });
    },
  });
}

/**
 * Hook to approve a review
 */
export function useApproveReview() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, notes }: { id: string; notes?: string }) =>
      reviewsApi.approveReview(id, notes),
    onSuccess: (data: ReviewTask) => {
      queryClient.setQueryData(reviewKeys.detail(data.id), data);
      queryClient.invalidateQueries({ queryKey: reviewKeys.lists() });
      queryClient.invalidateQueries({ queryKey: reviewKeys.stats() });
      queryClient.invalidateQueries({ queryKey: reviewKeys.next() });
      queryClient.invalidateQueries({ queryKey: documentKeys.detail(data.document_id) });
    },
  });
}

/**
 * Hook to reject a review
 */
export function useRejectReview() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, reason }: { id: string; reason: string }) =>
      reviewsApi.rejectReview(id, reason),
    onSuccess: (data: ReviewTask) => {
      queryClient.setQueryData(reviewKeys.detail(data.id), data);
      queryClient.invalidateQueries({ queryKey: reviewKeys.lists() });
      queryClient.invalidateQueries({ queryKey: reviewKeys.stats() });
      queryClient.invalidateQueries({ queryKey: reviewKeys.next() });
      queryClient.invalidateQueries({ queryKey: documentKeys.detail(data.document_id) });
    },
  });
}

/**
 * Hook to assign a review to current user
 */
export function useAssignReview() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => reviewsApi.assignReview(id),
    onSuccess: (data: ReviewTask) => {
      queryClient.setQueryData(reviewKeys.detail(data.id), data);
      queryClient.invalidateQueries({ queryKey: reviewKeys.lists() });
    },
  });
}

/**
 * Hook to skip a review
 */
export function useSkipReview() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => reviewsApi.skipReview(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: reviewKeys.lists() });
      queryClient.invalidateQueries({ queryKey: reviewKeys.next() });
    },
  });
}
