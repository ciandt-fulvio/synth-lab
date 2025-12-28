/**
 * ExperimentCard component (Refactored).
 *
 * Card display for an experiment in the list view.
 *
 * References:
 *   - Spec: specs/019-experiment-refactor/spec.md
 *   - Types: src/types/experiment.ts
 */

import { Badge } from '@/components/ui/badge';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Calendar, FlaskConical, MessageSquare, CheckCircle } from 'lucide-react';
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
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg font-semibold text-gray-900 line-clamp-1">
            {experiment.name}
          </CardTitle>
          {experiment.has_scorecard && (
            <Badge variant="outline" className="text-purple-600 border-purple-300 text-xs">
              Scorecard
            </Badge>
          )}
        </div>
        <CardDescription className="text-sm text-gray-600 line-clamp-2">
          {truncatedHypothesis}
        </CardDescription>
      </CardHeader>
      <CardContent className="pt-0">
        <div className="flex items-center justify-between text-sm text-muted-foreground mt-2">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-1" title="Análise Quantitativa">
              <FlaskConical className="h-4 w-4 text-purple-500" />
              {experiment.has_analysis ? (
                <CheckCircle className="h-3 w-3 text-green-500" />
              ) : (
                <span className="text-gray-400">-</span>
              )}
            </div>
            <div className="flex items-center gap-1" title="Entrevistas">
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
