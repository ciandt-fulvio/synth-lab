/**
 * ExperimentDetail page - Research Observatory Design.
 *
 * Structured as: Header (read-only) → Interviews (collapsible) → Analysis Report
 * Analysis follows narrative: Overview → Distribution → Segmentation → Edge Cases → Deep Dive → Insights
 *
 * References:
 *   - Spec: specs/019-experiment-refactor/spec.md
 */

import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { useExperiment, useRunAnalysis } from '@/hooks/use-experiments';
import { NewInterviewFromExperimentDialog } from '@/components/experiments/NewInterviewFromExperimentDialog';
import { AnalysisPhaseTabs, type AnalysisPhaseId } from '@/components/experiments/AnalysisPhaseTabs';
import {
  PhaseOverview,
  PhaseLocation,
  PhaseSegmentation,
  PhaseEdgeCases,
  PhaseExplainability,
  PhaseInsights,
} from '@/components/experiments/results';
import {
  ChevronDown,
  ChevronUp,
  MessageSquare,
  Plus,
  FlaskConical,
  Loader2,
  AlertTriangle,
  ArrowLeft,
} from 'lucide-react';
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

export default function ExperimentDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [isInterviewsOpen, setIsInterviewsOpen] = useState(false);
  const [isNewInterviewOpen, setIsNewInterviewOpen] = useState(false);

  const { data: experiment, isLoading, isError, error } = useExperiment(id ?? '');
  const runAnalysisMutation = useRunAnalysis();

  const handleRunAnalysis = () => {
    if (!id) return;
    runAnalysisMutation.mutate({ experimentId: id });
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
                  color="#8b5cf6"
                  delay={0}
                />
                <ScoreSlider
                  label="Esforço Inicial"
                  value={scorecard.initial_effort.score}
                  color="#f59e0b"
                  delay={100}
                />
                <ScoreSlider
                  label="Risco Percebido"
                  value={scorecard.perceived_risk.score}
                  color="#ef4444"
                  delay={200}
                />
                <ScoreSlider
                  label="Tempo p/ Valor"
                  value={scorecard.time_to_value.score}
                  color="#22c55e"
                  delay={300}
                />
              </div>
            )}
          </div>
        </div>

        {/* Interviews Section - Collapsible */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden mb-6">
          <Collapsible open={isInterviewsOpen} onOpenChange={setIsInterviewsOpen}>
            <div className="flex items-center justify-between px-5 py-4 border-b border-slate-100">
              <CollapsibleTrigger asChild>
                <button className="flex items-center gap-2 text-sm text-slate-600 hover:text-slate-900 transition-colors">
                  <div className="p-1.5 bg-slate-100 rounded-lg">
                    <MessageSquare className="w-4 h-4 text-slate-600" />
                  </div>
                  <span className="font-semibold text-slate-900">Entrevistas</span>
                  <Badge variant="secondary" className="text-xs bg-green-100 text-green-700 border-green-200">
                    {experiment.interview_count}
                  </Badge>
                  {isInterviewsOpen ? (
                    <ChevronUp className="w-4 h-4 text-slate-400" />
                  ) : (
                    <ChevronDown className="w-4 h-4 text-slate-400" />
                  )}
                </button>
              </CollapsibleTrigger>
              {experiment.has_interview_guide ? (
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => setIsNewInterviewOpen(true)}
                  className="btn-ghost text-indigo-600"
                >
                  <Plus className="w-4 h-4 mr-1" />
                  Nova Entrevista
                </Button>
              ) : (
                <span
                  className="inline-flex items-center gap-1 text-xs text-slate-400 cursor-not-allowed"
                  title="Guia de entrevista indisponível"
                >
                  <Plus className="w-4 h-4" />
                  Nova Entrevista
                </span>
              )}
            </div>

            <CollapsibleContent>
              <div className="px-5 py-4">
                {experiment.interview_count === 0 ? (
                  <p className="text-sm text-slate-500">
                    Nenhuma entrevista realizada ainda.
                  </p>
                ) : (
                  <div className="flex flex-wrap gap-2">
                    {experiment.interviews.map((interview) => (
                      <button
                        key={interview.exec_id}
                        onClick={() => navigate(`/experiments/${id}/interviews/${interview.exec_id}`)}
                        className="inline-flex items-center gap-2 px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm hover:bg-white hover:border-purple-200 hover:shadow-sm transition-all"
                      >
                        <span className="font-medium text-slate-700">
                          {interview.topic_name}
                        </span>
                        <span className="text-slate-400">
                          {interview.synth_count} synths
                        </span>
                        {interview.has_summary && (
                          <Badge variant="outline" className="text-xs py-0 border-green-200 text-green-600">
                            Resumo
                          </Badge>
                        )}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </CollapsibleContent>
          </Collapsible>
        </div>

        {/* Analysis Report Section */}
        {!hasScorecard ? (
          // No scorecard configured
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
          // No analysis yet - Show analysis phases with run button
          <AnalysisPhaseTabs
            onRunAnalysis={handleRunAnalysis}
            isLoading={runAnalysisMutation.isPending}
          />
        ) : analysis.status === 'running' ? (
          // Analysis running
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
          // Analysis failed
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
          // Analysis completed - Show phase tabs with real data
          <AnalysisPhaseTabs
            simulationId={analysis.simulation_id}
            hasAnalysis={true}
            renderPhase={(phaseId) => {
              const expId = id ?? '';
              const simId = analysis.simulation_id;
              switch (phaseId as AnalysisPhaseId) {
                case 'visao-geral':
                  // Uses experiment ID for new analysis chart endpoints
                  return <PhaseOverview experimentId={expId} analysis={analysis} />;
                case 'localizacao':
                  return <PhaseLocation simulationId={simId} />;
                case 'segmentacao':
                  return <PhaseSegmentation simulationId={simId} />;
                case 'casos-especiais':
                  return <PhaseEdgeCases simulationId={simId} />;
                case 'aprofundamento':
                  return <PhaseExplainability simulationId={simId} />;
                case 'insights':
                  return <PhaseInsights simulationId={simId} />;
                default:
                  return null;
              }
            }}
          />
        )}
      </main>

      {/* New Interview Modal */}
      <NewInterviewFromExperimentDialog
        open={isNewInterviewOpen}
        onOpenChange={setIsNewInterviewOpen}
        experimentId={id ?? ''}
      />
    </div>
  );
}
