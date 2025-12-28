// frontend/src/components/shared/ErrorBoundary.tsx
// Error boundary component to catch and handle React errors gracefully

import { Component, type ReactNode } from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

/**
 * Error Boundary component that catches JavaScript errors in child components.
 * Prevents the entire app from crashing when a component fails.
 */
export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    this.props.onError?.(error, errorInfo);
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="flex flex-col items-center justify-center p-8 text-center">
          <AlertTriangle className="h-12 w-12 text-amber-500 mb-4" />
          <h3 className="text-lg font-semibold text-slate-800 mb-2">
            Algo deu errado
          </h3>
          <p className="text-sm text-slate-500 mb-4 max-w-md">
            Ocorreu um erro inesperado. Tente novamente ou recarregue a página.
          </p>
          <Button
            variant="outline"
            onClick={this.handleRetry}
            className="gap-2"
          >
            <RefreshCw className="h-4 w-4" />
            Tentar novamente
          </Button>
        </div>
      );
    }

    return this.props.children;
  }
}

interface ChartErrorBoundaryProps {
  children: ReactNode;
  chartName?: string;
}

/**
 * Specialized error boundary for chart components.
 * Shows a compact error state that fits within chart containers.
 */
export function ChartErrorBoundary({ children, chartName }: ChartErrorBoundaryProps) {
  return (
    <ErrorBoundary
      fallback={
        <div className="flex flex-col items-center justify-center h-full min-h-[200px] p-4 text-center bg-slate-50 rounded-lg border border-slate-200">
          <AlertTriangle className="h-8 w-8 text-amber-500 mb-2" />
          <p className="text-sm font-medium text-slate-700">
            Erro ao carregar {chartName || 'gráfico'}
          </p>
          <p className="text-xs text-slate-500 mt-1">
            Tente recarregar a página
          </p>
        </div>
      }
    >
      {children}
    </ErrorBoundary>
  );
}
