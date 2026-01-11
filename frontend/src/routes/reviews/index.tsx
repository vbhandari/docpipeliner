/**
 * Review queue page
 */

import { useState } from 'react';
import { Link } from 'react-router-dom';
import { ClipboardCheck, AlertCircle, Clock, CheckCircle } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useReviews, useReviewStats } from '@/hooks/useReviews';
import { getPriorityColor, getPriorityLabel } from '@/types/review';
import { formatConfidence } from '@/types/extraction';
import { formatRelativeTime } from '@/lib/utils';

export default function ReviewQueue() {
  const [priorityFilter, setPriorityFilter] = useState<string>('');
  const { data: reviewsData, isLoading } = useReviews({
    status: 'pending',
    priority: priorityFilter || undefined,
    sort_by: 'priority',
    sort_order: 'desc',
  });
  const { data: stats } = useReviewStats();

  const reviews = reviewsData?.items ?? [];

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Review Queue</h1>
        <p className="text-muted-foreground">
          Documents requiring human review
        </p>
      </div>

      {/* Stats */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.pending ?? 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">In Progress</CardTitle>
            <ClipboardCheck className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.in_progress ?? 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Completed Today</CardTitle>
            <CheckCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.completed_today ?? 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Review Time</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {stats?.avg_review_time_seconds
                ? `${Math.round(stats.avg_review_time_seconds / 60)}m`
                : '--'}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-4">
            <span className="text-sm font-medium">Filter by priority:</span>
            <div className="flex gap-2">
              {['', 'urgent', 'high', 'normal', 'low'].map((priority) => (
                <Button
                  key={priority}
                  variant={priorityFilter === priority ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setPriorityFilter(priority)}
                >
                  {priority === '' ? 'All' : getPriorityLabel(priority as any)}
                </Button>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Review list */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertCircle className="h-5 w-5" />
            {reviews.length} Reviews Pending
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex items-center justify-center h-32">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary"></div>
            </div>
          ) : reviews.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              <CheckCircle className="mx-auto h-12 w-12 mb-4 opacity-50" />
              <p>No reviews pending</p>
              <p className="text-sm mt-1">All documents have been reviewed!</p>
            </div>
          ) : (
            <div className="space-y-4">
              {reviews.map((review) => (
                <Link
                  key={review.id}
                  to={`/reviews/${review.id}`}
                  className="block p-4 border rounded-lg hover:bg-accent transition-colors"
                >
                  <div className="flex items-start justify-between">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <Badge className={getPriorityColor(review.priority)}>
                          {getPriorityLabel(review.priority)}
                        </Badge>
                        <span className="font-medium">
                          {review.document.filename}
                        </span>
                      </div>
                      <p className="text-sm text-muted-foreground">
                        {review.document.document_type} •{' '}
                        Confidence: {formatConfidence(review.extraction_result.overall_confidence)} •{' '}
                        {review.flagged_fields.length} fields flagged
                      </p>
                      <p className="text-xs text-muted-foreground">
                        Uploaded {formatRelativeTime(review.created_at)}
                      </p>
                    </div>
                    <Button variant="outline" size="sm">
                      Review →
                    </Button>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
