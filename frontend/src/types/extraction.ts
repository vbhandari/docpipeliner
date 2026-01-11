/**
 * Extraction result types matching backend models
 */

import type { DocumentType } from './document';

export interface BoundingBox {
  x: number;
  y: number;
  width: number;
  height: number;
  page: number;
}

export interface ExtractedField {
  field_name: string;
  field_value: string;
  confidence: number;
  bounding_box?: BoundingBox;
  source_engine: string;
}

export interface ValidationError {
  field_name: string;
  error_type: 'missing' | 'invalid_format' | 'low_confidence' | 'cross_field_mismatch';
  message: string;
}

export interface LineItem {
  description: string;
  quantity?: number;
  unit_price?: number;
  total?: number;
  confidence: number;
}

export interface ExtractionResult {
  document_id: string;
  document_type: DocumentType;
  fields: ExtractedField[];
  line_items?: LineItem[];
  overall_confidence: number;
  validation_status: 'valid' | 'invalid' | 'needs_review';
  validation_errors: ValidationError[];
  ocr_engines_used: string[];
  processing_time_ms: number;
  extracted_at: string;
}

// Invoice-specific extraction
export interface InvoiceExtraction extends ExtractionResult {
  document_type: 'invoice';
  invoice_number?: string;
  vendor_name?: string;
  invoice_date?: string;
  due_date?: string;
  subtotal?: string;
  tax?: string;
  total_amount?: string;
  line_items: LineItem[];
}

// Insurance claim-specific extraction
export interface InsuranceClaimExtraction extends ExtractionResult {
  document_type: 'insurance_claim';
  claim_id?: string;
  policy_number?: string;
  claimant_name?: string;
  incident_date?: string;
  incident_description?: string;
  claim_amount?: string;
}

// Compliance form-specific extraction
export interface ComplianceFormExtraction extends ExtractionResult {
  document_type: 'compliance_form';
  entity_name?: string;
  filing_period?: string;
  signature_present?: boolean;
  sections_complete?: Record<string, boolean>;
}

// Helper functions
export function getConfidenceLevel(confidence: number): 'high' | 'medium' | 'low' {
  if (confidence >= 0.9) return 'high';
  if (confidence >= 0.7) return 'medium';
  return 'low';
}

export function getConfidenceColor(confidence: number): string {
  const level = getConfidenceLevel(confidence);
  const colors = {
    high: 'confidence-high',
    medium: 'confidence-medium',
    low: 'confidence-low',
  };
  return colors[level];
}

export function formatConfidence(confidence: number): string {
  return `${Math.round(confidence * 100)}%`;
}

export function getFieldByName(fields: ExtractedField[], name: string): ExtractedField | undefined {
  return fields.find((f) => f.field_name === name);
}

export function getLowConfidenceFields(fields: ExtractedField[], threshold = 0.85): ExtractedField[] {
  return fields.filter((f) => f.confidence < threshold);
}
