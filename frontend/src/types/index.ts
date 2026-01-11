/**
 * Re-export all types
 */

export * from './document';
export * from './extraction';
export * from './review';

// API response types
export interface ApiError {
  detail: string;
  status_code?: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// Analytics types
export interface AccuracyMetrics {
  overall: number;
  by_document_type: Record<string, number>;
  by_field: Record<string, number>;
  trend: AccuracyTrendPoint[];
}

export interface AccuracyTrendPoint {
  date: string;
  accuracy: number;
  document_count: number;
}

export interface EngineComparison {
  engine_name: string;
  accuracy: number;
  avg_processing_time_ms: number;
  document_count: number;
}

export interface ProcessingMetrics {
  total_documents: number;
  documents_today: number;
  avg_processing_time_ms: number;
  success_rate: number;
  review_rate: number;
}

export interface DriftAlert {
  id: string;
  alert_type: 'confidence_drop' | 'accuracy_drop' | 'template_change';
  severity: 'info' | 'warning' | 'critical';
  message: string;
  affected_field?: string;
  affected_document_type?: string;
  detected_at: string;
  acknowledged: boolean;
}

// Health check types
export interface HealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy';
  version: string;
  timestamp: string;
  services: {
    database: 'up' | 'down';
    storage: 'up' | 'down';
    ocr_tesseract: 'up' | 'down';
    ocr_paddle: 'up' | 'down';
  };
}
