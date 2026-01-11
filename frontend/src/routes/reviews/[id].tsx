/**
 * Review detail/interface page
 */

import { useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { ArrowLeft, Check, X, SkipForward } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  useReview,
  useSubmitCorrections,
  useApproveReview,
  useRejectReview,
  useSkipReview,
} from '@/hooks/useReviews';
import { getPriorityColor, getPriorityLabel, FieldCorrection } from '@/types/review';
import { formatConfidence, getConfidenceColor } from '@/types/extraction';

export default function ReviewDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: review, isLoading } = useReview(id!);
  const submitCorrections = useSubmitCorrections();
  const approveReview = useApproveReview();
  const rejectReview = useRejectReview();
  const skipReview = useSkipReview();

  const [corrections, setCorrections] = useState<Record<string, string>>({});
  const [notes, setNotes] = useState('');

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (!review) {
    return (
      <div className="text-center py-12">
        <p className="text-muted-foreground">Review not found</p>
        <Button variant="link" asChild>
          <Link to="/reviews">Back to reviews</Link>
        </Button>
      </div>
    );
  }

  const handleFieldChange = (fieldName: string, value: string) => {
    setCorrections((prev) => ({ ...prev, [fieldName]: value }));
  };

  const handleApprove = async () => {
    const fieldCorrections: FieldCorrection[] = Object.entries(corrections)
      .filter(([fieldName, value]) => {
        const original = review.extraction_result.fields.find(
          (f) => f.field_name === fieldName
        );
        return original && original.field_value !== value;
      })
      .map(([fieldName, correctedValue]) => {
        const original = review.extraction_result.fields.find(
          (f) => f.field_name === fieldName
        );
        return {
          field_name: fieldName,
          original_value: original?.field_value ?? '',
          corrected_value: correctedValue,
        };
      });

    if (fieldCorrections.length > 0) {
      await submitCorrections.mutateAsync({
        id: review.id,
        submission: {
          corrections: fieldCorrections,
          notes,
          action: 'approve',
        },
      });
    } else {
      await approveReview.mutateAsync({ id: review.id, notes });
    }

    navigate('/reviews');
  };

  const handleReject = async () => {
    const reason = prompt('Please provide a reason for rejection:');
    if (reason) {
      await rejectReview.mutateAsync({ id: review.id, reason });
      navigate('/reviews');
    }
  };

  const handleSkip = async () => {
    await skipReview.mutateAsync(review.id);
    navigate('/reviews');
  };

  const isPending =
    submitCorrections.isPending ||
    approveReview.isPending ||
    rejectReview.isPending ||
    skipReview.isPending;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" asChild>
            <Link to="/reviews">
              <ArrowLeft className="h-5 w-5" />
            </Link>
          </Button>
          <div>
            <h1 className="text-2xl font-bold">{review.document.filename}</h1>
            <div className="flex items-center gap-2 mt-1">
              <Badge className={getPriorityColor(review.priority)}>
                {getPriorityLabel(review.priority)}
              </Badge>
              <span className="text-muted-foreground">
                {review.flagged_fields.length} fields need review
              </span>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" onClick={handleSkip} disabled={isPending}>
            <SkipForward className="mr-2 h-4 w-4" />
            Skip
          </Button>
          <Button variant="destructive" onClick={handleReject} disabled={isPending}>
            <X className="mr-2 h-4 w-4" />
            Reject
          </Button>
          <Button onClick={handleApprove} disabled={isPending}>
            <Check className="mr-2 h-4 w-4" />
            Approve
          </Button>
        </div>
      </div>

      {/* Main content */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Document preview placeholder */}
        <Card>
          <CardHeader>
            <CardTitle>Document Preview</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="aspect-[3/4] bg-muted rounded-lg flex items-center justify-center">
              <p className="text-muted-foreground">
                PDF preview would be displayed here
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Field corrections */}
        <Card>
          <CardHeader>
            <CardTitle>
              Field Corrections
              <span className="ml-2 text-sm font-normal text-muted-foreground">
                Overall confidence:{' '}
                <span className={getConfidenceColor(review.extraction_result.overall_confidence)}>
                  {formatConfidence(review.extraction_result.overall_confidence)}
                </span>
              </span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {review.extraction_result.fields.map((field) => {
                const isFlagged = review.flagged_fields.includes(field.field_name);
                const currentValue = corrections[field.field_name] ?? field.field_value;

                return (
                  <div
                    key={field.field_name}
                    className={`p-4 rounded-lg border ${
                      isFlagged ? 'border-orange-300 bg-orange-50 dark:bg-orange-950/20' : ''
                    }`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <label className="font-medium">
                        {field.field_name}
                        {isFlagged && (
                          <Badge variant="warning" className="ml-2">
                            Flagged
                          </Badge>
                        )}
                      </label>
                      <span className={getConfidenceColor(field.confidence)}>
                        {formatConfidence(field.confidence)}
                      </span>
                    </div>
                    <input
                      type="text"
                      value={currentValue}
                      onChange={(e) => handleFieldChange(field.field_name, e.target.value)}
                      className="w-full px-3 py-2 border rounded-md bg-background"
                    />
                    {corrections[field.field_name] &&
                      corrections[field.field_name] !== field.field_value && (
                        <p className="text-xs text-muted-foreground mt-1">
                          Original: {field.field_value}
                        </p>
                      )}
                  </div>
                );
              })}
            </div>

            {/* Notes */}
            <div className="mt-6">
              <label className="block font-medium mb-2">Review Notes (optional)</label>
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Add any notes about this review..."
                className="w-full px-3 py-2 border rounded-md bg-background min-h-[100px]"
              />
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
