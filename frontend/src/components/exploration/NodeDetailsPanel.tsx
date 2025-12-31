/**
 * NodeDetailsPanel component.
 *
 * Side panel (Sheet) showing details of a selected scenario node.
 *
 * References:
 *   - Spec: specs/025-exploration-frontend/spec.md (US3)
 */

import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from '@/components/ui/sheet';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Progress } from '@/components/ui/progress';
import {
  formatSuccessRate,
  formatDelta,
  formatDuration,
  getCategoryDisplayName,
} from '@/lib/exploration-utils';
import type { ScenarioNode } from '@/types/exploration';
import { NODE_STATUS_BADGES } from '@/types/exploration';
import {
  ArrowRight,
  Clock,
  GitBranch,
  Lightbulb,
  TrendingUp,
  TrendingDown,
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
  const successRateDelta = parentNode?.simulation_results && node.simulation_results
    ? node.simulation_results.success_rate - parentNode.simulation_results.success_rate
    : null;

  const getBadgeVariant = (variant: string) => {
    switch (variant) {
      case 'success':
        return 'default';
      case 'error':
        return 'destructive';
      default:
        return 'secondary';
    }
  };

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="sm:max-w-[400px] overflow-y-auto">
        <SheetHeader>
          <SheetTitle className="flex items-center gap-2">
            <GitBranch className="h-5 w-5 text-indigo-600" />
            {isRoot ? 'Cenário Inicial (Baseline)' : 'Detalhes do Cenário'}
          </SheetTitle>
          <SheetDescription>
            Profundidade {node.depth} na árvore de exploração
          </SheetDescription>
        </SheetHeader>

        <div className="mt-6 space-y-6">
          {/* Status Badge */}
          <div className="flex items-center gap-2">
            <Badge variant={getBadgeVariant(statusConfig.variant)}>
              {statusConfig.label}
            </Badge>
            {node.execution_time_seconds && (
              <span className="text-xs text-muted-foreground flex items-center gap-1">
                <Clock className="h-3 w-3" />
                {formatDuration(node.execution_time_seconds)}
              </span>
            )}
          </div>

          {/* Action Applied */}
          {node.action_applied && (
            <div className="space-y-2">
              <h4 className="text-sm font-medium flex items-center gap-2">
                <ArrowRight className="h-4 w-4 text-indigo-600" />
                Ação Aplicada
              </h4>
              <p className="text-sm bg-muted/50 p-3 rounded-lg">
                {node.action_applied}
              </p>
              {node.action_category && (
                <p className="text-xs text-muted-foreground">
                  Categoria: {getCategoryDisplayName(node.action_category)}
                </p>
              )}
            </div>
          )}

          {/* Rationale */}
          {node.rationale && (
            <div className="space-y-2">
              <h4 className="text-sm font-medium flex items-center gap-2">
                <Lightbulb className="h-4 w-4 text-amber-500" />
                Justificativa
              </h4>
              <p className="text-sm text-muted-foreground bg-muted/50 p-3 rounded-lg">
                {node.rationale}
              </p>
            </div>
          )}

          <Separator />

          {/* Simulation Results */}
          {node.simulation_results && (
            <div className="space-y-3">
              <h4 className="text-sm font-medium">Resultados da Simulação</h4>

              {/* Success Rate with Delta */}
              <div className="space-y-1">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Success Rate</span>
                  <div className="flex items-center gap-2">
                    <span className="font-medium">
                      {formatSuccessRate(node.simulation_results.success_rate)}
                    </span>
                    {successRateDelta !== null && (
                      <span
                        className={`text-xs flex items-center gap-0.5 ${
                          successRateDelta >= 0 ? 'text-green-600' : 'text-red-600'
                        }`}
                      >
                        {successRateDelta >= 0 ? (
                          <TrendingUp className="h-3 w-3" />
                        ) : (
                          <TrendingDown className="h-3 w-3" />
                        )}
                        {formatDelta(successRateDelta)}
                      </span>
                    )}
                  </div>
                </div>
                <Progress
                  value={node.simulation_results.success_rate * 100}
                  className="h-2"
                />
              </div>

              {/* Fail Rate */}
              <div className="space-y-1">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Fail Rate</span>
                  <span className="font-medium">
                    {formatSuccessRate(node.simulation_results.fail_rate)}
                  </span>
                </div>
                <Progress
                  value={node.simulation_results.fail_rate * 100}
                  className="h-2 [&>div]:bg-red-500"
                />
              </div>

              {/* Did Not Try Rate */}
              <div className="space-y-1">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Did Not Try</span>
                  <span className="font-medium">
                    {formatSuccessRate(node.simulation_results.did_not_try_rate)}
                  </span>
                </div>
                <Progress
                  value={node.simulation_results.did_not_try_rate * 100}
                  className="h-2 [&>div]:bg-slate-400"
                />
              </div>
            </div>
          )}

          <Separator />

          {/* Scorecard Parameters */}
          <div className="space-y-3">
            <h4 className="text-sm font-medium">Parâmetros do Scorecard</h4>

            <div className="grid grid-cols-2 gap-3">
              <ScoreItem
                label="Complexidade"
                value={node.scorecard_params.complexity}
              />
              <ScoreItem
                label="Esforço Inicial"
                value={node.scorecard_params.initial_effort}
              />
              <ScoreItem
                label="Risco Percebido"
                value={node.scorecard_params.perceived_risk}
              />
              <ScoreItem
                label="Tempo até Valor"
                value={node.scorecard_params.time_to_value}
              />
            </div>
          </div>

          {/* Node Metadata */}
          <div className="text-xs text-muted-foreground space-y-1 pt-4 border-t">
            <p>ID: {node.id}</p>
            <p>Criado em: {new Date(node.created_at).toLocaleString('pt-BR')}</p>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
}

// Helper component for scorecard parameter display
function ScoreItem({ label, value }: { label: string; value: number }) {
  return (
    <div className="bg-muted/50 p-2 rounded">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="font-medium">{(value * 100).toFixed(0)}%</p>
    </div>
  );
}
