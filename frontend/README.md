# DocPipeliner Frontend

React 19 + TypeScript + Vite frontend for the DocPipeliner document processing system.

## Features

- **Document Management**: Upload, list, and view processed documents
- **Human-in-the-Loop Review**: Correct low-confidence extractions
- **Analytics Dashboard**: Monitor system performance and accuracy trends
- **Responsive Design**: Mobile-first with Tailwind CSS

## Tech Stack

- **React 19** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **TanStack Query** - Server state management
- **React Router** - Routing
- **shadcn/ui** - UI components
- **Lucide React** - Icons

## Getting Started

### Prerequisites

- Node.js 20+
- npm or pnpm

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

The app will be available at `http://localhost:3000`.

### Environment Variables

Create a `.env.local` file:

```env
VITE_API_URL=http://localhost:8000/api/v1
VITE_API_KEY=your-api-key
```

## Project Structure

```
src/
├── components/       # Reusable UI components
│   ├── ui/          # Base components (shadcn/ui)
│   ├── layout/      # Layout components
│   ├── documents/   # Document-related components
│   ├── review/      # Review interface components
│   └── analytics/   # Analytics components
├── hooks/           # React Query hooks
├── services/        # API client and services
├── types/           # TypeScript type definitions
├── lib/             # Utility functions
├── routes/          # Page components
│   ├── documents/   # Document pages
│   ├── reviews/     # Review pages
│   └── analytics/   # Analytics pages
└── styles/          # Global styles
```

## Available Scripts

```bash
# Development
npm run dev          # Start dev server
npm run build        # Build for production
npm run preview      # Preview production build

# Testing
npm run test         # Run tests
npm run test:ui      # Run tests with UI
npm run test:coverage # Run tests with coverage

# Code Quality
npm run lint         # Run ESLint
npm run typecheck    # Run TypeScript check
```

## Pages

| Route | Description |
|-------|-------------|
| `/` | Dashboard with overview stats |
| `/documents` | Document list with filters |
| `/documents/upload` | Upload new documents |
| `/documents/:id` | Document detail with extraction results |
| `/reviews` | Review queue for low-confidence documents |
| `/reviews/:id` | Review interface for corrections |
| `/analytics` | Analytics dashboard |

## API Integration

The frontend communicates with the FastAPI backend via REST API. All API calls are managed through TanStack Query for caching and state management.

### Hooks

- `useDocuments()` - Fetch document list
- `useDocument(id)` - Fetch single document
- `useUploadDocument()` - Upload mutation
- `useReviews()` - Fetch review queue
- `useSubmitCorrections()` - Submit review corrections

## Deployment

### Cloudflare Pages

```bash
# Build
npm run build

# Deploy (via Wrangler or Cloudflare dashboard)
npx wrangler pages deploy dist
```

### Environment Configuration

Set these environment variables in Cloudflare Pages:

- `VITE_API_URL` - Backend API URL
- `VITE_API_KEY` - API key (if required)

## License

Apache License 2.0
