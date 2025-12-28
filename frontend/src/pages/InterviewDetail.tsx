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
import { useArtifactStatesWithPolling } from '@/hooks/use-artifact-states';
import { usePrfaqGenerate } from '@/hooks/use-prfaq-generate';
import { useSummaryGenerate } from '@/hooks/use-summary-generate';
import { useExperiment } from '@/hooks/use-experiments';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { getPrfaqMarkdown } from '@/services/prfaq-api';
import { getSynthAvatarUrl } from '@/services/synths-api';
import { queryKeys } from '@/lib/query-keys';
import { ArtifactButton } from '@/components/shared/ArtifactButton';
import MarkdownPopup from '@/components/shared/MarkdownPopup';
import { TranscriptDialog } from '@/components/shared/TranscriptDialog';
import { LiveInterviewGrid } from '@/components/interviews/LiveInterviewGrid';
import SynthLabHeader from '@/components/shared/SynthLabHeader';
import { Avatar, AvatarImage, AvatarFallback } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  Loader2,
  User,
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
  const hasRedirectedRef = useRef(false);

  const { data: execution, isLoading, error } = useResearchDetail(execId!);
  const { data: transcripts } = useResearchTranscripts(execId!);
  const { data: artifactStates } = useArtifactStatesWithPolling(execId!);

  // Fetch experiment name for display (when linked to experiment)
  const experimentId = expId || execution?.experiment_id;
  const { data: experiment } = useExperiment(experimentId || '');
  const displayTitle = experiment?.name || execution?.topic_name || 'Entrevista';

  // T061: Auto-redirect legacy URLs to experiment-scoped URLs (only once)
  useEffect(() => {
    if (!hasRedirectedRef.current && !expId && execution?.experiment_id) {
      hasRedirectedRef.current = true;
      navigate(`/experiments/${execution.experiment_id}/interviews/${execId}`, { replace: true });
    }
  }, [expId, execution?.experiment_id, execId, navigate]);

  // Additional context comes from request (if any was provided)
  const additionalContext: string | null = null;  // TODO: Include in execution response if needed

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

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 via-white to-slate-50">
      {/* Standardized Header */}
      <SynthLabHeader
        subtitle="Entrevista do Experimento"
        backTo={expId ? `/experiments/${expId}` : '/'}
      />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        {/* Interview Hero Card - Topic Guide + Artefatos */}
        <AnimatedSection delay={0}>
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
            <div className="flex flex-col lg:flex-row lg:items-start gap-6">
              {/* LEFT: Interview Info */}
              <div className="flex-1">
                {/* Header com icon box */}
                <div className="flex items-center gap-3 mb-4">
                  <div className="p-2 bg-gradient-to-br from-purple-500 to-blue-500 rounded-xl text-white shadow-lg shadow-purple-200">
                    <MessageSquare className="h-5 w-5" />
                  </div>
                  <div className="flex items-center gap-2 flex-wrap">
                    <h2 className="text-2xl font-bold text-slate-900">{displayTitle}</h2>
                    {execution.status === 'running' && (
                      <Badge className="bg-green-100 text-green-700 border-green-200 animate-pulse">
                        <Radio className="h-3 w-3 mr-1" />
                        Ao Vivo
                      </Badge>
                    )}
                  </div>
                </div>

                {/* Interview description with date */}
                <div className="mb-4">
                  <p className="text-slate-600 leading-relaxed">
                    Entrevista realizada em {formattedStart}.
                  </p>
                </div>

                {/* Contexto adicional (se existir) */}
                {additionalContext && (
                  <div className="p-3 bg-purple-50 border border-purple-100 rounded-lg mb-4">
                    <p className="text-xs font-medium text-purple-700 mb-1">Contexto adicional</p>
                    <p className="text-sm text-purple-800">{additionalContext}</p>
                  </div>
                )}

                {/* Execution stats inline */}
                <div className="flex flex-wrap items-center gap-4 text-sm text-slate-500">
                  <span className="flex items-center gap-1.5">
                    <Users className="h-4 w-4" />
                    {execution.synth_count} synths
                  </span>
                  <span className="flex items-center gap-1.5">
                    <CheckCircle2 className="h-4 w-4 text-green-500" />
                    {execution.successful_count} concluídos
                  </span>
                  {execution.failed_count > 0 && (
                    <span className="flex items-center gap-1.5">
                      <XCircle className="h-4 w-4 text-red-500" />
                      {execution.failed_count} falhas
                    </span>
                  )}
                  {durationMinutes !== null && (
                    <span className="flex items-center gap-1.5">
                      <Clock className="h-4 w-4 text-amber-500" />
                      {durationMinutes} min
                    </span>
                  )}
                  <span className="flex items-center gap-1.5">
                    <Calendar className="h-4 w-4" />
                    {formattedStart}
                  </span>
                </div>
              </div>

              {/* RIGHT: Artefatos */}
              <div className="lg:w-64 lg:border-l lg:pl-6 lg:border-slate-200">
                <div className="flex items-center gap-2 mb-4">
                  <Sparkles className="h-4 w-4 text-purple-500" />
                  <h3 className="font-semibold text-slate-900">Artefatos</h3>
                </div>
                <div className="space-y-3">
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
          title={`Summary - ${displayTitle}`}
          markdownContent={summaryMarkdown}
        />
      )}

      {prfaqMarkdown && (
        <MarkdownPopup
          isOpen={prfaqOpen}
          onClose={() => setPrfaqOpen(false)}
          title={`PR/FAQ - ${displayTitle}${
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
