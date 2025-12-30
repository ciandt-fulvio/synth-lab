/**
 * AnalysisPhaseTabs - Tab-based navigation for analysis phases.
 *
 * Design: "Analysis Journey" - emphasizes the sequential narrative flow
 * from broad overview to actionable insights.
 *
 * Each phase represents a step in the research investigation:
 * Overview → Influência → Segmentation → Edge Cases → Insights
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import {
  TrendingUp,
  PieChart,
  Users,
  UserCheck,
  ChevronRight,
  Play,
  FlaskConical,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

export interface AnalysisPhase {
  id: string;
  title: string;
  shortTitle: string;
  icon: React.ReactNode;
  question: string;
  description: string;
}

export type AnalysisPhaseId =
  | 'visao-geral'
  | 'localizacao'
  | 'segmentacao'
  | 'casos-especiais';

export const ANALYSIS_PHASES: AnalysisPhase[] = [
  {
    id: 'visao-geral',
    title: 'Visão Geral',
    shortTitle: 'Geral',
    icon: <PieChart className="w-4 h-4" />,
    question: 'O que aconteceu?',
    description:
      'Panorama completo dos resultados: taxa de sucesso, falha e desistência. Identifica se o problema está na adoção ou na execução.',
  },
  {
    id: 'localizacao',
    title: 'Influência',
    shortTitle: 'Influência',
    icon: <TrendingUp className="w-4 h-4" />,
    question: 'Quais características dos usuários mais influenciam o resultado?',
    description:
      'Analisa correlações entre atributos dos synths e taxas de sucesso ou falha. Revela quais características importam mais para prever comportamento.',
  },
  {
    id: 'segmentacao',
    title: 'Segmentação',
    shortTitle: 'Segmentos',
    icon: <Users className="w-4 h-4" />,
    question: 'Que tipos de usuários seguem comportamentos distintos?',
    description:
      'Agrupa usuários por padrões de comportamento. Identifica perfis que performam melhor ou pior.',
  },
  {
    id: 'casos-especiais',
    title: 'Casos Especiais',
    shortTitle: 'Especiais',
    icon: <UserCheck className="w-4 h-4" />,
    question: 'Quem devemos entrevistar primeiro?',
    description:
      'Destaca outliers e casos extremos. Prioriza synths para entrevistas qualitativas aprofundadas.',
  },
];

interface AnalysisPhaseTabsProps {
  simulationId?: string;
  hasAnalysis?: boolean;
  onRunAnalysis?: () => void;
  isLoading?: boolean;
  children?: React.ReactNode;
  /** Render function for each phase */
  renderPhase?: (phaseId: string) => React.ReactNode;
  /** Optional action buttons to render in header */
  actions?: React.ReactNode;
}

export function AnalysisPhaseTabs({
  simulationId,
  hasAnalysis = false,
  onRunAnalysis,
  isLoading = false,
  children,
  renderPhase,
  actions,
}: AnalysisPhaseTabsProps) {
  const [activePhase, setActivePhase] = useState<string>('visao-geral');
  const containerRef = useRef<HTMLDivElement>(null);

  // Scroll to top of container when changing phase
  const scrollToContainer = useCallback(() => {
    if (containerRef.current) {
      containerRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }, []);

  // Keyboard navigation (←/→)
  const handleKeyDown = useCallback((event: KeyboardEvent) => {
    const currentIndex = ANALYSIS_PHASES.findIndex((p) => p.id === activePhase);

    if (event.key === 'ArrowRight') {
      event.preventDefault();
      const nextIndex = Math.min(ANALYSIS_PHASES.length - 1, currentIndex + 1);
      if (nextIndex !== currentIndex) {
        setActivePhase(ANALYSIS_PHASES[nextIndex].id);
        scrollToContainer();
      }
    } else if (event.key === 'ArrowLeft') {
      event.preventDefault();
      const prevIndex = Math.max(0, currentIndex - 1);
      if (prevIndex !== currentIndex) {
        setActivePhase(ANALYSIS_PHASES[prevIndex].id);
        scrollToContainer();
      }
    }
  }, [activePhase, scrollToContainer]);

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  const currentPhase = ANALYSIS_PHASES.find((p) => p.id === activePhase);
  const currentIndex = ANALYSIS_PHASES.findIndex((p) => p.id === activePhase);

  return (
    <div ref={containerRef} className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 border-b border-slate-100 bg-gradient-to-r from-slate-50 to-white">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-gradient-to-br from-violet-500 to-indigo-600 rounded-xl text-white shadow-lg shadow-violet-200/50">
              <PieChart className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-slate-900">
                Análise Quantitativa
              </h3>
              <p className="text-xs text-slate-500">
                4 fases de investigação
              </p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            {actions}
            <div className="text-xs text-slate-400 font-medium tracking-wider uppercase">
              Fase {currentIndex + 1} de 4
            </div>
          </div>
        </div>
      </div>

      {/* Tab Navigation - Horizontal Steps */}
      <div className="relative px-4 py-3 bg-slate-50/50 border-b border-slate-100">
        {/* Progress Line - spans from first to last icon (left-8 to right-8 = 64px total padding) */}
        <div className="absolute top-1/2 left-8 right-8 h-0.5 bg-slate-200 -translate-y-1/2 z-0" />
        <div
          className="absolute top-1/2 left-8 h-0.5 bg-gradient-to-r from-violet-500 to-indigo-500 -translate-y-1/2 z-0 transition-all duration-500"
          style={{
            width: currentIndex === 0
              ? '0px'
              : `calc(${(currentIndex / (ANALYSIS_PHASES.length - 1)) * 100}% - ${64 * (currentIndex / (ANALYSIS_PHASES.length - 1))}px)`
          }}
        />

        {/* Tab Buttons */}
        <div className="relative z-10 flex items-center justify-between">
          {ANALYSIS_PHASES.map((phase, index) => {
            const isActive = phase.id === activePhase;
            const isPast = index < currentIndex;
            const isFuture = index > currentIndex;

            return (
              <button
                key={phase.id}
                onClick={() => setActivePhase(phase.id)}
                className={cn(
                  'group flex flex-col items-center gap-1.5 transition-all duration-200',
                  'focus:outline-none focus-visible:ring-2 focus-visible:ring-violet-500 focus-visible:ring-offset-2 rounded-lg p-1'
                )}
              >
                {/* Icon Circle */}
                <div
                  className={cn(
                    'w-10 h-10 rounded-full flex items-center justify-center transition-all duration-300',
                    'border-2 shadow-sm',
                    isActive && 'bg-gradient-to-br from-violet-500 to-indigo-600 border-violet-500 text-white shadow-lg shadow-violet-200/50 scale-110',
                    isPast && 'bg-violet-100 border-violet-300 text-violet-600',
                    isFuture && 'bg-white border-slate-200 text-slate-400 group-hover:border-slate-300 group-hover:text-slate-500'
                  )}
                >
                  {phase.icon}
                </div>

                {/* Label */}
                <span
                  className={cn(
                    'text-xs font-medium transition-colors duration-200 max-w-[60px] text-center leading-tight',
                    isActive && 'text-violet-700',
                    isPast && 'text-violet-600',
                    isFuture && 'text-slate-400 group-hover:text-slate-500'
                  )}
                >
                  {phase.shortTitle}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Content Area */}
      <div className="p-6">
        {currentPhase && (
          <div className="space-y-4">
            {/* Phase Title & Question */}
            <div className="flex items-start gap-4">
              <div
                className={cn(
                  'p-3 rounded-xl bg-gradient-to-br from-violet-50 to-indigo-50',
                  'border border-violet-100'
                )}
              >
                <div className="text-violet-600">{currentPhase.icon}</div>
              </div>
              <div className="flex-1 min-w-0">
                <h4 className="text-lg font-semibold text-slate-900 mb-1">
                  {currentPhase.title}
                </h4>
                <p className="text-violet-600 font-medium italic">
                  "{currentPhase.question}"
                </p>
              </div>
            </div>

            {/* Description */}
            <p className="text-slate-600 leading-relaxed pl-16">
              {currentPhase.description}
            </p>

            {/* Phase Content or Empty State */}
            {hasAnalysis && renderPhase ? (
              <div className="mt-6">
                {renderPhase(activePhase)}
              </div>
            ) : (
              <div className="mt-6 p-8 rounded-xl border-2 border-dashed border-slate-200 bg-slate-50/50 text-center">
                <div className="w-12 h-12 rounded-full bg-slate-100 flex items-center justify-center mx-auto mb-3">
                  <FlaskConical className="w-6 h-6 text-slate-400" />
                </div>
                <p className="text-slate-500 text-sm mb-1">
                  Aguardando execução da análise
                </p>
                <p className="text-slate-400 text-xs">
                  Os resultados desta fase aparecerão aqui após executar a análise
                </p>
              </div>
            )}

            {/* Navigation Arrows */}
            <div className="flex items-center justify-between pt-4 border-t border-slate-100 mt-6">
              <button
                onClick={() => {
                  const prevIndex = Math.max(0, currentIndex - 1);
                  if (prevIndex !== currentIndex) {
                    setActivePhase(ANALYSIS_PHASES[prevIndex].id);
                    scrollToContainer();
                  }
                }}
                disabled={currentIndex === 0}
                className={cn(
                  'flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                  currentIndex === 0
                    ? 'text-slate-300 cursor-not-allowed'
                    : 'text-slate-600 hover:text-violet-600 hover:bg-violet-50'
                )}
              >
                <ChevronRight className="w-4 h-4 rotate-180" />
                Anterior
              </button>

              <button
                onClick={() => {
                  const nextIndex = Math.min(ANALYSIS_PHASES.length - 1, currentIndex + 1);
                  if (nextIndex !== currentIndex) {
                    setActivePhase(ANALYSIS_PHASES[nextIndex].id);
                    scrollToContainer();
                  }
                }}
                disabled={currentIndex === ANALYSIS_PHASES.length - 1}
                className={cn(
                  'flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                  currentIndex === ANALYSIS_PHASES.length - 1
                    ? 'text-slate-300 cursor-not-allowed'
                    : 'text-slate-600 hover:text-violet-600 hover:bg-violet-50'
                )}
              >
                Próxima
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Footer - Run Analysis CTA (only when no analysis) */}
      {!hasAnalysis && onRunAnalysis && (
        <div className="px-6 py-4 bg-gradient-to-r from-slate-50 to-violet-50/30 border-t border-slate-100">
          <Button
            onClick={onRunAnalysis}
            disabled={isLoading}
            className="w-full btn-primary"
          >
            <Play className="w-4 h-4 mr-2" />
            {isLoading ? 'Executando...' : 'Executar Análise Completa'}
          </Button>
        </div>
      )}
    </div>
  );
}

export default AnalysisPhaseTabs;
