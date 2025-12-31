/**
 * WinningPathPanel component.
 *
 * Displays the winning path from root to winner node.
 *
 * References:
 *   - Spec: specs/025-exploration-frontend/spec.md (US4)
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { formatSuccessRate, formatDelta, getCategoryDisplayName } from '@/lib/exploration-utils';
import type { WinningPath, PathStep } from '@/types/exploration';
import { Trophy, ArrowDown, TrendingUp } from 'lucide-react';

interface WinningPathPanelProps {
  path: WinningPath;
  onStepClick?: (depth: number) => void;
  className?: string;
}

export function WinningPathPanel({
  path,
  onStepClick,
  className = '',
}: WinningPathPanelProps) {
  return (
    <Card className={className}>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-lg">
          <Trophy className="h-5 w-5 text-amber-500" />
          Caminho Vencedor
        </CardTitle>
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <TrendingUp className="h-4 w-4 text-green-600" />
          Melhoria total: {formatDelta(path.total_improvement)}
        </div>
      </CardHeader>
      <CardContent className="space-y-0">
        {path.path.map((step, index) => (
          <PathStepCard
            key={index}
            step={step}
            isFirst={index === 0}
            isLast={index === path.path.length - 1}
            onClick={() => onStepClick?.(step.depth)}
          />
        ))}
      </CardContent>
    </Card>
  );
}

interface PathStepCardProps {
  step: PathStep;
  isFirst: boolean;
  isLast: boolean;
  onClick?: () => void;
}

function PathStepCard({ step, isFirst, isLast, onClick }: PathStepCardProps) {
  return (
    <div className="relative">
      {/* Connector line */}
      {!isFirst && (
        <div className="absolute left-4 -top-3 h-3 w-0.5 bg-amber-300" />
      )}

      {/* Step content */}
      <div
        className={`
          relative flex gap-3 p-3 rounded-lg border cursor-pointer
          transition-colors hover:bg-muted/50
          ${isLast ? 'border-green-200 bg-green-50' : 'border-slate-200'}
        `}
        onClick={onClick}
      >
        {/* Step indicator */}
        <div
          className={`
            flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium
            ${isLast ? 'bg-green-500 text-white' : 'bg-amber-100 text-amber-700'}
          `}
        >
          {isFirst ? '0' : step.depth}
        </div>

        {/* Step details */}
        <div className="flex-1 min-w-0">
          {isFirst ? (
            <div>
              <p className="font-medium text-sm">Cenário Inicial (Baseline)</p>
              <p className="text-sm text-muted-foreground mt-1">
                Taxa de sucesso: {formatSuccessRate(step.success_rate)}
              </p>
            </div>
          ) : (
            <div>
              <p className="font-medium text-sm line-clamp-2">{step.action}</p>
              {step.category && (
                <Badge variant="secondary" className="mt-1 text-xs">
                  {getCategoryDisplayName(step.category)}
                </Badge>
              )}
              <div className="flex items-center gap-3 mt-2 text-sm">
                <span className="text-muted-foreground">
                  {formatSuccessRate(step.success_rate)}
                </span>
                <span
                  className={`flex items-center gap-1 ${
                    step.delta_success_rate >= 0 ? 'text-green-600' : 'text-red-600'
                  }`}
                >
                  <TrendingUp className="h-3 w-3" />
                  {formatDelta(step.delta_success_rate)}
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Winner badge */}
        {isLast && (
          <Trophy className="h-5 w-5 text-green-600 flex-shrink-0" />
        )}
      </div>

      {/* Connector line to next */}
      {!isLast && (
        <div className="flex justify-center py-1">
          <ArrowDown className="h-4 w-4 text-amber-400" />
        </div>
      )}
    </div>
  );
}
