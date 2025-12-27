/**
 * T023 ExperimentCard component.
 *
 * Card display for an experiment in the list view.
 *
 * References:
 *   - Spec: specs/018-experiment-hub/spec.md (US1)
 *   - Types: src/types/experiment.ts
 */

import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Calendar, FlaskConical, MessageSquare } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import type { ExperimentSummary } from '@/types/experiment';

interface ExperimentCardProps {
  experiment: ExperimentSummary;
  onClick: (id: string) => void;
}

export function ExperimentCard({ experiment, onClick }: ExperimentCardProps) {
  const formattedDate = formatDistanceToNow(new Date(experiment.created_at), {
    addSuffix: true,
    locale: ptBR,
  });

  // Truncate hypothesis to ~100 chars with ellipsis
  const truncatedHypothesis = experiment.hypothesis.length > 100
    ? `${experiment.hypothesis.slice(0, 97)}...`
    : experiment.hypothesis;

  return (
    <Card
      className="cursor-pointer hover:shadow-lg transition-all duration-200 hover:border-purple-200"
      onClick={() => onClick(experiment.id)}
    >
      <CardHeader className="pb-2">
        <CardTitle className="text-lg font-semibold text-gray-900 line-clamp-1">
          {experiment.name}
        </CardTitle>
        <CardDescription className="text-sm text-gray-600 line-clamp-2">
          {truncatedHypothesis}
        </CardDescription>
      </CardHeader>
      <CardContent className="pt-0">
        <div className="flex items-center justify-between text-sm text-muted-foreground mt-2">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-1">
              <FlaskConical className="h-4 w-4 text-purple-500" />
              <span>{experiment.simulation_count}</span>
            </div>
            <div className="flex items-center gap-1">
              <MessageSquare className="h-4 w-4 text-blue-500" />
              <span>{experiment.interview_count}</span>
            </div>
          </div>
          <div className="flex items-center gap-1 text-xs">
            <Calendar className="h-3 w-3" />
            <span>{formattedDate}</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
