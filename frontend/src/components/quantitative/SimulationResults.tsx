/**
 * SimulationResults container component.
 *
 * Orchestrates DistributionChart, SegmentCards, and SensitivityBars
 * into a unified simulation results view with tabbed navigation.
 *
 * References:
 *   - Components: DistributionChart, SegmentCards, SensitivityBars
 *   - Types: src/types/quantitative-analysis.ts (SimulationRun)
 */

import { useState } from 'react';
import type { ReactNode } from 'react';
import { BarChart3, Users, Activity } from 'lucide-react';
import type { SimulationRun } from '@/types/quantitative-analysis';
import { DistributionChart } from './DistributionChart';
import { SegmentCards } from './SegmentCards';
import { SensitivityBars } from './SensitivityBars';

interface SimulationResultsProps {
  run: SimulationRun;
  actions?: ReactNode;
}

type ResultTab = 'distribution' | 'segments' | 'sensitivity';

const TABS: { key: ResultTab; label: string; icon: typeof BarChart3 }[] = [
  { key: 'distribution', label: 'Distribuição', icon: BarChart3 },
  { key: 'segments', label: 'Segmentos', icon: Users },
  { key: 'sensitivity', label: 'Sensibilidade', icon: Activity },
];

export function SimulationResults({ run, actions }: SimulationResultsProps) {
  const [activeTab, setActiveTab] = useState<ResultTab>('distribution');

  return (
    <div className="space-y-4">
      {/* Results header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-slate-800">Resultados da Simulação</h3>
          <p className="text-sm text-slate-500">
            {run.n_iterations.toLocaleString('pt-BR')} iterações, {run.n_synths} synths
          </p>
        </div>
        {actions && <div className="flex items-center gap-3">{actions}</div>}
      </div>

      {/* Tab navigation */}
      <div className="flex gap-1 border-b border-slate-200">
        {TABS.map(({ key, label, icon: Icon }) => (
          <button
            key={key}
            onClick={() => setActiveTab(key)}
            className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium transition-colors border-b-2 -mb-px ${
              activeTab === key
                ? 'border-indigo-600 text-indigo-600'
                : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'
            }`}
          >
            <Icon className="w-4 h-4" />
            {label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div className="pt-2">
        {activeTab === 'distribution' && (
          <DistributionChart
            distribution={run.distribution}
            stats={run.stats}
            interpretation={run.interpretations?.distribution}
          />
        )}
        {activeTab === 'segments' && (
          <SegmentCards
            segments={run.segments}
            interpretation={run.interpretations?.segments}
          />
        )}
        {activeTab === 'sensitivity' && (
          <SensitivityBars
            sensitivity={run.sensitivity}
            interpretation={run.interpretations?.sensitivity}
          />
        )}
      </div>
    </div>
  );
}
