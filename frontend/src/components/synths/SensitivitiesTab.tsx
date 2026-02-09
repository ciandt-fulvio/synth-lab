// src/components/synths/SensitivitiesTab.tsx
//
// Editorial-quality sensitivities visualization tab for SynthDetailDialog.
// Inspired by data journalism aesthetics (The Economist, FiveThirtyEight).
//
// Design: Museum-quality data presentation with refined typography,
// generous whitespace, and surgical color accents.

import { HelpCircle } from 'lucide-react';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { cn } from '@/lib/utils';

interface SensitivityData {
  key: string;
  name: string;
  value: number;
  groupAverage: number;
  description: string;
}

interface SensitivitiesTabProps {
  sensitivities: Record<string, number>;
  groupAverages?: Record<string, number>;
}

const SENSITIVITY_METADATA: Record<string, { name: string; description: string }> = {
  risk_aversion: {
    name: 'Aversão a Risco',
    description: 'Sensibilidade a ações irreversíveis. Valores altos indicam maior cautela em decisões com consequências permanentes.',
  },
  social_dependency: {
    name: 'Dependência Social',
    description: 'Importância da validação social. Valores altos indicam maior influência do comportamento de outros na tomada de decisão.',
  },
  institutional_trust_level: {
    name: 'Confiança Institucional',
    description: 'Nível de confiança em instituições. Valores altos indicam maior propensão a confiar em autoridades e sistemas estabelecidos.',
  },
  habit_plasticity: {
    name: 'Plasticidade de Hábitos',
    description: 'Facilidade em mudar rotinas. Valores altos indicam maior adaptabilidade e flexibilidade comportamental.',
  },
  friction_tolerance: {
    name: 'Tolerância a Fricção',
    description: 'Tolerância a processos complexos. Valores altos indicam maior paciência com interfaces ou fluxos trabalhosos.',
  },
  pragmatism: {
    name: 'Pragmatismo',
    description: 'Foco em utilidade prática vs. novidade. Valores altos indicam priorização de benefícios tangíveis sobre experiências hedônicas.',
  },
  digital_capability: {
    name: 'Capacidade Digital',
    description: 'Habilidade técnica digital. Valores altos indicam maior fluência com tecnologias e interfaces digitais.',
  },
  motor_ability: {
    name: 'Habilidade Motora',
    description: 'Capacidade motora/visual para operar interfaces. Valores altos indicam plena capacidade física de interação.',
  },
  subject_domain: {
    name: 'Domínio do Assunto',
    description: 'Conhecimento do domínio da funcionalidade. Valores altos indicam expertise na área específica.',
  },
};

function SensitivityBar({ sensitivity }: { sensitivity: SensitivityData }) {
  const { name, value, groupAverage, description } = sensitivity;
  const percentage = value * 100;
  const avgPercentage = groupAverage * 100;

  // Calculate deviation for subtle visual feedback
  const deviation = Math.abs(value - groupAverage);
  const isAboveAverage = value > groupAverage;
  const isSignificantDeviation = deviation > 0.15;

  return (
    <div className="group relative">
      {/* Header Row */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <TooltipProvider delayDuration={200}>
            <Tooltip>
              <TooltipTrigger asChild>
                <button
                  className="text-slate-400 hover:text-slate-600 transition-colors"
                  aria-label={`Informação sobre ${name}`}
                >
                  <HelpCircle className="h-3.5 w-3.5" />
                </button>
              </TooltipTrigger>
              <TooltipContent
                side="right"
                className="max-w-xs bg-slate-800 text-slate-50 border-slate-700"
              >
                <p className="text-sm leading-relaxed">{description}</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
          <h4 className="text-[15px] font-medium text-slate-700">
            {name}
          </h4>
        </div>
        <div className="flex items-baseline gap-3">
          <span className="text-xs text-slate-400 font-light tabular-nums">
            média <span className="text-slate-500 font-medium">{avgPercentage.toFixed(0)}%</span>
          </span>
          <span
            className={cn(
              'text-lg font-semibold tabular-nums transition-colors',
              isSignificantDeviation
                ? isAboveAverage
                  ? 'text-teal-600'
                  : 'text-amber-600'
                : 'text-slate-700'
            )}
          >
            {percentage.toFixed(0)}%
          </span>
        </div>
      </div>

      {/* Bar Chart */}
      <div className="relative h-9 bg-slate-50 rounded-sm overflow-hidden border border-slate-200">
        {/* Filled portion (synth value) */}
        <div
          className={cn(
            'absolute left-0 top-0 h-full transition-all duration-700 ease-out',
            isSignificantDeviation
              ? isAboveAverage
                ? 'bg-gradient-to-r from-teal-100 to-teal-200'
                : 'bg-gradient-to-r from-amber-100 to-amber-200'
              : 'bg-gradient-to-r from-slate-200 to-slate-300'
          )}
          style={{
            width: `${percentage}%`,
            transitionDelay: '100ms',
          }}
        />

        {/* Group average marker */}
        <div
          className="absolute top-0 bottom-0 w-0.5 bg-slate-700 shadow-sm z-10"
          style={{
            left: `${avgPercentage}%`,
            transition: 'left 700ms ease-out',
          }}
        >
          {/* Triangle indicator at top */}
          <div className="absolute -top-1 left-1/2 -translate-x-1/2 w-0 h-0 border-l-[4px] border-r-[4px] border-t-[5px] border-l-transparent border-r-transparent border-t-slate-700" />
        </div>

        {/* Scale markers (0%, 50%, 100%) */}
        <div className="absolute inset-0 flex items-center justify-between px-2 pointer-events-none">
          <span className="text-[10px] text-slate-400 font-mono">0</span>
          <span className="text-[10px] text-slate-400 font-mono opacity-50">50</span>
          <span className="text-[10px] text-slate-400 font-mono">100</span>
        </div>
      </div>

      {/* Subtle deviation indicator */}
      {isSignificantDeviation && (
        <div className="mt-1 flex items-center justify-end gap-1.5">
          <div
            className={cn(
              'h-1 w-1 rounded-full',
              isAboveAverage ? 'bg-teal-500' : 'bg-amber-500'
            )}
          />
          <span className="text-[11px] text-slate-500 font-light">
            {isAboveAverage ? 'acima' : 'abaixo'} da média do grupo
          </span>
        </div>
      )}
    </div>
  );
}

export function SensitivitiesTab({ sensitivities, groupAverages = {} }: SensitivitiesTabProps) {
  // Transform data into structured format
  const sensitivityData: SensitivityData[] = Object.entries(SENSITIVITY_METADATA).map(
    ([key, meta]) => ({
      key,
      name: meta.name,
      value: sensitivities[key] ?? 0.5,
      groupAverage: groupAverages[key] ?? 0.5,
      description: meta.description,
    })
  );

  return (
    <div className="py-6 px-1">
      {/* Editorial Header */}
      <div className="mb-8 border-b border-slate-200 pb-4">
        <h3 className="text-2xl font-semibold text-slate-800 tracking-tight mb-1.5">
          Sensibilidades
        </h3>
        <p className="text-sm text-slate-500 leading-relaxed max-w-2xl">
          Fatores psicológicos que modulam a resposta do synth aos mecanismos da funcionalidade.
          Valores entre 0 (baixo) e 1 (alto). A linha vertical indica a média do grupo.
        </p>
      </div>

      {/* Sensitivity Bars Grid */}
      <div className="space-y-7">
        {sensitivityData.map((sensitivity) => (
          <SensitivityBar key={sensitivity.key} sensitivity={sensitivity} />
        ))}
      </div>

      {/* Legend Footer */}
      <div className="mt-10 pt-6 border-t border-slate-200">
        <div className="flex items-start gap-6 text-xs text-slate-500">
          <div className="flex items-center gap-2">
            <div className="h-4 w-0.5 bg-slate-700" />
            <span>Média do grupo</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="h-4 w-6 bg-gradient-to-r from-teal-100 to-teal-200 rounded-sm border border-teal-300" />
            <span>Acima da média</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="h-4 w-6 bg-gradient-to-r from-amber-100 to-amber-200 rounded-sm border border-amber-300" />
            <span>Abaixo da média</span>
          </div>
        </div>
      </div>
    </div>
  );
}
