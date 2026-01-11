/**
 * Analytics dashboard page
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { BarChart3, TrendingUp, Zap, AlertTriangle } from 'lucide-react';

export default function Analytics() {
  // Placeholder data - would come from useAnalytics hook
  const metrics = {
    accuracy: 92.3,
    avgProcessingTime: 47,
    throughput: 178,
    accuracyTrend: '+1.2%',
    timeTrend: '-3s',
    throughputTrend: '+12%',
  };

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Analytics</h1>
        <p className="text-muted-foreground">
          Monitor system performance and accuracy trends
        </p>
      </div>

      {/* Key metrics */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Accuracy</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics.accuracy}%</div>
            <p className="text-xs text-green-600">{metrics.accuracyTrend} from last week</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Processing Time</CardTitle>
            <Zap className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics.avgProcessingTime}s</div>
            <p className="text-xs text-green-600">{metrics.timeTrend} from last week</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Daily Throughput</CardTitle>
            <BarChart3 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics.throughput}/day</div>
            <p className="text-xs text-green-600">{metrics.throughputTrend} from last week</p>
          </CardContent>
        </Card>
      </div>

      {/* Charts placeholder */}
      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Extraction Accuracy Over Time</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64 bg-muted rounded-lg flex items-center justify-center">
              <p className="text-muted-foreground">
                Accuracy trend chart would be displayed here
              </p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>OCR Engine Comparison</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-sm font-medium">Tesseract</span>
                  <span className="text-sm text-muted-foreground">91.2%</span>
                </div>
                <div className="h-2 bg-muted rounded-full overflow-hidden">
                  <div className="h-full bg-primary" style={{ width: '91.2%' }}></div>
                </div>
              </div>
              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-sm font-medium">PaddleOCR</span>
                  <span className="text-sm text-muted-foreground">93.1%</span>
                </div>
                <div className="h-2 bg-muted rounded-full overflow-hidden">
                  <div className="h-full bg-primary" style={{ width: '93.1%' }}></div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Document type distribution */}
      <Card>
        <CardHeader>
          <CardTitle>Document Type Distribution</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-3">
            <div className="text-center p-4 bg-muted rounded-lg">
              <div className="text-3xl font-bold text-primary">62%</div>
              <div className="text-sm text-muted-foreground">Invoices</div>
            </div>
            <div className="text-center p-4 bg-muted rounded-lg">
              <div className="text-3xl font-bold text-primary">24%</div>
              <div className="text-sm text-muted-foreground">Insurance Claims</div>
            </div>
            <div className="text-center p-4 bg-muted rounded-lg">
              <div className="text-3xl font-bold text-primary">14%</div>
              <div className="text-sm text-muted-foreground">Compliance Forms</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Drift alerts */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-orange-500" />
            Drift Alerts
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="flex items-start gap-3 p-3 bg-orange-50 dark:bg-orange-950/20 rounded-lg border border-orange-200 dark:border-orange-800">
              <AlertTriangle className="h-5 w-5 text-orange-500 mt-0.5" />
              <div>
                <p className="font-medium">Invoice accuracy dropped 3.2% over last 48 hours</p>
                <p className="text-sm text-muted-foreground">
                  Affected field: vendor_name • Possible template change detected
                </p>
              </div>
            </div>
            <p className="text-sm text-muted-foreground text-center py-4">
              No other alerts at this time
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
