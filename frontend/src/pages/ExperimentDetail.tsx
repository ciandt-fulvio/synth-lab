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
import { useExperiment } from '@/hooks/use-experiments';
import { NewInterviewFromExperimentDialog } from '@/components/experiments/NewInterviewFromExperimentDialog';
import { AnalysisPhaseTabs } from '@/components/experiments/AnalysisPhaseTabs';
import {
  ChevronDown,
  ChevronUp,
  MessageSquare,
  Plus,
  FlaskConical,
  Loader2,
  TrendingUp,
  Users,
  AlertTriangle,
  Lightbulb,
  BarChart3,
  Target,
} from 'lucide-react';
import { SynthLabHeader } from '@/components/shared/SynthLabHeader';
import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';

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
// Analysis Section Components
// =============================================================================

interface AnalysisSectionProps {
  icon: React.ReactNode;
  title: string;
  children: React.ReactNode;
  delay?: number;
}

function AnalysisSection({ icon, title, children, delay = 0 }: AnalysisSectionProps) {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setIsVisible(true), delay);
    return () => clearTimeout(timer);
  }, [delay]);

  return (
    <div
      className={`bg-white rounded-xl border border-slate-200 p-6 transition-all duration-500 ${
        isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
      }`}
    >
      <div className="flex items-center gap-3 mb-4">
        <div className="p-2 rounded-lg bg-slate-100 text-slate-600">
          {icon}
        </div>
        <h3 className="text-lg font-semibold text-slate-800">{title}</h3>
      </div>
      {children}
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

  // Analysis data (mock for visualization - will be replaced with real data)
  const analysis = experiment.analysis;
  const hasAnalysis = analysis && analysis.status === 'completed';

  // Outcome distribution for pie chart
  const outcomeData = hasAnalysis && analysis.aggregated_outcomes
    ? [
        { name: 'Sucesso', value: analysis.aggregated_outcomes.success_rate * 100, color: '#22c55e' },
        { name: 'Falhou', value: analysis.aggregated_outcomes.failed_rate * 100, color: '#ef4444' },
        { name: 'Não tentou', value: analysis.aggregated_outcomes.did_not_try_rate * 100, color: '#94a3b8' },
      ]
    : [];

  // Segment data (mock - would come from API)
  const segmentData = [
    { segment: 'Tech-savvy', success: 78, failed: 15, notTried: 7 },
    { segment: 'Casual', success: 52, failed: 28, notTried: 20 },
    { segment: 'Beginner', success: 35, failed: 40, notTried: 25 },
    { segment: 'Power User', success: 85, failed: 10, notTried: 5 },
  ];

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
              <Button
                size="sm"
                variant="ghost"
                onClick={() => setIsNewInterviewOpen(true)}
                className="btn-ghost text-indigo-600"
              >
                <Plus className="w-4 h-4 mr-1" />
                Nova Entrevista
              </Button>
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
          // No analysis yet - Show analysis phases with tabs
          <AnalysisPhaseTabs />
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
            <Button variant="outline">
              Tentar Novamente
            </Button>
          </div>
        ) : (
          // Analysis completed - Show full report
          <div className="space-y-6">
            {/* Section 1: Overview */}
            <AnalysisSection
              icon={<TrendingUp className="w-5 h-5" />}
              title="Visão Geral"
              delay={0}
            >
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* Success Rate - Big Number */}
                <div className="col-span-1 flex flex-col items-center justify-center p-6 bg-gradient-to-br from-green-50 to-emerald-50 rounded-xl">
                  <span className="text-5xl font-bold text-green-600">
                    {Math.round((analysis.aggregated_outcomes?.success_rate ?? 0) * 100)}%
                  </span>
                  <span className="text-sm font-medium text-green-700 mt-2">
                    Taxa de Sucesso
                  </span>
                </div>

                {/* Outcome Distribution Pie */}
                <div className="col-span-2">
                  <ResponsiveContainer width="100%" height={200}>
                    <PieChart>
                      <Pie
                        data={outcomeData}
                        cx="50%"
                        cy="50%"
                        innerRadius={50}
                        outerRadius={80}
                        paddingAngle={2}
                        dataKey="value"
                        animationBegin={200}
                        animationDuration={800}
                      >
                        {outcomeData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip
                        formatter={(value: number) => `${value.toFixed(1)}%`}
                        contentStyle={{
                          borderRadius: '8px',
                          border: '1px solid #e2e8f0',
                          boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
                        }}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                  <div className="flex justify-center gap-6 mt-2">
                    {outcomeData.map((item) => (
                      <div key={item.name} className="flex items-center gap-2">
                        <div
                          className="w-3 h-3 rounded-full"
                          style={{ backgroundColor: item.color }}
                        />
                        <span className="text-sm text-slate-600">{item.name}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </AnalysisSection>

            {/* Section 2: Distribution / Location */}
            <AnalysisSection
              icon={<BarChart3 className="w-5 h-5" />}
              title="Localização dos Resultados"
              delay={150}
            >
              <p className="text-slate-600 mb-4">
                Distribuição dos resultados por diferentes dimensões de análise.
              </p>
              <div className="bg-slate-50 rounded-lg p-4">
                <ResponsiveContainer width="100%" height={250}>
                  <BarChart data={segmentData} layout="vertical">
                    <XAxis type="number" domain={[0, 100]} />
                    <YAxis type="category" dataKey="segment" width={100} />
                    <Tooltip
                      contentStyle={{
                        borderRadius: '8px',
                        border: '1px solid #e2e8f0',
                      }}
                    />
                    <Bar dataKey="success" stackId="a" fill="#22c55e" name="Sucesso" animationDuration={800} />
                    <Bar dataKey="failed" stackId="a" fill="#ef4444" name="Falhou" animationDuration={800} />
                    <Bar dataKey="notTried" stackId="a" fill="#94a3b8" name="Não tentou" animationDuration={800} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </AnalysisSection>

            {/* Section 3: Segmentation */}
            <AnalysisSection
              icon={<Users className="w-5 h-5" />}
              title="Segmentação"
              delay={300}
            >
              <p className="text-slate-600 mb-4">
                Análise de performance por perfil de usuário.
              </p>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {segmentData.map((seg, i) => (
                  <div
                    key={seg.segment}
                    className="bg-slate-50 rounded-lg p-4 text-center"
                    style={{ animationDelay: `${i * 100}ms` }}
                  >
                    <div className="text-2xl font-bold text-slate-800">
                      {seg.success}%
                    </div>
                    <div className="text-sm text-slate-500 mt-1">
                      {seg.segment}
                    </div>
                    <div className="w-full bg-slate-200 rounded-full h-1.5 mt-2">
                      <div
                        className="bg-green-500 h-1.5 rounded-full transition-all duration-1000"
                        style={{ width: `${seg.success}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </AnalysisSection>

            {/* Section 4: Edge Cases */}
            <AnalysisSection
              icon={<AlertTriangle className="w-5 h-5" />}
              title="Casos Especiais"
              delay={450}
            >
              <div className="space-y-3">
                <div className="flex items-start gap-3 p-3 bg-amber-50 border border-amber-200 rounded-lg">
                  <AlertTriangle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="text-sm font-medium text-amber-800">
                      Usuários iniciantes com dificuldade
                    </p>
                    <p className="text-sm text-amber-700 mt-1">
                      40% dos iniciantes falharam na primeira tentativa. Considere melhorar o onboarding.
                    </p>
                  </div>
                </div>
                <div className="flex items-start gap-3 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                  <Target className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="text-sm font-medium text-blue-800">
                      Power Users excelentes
                    </p>
                    <p className="text-sm text-blue-700 mt-1">
                      85% de sucesso entre power users. Funcionalidade bem alinhada com usuários avançados.
                    </p>
                  </div>
                </div>
              </div>
            </AnalysisSection>

            {/* Section 5: Deep Dive */}
            <AnalysisSection
              icon={<FlaskConical className="w-5 h-5" />}
              title="Explicação Profunda"
              delay={600}
            >
              <div className="prose prose-slate max-w-none">
                <p className="text-slate-600 leading-relaxed">
                  A análise revela uma correlação significativa entre a <strong>complexidade percebida</strong> e
                  a taxa de sucesso. Usuários que consideraram a feature "simples" tiveram 3x mais chances
                  de completar a tarefa com sucesso.
                </p>
                <p className="text-slate-600 leading-relaxed mt-3">
                  O principal ponto de fricção identificado foi o <strong>tempo para primeiro valor</strong>.
                  Usuários que não perceberam benefício nos primeiros 30 segundos apresentaram taxa de
                  abandono 2.5x maior que a média.
                </p>
              </div>
            </AnalysisSection>

            {/* Section 6: LLM Insights */}
            <AnalysisSection
              icon={<Lightbulb className="w-5 h-5" />}
              title="Insights & Recomendações"
              delay={750}
            >
              <div className="space-y-4">
                <div className="p-4 bg-gradient-to-r from-violet-50 to-purple-50 border border-violet-200 rounded-lg">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-xs font-medium text-violet-700 bg-violet-100 px-2 py-0.5 rounded">
                      Recomendação Principal
                    </span>
                  </div>
                  <p className="text-slate-700">
                    Simplificar o fluxo inicial removendo 2 passos opcionais pode aumentar a
                    taxa de sucesso em aproximadamente 15-20% baseado nos padrões identificados.
                  </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="p-4 bg-slate-50 rounded-lg">
                    <h4 className="font-medium text-slate-800 mb-2">O que funcionou</h4>
                    <ul className="text-sm text-slate-600 space-y-1">
                      <li>• Interface limpa e focada</li>
                      <li>• Feedback imediato de progresso</li>
                      <li>• Linguagem acessível</li>
                    </ul>
                  </div>
                  <div className="p-4 bg-slate-50 rounded-lg">
                    <h4 className="font-medium text-slate-800 mb-2">Oportunidades</h4>
                    <ul className="text-sm text-slate-600 space-y-1">
                      <li>• Reduzir passos obrigatórios</li>
                      <li>• Adicionar exemplos práticos</li>
                      <li>• Melhorar mensagens de erro</li>
                    </ul>
                  </div>
                </div>
              </div>
            </AnalysisSection>
          </div>
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
