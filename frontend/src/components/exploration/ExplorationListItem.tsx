/**
 * ExplorationListItem component.
 *
 * Single item in the explorations list.
 *
 * References:
 *   - Spec: specs/025-exploration-frontend/spec.md (US6)
 */

import { Link } from 'react-router-dom';
import { formatDistanceToNow } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import { ExplorationStatusBadge } from './ExplorationStatusBadge';
import { formatSuccessRate } from '@/lib/exploration-utils';
import type { ExplorationSummary, ExplorationStatus } from '@/types/exploration';
import { ChevronRight, Network, GitBranch, Target } from 'lucide-react';

interface ExplorationListItemProps {
  exploration: ExplorationSummary;
  experimentId: string;
}

export function ExplorationListItem({
  exploration,
  experimentId,
}: ExplorationListItemProps) {
  const isRunning = exploration.status === 'running';

  return (
    <Link
      to={`/experiments/${experimentId}/explorations/${exploration.id}`}
      className="block"
    >
      <div
        className={`
          flex items-center gap-4 p-4 rounded-lg border bg-white
          transition-all hover:shadow-md hover:border-indigo-200
          ${isRunning ? 'border-blue-200 bg-blue-50/30' : ''}
        `}
      >
        {/* Icon */}
        <div
          className={`
            flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center
            ${isRunning ? 'bg-blue-100' : 'bg-slate-100'}
          `}
        >
          <Network
            className={`h-5 w-5 ${isRunning ? 'text-blue-600' : 'text-slate-600'}`}
          />
        </div>

        {/* Main Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <ExplorationStatusBadge status={exploration.status as ExplorationStatus} />
          </div>

          <div className="flex items-center gap-4 text-sm text-muted-foreground">
            <span className="flex items-center gap-1">
              <Target className="h-3.5 w-3.5" />
              Meta: {formatSuccessRate(exploration.goal_value)}
            </span>
            <span className="flex items-center gap-1">
              <GitBranch className="h-3.5 w-3.5" />
              {exploration.total_nodes} nós
            </span>
            {exploration.best_success_rate !== null && (
              <span className="font-medium text-slate-700">
                Melhor: {formatSuccessRate(exploration.best_success_rate)}
              </span>
            )}
          </div>

          <p className="text-xs text-muted-foreground mt-1">
            Iniciado{' '}
            {formatDistanceToNow(new Date(exploration.started_at), {
              addSuffix: true,
              locale: ptBR,
            })}
          </p>
        </div>

        {/* Arrow */}
        <ChevronRight className="h-5 w-5 text-slate-400 flex-shrink-0" />
      </div>
    </Link>
  );
}
