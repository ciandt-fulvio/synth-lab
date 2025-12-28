// frontend/src/components/shared/ChartContainer.tsx
// Wrapper component for charts with loading, error, and empty states

import { AlertCircle, RefreshCw, BarChart3 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { ChartErrorBoundary } from '@/components/shared/ErrorBoundary';

interface ChartContainerProps {
  title: string;
  description?: string;
  isLoading: boolean;
  isError: boolean;
  isEmpty: boolean;
  onRetry?: () => void;
  emptyMessage?: string;
  errorMessage?: string;
  children: React.ReactNode;
  className?: string;
  height?: number;
}

export function ChartContainer({
  title,
  description,
  isLoading,
  isError,
  isEmpty,
  onRetry,
  emptyMessage = 'Nenhum dado disponível para este gráfico.',
  errorMessage = 'Erro ao carregar os dados. Tente novamente.',
  children,
  className = '',
  height = 300,
}: ChartContainerProps) {
  return (
    <Card className={`card ${className}`}>
      <CardHeader className="pb-2">
        <CardTitle className="text-card-title flex items-center gap-2">
          <BarChart3 className="h-4 w-4 text-slate-500" />
          {title}
        </CardTitle>
        {description && (
          <p className="text-meta">{description}</p>
        )}
      </CardHeader>
      <CardContent>
        {isLoading && (
          <div className="flex flex-col items-center justify-center gap-4" style={{ height }}>
            <Skeleton className="w-full h-full rounded-lg" />
          </div>
        )}

        {isError && !isLoading && (
          <div
            className="flex flex-col items-center justify-center gap-4 text-center"
            style={{ height }}
          >
            <div className="icon-box-neutral">
              <AlertCircle className="h-6 w-6 text-red-500" />
            </div>
            <div>
              <p className="text-body text-red-600 font-medium mb-1">Erro</p>
              <p className="text-meta">{errorMessage}</p>
            </div>
            {onRetry && (
              <Button
                variant="outline"
                size="sm"
                onClick={onRetry}
                className="btn-secondary"
              >
                <RefreshCw className="h-4 w-4 mr-2" />
                Tentar Novamente
              </Button>
            )}
          </div>
        )}

        {isEmpty && !isLoading && !isError && (
          <div
            className="flex flex-col items-center justify-center gap-4 text-center"
            style={{ height }}
          >
            <div className="icon-box-neutral">
              <BarChart3 className="h-6 w-6 text-slate-400" />
            </div>
            <div>
              <p className="text-body text-slate-500 font-medium mb-1">Sem Dados</p>
              <p className="text-meta">{emptyMessage}</p>
            </div>
          </div>
        )}

        {!isLoading && !isError && !isEmpty && (
          <div style={{ minHeight: height }}>
            <ChartErrorBoundary chartName={title}>
              {children}
            </ChartErrorBoundary>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// Compact version for smaller charts in grids
interface ChartContainerCompactProps {
  title: string;
  isLoading: boolean;
  isError: boolean;
  isEmpty: boolean;
  onRetry?: () => void;
  children: React.ReactNode;
  className?: string;
}

export function ChartContainerCompact({
  title,
  isLoading,
  isError,
  isEmpty,
  onRetry,
  children,
  className = '',
}: ChartContainerCompactProps) {
  return (
    <div className={`bg-white rounded-lg border border-slate-200 p-4 ${className}`}>
      <h4 className="text-sm font-medium text-slate-700 mb-3">{title}</h4>

      {isLoading && (
        <div className="flex items-center justify-center h-48">
          <Skeleton className="w-full h-full rounded" />
        </div>
      )}

      {isError && !isLoading && (
        <div className="flex flex-col items-center justify-center h-48 gap-2">
          <AlertCircle className="h-5 w-5 text-red-500" />
          <p className="text-xs text-red-600">Erro ao carregar</p>
          {onRetry && (
            <Button variant="ghost" size="sm" onClick={onRetry} className="text-xs">
              <RefreshCw className="h-3 w-3 mr-1" />
              Retry
            </Button>
          )}
        </div>
      )}

      {isEmpty && !isLoading && !isError && (
        <div className="flex flex-col items-center justify-center h-48 gap-2">
          <BarChart3 className="h-5 w-5 text-slate-300" />
          <p className="text-xs text-slate-400">Sem dados</p>
        </div>
      )}

      {!isLoading && !isError && !isEmpty && (
        <ChartErrorBoundary chartName={title}>
          {children}
        </ChartErrorBoundary>
      )}
    </div>
  );
}
