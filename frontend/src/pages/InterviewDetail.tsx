/**
 * InterviewDetail page - Research Observatory Design.
 *
 * Displays interview execution details with live monitoring.
 *
 * References:
 *   - Spec: specs/018-experiment-hub/spec.md
 */

import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useResearchDetail, useResearchTranscripts, useResearchSummary } from '@/hooks/use-research';
import { useTopicDetail } from '@/hooks/use-topics';
import { useArtifactStatesWithPolling } from '@/hooks/use-artifact-states';
import { usePrfaqGenerate } from '@/hooks/use-prfaq-generate';
import { useSummaryGenerate } from '@/hooks/use-summary-generate';
import { useQuery, useQueryClient } from '@tanstack/react-query';
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
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  Loader2,
  ArrowLeft,
  User,
  FileText,
  Users,
  CheckCircle2,
  XCircle,
  Clock,
  Calendar,
  MessageSquare,
  Sparkles,
  Radio,
} from 'lucide-react';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';

// =============================================================================
// Animated Section Component
// =============================================================================

interface AnimatedSectionProps {
  children: React.ReactNode;
  delay?: number;
}

function AnimatedSection({ children, delay = 0 }: AnimatedSectionProps) {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setIsVisible(true), delay);
    return () => clearTimeout(timer);
  }, [delay]);

  return (
    <div
      className={`transition-all duration-500 ease-out ${
        isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
      }`}
    >
      {children}
    </div>
  );
}

// =============================================================================
// Main Component
// =============================================================================

export default function InterviewDetail() {
  const { execId, expId } = useParams<{ execId: string; expId?: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [summaryOpen, setSummaryOpen] = useState(false);
  const [prfaqOpen, setPrfaqOpen] = useState(false);
  const [selectedSynthId, setSelectedSynthId] = useState<string | null>(null);
  const [aggressivePolling, setAggressivePolling] = useState(false);
  const aggressivePollingTimerRef = useRef<NodeJS.Timeout | null>(null);

  const { data: execution, isLoading, error } = useResearchDetail(execId!);
  const { data: transcripts } = useResearchTranscripts(execId!);
  const { data: artifactStates } = useArtifactStatesWithPolling(execId!);

  // T061: Auto-redirect legacy URLs to experiment-scoped URLs
  useEffect(() => {
    if (!expId && execution?.experiment_id) {
      navigate(`/experiments/${execution.experiment_id}/interviews/${execId}`, { replace: true });
    }
  }, [expId, execution?.experiment_id, execId, navigate]);

  // Fetch topic details for question preview
  const { data: topicDetail } = useTopicDetail(execution?.topic_name ?? null);

  // Mock additional context
  const additionalContext = execution?.topic_name === 'compra-amazon'
    ? 'Focar em experiências de compra mobile e comparação de preços'
    : null;

  // Handle transcription completion
  const handleTranscriptionCompleted = (data: import('@/types/sse-events').TranscriptionCompletedEvent) => {
    console.log('[InterviewDetail] Transcription completed', data);
    queryClient.invalidateQueries({ queryKey: queryKeys.artifactStates(execId!) });
    setAggressivePolling(true);

    if (aggressivePollingTimerRef.current) {
      clearTimeout(aggressivePollingTimerRef.current);
    }

    aggressivePollingTimerRef.current = setTimeout(() => {
      setAggressivePolling(false);
    }, 60000);
  };

  // Handle execution completion
  const handleExecutionCompleted = () => {
    queryClient.invalidateQueries({ queryKey: queryKeys.researchDetail(execId!) });
    queryClient.invalidateQueries({ queryKey: queryKeys.researchTranscripts(execId!) });
    queryClient.invalidateQueries({ queryKey: queryKeys.artifactStates(execId!) });
  };

  // Aggressive polling effect
  useEffect(() => {
    if (!aggressivePolling || !execId) return;

    const interval = setInterval(() => {
      queryClient.invalidateQueries({ queryKey: queryKeys.artifactStates(execId) });
    }, 2000);

    return () => clearInterval(interval);
  }, [aggressivePolling, execId, queryClient]);

  // Cleanup timer on unmount
  useEffect(() => {
    return () => {
      if (aggressivePollingTimerRef.current) {
        clearTimeout(aggressivePollingTimerRef.current);
      }
    };
  }, []);

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
      <div className="min-h-screen bg-gradient-to-b from-slate-50 via-white to-slate-50 flex items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <Loader2 className="h-8 w-8 animate-spin text-purple-500" />
          <p className="text-sm text-slate-500">Carregando entrevista...</p>
        </div>
      </div>
    );
  }

  if (error || !execution) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-slate-50 via-white to-slate-50 p-6">
        <div className="max-w-3xl mx-auto">
          <Alert variant="destructive" className="border-red-200 bg-red-50">
            <AlertDescription className="text-red-700">
              Erro ao carregar detalhes da entrevista: {error?.message || 'Entrevista não encontrada'}
            </AlertDescription>
          </Alert>
        </div>
      </div>
    );
  }

  const formattedStart = format(new Date(execution.started_at), "dd/MM/yyyy 'às' HH:mm", {
    locale: ptBR,
  });

  const durationMinutes = execution.completed_at
    ? Math.round((new Date(execution.completed_at).getTime() - new Date(execution.started_at).getTime()) / 60000)
    : null;

  const firstScript = topicDetail?.script?.[0];
  const contextDefinition = firstScript?.context_definition;

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 via-white to-slate-50">
      {/* Sticky Header */}
      <header className="sticky top-0 z-50 bg-white/80 backdrop-blur-md border-b border-slate-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => expId ? navigate(`/experiments/${expId}`) : navigate('/')}
              className="btn-ghost-icon"
            >
              <ArrowLeft className="h-5 w-5" />
            </Button>
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <h1 className="text-xl font-bold text-slate-900">{execution.topic_name}</h1>
                <StatusBadge status={execution.status} />
                {execution.status === 'running' && (
                  <Badge className="bg-green-100 text-green-700 border-green-200 animate-pulse">
                    <Radio className="h-3 w-3 mr-1" />
                    Ao Vivo
                  </Badge>
                )}
              </div>
              <p className="text-sm text-slate-500">
                {expId ? 'Entrevista do experimento' : 'Detalhes da entrevista'}
              </p>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        {/* Topic Guide + Execution Stats */}
        <AnimatedSection delay={0}>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            {/* Topic Guide - 2/3 width */}
            <div className="lg:col-span-2 bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
              <div className="px-5 py-4 border-b border-slate-100">
                <div className="flex items-center gap-2">
                  <div className="p-1.5 bg-blue-100 rounded-lg">
                    <FileText className="h-4 w-4 text-blue-600" />
                  </div>
                  <h3 className="font-semibold text-slate-900">Topic Guide</h3>
                </div>
              </div>
              <div className="p-5 space-y-4">
                {contextDefinition ? (
                  <p className="text-sm text-slate-600 leading-relaxed">{contextDefinition}</p>
                ) : firstScript?.ask ? (
                  <p className="text-sm text-slate-600 leading-relaxed line-clamp-3">{firstScript.ask}</p>
                ) : (
                  <p className="text-sm text-slate-400 italic">Carregando...</p>
                )}

                {additionalContext && (
                  <div className="p-3 bg-purple-50 rounded-lg border border-purple-100">
                    <p className="text-xs font-medium text-purple-700 mb-1">Contexto adicional</p>
                    <p className="text-sm text-purple-600">{additionalContext}</p>
                  </div>
                )}

                {/* Execution Stats */}
                <div className="pt-4 border-t border-slate-100">
                  <p className="text-xs font-medium text-slate-400 uppercase tracking-wide mb-3">Execução</p>
                  <div className="flex flex-wrap items-center gap-4">
                    <div className="flex items-center gap-2 text-sm">
                      <div className="p-1 bg-slate-100 rounded">
                        <Users className="h-3.5 w-3.5 text-slate-500" />
                      </div>
                      <span className="text-slate-700">{execution.synth_count} synths</span>
                    </div>
                    <div className="flex items-center gap-2 text-sm">
                      <div className="p-1 bg-green-100 rounded">
                        <CheckCircle2 className="h-3.5 w-3.5 text-green-600" />
                      </div>
                      <span className="text-slate-700">{execution.successful_count} concluídos</span>
                    </div>
                    {execution.failed_count > 0 && (
                      <div className="flex items-center gap-2 text-sm">
                        <div className="p-1 bg-red-100 rounded">
                          <XCircle className="h-3.5 w-3.5 text-red-500" />
                        </div>
                        <span className="text-slate-700">{execution.failed_count} falhas</span>
                      </div>
                    )}
                    {durationMinutes !== null && (
                      <div className="flex items-center gap-2 text-sm">
                        <div className="p-1 bg-amber-100 rounded">
                          <Clock className="h-3.5 w-3.5 text-amber-600" />
                        </div>
                        <span className="text-slate-700">{durationMinutes} min</span>
                      </div>
                    )}
                    <div className="flex items-center gap-2 text-sm">
                      <div className="p-1 bg-blue-100 rounded">
                        <Calendar className="h-3.5 w-3.5 text-blue-500" />
                      </div>
                      <span className="text-slate-600 text-xs">{formattedStart}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Artifacts - 1/3 width */}
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
              <div className="px-5 py-4 border-b border-slate-100">
                <div className="flex items-center gap-2">
                  <div className="p-1.5 bg-purple-100 rounded-lg">
                    <Sparkles className="h-4 w-4 text-purple-600" />
                  </div>
                  <h3 className="font-semibold text-slate-900">Artefatos</h3>
                </div>
              </div>
              <div className="p-5 flex flex-col gap-3">
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
                  <div className="flex items-center justify-center py-6">
                    <Loader2 className="h-5 w-5 animate-spin text-slate-400" />
                  </div>
                )}
              </div>
            </div>
          </div>
        </AnimatedSection>

        {/* Live Interview Cards - Real-time monitoring */}
        {execution.status === 'running' && execId && (
          <AnimatedSection delay={100}>
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
              <div className="px-5 py-4 border-b border-slate-100">
                <div className="flex items-center gap-2">
                  <div className="p-1.5 bg-green-100 rounded-lg">
                    <Radio className="h-4 w-4 text-green-600" />
                  </div>
                  <h3 className="font-semibold text-slate-900">Entrevistas ao Vivo</h3>
                  <Badge className="bg-green-100 text-green-700 border-green-200 text-xs animate-pulse">
                    Em andamento
                  </Badge>
                </div>
              </div>
              <div className="p-5">
                <LiveInterviewGrid
                  execId={execId}
                  onExecutionCompleted={handleExecutionCompleted}
                  onTranscriptionCompleted={handleTranscriptionCompleted}
                />
              </div>
            </div>
          </AnimatedSection>
        )}

        {/* Transcripts Grid */}
        {transcripts && transcripts.data.length > 0 && (
          <AnimatedSection delay={200}>
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
              <div className="px-5 py-4 border-b border-slate-100">
                <div className="flex items-center gap-2">
                  <div className="p-1.5 bg-slate-100 rounded-lg">
                    <MessageSquare className="h-4 w-4 text-slate-600" />
                  </div>
                  <h3 className="font-semibold text-slate-900">Synths Entrevistados</h3>
                  <Badge variant="secondary" className="bg-slate-100 text-slate-600 text-xs">
                    {transcripts.data.length}
                  </Badge>
                </div>
              </div>
              <div className="p-5">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                  {transcripts.data.map((transcript, index) => (
                    <div
                      key={transcript.synth_id}
                      className="p-4 bg-slate-50 border border-slate-200 rounded-xl hover:bg-white hover:shadow-md hover:border-purple-200 transition-all cursor-pointer group"
                      onClick={() => setSelectedSynthId(transcript.synth_id)}
                      style={{ animationDelay: `${index * 50}ms` }}
                    >
                      <div className="flex items-center gap-3">
                        <Avatar className="h-12 w-12 border-2 border-white shadow-sm group-hover:border-purple-200 transition-colors">
                          <AvatarImage
                            src={getSynthAvatarUrl(transcript.synth_id)}
                            alt={transcript.synth_name || transcript.synth_id}
                          />
                          <AvatarFallback className="bg-gradient-to-br from-purple-100 to-blue-100 text-purple-600">
                            <User className="h-5 w-5" />
                          </AvatarFallback>
                        </Avatar>
                        <div className="flex-1 min-w-0">
                          <div className="font-medium text-sm text-slate-900 truncate group-hover:text-purple-700 transition-colors">
                            {transcript.synth_name || transcript.synth_id}
                          </div>
                          <div className="flex items-center gap-2 text-xs text-slate-500">
                            <span>{transcript.turn_count} turnos</span>
                            <span className="text-slate-300">•</span>
                            <span className={
                              transcript.status === 'completed' ? 'text-green-600' :
                              transcript.status === 'failed' ? 'text-red-500' :
                              'text-amber-500'
                            }>
                              {transcript.status}
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </AnimatedSection>
        )}
      </main>

      {/* Modals */}
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
