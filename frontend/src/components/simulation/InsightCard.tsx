/**
 * InsightCard component for displaying simulation insights.
 *
 * Collapsible card with insight details and trace link.
 *
 * References:
 *   - Types: types/simulation-insight.ts
 */

import { useState } from 'react';
import {
  ChevronDown,
  ChevronRight,
  Lightbulb,
  AlertTriangle,
  Users,
  Target,
  ExternalLink,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import type { SimulationInsight } from '@/types/simulation-insight';

interface InsightCardProps {
  /**
   * Insight data.
   */
  insight: SimulationInsight;

  /**
   * Optional callback when trace link is clicked.
   */
  onTraceClick?: () => void;

  /**
   * Whether the card starts expanded.
   */
  defaultExpanded?: boolean;
}

const INSIGHT_ICONS: Record<SimulationInsight['insight_type'], typeof Lightbulb> = {
  key_driver: Target,
  failure_mode: AlertTriangle,
  cluster_finding: Users,
  recommendation: Lightbulb,
};

const INSIGHT_STYLES: Record<SimulationInsight['insight_type'], { bg: string; border: string; iconColor: string }> = {
  key_driver: { bg: 'bg-blue-50', border: 'border-blue-200', iconColor: 'text-blue-600' },
  failure_mode: { bg: 'bg-red-50', border: 'border-red-200', iconColor: 'text-red-600' },
  cluster_finding: { bg: 'bg-slate-50', border: 'border-slate-200', iconColor: 'text-slate-600' },
  recommendation: { bg: 'bg-green-50', border: 'border-green-200', iconColor: 'text-green-600' },
};

const INSIGHT_LABELS: Record<SimulationInsight['insight_type'], string> = {
  key_driver: 'Key Driver',
  failure_mode: 'Failure Mode',
  cluster_finding: 'Cluster Finding',
  recommendation: 'Recommendation',
};

/**
 * InsightCard component.
 *
 * @example
 * <InsightCard
 *   insight={insight}
 *   onTraceClick={() => console.log('trace')}
 * />
 */
export function InsightCard({
  insight,
  onTraceClick,
  defaultExpanded = false,
}: InsightCardProps) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);

  const Icon = INSIGHT_ICONS[insight.insight_type] || Lightbulb;
  const styles = INSIGHT_STYLES[insight.insight_type] || INSIGHT_STYLES.recommendation;
  const label = INSIGHT_LABELS[insight.insight_type] || 'Insight';

  return (
    <Card className={`${styles.bg} ${styles.border}`}>
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between">
          <div className="flex items-start gap-3">
            <Button
              variant="ghost"
              size="sm"
              className="h-6 w-6 p-0"
              onClick={() => setIsExpanded(!isExpanded)}
            >
              {isExpanded ? (
                <ChevronDown className="h-4 w-4" />
              ) : (
                <ChevronRight className="h-4 w-4" />
              )}
            </Button>
            <div>
              <div className="flex items-center gap-2">
                <Icon className={`h-5 w-5 ${styles.iconColor}`} />
                <CardTitle className="text-base">{insight.title}</CardTitle>
              </div>
              <CardDescription className="mt-1">
                <span
                  className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${styles.iconColor} bg-white/50`}
                >
                  {label}
                </span>
                {insight.confidence !== undefined && insight.confidence > 0 && (
                  <span className="ml-2 text-slate-500">
                    {(insight.confidence * 100).toFixed(0)}% confidence
                  </span>
                )}
              </CardDescription>
            </div>
          </div>
          {onTraceClick && (
            <Button
              variant="ghost"
              size="sm"
              onClick={onTraceClick}
              className="text-slate-500 hover:text-slate-700"
            >
              <ExternalLink className="h-4 w-4 mr-1" />
              Trace
            </Button>
          )}
        </div>
      </CardHeader>

      {isExpanded && (
        <CardContent className="pt-2">
          <div className="space-y-4">
            {/* Description */}
            <p className="text-sm text-slate-700 whitespace-pre-wrap">
              {insight.description}
            </p>

            {/* Recommended Actions */}
            {insight.recommended_actions && insight.recommended_actions.length > 0 && (
              <div>
                <h4 className="text-sm font-medium text-slate-900 mb-2">
                  Recommended Actions
                </h4>
                <ul className="space-y-2">
                  {insight.recommended_actions.map((action, index) => (
                    <li
                      key={index}
                      className="flex items-start gap-2 p-2 rounded bg-white/50"
                    >
                      <div className="flex-1">
                        <p className="text-sm text-slate-800">{action.action}</p>
                        <div className="flex items-center gap-3 mt-1 text-xs text-slate-500">
                          {action.priority && (
                            <span>Priority: {action.priority}</span>
                          )}
                          {action.impact && (
                            <span>Impact: {action.impact}</span>
                          )}
                        </div>
                      </div>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Evidence References */}
            {Object.keys(insight.evidence_references).length > 0 && (
              <div className="text-xs text-slate-500">
                <span className="font-medium">Evidence:</span>{' '}
                {Object.keys(insight.evidence_references).join(', ')}
              </div>
            )}
          </div>
        </CardContent>
      )}
    </Card>
  );
}
