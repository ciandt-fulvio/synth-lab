// src/components/interviews/InterviewList.tsx

import { useNavigate } from 'react-router-dom';
import { InterviewCard } from './InterviewCard';
import { useResearchList } from '@/hooks/use-research';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2, FileQuestion } from 'lucide-react';

export function InterviewList() {
  const navigate = useNavigate();
  const { data, isLoading, error } = useResearchList();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertDescription>
          Erro ao carregar entrevistas: {error.message}
        </AlertDescription>
      </Alert>
    );
  }

  if (!data || data.data.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <FileQuestion className="h-12 w-12 text-muted-foreground mb-4" />
        <h3 className="text-lg font-semibold mb-2">Nenhuma entrevista encontrada</h3>
        <p className="text-sm text-muted-foreground">
          Crie uma nova entrevista a partir de um experimento
        </p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {data.data.map((execution) => (
        <InterviewCard
          key={execution.exec_id}
          execution={execution}
          onClick={(execId) => navigate(`/interviews/${execId}`)}
        />
      ))}
    </div>
  );
}
