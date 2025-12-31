/**
 * NodeDetailsPanel component.
 *
 * Side panel (Sheet) showing details of a selected scenario node.
 * Refined layout with visual hierarchy and comfortable spacing.
 *
 * References:
 *   - Spec: specs/025-exploration-frontend/spec.md (US3)
 */

import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet';
import { Badge } from '@/components/ui/badge';
import {
  formatSuccessRate,
  formatDelta,
  formatDuration,
  getCategoryDisplayName,
} from '@/lib/exploration-utils';
import type { ScenarioNode } from '@/types/exploration';
import { NODE_STATUS_BADGES } from '@/types/exploration';
import {
  Clock,
  Layers,
  Lightbulb,
  Sparkles,
  TrendingUp,
  TrendingDown,
  Target,
  Gauge,
} from 'lucide-react';

interface NodeDetailsPanelProps {
  /** The selected node to display */
  node: ScenarioNode | null;
  /** Whether the panel is open */
  open: boolean;
  /** Callback when panel is closed */
  onOpenChange: (open: boolean) => void;
  /** Parent node for delta calculation */
  parentNode?: ScenarioNode | null;
}

export function NodeDetailsPanel({
  node,
  open,
  onOpenChange,
  parentNode,
}: NodeDetailsPanelProps) {
  if (!node) return null;

  const isRoot = node.parent_id === null;
  const statusConfig = NODE_STATUS_BADGES[node.node_status];

  // Calculate delta from parent
  const successRateDelta =
    parentNode?.simulation_results && node.simulation_results
      ? node.simulation_results.success_rate -
        parentNode.simulation_results.success_rate
      : null;

  const getStatusStyles = (variant: string) => {
    switch (variant) {
      case 'success':
        return 'bg-emerald-50 text-emerald-700 border-emerald-200';
      case 'error':
        return 'bg-rose-50 text-rose-700 border-rose-200';
      case 'info':
        return 'bg-sky-50 text-sky-700 border-sky-200';
      default:
        return 'bg-slate-100 text-slate-600 border-slate-200';
    }
  };

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="sm:max-w-[420px] flex flex-col p-0 gap-0 border-l border-slate-200/80">
        {/* Header with gradient accent */}
        <div className="relative px-6 pt-6 pb-4 bg-gradient-to-b from-slate-50 to-white border-b border-slate-100">
          <SheetHeader className="space-y-1">
            <div className="flex items-center justify-between">
              <SheetTitle className="flex items-center gap-2.5 text-lg font-semibold text-slate-800">
                <div className="p-1.5 rounded-lg bg-indigo-100">
                  <Layers className="h-4 w-4 text-indigo-600" />
                </div>
                {isRoot ? 'Baseline' : 'Detalhes do Cenário'}
              </SheetTitle>
            </div>
            <p className="text-sm text-slate-500">
              Profundidade {node.depth} na árvore
            </p>
          </SheetHeader>

          {/* Status row */}
          <div className="flex items-center gap-3 mt-4">
            <Badge
              variant="outline"
              className={`px-2.5 py-1 text-xs font-medium border ${getStatusStyles(statusConfig.variant)}`}
            >
              {statusConfig.label}
            </Badge>
            {node.execution_time_seconds && (
              <span className="text-xs text-slate-400 flex items-center gap-1.5">
                <Clock className="h-3.5 w-3.5" />
                {formatDuration(node.execution_time_seconds)}
              </span>
            )}
          </div>
        </div>

        {/* Main content */}
        <div className="flex-1 px-6 py-5 space-y-5 overflow-y-auto">
          {/* Action Applied */}
          {node.action_applied && (
            <section className="space-y-2.5">
              <div className="flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-indigo-500" />
                <h3 className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                  Ação Aplicada
                </h3>
                {node.action_category && (
                  <span className="ml-auto text-[11px] text-slate-400 bg-slate-100 px-2 py-0.5 rounded-full">
                    {getCategoryDisplayName(node.action_category)}
                  </span>
                )}
              </div>
              <div className="relative">
                <div className="absolute left-0 top-0 bottom-0 w-1 rounded-full bg-gradient-to-b from-indigo-400 to-violet-400" />
                <p className="text-sm text-slate-700 leading-relaxed pl-4 py-1">
                  {node.action_applied}
                </p>
              </div>
            </section>
          )}

          {/* Rationale */}
          {node.rationale && (
            <section className="space-y-2.5">
              <div className="flex items-center gap-2">
                <Lightbulb className="h-4 w-4 text-amber-500" />
                <h3 className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                  Justificativa
                </h3>
              </div>
              <p className="text-[13px] text-slate-500 leading-relaxed bg-amber-50/50 border border-amber-100 rounded-lg p-3">
                {node.rationale}
              </p>
            </section>
          )}

          {/* Simulation Results - Hero Section */}
          {node.simulation_results && (
            <section className="space-y-3 pt-2">
              <div className="flex items-center gap-2">
                <Target className="h-4 w-4 text-emerald-500" />
                <h3 className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                  Resultados da Simulação
                </h3>
              </div>

              {/* Success Rate - Hero metric */}
              <div className="bg-gradient-to-br from-slate-50 to-slate-100/50 border border-slate-200/80 rounded-xl p-4">
                <div className="flex items-end justify-between mb-3">
                  <div>
                    <p className="text-xs text-slate-400 mb-1">Taxa de Sucesso</p>
                    <div className="flex items-baseline gap-2">
                      <span className="text-3xl font-bold text-slate-800 tabular-nums">
                        {formatSuccessRate(node.simulation_results.success_rate)}
                      </span>
                      {successRateDelta !== null && (
                        <DeltaIndicator delta={successRateDelta} size="normal" />
                      )}
                    </div>
                  </div>
                  <div className="text-right space-y-1">
                    <MetricPill
                      label="Falha"
                      value={formatSuccessRate(node.simulation_results.fail_rate)}
                      color="rose"
                    />
                    <MetricPill
                      label="Não tentou"
                      value={formatSuccessRate(node.simulation_results.did_not_try_rate)}
                      color="slate"
                    />
                  </div>
                </div>

                {/* Progress visualization */}
                <div className="h-2 w-full bg-slate-200 rounded-full overflow-hidden flex">
                  <div
                    className="h-full bg-gradient-to-r from-emerald-400 to-emerald-500 transition-all duration-500"
                    style={{ width: `${node.simulation_results.success_rate * 100}%` }}
                  />
                  <div
                    className="h-full bg-rose-400 transition-all duration-500"
                    style={{ width: `${node.simulation_results.fail_rate * 100}%` }}
                  />
                  <div
                    className="h-full bg-slate-300 transition-all duration-500"
                    style={{ width: `${node.simulation_results.did_not_try_rate * 100}%` }}
                  />
                </div>
              </div>
            </section>
          )}

          {/* Scorecard Parameters */}
          <section className="space-y-3 pt-2">
            <div className="flex items-center gap-2">
              <Gauge className="h-4 w-4 text-violet-500" />
              <h3 className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                Parâmetros do Scorecard
              </h3>
            </div>

            <div className="grid grid-cols-2 gap-2.5">
              <ScoreItem
                label="Complexidade"
                value={node.scorecard_params.complexity}
                parentValue={parentNode?.scorecard_params.complexity}
              />
              <ScoreItem
                label="Esforço Inicial"
                value={node.scorecard_params.initial_effort}
                parentValue={parentNode?.scorecard_params.initial_effort}
              />
              <ScoreItem
                label="Risco Percebido"
                value={node.scorecard_params.perceived_risk}
                parentValue={parentNode?.scorecard_params.perceived_risk}
              />
              <ScoreItem
                label="Tempo p/ Valor"
                value={node.scorecard_params.time_to_value}
                parentValue={parentNode?.scorecard_params.time_to_value}
              />
            </div>
          </section>
        </div>

        {/* Footer */}
        <div className="px-6 py-3 border-t border-slate-100 bg-slate-50/50 flex items-center justify-between">
          <span className="text-[11px] text-slate-400 font-mono">
            {node.id.slice(0, 12)}...
          </span>
          <span className="text-[11px] text-slate-400">
            {new Date(node.created_at).toLocaleString('pt-BR', {
              day: '2-digit',
              month: '2-digit',
              year: '2-digit',
              hour: '2-digit',
              minute: '2-digit',
            })}
          </span>
        </div>
      </SheetContent>
    </Sheet>
  );
}

// Small metric pill for fail/did-not-try rates
function MetricPill({
  label,
  value,
  color,
}: {
  label: string;
  value: string;
  color: 'rose' | 'slate';
}) {
  const colorClasses = {
    rose: 'bg-rose-50 text-rose-600 border-rose-100',
    slate: 'bg-slate-100 text-slate-500 border-slate-200',
  };

  return (
    <div
      className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-[11px] border ${colorClasses[color]}`}
    >
      <span className="text-slate-400">{label}</span>
      <span className="font-semibold tabular-nums">{value}</span>
    </div>
  );
}

// Delta indicator component
function DeltaIndicator({
  delta,
  size = 'small',
}: {
  delta: number;
  size?: 'small' | 'normal';
}) {
  const isPositive = delta >= 0;
  const sizeClasses = size === 'normal' ? 'text-sm' : 'text-[10px]';
  const iconSize = size === 'normal' ? 'h-4 w-4' : 'h-3 w-3';

  return (
    <span
      className={`${sizeClasses} flex items-center gap-0.5 font-semibold ${
        isPositive ? 'text-emerald-600' : 'text-rose-600'
      }`}
    >
      {isPositive ? (
        <TrendingUp className={iconSize} />
      ) : (
        <TrendingDown className={iconSize} />
      )}
      {formatDelta(delta)}
    </span>
  );
}

// Helper component for scorecard parameter display with delta
function ScoreItem({
  label,
  value,
  parentValue,
}: {
  label: string;
  value: number;
  parentValue?: number;
}) {
  const delta = parentValue !== undefined ? value - parentValue : null;
  const hasDelta = delta !== null && Math.abs(delta) > 0.001;

  // For scorecard params, lower is generally better
  // negative delta = green (improved), positive = red (worse)
  const isImprovement = delta !== null && delta < 0;
  const isWorse = delta !== null && delta > 0;

  return (
    <div className="bg-white border border-slate-200/80 rounded-lg px-3 py-2.5 hover:border-slate-300 transition-colors">
      <p className="text-[11px] text-slate-400 mb-1">{label}</p>
      <div className="flex items-center justify-between">
        <span className="text-base font-semibold text-slate-700 tabular-nums">
          {(value * 100).toFixed(0)}%
        </span>
        {hasDelta && (
          <span
            className={`text-[11px] flex items-center gap-0.5 font-medium px-1.5 py-0.5 rounded ${
              isImprovement
                ? 'text-emerald-600 bg-emerald-50'
                : isWorse
                  ? 'text-rose-600 bg-rose-50'
                  : 'text-slate-500 bg-slate-50'
            }`}
          >
            {isImprovement ? (
              <TrendingDown className="h-3 w-3" />
            ) : (
              <TrendingUp className="h-3 w-3" />
            )}
            {Math.abs(delta * 100).toFixed(0)}
          </span>
        )}
      </div>
    </div>
  );
}
