// src/pages/InterviewDetail.tsx

import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useResearchDetail, useResearchTranscripts, useResearchSummary } from '@/hooks/use-research';
import { useArtifactStatesWithPolling } from '@/hooks/use-artifact-states';
import { usePrfaqGenerate } from '@/hooks/use-prfaq-generate';
import { useSummaryGenerate } from '@/hooks/use-summary-generate';
import { useQuery } from '@tanstack/react-query';
import { getPrfaqMarkdown } from '@/services/prfaq-api';
import { getSynthAvatarUrl } from '@/services/synths-api';
import { queryKeys } from '@/lib/query-keys';
import { StatusBadge } from '@/components/shared/StatusBadge';
import { ArtifactButton } from '@/components/shared/ArtifactButton';
import MarkdownPopup from '@/components/shared/MarkdownPopup';
import { TranscriptDialog } from '@/components/shared/TranscriptDialog';
import { LiveInterviewGrid } from '@/components/interviews/LiveInterviewGrid';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Avatar, AvatarImage, AvatarFallback } from '@/components/ui/avatar';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2, ArrowLeft, User } from 'lucide-react';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';

export default function InterviewDetail() {
  const { execId } = useParams<{ execId: string }>();
  const navigate = useNavigate();

  const [summaryOpen, setSummaryOpen] = useState(false);
  const [prfaqOpen, setPrfaqOpen] = useState(false);
  const [selectedSynthId, setSelectedSynthId] = useState<string | null>(null);

  const { data: execution, isLoading, error } = useResearchDetail(execId!);
  const { data: transcripts } = useResearchTranscripts(execId!);
  const { data: artifactStates } = useArtifactStatesWithPolling(execId!);

  // Fetch content based on artifact states
  const summaryAvailable = artifactStates?.summary.state === 'available';
  const prfaqAvailable = artifactStates?.prfaq.state === 'available';

  const { data: summaryMarkdown } = useResearchSummary(execId!, summaryAvailable);
  const { data: prfaqMarkdown } = useQuery({
    queryKey: queryKeys.prfaqMarkdown(execId!),
    queryFn: () => getPrfaqMarkdown(execId!),
    enabled: prfaqAvailable,
  });

  const generatePrfaqMutation = usePrfaqGenerate(execId!);
  const generateSummaryMutation = useSummaryGenerate(execId!);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  if (error || !execution) {
    return (
      <div className="container mx-auto p-6">
        <Alert variant="destructive">
          <AlertDescription>
            Erro ao carregar detalhes da entrevista: {error?.message || 'Entrevista não encontrada'}
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  const formattedStart = format(new Date(execution.started_at), "dd/MM/yyyy 'às' HH:mm", {
    locale: ptBR,
  });

  const formattedEnd = execution.completed_at
    ? format(new Date(execution.completed_at), "dd/MM/yyyy 'às' HH:mm", { locale: ptBR })
    : 'Em andamento';

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => navigate('/')}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <h1 className="text-2xl font-bold">{execution.topic_name}</h1>
        <StatusBadge status={execution.status} />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Informações da Entrevista</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <div>
              <span className="font-semibold">Iniciado:</span> {formattedStart}
            </div>
            <div>
              <span className="font-semibold">Concluído:</span> {formattedEnd}
            </div>
            <div>
              <span className="font-semibold">Total de Synths:</span> {execution.synth_count}
            </div>
            <div>
              <span className="font-semibold">Bem-sucedidos:</span> {execution.successful_count}
            </div>
            <div>
              <span className="font-semibold">Falhas:</span> {execution.failed_count}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Artefatos</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-3">
            {artifactStates ? (
              <>
                <ArtifactButton
                  state={artifactStates.summary.state}
                  artifactType="summary"
                  prerequisiteMessage={artifactStates.summary.prerequisite_message ?? undefined}
                  errorMessage={artifactStates.summary.error_message ?? undefined}
                  onGenerate={() => generateSummaryMutation.mutate()}
                  onView={() => setSummaryOpen(true)}
                  onRetry={() => generateSummaryMutation.mutate()}
                  isPending={generateSummaryMutation.isPending}
                  className="w-full"
                />
                <ArtifactButton
                  state={artifactStates.prfaq.state}
                  artifactType="prfaq"
                  prerequisiteMessage={artifactStates.prfaq.prerequisite_message ?? undefined}
                  errorMessage={artifactStates.prfaq.error_message ?? undefined}
                  onGenerate={() => generatePrfaqMutation.mutate()}
                  onView={() => setPrfaqOpen(true)}
                  onRetry={() => generatePrfaqMutation.mutate()}
                  isPending={generatePrfaqMutation.isPending}
                  className="w-full"
                />
              </>
            ) : (
              <div className="flex items-center justify-center py-4">
                <Loader2 className="h-4 w-4 animate-spin" />
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Live Interview Cards - Real-time monitoring */}
      {execution.status === 'in_progress' && execId && (
        <Card>
          <CardHeader>
            <CardTitle>Entrevistas ao Vivo</CardTitle>
          </CardHeader>
          <CardContent>
            <LiveInterviewGrid execId={execId} />
          </CardContent>
        </Card>
      )}

      {transcripts && transcripts.data.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Synths Entrevistados</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {transcripts.data.map((transcript) => (
                <div
                  key={transcript.synth_id}
                  className="p-3 border rounded-md hover:shadow-md transition-shadow cursor-pointer"
                  onClick={() => setSelectedSynthId(transcript.synth_id)}
                >
                  <div className="flex items-center gap-3 mb-2">
                    <Avatar className="h-12 w-12">
                      <AvatarImage
                        src={getSynthAvatarUrl(transcript.synth_id)}
                        alt={transcript.synth_name || transcript.synth_id}
                      />
                      <AvatarFallback>
                        <User className="h-6 w-6" />
                      </AvatarFallback>
                    </Avatar>
                    <div className="flex-1 min-w-0">
                      <div className="font-semibold text-sm truncate">
                        {transcript.synth_name || transcript.synth_id}
                      </div>
                      <div className="text-xs text-muted-foreground">
                        {transcript.turn_count} turnos • {transcript.status}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {summaryMarkdown && (
        <MarkdownPopup
          isOpen={summaryOpen}
          onClose={() => setSummaryOpen(false)}
          title={`Summary - ${execution.topic_name}`}
          markdownContent={summaryMarkdown}
        />
      )}

      {prfaqMarkdown && (
        <MarkdownPopup
          isOpen={prfaqOpen}
          onClose={() => setPrfaqOpen(false)}
          title={`PR/FAQ - ${execution.topic_name}${
            artifactStates?.prfaq.completed_at
              ? ` (${format(new Date(artifactStates.prfaq.completed_at), "dd/MM/yyyy 'às' HH:mm", { locale: ptBR })})`
              : ''
          }`}
          markdownContent={prfaqMarkdown}
        />
      )}

      <TranscriptDialog
        execId={execId!}
        synthId={selectedSynthId}
        open={!!selectedSynthId}
        onOpenChange={(open) => {
          if (!open) setSelectedSynthId(null);
        }}
      />
    </div>
  );
}
