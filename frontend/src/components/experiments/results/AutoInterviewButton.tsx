// frontend/src/components/experiments/results/AutoInterviewButton.tsx
// Button to create automatic interview with extreme cases (top 5 + bottom 5)

import { useState } from 'react';
import { Users, Loader2, ExternalLink } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { useCreateAutoInterview } from '@/hooks/use-experiments';
import { toast } from 'sonner';

interface AutoInterviewButtonProps {
  experimentId: string;
}

export function AutoInterviewButton({ experimentId }: AutoInterviewButtonProps) {
  const createAutoInterview = useCreateAutoInterview();
  const [interviewId, setInterviewId] = useState<string | null>(null);

  const handleCreateInterview = () => {
    createAutoInterview.mutate(experimentId, {
      onSuccess: (response) => {
        setInterviewId(response.interview_id);
        toast.success('Entrevista criada com sucesso', {
          description: '10 casos extremos selecionados (5 melhores + 5 piores)',
        });
      },
      onError: (error) => {
        const errorMessage = error instanceof Error ? error.message : 'Erro ao criar entrevista';
        toast.error('Falha ao criar entrevista', {
          description: errorMessage,
        });
      },
    });
  };

  return (
    <Card className="card">
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-card-title flex items-center gap-2 mb-2">
              <Users className="h-4 w-4 text-indigo-600" />
              Entrevista Automática
            </h3>
            <p className="text-meta">
              Crie uma entrevista com os 10 casos mais extremos (5 melhores + 5 piores)
            </p>
          </div>

          <div className="flex items-center gap-3">
            {interviewId && (
              <Button
                variant="outline"
                size="sm"
                asChild
                className="btn-secondary"
              >
                <a href={`/interviews/${interviewId}`}>
                  <ExternalLink className="h-4 w-4 mr-2" />
                  Ver Entrevista
                </a>
              </Button>
            )}

            <Button
              onClick={handleCreateInterview}
              disabled={createAutoInterview.isPending || !!interviewId}
              size="sm"
              className="btn-primary"
            >
              {createAutoInterview.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Criando...
                </>
              ) : (
                <>
                  <Users className="h-4 w-4 mr-2" />
                  {interviewId ? 'Entrevista Criada' : 'Entrevistar Casos Extremos'}
                </>
              )}
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
