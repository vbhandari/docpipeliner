-- DocPipeliner Initial Database Schema
-- Migration: 001_initial_schema
-- Description: Create core tables for document processing pipeline

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Document types enum
CREATE TYPE document_type AS ENUM (
    'invoice',
    'insurance_claim',
    'compliance_form',
    'unknown'
);

-- Document status enum
CREATE TYPE document_status AS ENUM (
    'uploaded',
    'preprocessing',
    'ocr_processing',
    'extracting',
    'validating',
    'needs_review',
    'in_review',
    'completed',
    'failed'
);

-- Validation status enum
CREATE TYPE validation_status AS ENUM (
    'valid',
    'invalid',
    'needs_review'
);

-- Review task status enum
CREATE TYPE review_task_status AS ENUM (
    'pending',
    'assigned',
    'in_progress',
    'completed',
    'rejected'
);

-- Review task priority enum
CREATE TYPE review_task_priority AS ENUM (
    'low',
    'medium',
    'high',
    'urgent'
);

-- Documents table
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    filename VARCHAR(255) NOT NULL,
    document_type document_type NOT NULL DEFAULT 'unknown',
    storage_path TEXT NOT NULL,
    status document_status NOT NULL DEFAULT 'uploaded',
    metadata JSONB DEFAULT '{}',
    page_count INTEGER,
    file_size_bytes BIGINT,
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Pages table
CREATE TABLE pages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    page_number INTEGER NOT NULL,
    image_path TEXT NOT NULL,
    classification VARCHAR(50),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(document_id, page_number)
);

-- OCR results table
CREATE TABLE ocr_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    page_id UUID NOT NULL REFERENCES pages(id) ON DELETE CASCADE,
    engine VARCHAR(50) NOT NULL,
    raw_text TEXT NOT NULL,
    words JSONB DEFAULT '[]',
    avg_confidence FLOAT NOT NULL,
    processing_ms INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Extraction results table
CREATE TABLE extraction_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    document_type document_type NOT NULL,
    extractor_version VARCHAR(20) NOT NULL DEFAULT '1.0.0',
    fields JSONB DEFAULT '[]',
    overall_confidence FLOAT NOT NULL,
    validation_status validation_status NOT NULL DEFAULT 'needs_review',
    validation_errors JSONB DEFAULT '[]',
    raw_ocr_text TEXT,
    processing_metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Review tasks table
CREATE TABLE review_tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    status review_task_status NOT NULL DEFAULT 'pending',
    priority review_task_priority NOT NULL DEFAULT 'medium',
    assigned_to VARCHAR(255),
    reason TEXT,
    flagged_fields JSONB DEFAULT '[]',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

-- Field corrections table
CREATE TABLE field_corrections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    review_task_id UUID NOT NULL REFERENCES review_tasks(id) ON DELETE CASCADE,
    field_name VARCHAR(100) NOT NULL,
    original_value TEXT NOT NULL,
    corrected_value TEXT NOT NULL,
    correction_reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for common queries
CREATE INDEX idx_documents_status ON documents(status);
CREATE INDEX idx_documents_document_type ON documents(document_type);
CREATE INDEX idx_documents_created_at ON documents(created_at DESC);

CREATE INDEX idx_pages_document_id ON pages(document_id);

CREATE INDEX idx_ocr_results_page_id ON ocr_results(page_id);
CREATE INDEX idx_ocr_results_engine ON ocr_results(engine);

CREATE INDEX idx_extraction_results_document_id ON extraction_results(document_id);
CREATE INDEX idx_extraction_results_validation_status ON extraction_results(validation_status);

CREATE INDEX idx_review_tasks_document_id ON review_tasks(document_id);
CREATE INDEX idx_review_tasks_status ON review_tasks(status);
CREATE INDEX idx_review_tasks_priority ON review_tasks(priority);
CREATE INDEX idx_review_tasks_assigned_to ON review_tasks(assigned_to);

CREATE INDEX idx_field_corrections_review_task_id ON field_corrections(review_task_id);

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_documents_updated_at
    BEFORE UPDATE ON documents
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_review_tasks_updated_at
    BEFORE UPDATE ON review_tasks
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Row Level Security (RLS) policies
-- Enable RLS on all tables
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE pages ENABLE ROW LEVEL SECURITY;
ALTER TABLE ocr_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE extraction_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE review_tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE field_corrections ENABLE ROW LEVEL SECURITY;

-- Service role has full access (for backend)
CREATE POLICY "Service role has full access to documents"
    ON documents FOR ALL
    USING (auth.role() = 'service_role');

CREATE POLICY "Service role has full access to pages"
    ON pages FOR ALL
    USING (auth.role() = 'service_role');

CREATE POLICY "Service role has full access to ocr_results"
    ON ocr_results FOR ALL
    USING (auth.role() = 'service_role');

CREATE POLICY "Service role has full access to extraction_results"
    ON extraction_results FOR ALL
    USING (auth.role() = 'service_role');

CREATE POLICY "Service role has full access to review_tasks"
    ON review_tasks FOR ALL
    USING (auth.role() = 'service_role');

CREATE POLICY "Service role has full access to field_corrections"
    ON field_corrections FOR ALL
    USING (auth.role() = 'service_role');
