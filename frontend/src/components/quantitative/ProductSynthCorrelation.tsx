/**
 * ProductSynthCorrelation component.
 *
 * Heatmap showing how product attributes correlate with adoption
 * across demographic clusters (diff in pp between high and low calibration).
 *
 * References:
 *   - Types: src/types/quantitative-analysis.ts (ProductSynthCorrelationResponse)
 *   - Hook: useProductSynthCorrelations
 */

import { Loader2, Grid3X3 } from 'lucide-react';
import { useProductSynthCorrelations } from '@/hooks/use-quantitative-analysis';

interface ProductSynthCorrelationProps {
  experimentId: string;
}

const CLUSTER_LABELS: Record<string, string> = {
  jovem_baixa_renda: 'Jovem + Baixa Renda',
  jovem_alta_renda: 'Jovem + Alta Renda',
  maduro_baixa_renda: 'Maduro + Baixa Renda',
  maduro_alta_renda: 'Maduro + Alta Renda',
};

function cellColor(value: number): string {
  if (value >= 10) return 'bg-emerald-600 text-white';
  if (value >= 5) return 'bg-emerald-400 text-white';
  if (value >= 2) return 'bg-emerald-200 text-emerald-900';
  if (value > -2) return 'bg-slate-100 text-slate-500';
  if (value > -5) return 'bg-red-200 text-red-900';
  if (value > -10) return 'bg-red-400 text-white';
  return 'bg-red-600 text-white';
}

export function ProductSynthCorrelation({ experimentId }: ProductSynthCorrelationProps) {
  const { data, isLoading } = useProductSynthCorrelations(experimentId);

  if (isLoading) {
    return (
      <div className="text-center py-6">
        <Loader2 className="w-5 h-5 text-violet-500 mx-auto animate-spin" />
      </div>
    );
  }

  if (!data || data.product_attributes.length === 0) return null;

  const { product_attributes, clusters, matrix } = data;

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 space-y-4">
      <div>
        <div className="flex items-center gap-2 mb-1">
          <Grid3X3 className="w-4 h-4 text-slate-400" />
          <h3 className="text-base font-semibold text-slate-800">
            Produto × Cluster Demográfico
          </h3>
        </div>
        <p className="text-sm text-slate-500">
          Diferença em pontos percentuais na adoção entre calibração alta e baixa de cada atributo, por cluster.
        </p>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm border-collapse">
          <thead>
            <tr>
              <th className="text-left py-2 px-3 text-xs font-medium text-slate-500 border-b border-slate-200">
                Cluster
              </th>
              {product_attributes.map((attr) => (
                <th
                  key={attr}
                  className="text-center py-2 px-3 text-xs font-medium text-slate-500 border-b border-slate-200"
                >
                  {attr}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {clusters.map((cluster) => (
              <tr key={cluster} className="border-b border-slate-100 last:border-0">
                <td className="py-2.5 px-3 text-sm font-medium text-slate-700">
                  {CLUSTER_LABELS[cluster] ?? cluster}
                </td>
                {product_attributes.map((attr) => {
                  const val = matrix[cluster]?.[attr] ?? 0;
                  return (
                    <td key={attr} className="py-2.5 px-3 text-center">
                      <span
                        className={`inline-block rounded-md px-2.5 py-0.5 text-xs font-semibold ${cellColor(val)}`}
                      >
                        {val > 0 ? '+' : ''}{val.toFixed(1)} pp
                      </span>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Legend */}
      <div className="flex items-center gap-4 text-xs text-slate-400 pt-1">
        <div className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded bg-emerald-600" />
          <span>≥ +10 pp</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded bg-emerald-200" />
          <span>+2–10 pp</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded bg-slate-100 border border-slate-300" />
          <span>neutro</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded bg-red-200" />
          <span>−2–10 pp</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded bg-red-600" />
          <span>≤ −10 pp</span>
        </div>
      </div>
    </div>
  );
}
