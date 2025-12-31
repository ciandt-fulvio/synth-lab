// src/components/interviews/InterviewCard.tsx

import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { StatusBadge, EXECUTION_STATUS_CONFIG } from '@/components/shared/StatusBadge';
import { Calendar, Users } from 'lucide-react';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import type { ResearchExecutionSummary } from '@/types';

interface InterviewCardProps {
  execution: ResearchExecutionSummary;
  onClick: (execId: string) => void;
}

export function InterviewCard({ execution, onClick }: InterviewCardProps) {
  const formattedDate = format(new Date(execution.started_at), "dd/MM/yyyy 'às' HH:mm", {
    locale: ptBR,
  });

  return (
    <Card
      className="cursor-pointer hover:shadow-lg transition-shadow"
      onClick={() => onClick(execution.exec_id)}
    >
      <CardHeader>
        <div className="flex items-start justify-between">
          <CardTitle className="text-lg">{execution.topic_name}</CardTitle>
          <StatusBadge status={execution.status} />
        </div>
        <CardDescription className="flex items-center gap-1 text-sm">
          <Calendar className="h-3 w-3" />
          {formattedDate}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Users className="h-4 w-4" />
          <span>{execution.synth_count} synth(s)</span>
        </div>
      </CardContent>
    </Card>
  );
}
