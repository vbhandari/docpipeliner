/**
 * Review types for HITL workflow
 */

import type { Document } from './document';
import type { ExtractionResult, ExtractedField } from './extraction';

export type ReviewStatus = 'pending' | 'in_progress' | 'completed' | 'rejected';
export type ReviewPriority = 'low' | 'normal' | 'high' | 'urgent';

export interface ReviewTask {
  id: string;
  document_id: string;
  document: Document;
  extraction_result: ExtractionResult;
  status: ReviewStatus;
  priority: ReviewPriority;
  assigned_to?: string;
  flagged_fields: string[];
  created_at: string;
  updated_at: string;
  completed_at?: string;
}

export interface FieldCorrection {
  field_name: string;
  original_value: string;
  corrected_value: string;
  correction_reason?: string;
}

export interface ReviewSubmission {
  corrections: FieldCorrection[];
  notes?: string;
  action: 'approve' | 'reject';
}

export interface ReviewListParams {
  page?: number;
  page_size?: number;
  status?: ReviewStatus;
  priority?: ReviewPriority;
  document_type?: string;
  sort_by?: 'created_at' | 'priority' | 'confidence';
  sort_order?: 'asc' | 'desc';
}

export interface ReviewListResponse {
  items: ReviewTask[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface ReviewStats {
  pending: number;
  in_progress: number;
  completed_today: number;
  avg_review_time_seconds: number;
}

// Helper functions
export function getPriorityLabel(priority: ReviewPriority): string {
  const labels: Record<ReviewPriority, string> = {
    low: 'Low',
    normal: 'Normal',
    high: 'High',
    urgent: 'Urgent',
  };
  return labels[priority];
}

export function getPriorityColor(priority: ReviewPriority): string {
  const colors: Record<ReviewPriority, string> = {
    low: 'bg-gray-100 text-gray-800',
    normal: 'bg-blue-100 text-blue-800',
    high: 'bg-orange-100 text-orange-800',
    urgent: 'bg-red-100 text-red-800',
  };
  return colors[priority];
}

export function getReviewStatusLabel(status: ReviewStatus): string {
  const labels: Record<ReviewStatus, string> = {
    pending: 'Pending',
    in_progress: 'In Progress',
    completed: 'Completed',
    rejected: 'Rejected',
  };
  return labels[status];
}

export function isFlaggedField(field: ExtractedField, flaggedFields: string[]): boolean {
  return flaggedFields.includes(field.field_name);
}

export function calculatePriority(confidence: number, age_hours: number): ReviewPriority {
  // Lower confidence = higher priority
  // Older documents = higher priority
  const confidenceScore = (1 - confidence) * 50;
  const ageScore = Math.min(age_hours / 24, 1) * 50;
  const totalScore = confidenceScore + ageScore;

  if (totalScore >= 75) return 'urgent';
  if (totalScore >= 50) return 'high';
  if (totalScore >= 25) return 'normal';
  return 'low';
}
