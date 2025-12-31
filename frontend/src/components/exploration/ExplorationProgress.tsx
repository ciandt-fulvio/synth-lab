/**
 * ExplorationProgress component.
 *
 * Displays real-time progress indicators for a running exploration.
 *
 * References:
 *   - Spec: specs/025-exploration-frontend/spec.md (US5)
 */

import { Progress } from '@/components/ui/progress';
import { ExplorationStatusBadge } from './ExplorationStatusBadge';
import type { Exploration } from '@/types/exploration';
import { formatSuccessRate } from '@/lib/exploration-utils';
import { GitBranch, Layers, Cpu, TrendingUp } from 'lucide-react';

interface ExplorationProgressProps {
  exploration: Exploration;
  className?: string;
}

export function ExplorationProgress({
  exploration,
  className = '',
}: ExplorationProgressProps) {
  const isRunning = exploration.status === 'running';
  const depthProgress = (exploration.current_depth / exploration.config.max_depth) * 100;
  const llmProgress = (exploration.total_llm_calls / exploration.config.max_llm_calls) * 100;

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Status and Goal */}
      <div className="flex items-center justify-between">
        <ExplorationStatusBadge status={exploration.status} />
        <div className="text-sm text-muted-foreground">
          Meta: {formatSuccessRate(exploration.goal.value)}
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {/* Current Depth */}
        <MetricCard
          icon={<Layers className="h-4 w-4 text-indigo-600" />}
          label="Profundidade"
          value={`${exploration.current_depth}/${exploration.config.max_depth}`}
          progress={depthProgress}
          showProgress={isRunning}
        />

        {/* Total Nodes */}
        <MetricCard
          icon={<GitBranch className="h-4 w-4 text-blue-600" />}
          label="Nós Criados"
          value={exploration.total_nodes.toString()}
        />

        {/* LLM Calls */}
        <MetricCard
          icon={<Cpu className="h-4 w-4 text-purple-600" />}
          label="Chamadas LLM"
          value={`${exploration.total_llm_calls}/${exploration.config.max_llm_calls}`}
          progress={llmProgress}
          showProgress={isRunning}
        />

        {/* Best Success Rate */}
        <MetricCard
          icon={<TrendingUp className="h-4 w-4 text-green-600" />}
          label="Melhor Taxa"
          value={formatSuccessRate(exploration.best_success_rate)}
          highlight={exploration.status === 'goal_achieved'}
        />
      </div>

      {/* Running Indicator */}
      {isRunning && (
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <div className="h-2 w-2 rounded-full bg-blue-500 animate-pulse" />
          Explorando cenários...
        </div>
      )}
    </div>
  );
}

// Helper component for metric display
interface MetricCardProps {
  icon: React.ReactNode;
  label: string;
  value: string;
  progress?: number;
  showProgress?: boolean;
  highlight?: boolean;
}

function MetricCard({
  icon,
  label,
  value,
  progress,
  showProgress,
  highlight,
}: MetricCardProps) {
  return (
    <div
      className={`bg-white rounded-lg border p-3 space-y-2 ${
        highlight ? 'border-green-200 bg-green-50' : ''
      }`}
    >
      <div className="flex items-center gap-2">
        {icon}
        <span className="text-xs text-muted-foreground">{label}</span>
      </div>
      <p className={`font-semibold ${highlight ? 'text-green-700' : ''}`}>
        {value}
      </p>
      {showProgress && progress !== undefined && (
        <Progress value={progress} className="h-1" />
      )}
    </div>
  );
}
