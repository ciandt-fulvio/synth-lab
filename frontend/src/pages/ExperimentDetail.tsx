/**
 * ExperimentDetail page - Research Observatory Design.
 *
 * Structured as: Header (read-only) → Tabs (Analysis | Interviews | Explorations)
 * Analysis follows narrative: Overview → Distribution → Segmentation → Edge Cases
 *
 * References:
 *   - Spec: specs/019-experiment-refactor/spec.md
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';
import { useExperiment, useRunAnalysis, useDeleteExperiment } from '@/hooks/use-experiments';
import { useExplorations } from '@/hooks/use-exploration';
import { NewInterviewFromExperimentDialog } from '@/components/experiments/NewInterviewFromExperimentDialog';
import { AnalysisPhaseTabs, type AnalysisPhaseId } from '@/components/experiments/AnalysisPhaseTabs';
import {
  PhaseOverview,
  PhaseLocation,
  PhaseSegmentation,
  PhaseEdgeCases,
} from '@/components/experiments/results';
import { ViewSummaryButton } from '@/components/experiments/results/ViewSummaryButton';
import { ExplorationList } from '@/components/exploration/ExplorationList';
import { NewExplorationDialog } from '@/components/exploration/NewExplorationDialog';
import { MaterialUpload } from '@/components/experiments/MaterialUpload';
import { MaterialGallery } from '@/components/experiments/MaterialGallery';
import { useMaterials } from '@/hooks/use-materials';
import { DocumentsList } from '@/components/experiments/DocumentsList';
import { useDocuments } from '@/hooks/use-documents';
import {
  ChevronLeft,
  ChevronRight,
  MessageSquare,
  MessageCircle,
  Plus,
  FlaskConical,
  Loader2,
  AlertTriangle,
  ArrowLeft,
  Trash2,
  PieChart,
  Network,
  Info,
  Users,
  Paperclip,
  FileText,
} from 'lucide-react';
import { format, formatDistanceToNow } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import { SynthLabHeader } from '@/components/shared/SynthLabHeader';

// =============================================================================
// Scorecard Slider Component (Read-only)
// =============================================================================

interface ScoreSliderProps {
  label: string;
  value: number;
  color: string;
  delay?: number;
}

function ScoreSlider({ label, value, color, delay = 0 }: ScoreSliderProps) {
  const [animatedValue, setAnimatedValue] = useState(0);

  useEffect(() => {
    const timer = setTimeout(() => {
      const duration = 800;
      const steps = 40;
      const increment = value / steps;
      let current = 0;

      const interval = setInterval(() => {
        current += increment;
        if (current >= value) {
          setAnimatedValue(value);
          clearInterval(interval);
        } else {
          setAnimatedValue(current);
        }
      }, duration / steps);

      return () => clearInterval(interval);
    }, delay);

    return () => clearTimeout(timer);
  }, [value, delay]);

  return (
    <div className="flex items-center gap-3 min-w-[180px]">
      <div className="flex-1">
        <div className="flex items-center justify-between mb-1">
          <span className="text-xs font-medium text-slate-600">{label}</span>
          <span className="text-xs font-bold text-slate-700" style={{ color }}>
            {Math.round(animatedValue * 100)}%
          </span>
        </div>
        <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
          <div
            className="h-full rounded-full transition-all duration-800 ease-out"
            style={{
              width: `${animatedValue * 100}%`,
              backgroundColor: color,
            }}
          />
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// Main Component
// =============================================================================

const INTERVIEWS_PER_PAGE = 4;

export default function ExperimentDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [isNewInterviewOpen, setIsNewInterviewOpen] = useState(false);
  const [interviewPage, setInterviewPage] = useState(0);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [isNewExplorationOpen, setIsNewExplorationOpen] = useState(false);

  // Tab underline animation state
  // Initialize activeTab from query param 'tab' if present, otherwise default to 'analysis'
  const tabFromQuery = searchParams.get('tab');
  const initialTab = ['analysis', 'interviews', 'explorations', 'materials', 'reports'].includes(tabFromQuery ?? '')
    ? tabFromQuery!
    : 'analysis';
  const [activeTab, setActiveTab] = useState(initialTab);
  const [underlineStyle, setUnderlineStyle] = useState({ left: 0, width: 0 });
  const tabsListRef = useRef<HTMLDivElement>(null);
  const tabRefs = useRef<Map<string, HTMLButtonElement>>(new Map());

  // Sync activeTab with query param when it changes
  useEffect(() => {
    const newTab = searchParams.get('tab');
    const validTab = ['analysis', 'interviews', 'explorations', 'materials', 'reports'].includes(newTab ?? '')
      ? newTab!
      : 'analysis';
    setActiveTab(validTab);
  }, [searchParams]);

  const updateUnderline = useCallback(() => {
    const activeTabEl = tabRefs.current.get(activeTab);
    const listEl = tabsListRef.current;
    if (activeTabEl && listEl) {
      const listRect = listEl.getBoundingClientRect();
      const tabRect = activeTabEl.getBoundingClientRect();
      setUnderlineStyle({
        left: tabRect.left - listRect.left,
        width: tabRect.width,
      });
    }
  }, [activeTab]);

  useEffect(() => {
    updateUnderline();
    window.addEventListener('resize', updateUnderline);
    return () => window.removeEventListener('resize', updateUnderline);
  }, [updateUnderline]);

  const { data: experiment, isLoading, isError, error } = useExperiment(id ?? '');
  const runAnalysisMutation = useRunAnalysis();
  const deleteMutation = useDeleteExperiment();
  const { data: explorations, isLoading: isLoadingExplorations } = useExplorations(id ?? '');
  const { data: materials, refetch: refetchMaterials } = useMaterials(id ?? '');
  const { data: documents } = useDocuments(id ?? '');

  const handleRunAnalysis = () => {
    if (!id) return;
    runAnalysisMutation.mutate(
      { experimentId: id },
      {
        onSuccess: () => {
          toast.success('Análise iniciada com sucesso');
        },
        onError: (error) => {
          const message =
            error instanceof Error
              ? error.message
              : 'Erro desconhecido ao executar análise';
          toast.error(message);
        },
      }
    );
  };

  const handleDelete = () => {
    if (!id) return;
    deleteMutation.mutate(id, {
      onSuccess: () => {
        toast.success('Experimento excluído com sucesso');
        navigate('/');
      },
      onError: (error) => {
        const message =
          error instanceof Error
            ? error.message
            : 'Erro desconhecido ao excluir experimento';
        toast.error(message);
      },
    });
  };

  const handleExplorationSuccess = (explorationId: string) => {
    navigate(`/experiments/${id}/explorations/${explorationId}`);
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
        <div className="max-w-6xl mx-auto px-6 py-8">
          <Skeleton className="h-8 w-48 mb-4" />
          <Skeleton className="h-24 w-full mb-6" />
          <Skeleton className="h-64 w-full" />
        </div>
      </div>
    );
  }

  // Error state
  if (isError || !experiment) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center">
        <div className="text-center bg-white rounded-xl p-8 shadow-sm border border-slate-200">
          <FlaskConical className="w-12 h-12 text-slate-400 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-slate-800 mb-2">
            Experimento não encontrado
          </h2>
          <p className="text-slate-500 mb-4">
            {error?.message || 'O experimento solicitado não existe.'}
          </p>
          <Button onClick={() => navigate('/')} variant="outline">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Voltar
          </Button>
        </div>
      </div>
    );
  }

  // Scorecard data
  const scorecard = experiment.scorecard_data;
  const hasScorecard = experiment.has_scorecard && scorecard;

  // Truncate description to 2 lines (~150 chars)
  const truncatedDescription = experiment.description
    ? experiment.description.length > 150
      ? `${experiment.description.slice(0, 147)}...`
      : experiment.description
    : null;

  // Analysis data
  const analysis = experiment.analysis;
  const hasAnalysis = analysis && analysis.status === 'completed';

  // Exploration data
  const hasRunningExploration = explorations?.some((e) => e.status === 'running');
  const isExplorationButtonDisabled = !hasAnalysis || hasRunningExploration;

  // Get analysis status for badge
  const getAnalysisStatus = () => {
    if (!hasScorecard) return { label: 'Sem scorecard', count: false };
    if (!analysis) return { label: 'Não iniciada', count: false };
    if (analysis.status === 'running') return { label: 'Executando...', count: false };
    if (analysis.status === 'failed') return { label: 'Falhou', count: false };
    return { label: '4', count: true };
  };

  const analysisStatus = getAnalysisStatus();

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 via-white to-slate-50">
      <SynthLabHeader subtitle="Detalhe do Experimento" backTo="/" />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Experiment Header Section */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 mb-6">
          <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-6">
            {/* Left: Experiment Info */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-3 mb-3">
                <div className="p-2 bg-gradient-to-br from-purple-500 to-blue-500 rounded-xl text-white shadow-lg shadow-purple-200">
                  <FlaskConical className="h-5 w-5" />
                </div>
                <h2 className="text-2xl font-bold text-slate-900">
                  {experiment.name}
                </h2>
              </div>
              <p className="text-slate-600 leading-relaxed mb-2">
                {experiment.hypothesis}
              </p>
              {truncatedDescription && (
                <p className="text-sm text-slate-400 leading-relaxed">
                  {truncatedDescription}
                </p>
              )}
            </div>

            {/* Right: Scorecard Sliders */}
            {hasScorecard && (
              <div className="flex-shrink-0 w-full lg:w-auto lg:min-w-[220px] space-y-3 pt-2 lg:pt-0 lg:border-l lg:border-slate-200 lg:pl-6">
                <ScoreSlider
                  label="Complexidade"
                  value={scorecard.complexity.score}
                  color="#0d9488"
                  delay={0}
                />
                <ScoreSlider
                  label="Esforço Inicial"
                  value={scorecard.initial_effort.score}
                  color="#14b8a6"
                  delay={100}
                />
                <ScoreSlider
                  label="Risco Percebido"
                  value={scorecard.perceived_risk.score}
                  color="#2dd4bf"
                  delay={200}
                />
                <ScoreSlider
                  label="Tempo p/ Valor"
                  value={scorecard.time_to_value.score}
                  color="#5eead4"
                  delay={300}
                />
              </div>
            )}
          </div>
        </div>

        {/* Main Tabs Section */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          {/* Tab Navigation - Underline Style */}
          <div className="relative mb-6">
            <TabsList
              ref={tabsListRef}
              className="relative w-full h-auto p-0 bg-transparent rounded-none border-b border-slate-200 grid grid-cols-5"
            >
              {/* Analysis Tab */}
              <TabsTrigger
                ref={(el) => el && tabRefs.current.set('analysis', el)}
                value="analysis"
                className="relative flex items-center justify-center gap-2.5 px-4 py-4 rounded-none bg-transparent data-[state=active]:bg-transparent data-[state=active]:shadow-none data-[state=active]:text-violet-700 text-slate-500 hover:text-slate-700 transition-colors duration-200"
              >
                <PieChart className="h-4 w-4" />
                <span className="font-semibold">Análise</span>
                <Badge
                  variant="secondary"
                  className={`ml-1 text-[10px] px-2 py-0.5 rounded-full transition-colors ${
                    activeTab === 'analysis'
                      ? 'bg-violet-100 text-violet-700'
                      : analysisStatus.count
                        ? 'bg-slate-100 text-slate-600'
                        : 'bg-slate-100/60 text-slate-400'
                  }`}
                >
                  {analysisStatus.label}
                </Badge>
              </TabsTrigger>

              {/* Interviews Tab */}
              <TabsTrigger
                ref={(el) => el && tabRefs.current.set('interviews', el)}
                value="interviews"
                className="relative flex items-center justify-center gap-2.5 px-4 py-4 rounded-none bg-transparent data-[state=active]:bg-transparent data-[state=active]:shadow-none data-[state=active]:text-violet-700 text-slate-500 hover:text-slate-700 transition-colors duration-200"
              >
                <MessageSquare className="h-4 w-4" />
                <span className="font-semibold">Entrevistas</span>
                <Badge
                  variant="secondary"
                  className={`ml-1 text-[10px] px-2 py-0.5 rounded-full transition-colors ${
                    activeTab === 'interviews'
                      ? 'bg-violet-100 text-violet-700'
                      : 'bg-slate-100 text-slate-600'
                  }`}
                >
                  {experiment.interview_count}
                </Badge>
              </TabsTrigger>

              {/* Explorations Tab */}
              <TabsTrigger
                ref={(el) => el && tabRefs.current.set('explorations', el)}
                value="explorations"
                className="relative flex items-center justify-center gap-2.5 px-4 py-4 rounded-none bg-transparent data-[state=active]:bg-transparent data-[state=active]:shadow-none data-[state=active]:text-violet-700 text-slate-500 hover:text-slate-700 transition-colors duration-200 disabled:opacity-40 disabled:cursor-not-allowed"
                disabled={!hasScorecard || !hasAnalysis}
              >
                <Network className="h-4 w-4" />
                <span className="font-semibold">Explorações</span>
                <Badge
                  variant="secondary"
                  className={`ml-1 text-[10px] px-2 py-0.5 rounded-full transition-colors ${
                    activeTab === 'explorations'
                      ? 'bg-violet-100 text-violet-700'
                      : 'bg-slate-100 text-slate-600'
                  }`}
                >
                  {hasScorecard && hasAnalysis ? (explorations?.length ?? 0) : '—'}
                </Badge>
              </TabsTrigger>

              {/* Materials Tab */}
              <TabsTrigger
                ref={(el) => el && tabRefs.current.set('materials', el)}
                value="materials"
                className="relative flex items-center justify-center gap-2.5 px-4 py-4 rounded-none bg-transparent data-[state=active]:bg-transparent data-[state=active]:shadow-none data-[state=active]:text-violet-700 text-slate-500 hover:text-slate-700 transition-colors duration-200"
              >
                <Paperclip className="h-4 w-4" />
                <span className="font-semibold">Materiais</span>
                <Badge
                  variant="secondary"
                  className={`ml-1 text-[10px] px-2 py-0.5 rounded-full transition-colors ${
                    activeTab === 'materials'
                      ? 'bg-violet-100 text-violet-700'
                      : 'bg-slate-100 text-slate-600'
                  }`}
                >
                  {materials?.materials?.length ?? 0}
                </Badge>
              </TabsTrigger>

              {/* Reports Tab */}
              <TabsTrigger
                ref={(el) => el && tabRefs.current.set('reports', el)}
                value="reports"
                className="relative flex items-center justify-center gap-2.5 px-4 py-4 rounded-none bg-transparent data-[state=active]:bg-transparent data-[state=active]:shadow-none data-[state=active]:text-violet-700 text-slate-500 hover:text-slate-700 transition-colors duration-200"
              >
                <FileText className="h-4 w-4" />
                <span className="font-semibold">Relatórios</span>
                <Badge
                  variant="secondary"
                  className={`ml-1 text-[10px] px-2 py-0.5 rounded-full transition-colors ${
                    activeTab === 'reports'
                      ? 'bg-violet-100 text-violet-700'
                      : 'bg-slate-100 text-slate-600'
                  }`}
                >
                  {documents?.length ?? 0}
                </Badge>
              </TabsTrigger>

              {/* Animated Underline */}
              <div
                className="absolute bottom-0 h-[3px] bg-gradient-to-r from-violet-500 to-indigo-500 rounded-full transition-all duration-300 ease-out"
                style={{
                  left: underlineStyle.left,
                  width: underlineStyle.width,
                }}
              />
            </TabsList>
          </div>

          {/* Analysis Content */}
          <TabsContent value="analysis" className="mt-0">
            {!hasScorecard ? (
              <div className="bg-white rounded-xl border border-dashed border-slate-300 p-12 text-center">
                <FlaskConical className="w-12 h-12 text-slate-300 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-slate-600 mb-2">
                  Scorecard não configurado
                </h3>
                <p className="text-slate-400">
                  Configure o scorecard no formulário de criação para executar análises.
                </p>
              </div>
            ) : !analysis ? (
              <AnalysisPhaseTabs
                onRunAnalysis={handleRunAnalysis}
                isLoading={runAnalysisMutation.isPending}
              />
            ) : analysis.status === 'running' ? (
              <div className="bg-white rounded-xl border border-slate-200 p-12 text-center">
                <Loader2 className="w-12 h-12 text-primary mx-auto mb-4 animate-spin" />
                <h3 className="text-lg font-medium text-slate-700 mb-2">
                  Análise em execução
                </h3>
                <p className="text-slate-500">
                  Aguarde enquanto os synths avaliam a feature...
                </p>
              </div>
            ) : analysis.status === 'failed' ? (
              <div className="bg-white rounded-xl border border-red-200 p-12 text-center">
                <AlertTriangle className="w-12 h-12 text-red-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-red-700 mb-2">
                  Análise falhou
                </h3>
                <p className="text-slate-500 mb-6">
                  Ocorreu um erro durante a execução. Tente novamente.
                </p>
                <Button
                  variant="outline"
                  onClick={handleRunAnalysis}
                  disabled={runAnalysisMutation.isPending}
                >
                  {runAnalysisMutation.isPending ? (
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  ) : null}
                  Tentar Novamente
                </Button>
              </div>
            ) : (
              <AnalysisPhaseTabs
                simulationId={analysis.simulation_id}
                hasAnalysis={true}
                actions={id ? <ViewSummaryButton experimentId={id} /> : null}
                renderPhase={(phaseId) => {
                  const expId = id ?? '';
                  switch (phaseId as AnalysisPhaseId) {
                    case 'visao-geral':
                      return <PhaseOverview experimentId={expId} analysis={analysis} />;
                    case 'localizacao':
                      return <PhaseLocation experimentId={expId} />;
                    case 'segmentacao':
                      return <PhaseSegmentation experimentId={expId} />;
                    case 'casos-especiais':
                      return <PhaseEdgeCases experimentId={expId} />;
                    default:
                      return null;
                  }
                }}
              />
            )}
          </TabsContent>

          {/* Interviews Content */}
          <TabsContent value="interviews" className="mt-0">
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm">
              {/* Header with action */}
              <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-slate-100 rounded-lg">
                    <MessageSquare className="w-5 h-5 text-slate-600" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-slate-900">Entrevistas</h3>
                    <p className="text-sm text-slate-500">
                      {experiment.interview_count} entrevista(s) realizada(s)
                    </p>
                  </div>
                </div>
                {experiment.has_interview_guide ? (
                  <Button
                    size="sm"
                    onClick={() => setIsNewInterviewOpen(true)}
                    className="btn-primary"
                  >
                    <Plus className="w-4 h-4 mr-1" />
                    Nova Entrevista
                  </Button>
                ) : (
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <span>
                        <Button size="sm" disabled className="opacity-50">
                          <Plus className="w-4 h-4 mr-1" />
                          Nova Entrevista
                        </Button>
                      </span>
                    </TooltipTrigger>
                    <TooltipContent>
                      <p className="flex items-center gap-1.5">
                        <Info className="h-3.5 w-3.5" />
                        Guia de entrevista indisponível
                      </p>
                    </TooltipContent>
                  </Tooltip>
                )}
              </div>

              {/* Content */}
              <div className="p-6">
                {experiment.interview_count === 0 ? (
                  <div className="text-center py-8">
                    <MessageSquare className="w-10 h-10 text-slate-300 mx-auto mb-3" />
                    <p className="text-slate-500">
                      Nenhuma entrevista realizada ainda.
                    </p>
                    <p className="text-sm text-slate-400 mt-1">
                      Clique em "Nova Entrevista" para começar.
                    </p>
                  </div>
                ) : (
                  <>
                    {/* Cards */}
                    <div className="space-y-3">
                      {(() => {
                        const sorted = [...experiment.interviews].sort(
                          (a, b) => new Date(b.started_at).getTime() - new Date(a.started_at).getTime()
                        );
                        const paged = sorted.slice(
                          interviewPage * INTERVIEWS_PER_PAGE,
                          (interviewPage + 1) * INTERVIEWS_PER_PAGE
                        );
                        return paged.map((interview) => {
                          const contextPreview = interview.additional_context
                            ? interview.additional_context.length > 80
                              ? `${interview.additional_context.slice(0, 80)}…`
                              : interview.additional_context
                            : null;
                          return (
                            <div
                              key={interview.exec_id}
                              onClick={() => navigate(`/experiments/${id}/interviews/${interview.exec_id}`)}
                              className="flex items-center gap-4 p-4 rounded-lg border bg-white transition-all hover:shadow-md hover:border-slate-300 cursor-pointer"
                            >
                              {/* Icon */}
                              <div className="flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center bg-slate-100">
                                <MessageSquare className="h-5 w-5 text-slate-600" />
                              </div>

                              {/* Main Content */}
                              <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-2 mb-1">
                                  <span className="text-sm font-medium text-slate-700">
                                    {formatDistanceToNow(new Date(interview.started_at), {
                                      addSuffix: true,
                                      locale: ptBR,
                                    })}
                                  </span>
                                  {interview.has_summary && (
                                    <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-medium bg-emerald-50 text-emerald-700 border border-emerald-200/60">
                                      Summary
                                    </span>
                                  )}
                                  {interview.has_prfaq && (
                                    <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-medium bg-sky-50 text-sky-700 border border-sky-200/60">
                                      PR/FAQ
                                    </span>
                                  )}
                                </div>

                                <div className="flex items-center gap-4 text-sm text-muted-foreground">
                                  <span className="flex items-center gap-1">
                                    <Users className="h-3.5 w-3.5" />
                                    {interview.synth_count} synths
                                  </span>
                                  <span className="flex items-center gap-1">
                                    <MessageCircle className="h-3.5 w-3.5" />
                                    {interview.total_turns} turnos
                                  </span>
                                </div>

                                {contextPreview && (
                                  <p className="text-xs text-slate-400 mt-1 truncate">
                                    {contextPreview}
                                  </p>
                                )}
                              </div>

                              {/* Arrow */}
                              <ChevronRight className="h-5 w-5 text-slate-400 flex-shrink-0" />
                            </div>
                          );
                        });
                      })()}
                    </div>

                    {/* Pagination */}
                    {experiment.interviews.length > INTERVIEWS_PER_PAGE && (
                      <div className="flex items-center justify-between pt-4 mt-4 border-t border-slate-100">
                        <span className="text-sm text-slate-500">
                          {interviewPage * INTERVIEWS_PER_PAGE + 1}–{Math.min((interviewPage + 1) * INTERVIEWS_PER_PAGE, experiment.interviews.length)} de {experiment.interviews.length}
                        </span>
                        <div className="flex items-center gap-1">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => setInterviewPage(p => Math.max(0, p - 1))}
                            disabled={interviewPage === 0}
                          >
                            <ChevronLeft className="w-4 h-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => setInterviewPage(p => Math.min(Math.ceil(experiment.interviews.length / INTERVIEWS_PER_PAGE) - 1, p + 1))}
                            disabled={interviewPage >= Math.ceil(experiment.interviews.length / INTERVIEWS_PER_PAGE) - 1}
                          >
                            <ChevronRight className="w-4 h-4" />
                          </Button>
                        </div>
                      </div>
                    )}
                  </>
                )}
              </div>
            </div>
          </TabsContent>

          {/* Explorations Content */}
          <TabsContent value="explorations" className="mt-0">
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm">
              {/* Header with action */}
              <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-slate-100 rounded-lg">
                    <Network className="w-5 h-5 text-slate-600" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-slate-900">Explorações de Cenários</h3>
                    <p className="text-sm text-slate-500">
                      {explorations?.length || 0} exploração(ões)
                      {hasRunningExploration && ' • 1 em execução'}
                    </p>
                  </div>
                </div>

                {isExplorationButtonDisabled && !hasRunningExploration ? (
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <span>
                        <Button size="sm" disabled className="opacity-50">
                          <Plus className="mr-2 h-4 w-4" />
                          Iniciar Exploração
                        </Button>
                      </span>
                    </TooltipTrigger>
                    <TooltipContent>
                      <p className="flex items-center gap-1.5">
                        <Info className="h-3.5 w-3.5" />
                        Execute uma análise primeiro
                      </p>
                    </TooltipContent>
                  </Tooltip>
                ) : hasRunningExploration ? (
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <span>
                        <Button size="sm" disabled className="opacity-50">
                          <Plus className="mr-2 h-4 w-4" />
                          Iniciar Exploração
                        </Button>
                      </span>
                    </TooltipTrigger>
                    <TooltipContent>
                      <p className="flex items-center gap-1.5">
                        <Info className="h-3.5 w-3.5" />
                        Aguarde a exploração atual terminar
                      </p>
                    </TooltipContent>
                  </Tooltip>
                ) : (
                  <Button
                    size="sm"
                    onClick={() => setIsNewExplorationOpen(true)}
                    className="btn-primary"
                  >
                    <Plus className="mr-2 h-4 w-4" />
                    Iniciar Exploração
                  </Button>
                )}
              </div>

              {/* Content */}
              <div className="p-6">
                <ExplorationList
                  explorations={explorations}
                  experimentId={id ?? ''}
                  isLoading={isLoadingExplorations}
                />
              </div>
            </div>
          </TabsContent>

          {/* Materials Content */}
          <TabsContent value="materials" className="mt-0">
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm">
              {/* Header */}
              <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-slate-100 rounded-lg">
                    <Paperclip className="w-5 h-5 text-slate-600" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-slate-900">Materiais</h3>
                    <p className="text-sm text-slate-500">
                      {materials?.materials?.length ?? 0} arquivo(s) anexado(s)
                    </p>
                  </div>
                </div>
              </div>

              {/* Content */}
              <div className="p-6 space-y-6">
                {/* Gallery - Show existing materials */}
                <MaterialGallery experimentId={id ?? ''} />

                {/* Upload - Add new materials */}
                <div className="pt-6 border-t border-slate-100">
                  <MaterialUpload
                    experimentId={id ?? ''}
                    onUploadComplete={() => refetchMaterials()}
                  />
                </div>
              </div>
            </div>
          </TabsContent>

          {/* Reports Content */}
          <TabsContent value="reports" className="mt-0">
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm">
              {/* Header */}
              <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-slate-100 rounded-lg">
                    <FileText className="w-5 h-5 text-slate-600" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-slate-900">Relatórios</h3>
                    <p className="text-sm text-slate-500">
                      Documentos gerados a partir de análises e explorações
                    </p>
                  </div>
                </div>
              </div>

              {/* Content */}
              <div className="p-6">
                <DocumentsList experimentId={id ?? ''} />
              </div>
            </div>
          </TabsContent>
        </Tabs>

        {/* Delete Section */}
        <div className="mt-8 pt-6 border-t border-slate-200">
          <Button
            variant="outline"
            onClick={() => setIsDeleteDialogOpen(true)}
            className="text-red-600 border-red-300 hover:bg-red-50 hover:text-red-700 hover:border-red-400"
          >
            <Trash2 className="w-4 h-4 mr-2" />
            Deletar
          </Button>
        </div>
      </main>

      {/* New Interview Modal */}
      <NewInterviewFromExperimentDialog
        open={isNewInterviewOpen}
        onOpenChange={setIsNewInterviewOpen}
        experimentId={id ?? ''}
      />

      {/* New Exploration Dialog */}
      <NewExplorationDialog
        open={isNewExplorationOpen}
        onOpenChange={setIsNewExplorationOpen}
        experimentId={id ?? ''}
        baselineSuccessRate={analysis?.aggregated_outcomes?.success_rate}
        onSuccess={handleExplorationSuccess}
      />

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={isDeleteDialogOpen} onOpenChange={setIsDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Excluir experimento?</AlertDialogTitle>
            <AlertDialogDescription>
              Esta ação não pode ser desfeita. O experimento "{experiment?.name}" será
              permanentemente removido da listagem.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              disabled={deleteMutation.isPending}
              className="bg-red-600 hover:bg-red-700 focus:ring-red-600"
            >
              {deleteMutation.isPending ? (
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <Trash2 className="w-4 h-4 mr-2" />
              )}
              Excluir
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
