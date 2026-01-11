/**
 * Review API service for HITL workflow
 */

import { api } from './api';
import type {
  ReviewTask,
  ReviewListParams,
  ReviewListResponse,
  ReviewSubmission,
  ReviewStats,
} from '@/types';

/**
 * List review tasks with optional filters
 */
export async function listReviews(
  params: ReviewListParams = {}
): Promise<ReviewListResponse> {
  const searchParams = new URLSearchParams();

  if (params.page) searchParams.set('page', params.page.toString());
  if (params.page_size) searchParams.set('page_size', params.page_size.toString());
  if (params.status) searchParams.set('status', params.status);
  if (params.priority) searchParams.set('priority', params.priority);
  if (params.document_type) searchParams.set('document_type', params.document_type);
  if (params.sort_by) searchParams.set('sort_by', params.sort_by);
  if (params.sort_order) searchParams.set('sort_order', params.sort_order);

  const response = await api.get('reviews', { searchParams });
  return response.json();
}

/**
 * Get a single review task by ID
 */
export async function getReview(id: string): Promise<ReviewTask> {
  const response = await api.get(`reviews/${id}`);
  return response.json();
}

/**
 * Submit corrections for a review task
 */
export async function submitCorrections(
  id: string,
  submission: ReviewSubmission
): Promise<ReviewTask> {
  const response = await api.post(`reviews/${id}/corrections`, {
    json: submission,
  });
  return response.json();
}

/**
 * Approve a review task (mark as completed)
 */
export async function approveReview(
  id: string,
  notes?: string
): Promise<ReviewTask> {
  const response = await api.post(`reviews/${id}/approve`, {
    json: { notes },
  });
  return response.json();
}

/**
 * Reject a review task
 */
export async function rejectReview(
  id: string,
  reason: string
): Promise<ReviewTask> {
  const response = await api.post(`reviews/${id}/reject`, {
    json: { reason },
  });
  return response.json();
}

/**
 * Assign a review task to the current user
 */
export async function assignReview(id: string): Promise<ReviewTask> {
  const response = await api.post(`reviews/${id}/assign`);
  return response.json();
}

/**
 * Unassign a review task
 */
export async function unassignReview(id: string): Promise<ReviewTask> {
  const response = await api.post(`reviews/${id}/unassign`);
  return response.json();
}

/**
 * Skip a review task (move to end of queue)
 */
export async function skipReview(id: string): Promise<void> {
  await api.post(`reviews/${id}/skip`);
}

/**
 * Get review statistics
 */
export async function getReviewStats(): Promise<ReviewStats> {
  const response = await api.get('reviews/stats');
  return response.json();
}

/**
 * Get the next review task in queue
 */
export async function getNextReview(): Promise<ReviewTask | null> {
  try {
    const response = await api.get('reviews/next');
    return response.json();
  } catch {
    // No reviews available
    return null;
  }
}
