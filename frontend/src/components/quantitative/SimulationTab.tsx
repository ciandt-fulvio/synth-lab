/**
 * SimulationTab container component.
 *
 * Displays batch simulation results: scenario ranking, product impact,
 * scenario distribution, and best/median/worst comparison.
 *
 * References:
 *   - Hooks: src/hooks/use-quantitative-analysis.ts
 *   - Components: ScenarioRanking, ProductImpactChart, ScenarioDistribution, ScenarioComparison
 */

import { Loader2, Activity } from 'lucide-react';
import { useLatestBatch, useCausalModel } from '@/hooks/use-quantitative-analysis';
import { ScenarioRanking } from './ScenarioRanking';
import { ProductImpactChart } from './ProductImpactChart';
import { ScenarioDistribution } from './ScenarioDistribution';
import { ScenarioComparison } from './ScenarioComparison';
import { SynthProfileAnalysis } from './SynthProfileAnalysis';
import { ProductSynthCorrelation } from './ProductSynthCorrelation';
import { SimulationReport } from './SimulationReport';

interface SimulationTabProps {
  experimentId: string;
  onGenerateGuide?: () => void;
}

export function SimulationTab({ experimentId }: SimulationTabProps) {
  const { data: batch, isLoading } = useLatestBatch(experimentId);
  const { data: causalModel } = useCausalModel(experimentId);

  if (isLoading) {
    return (
      <div className="text-center py-12">
        <Loader2 className="w-8 h-8 text-violet-500 mx-auto mb-3 animate-spin" />
        <p className="text-slate-500">Carregando resultados...</p>
      </div>
    );
  }

  if (!batch || batch.scenarios.length === 0) {
    return (
      <div className="text-center py-12">
        <Activity className="w-10 h-10 text-slate-300 mx-auto mb-3" />
        <p className="text-slate-500">Nenhuma simulação realizada ainda.</p>
        <p className="text-sm text-slate-400 mt-1">
          Execute a simulação na aba &quot;Análise Quanti&quot;.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Summary bar */}
      <div className="flex items-center gap-3 text-xs text-slate-400 font-medium">
        <span className="px-2.5 py-1 bg-slate-100 rounded-full">
          {batch.n_scenarios} cenários
        </span>
        <span className="text-slate-300">×</span>
        <span className="px-2.5 py-1 bg-slate-100 rounded-full">
          {batch.n_synths} synths
        </span>
        <span className="text-slate-300">×</span>
        <span className="px-2.5 py-1 bg-slate-100 rounded-full">
          {batch.n_repetitions} repetições
        </span>
      </div>

      <ScenarioComparison scenarios={batch.scenarios} nodeMetadata={causalModel?.node_metadata ?? null} />
      <ScenarioDistribution scenarios={batch.scenarios} />
      <ProductImpactChart scenarios={batch.scenarios} />
      <SynthProfileAnalysis experimentId={experimentId} />
      <ProductSynthCorrelation experimentId={experimentId} />
      <SimulationReport experimentId={experimentId} />
      <ScenarioRanking scenarios={batch.scenarios} />
    </div>
  );
}
