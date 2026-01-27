/**
 * FailureModeCard component for displaying failure mode patterns.
 *
 * Shows failure mode conditions, frequency, and severity.
 *
 * References:
 *   - Types: types/simulation-insight.ts
 */

import { AlertTriangle, AlertCircle, Info } from 'lucide-react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import type { FailureMode, SeverityLevel } from '@/types/simulation-insight';

interface FailureModeCardProps {
  /**
   * Failure mode data.
   */
  failureMode: FailureMode;

  /**
   * Optional click handler for drill-down.
   */
  onClick?: () => void;
}

const SEVERITY_STYLES: Record<SeverityLevel, { bg: string; border: string; icon: typeof AlertCircle }> = {
  low: { bg: 'bg-blue-50', border: 'border-blue-200', icon: Info },
  medium: { bg: 'bg-amber-50', border: 'border-amber-200', icon: AlertCircle },
  high: { bg: 'bg-orange-50', border: 'border-orange-200', icon: AlertTriangle },
  critical: { bg: 'bg-red-50', border: 'border-red-200', icon: AlertTriangle },
};

const SEVERITY_LABELS: Record<SeverityLevel, { text: string; color: string }> = {
  low: { text: 'Low', color: 'text-blue-700' },
  medium: { text: 'Medium', color: 'text-amber-700' },
  high: { text: 'High', color: 'text-orange-700' },
  critical: { text: 'Critical', color: 'text-red-700' },
};

/**
 * Format condition for display.
 */
function formatCondition(operator: string, value: number): string {
  const opMap: Record<string, string> = {
    '<': '<',
    '<=': '≤',
    '>': '>',
    '>=': '≥',
    '==': '=',
  };
  return `${opMap[operator] || operator} ${value.toFixed(2)}`;
}

/**
 * FailureModeCard component.
 *
 * @example
 * <FailureModeCard
 *   failureMode={failureMode}
 *   onClick={() => console.log('clicked')}
 * />
 */
export function FailureModeCard({ failureMode, onClick }: FailureModeCardProps) {
  const severity = failureMode.severity as SeverityLevel;
  const styles = SEVERITY_STYLES[severity] || SEVERITY_STYLES.medium;
  const label = SEVERITY_LABELS[severity] || SEVERITY_LABELS.medium;
  const Icon = styles.icon;

  return (
    <Card
      className={`${styles.bg} ${styles.border} ${onClick ? 'cursor-pointer hover:shadow-md transition-shadow' : ''}`}
      onClick={onClick}
    >
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2">
            <Icon className={`h-5 w-5 ${label.color}`} />
            <CardTitle className="text-base">{failureMode.description}</CardTitle>
          </div>
          <span className={`text-xs font-medium ${label.color}`}>
            {label.text}
          </span>
        </div>
        <CardDescription className="text-slate-600">
          Occurs in {(failureMode.frequency * 100).toFixed(1)}% of scenarios
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {/* Pattern conditions */}
          <div className="text-sm">
            <span className="font-medium text-slate-700">When:</span>
            <ul className="mt-1 space-y-1">
              {Object.entries(failureMode.pattern).map(([varName, condition]) => (
                <li key={varName} className="flex items-center gap-2">
                  <span className="text-slate-600">{varName}</span>
                  <span className="font-mono text-slate-800">
                    {formatCondition(condition.operator, condition.value)}
                  </span>
                </li>
              ))}
            </ul>
          </div>

          {/* Outcome threshold */}
          <div className="text-sm">
            <span className="font-medium text-slate-700">Then:</span>
            <ul className="mt-1 space-y-1">
              {Object.entries(failureMode.outcome_threshold).map(([outName, threshold]) => (
                <li key={outName} className="flex items-center gap-2">
                  <span className="text-slate-600">{outName}</span>
                  <span className="font-mono text-slate-800">
                    {formatCondition(threshold.operator, threshold.value)}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
