import { Routes, Route } from 'react-router-dom';
import { MainLayout } from './components/layout/MainLayout';

// Lazy load pages for code splitting
import { lazy, Suspense } from 'react';

const Dashboard = lazy(() => import('./routes/index'));
const DocumentList = lazy(() => import('./routes/documents/index'));
const DocumentUpload = lazy(() => import('./routes/documents/upload'));
const DocumentDetail = lazy(() => import('./routes/documents/[id]'));
const ReviewQueue = lazy(() => import('./routes/reviews/index'));
const ReviewDetail = lazy(() => import('./routes/reviews/[id]'));
const Analytics = lazy(() => import('./routes/analytics/index'));

// Loading fallback
function PageLoader() {
  return (
    <div className="flex items-center justify-center h-64">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
    </div>
  );
}

function App() {
  return (
    <MainLayout>
      <Suspense fallback={<PageLoader />}>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/documents" element={<DocumentList />} />
          <Route path="/documents/upload" element={<DocumentUpload />} />
          <Route path="/documents/:id" element={<DocumentDetail />} />
          <Route path="/reviews" element={<ReviewQueue />} />
          <Route path="/reviews/:id" element={<ReviewDetail />} />
          <Route path="/analytics" element={<Analytics />} />
        </Routes>
      </Suspense>
    </MainLayout>
  );
}

export default App;
