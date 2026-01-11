/**
 * Dashboard page - Home route
 */

import { Link } from 'react-router-dom';
import { FileText, Clock, AlertCircle, Upload, ArrowRight } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useDocuments } from '@/hooks/useDocuments';
import { useReviewStats } from '@/hooks/useReviews';
import { formatRelativeTime, getStatusColor, getStatusLabel } from '@/types';

function StatsCard({
  title,
  value,
  subtitle,
  icon: Icon,
}: {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: React.ComponentType<{ className?: string }>;
}) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        <Icon className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        {subtitle && (
          <p className="text-xs text-muted-foreground">{subtitle}</p>
        )}
      </CardContent>
    </Card>
  );
}

export default function Dashboard() {
  const { data: documentsData, isLoading: documentsLoading } = useDocuments({
    page_size: 5,
    sort_by: 'created_at',
    sort_order: 'desc',
  });

  const { data: reviewStats, isLoading: reviewsLoading } = useReviewStats();

  const totalDocuments = documentsData?.total ?? 0;
  const recentDocuments = documentsData?.items ?? [];
  const pendingReviews = reviewStats?.pending ?? 0;
  const processingCount = recentDocuments.filter(
    (d) => ['preprocessing', 'ocr_processing', 'extracting', 'validating'].includes(d.status)
  ).length;

  return (
    <div className="space-y-8">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-muted-foreground">
            Overview of your document processing pipeline
          </p>
        </div>
        <Button asChild>
          <Link to="/documents/upload">
            <Upload className="mr-2 h-4 w-4" />
            Upload Document
          </Link>
        </Button>
      </div>

      {/* Stats cards */}
      <div className="grid gap-4 md:grid-cols-3">
        <StatsCard
          title="Total Documents"
          value={documentsLoading ? '...' : totalDocuments}
          subtitle="All time"
          icon={FileText}
        />
        <StatsCard
          title="Processing"
          value={documentsLoading ? '...' : processingCount}
          subtitle="Currently in queue"
          icon={Clock}
        />
        <StatsCard
          title="Needs Review"
          value={reviewsLoading ? '...' : pendingReviews}
          subtitle="Awaiting human review"
          icon={AlertCircle}
        />
      </div>

      {/* Recent documents */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Recent Documents</CardTitle>
          <Button variant="ghost" size="sm" asChild>
            <Link to="/documents">
              View All
              <ArrowRight className="ml-2 h-4 w-4" />
            </Link>
          </Button>
        </CardHeader>
        <CardContent>
          {documentsLoading ? (
            <div className="flex items-center justify-center h-32">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary"></div>
            </div>
          ) : recentDocuments.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <FileText className="mx-auto h-12 w-12 mb-4 opacity-50" />
              <p>No documents yet</p>
              <Button variant="link" asChild className="mt-2">
                <Link to="/documents/upload">Upload your first document</Link>
              </Button>
            </div>
          ) : (
            <div className="space-y-4">
              {recentDocuments.map((doc) => (
                <Link
                  key={doc.id}
                  to={`/documents/${doc.id}`}
                  className="flex items-center justify-between p-3 rounded-lg border hover:bg-accent transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <FileText className="h-5 w-5 text-muted-foreground" />
                    <div>
                      <p className="font-medium">{doc.filename}</p>
                      <p className="text-sm text-muted-foreground">
                        {doc.document_type} • {formatRelativeTime(doc.created_at)}
                      </p>
                    </div>
                  </div>
                  <Badge className={getStatusColor(doc.status)}>
                    {getStatusLabel(doc.status)}
                  </Badge>
                </Link>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
