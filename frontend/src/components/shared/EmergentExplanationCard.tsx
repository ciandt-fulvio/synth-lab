// frontend/src/components/shared/EmergentExplanationCard.tsx
// Display emergent state explanation from mechanism×sensitivity interactions
// Reference: specs/038-mechanism-based-simulation/spec.md

import { Zap, TrendingUp, TrendingDown, Minus, ArrowRight } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import type { InteractionContribution, SegmentExplanation } from '@/types/simulation';

// =============================================================================
// Individual Interaction Contribution Display
// =============================================================================

interface InteractionItemProps {
  contribution: InteractionContribution;
  showDelta?: boolean;
  delta?: number;
}

/**
 * Displays a single mechanism × sensitivity interaction with visual indicator.
 */
function InteractionItem({ contribution, showDelta, delta }: InteractionItemProps) {
  const { mechanism, sensitivity, product } = contribution;
  const percentage = Math.round(product * 100);

  // Format mechanism/sensitivity names for display
  const formatName = (name: string) =>
    name.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');

  return (
    <div className="flex items-center gap-3 py-2 border-b border-slate-100 last:border-0">
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-1.5 text-sm font-medium text-slate-700">
          <span className="truncate">{formatName(mechanism)}</span>
          <span className="text-slate-400">×</span>
          <span className="truncate">{formatName(sensitivity)}</span>
        </div>
        <div className="mt-1.5">
          <Progress value={percentage} className="h-1.5" />
        </div>
      </div>
      <div className="flex items-center gap-2">
        <Badge variant="secondary" className="font-mono text-xs">
          {product.toFixed(2)}
        </Badge>
        {showDelta && delta !== undefined && (
          <div className={`flex items-center gap-0.5 text-xs ${
            delta > 0 ? 'text-red-600' : delta < 0 ? 'text-green-600' : 'text-slate-400'
          }`}>
            {delta > 0 ? (
              <TrendingUp className="h-3.5 w-3.5" />
            ) : delta < 0 ? (
              <TrendingDown className="h-3.5 w-3.5" />
            ) : (
              <Minus className="h-3.5 w-3.5" />
            )}
            <span>{delta > 0 ? '+' : ''}{(delta * 100).toFixed(0)}%</span>
          </div>
        )}
      </div>
    </div>
  );
}

// =============================================================================
// Emergent Explanation Card (for individual synth)
// =============================================================================

interface EmergentExplanationCardProps {
  topContributors: InteractionContribution[];
  perceivedRiskDelta?: number;
  initialEffortDelta?: number;
  className?: string;
}

/**
 * Card showing emergent state explanation for a single synth.
 * Displays top mechanism×sensitivity interactions that affect this synth's behavior.
 */
export function EmergentExplanationCard({
  topContributors,
  perceivedRiskDelta,
  initialEffortDelta,
  className = '',
}: EmergentExplanationCardProps) {
  if (!topContributors || topContributors.length === 0) {
    return null;
  }

  return (
    <Card className={`card ${className}`}>
      <CardHeader className="pb-2">
        <CardTitle className="text-card-title flex items-center gap-2">
          <Zap className="h-4 w-4 text-amber-500" />
          Fatores de Comportamento
        </CardTitle>
        <p className="text-meta">
          Interações mecanismo × sensibilidade que mais influenciam este synth
        </p>
      </CardHeader>
      <CardContent>
        {/* Delta summary if available */}
        {(perceivedRiskDelta !== undefined || initialEffortDelta !== undefined) && (
          <div className="flex gap-4 mb-4 p-3 bg-slate-50 rounded-lg">
            {perceivedRiskDelta !== undefined && (
              <div className="flex-1">
                <span className="text-xs text-slate-500">Risco Percebido</span>
                <div className={`text-sm font-medium ${
                  perceivedRiskDelta > 0 ? 'text-red-600' : 'text-green-600'
                }`}>
                  {perceivedRiskDelta > 0 ? '+' : ''}{(perceivedRiskDelta * 100).toFixed(0)}%
                </div>
              </div>
            )}
            {initialEffortDelta !== undefined && (
              <div className="flex-1">
                <span className="text-xs text-slate-500">Esforço Inicial</span>
                <div className={`text-sm font-medium ${
                  initialEffortDelta > 0 ? 'text-red-600' : 'text-green-600'
                }`}>
                  {initialEffortDelta > 0 ? '+' : ''}{(initialEffortDelta * 100).toFixed(0)}%
                </div>
              </div>
            )}
          </div>
        )}

        {/* Top contributors */}
        <div className="divide-y divide-slate-100">
          {topContributors.map((contrib, idx) => (
            <InteractionItem
              key={`${contrib.mechanism}-${contrib.sensitivity}-${idx}`}
              contribution={contrib}
            />
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

// =============================================================================
// Segment Explanation Card (for group comparison)
// =============================================================================

interface SegmentExplanationCardProps {
  explanation: SegmentExplanation;
  className?: string;
}

/**
 * Card showing why a segment of synths behaves differently from the population.
 * Displays success rate comparison and top differentiating factors.
 */
export function SegmentExplanationCard({
  explanation,
  className = '',
}: SegmentExplanationCardProps) {
  const {
    segment_size,
    segment_avg_success,
    population_avg_success,
    top_differentiating_factors,
    explanation_text,
  } = explanation;

  const successDiff = segment_avg_success - population_avg_success;
  const successDiffPct = (successDiff * 100).toFixed(1);

  return (
    <Card className={`card ${className}`}>
      <CardHeader className="pb-2">
        <CardTitle className="text-card-title flex items-center gap-2">
          <Zap className="h-4 w-4 text-amber-500" />
          Explicação do Segmento
        </CardTitle>
        <p className="text-meta">
          Por que este grupo de {segment_size} synths se comporta diferente
        </p>
      </CardHeader>
      <CardContent>
        {/* Success rate comparison */}
        <div className="flex items-center gap-4 mb-4 p-4 bg-slate-50 rounded-lg">
          <div className="flex-1 text-center">
            <span className="text-xs text-slate-500 block">Segmento</span>
            <span className="text-lg font-semibold text-slate-900">
              {(segment_avg_success * 100).toFixed(1)}%
            </span>
          </div>
          <ArrowRight className="h-4 w-4 text-slate-400" />
          <div className="flex-1 text-center">
            <span className="text-xs text-slate-500 block">População</span>
            <span className="text-lg font-semibold text-slate-500">
              {(population_avg_success * 100).toFixed(1)}%
            </span>
          </div>
          <div className="flex-1 text-center">
            <span className="text-xs text-slate-500 block">Diferença</span>
            <span className={`text-lg font-semibold ${
              successDiff > 0 ? 'text-green-600' : successDiff < 0 ? 'text-red-600' : 'text-slate-500'
            }`}>
              {successDiff > 0 ? '+' : ''}{successDiffPct}pp
            </span>
          </div>
        </div>

        {/* Top differentiating factors */}
        {top_differentiating_factors.length > 0 && (
          <div className="mb-4">
            <h4 className="text-sm font-medium text-slate-700 mb-2">
              Fatores Diferenciadores
            </h4>
            <div className="divide-y divide-slate-100">
              {top_differentiating_factors.map((factor, idx) => (
                <InteractionItem
                  key={`${factor.interaction.mechanism}-${factor.interaction.sensitivity}-${idx}`}
                  contribution={factor.interaction}
                  showDelta
                  delta={factor.delta}
                />
              ))}
            </div>
          </div>
        )}

        {/* Explanation text */}
        {explanation_text && (
          <div className="p-3 bg-amber-50 border border-amber-100 rounded-lg">
            <p className="text-sm text-amber-900 whitespace-pre-line">
              {explanation_text}
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export default EmergentExplanationCard;
