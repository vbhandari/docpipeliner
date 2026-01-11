# DocPipeliner

A robust document ingestion framework featuring multi-stage OCR processing, automated validation, and distributed task management.

## Overview

DocPipeliner is a cloud-native Intelligent Document Processing (IDP) pipeline designed to extract structured data from semi-structured PDF documents (invoices, insurance forms, compliance filings). The system differentiates itself through:

- **Multi-engine OCR comparison** with pluggable architecture (Tesseract + PaddleOCR)
- **Explicit confidence scoring** and uncertainty handling
- **Automated validation** with cross-field checks
- **Human-in-the-loop workflow** for low-confidence documents
- **Observability and drift detection** for production reliability
- **Comprehensive testing strategy** for probabilistic outputs

## Architecture

See [plans/architecture.md](plans/architecture.md) for detailed architecture documentation.

### Technology Stack

| Layer | Technology |
|-------|------------|
| Backend API | FastAPI (Python) |
| Frontend | React 19 + TypeScript + Vite |
| Database | Supabase (PostgreSQL) |
| Object Storage | Cloudflare R2 |
| Task Queue | Cloudflare Queues |
| OCR Engines | Tesseract + PaddleOCR |
| Deployment | Railway.app (backend), Cloudflare Pages (frontend) |

## Project Structure

```
docpipeliner/
├── backend/                    # FastAPI backend
│   ├── src/docpipeliner/      # Main application code
│   │   ├── api/               # API routes
│   │   ├── models/            # Pydantic models
│   │   ├── ocr/               # OCR engine implementations
│   │   ├── storage/           # Storage clients (R2, Supabase)
│   │   └── main.py            # Application entry point
│   ├── supabase/              # Database migrations
│   ├── tests/                 # Test suite
│   ├── Dockerfile
│   └── pyproject.toml
├── frontend/                   # React frontend (coming soon)
├── plans/                      # Architecture documentation
└── README.md
```

## Getting Started

### Prerequisites

- Python 3.11+
- Tesseract OCR installed (`apt install tesseract-ocr`)
- Supabase account
- Cloudflare account (for R2 storage)

### Backend Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/docpipeliner.git
   cd docpipeliner
   ```

2. Create a virtual environment:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

4. Copy environment configuration:
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

5. Run database migrations:
   ```bash
   # Apply migrations in Supabase dashboard or using supabase CLI
   ```

6. Start the development server:
   ```bash
   python -m docpipeliner.main
   # Or with uvicorn directly:
   uvicorn docpipeliner.main:app --reload
   ```

7. Access the API documentation at http://localhost:8000/docs

### Running Tests

```bash
cd backend
pytest
```

## API Endpoints

### Documents

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/documents` | Upload a new document |
| GET | `/api/v1/documents` | List documents |
| GET | `/api/v1/documents/{id}` | Get document details |
| GET | `/api/v1/documents/{id}/status` | Get processing status |
| GET | `/api/v1/documents/{id}/results` | Get extraction results |
| DELETE | `/api/v1/documents/{id}` | Delete a document |

### Reviews

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/reviews` | List review tasks |
| GET | `/api/v1/reviews/{id}` | Get review task details |
| POST | `/api/v1/reviews/{id}/corrections` | Submit corrections |
| POST | `/api/v1/reviews/{id}/approve` | Approve extraction |

### Health

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Basic health check |
| GET | `/health/detailed` | Detailed health with dependencies |

## Supported Document Types

1. **Invoices** - Extract invoice number, vendor, date, line items, totals
2. **Insurance Claims** - Extract claim ID, policy number, claimant, incident details
3. **Compliance Forms** - Extract entity name, filing period, signatures, completeness

## OCR Engines

DocPipeliner supports multiple OCR engines through a pluggable architecture:

- **Tesseract** - Open-source OCR engine (default)
- **PaddleOCR** - Deep learning-based OCR with better accuracy for complex layouts

Engines can be used individually or in parallel for result comparison and consensus.

## Configuration

Key environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `CONFIDENCE_THRESHOLD` | Minimum confidence for auto-approval | 0.85 |
| `MAX_FILE_SIZE_MB` | Maximum upload file size | 50 |
| `TESSERACT_LANG` | Tesseract language | eng |
| `PADDLEOCR_USE_GPU` | Enable GPU for PaddleOCR | false |

See [backend/.env.example](backend/.env.example) for all options.

## Development Roadmap

- [x] Phase 1: Foundation (FastAPI, database, upload API, Tesseract)
- [ ] Phase 2: Extraction & Validation (extractors, PaddleOCR, validation)
- [ ] Phase 3: Queue & Workers (async processing)
- [ ] Phase 4: Frontend & HITL (React UI, review interface)
- [ ] Phase 5: Testing & Quality (test suites, drift detection)
- [ ] Phase 6: Additional Extractors (insurance, compliance)

## Contributing

Contributions are welcome! Please read our contributing guidelines before submitting PRs.

## License

Apache License 2.0 - see [LICENSE](LICENSE) for details.
