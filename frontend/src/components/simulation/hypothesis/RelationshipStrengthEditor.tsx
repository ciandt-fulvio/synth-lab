/**
 * RelationshipStrengthEditor component.
 *
 * Editor for adjusting the strength of high-importance relationships.
 * Filters edges with strength_estimated = 'high'.
 *
 * References:
 *   - Design: Scientific editorial style
 */

import { useMemo } from 'react';
import { Link2, Info, ArrowRight } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import type { Variable, Edge } from '@/types/causal-dag';

export type RelationshipStrength = 'weak' | 'medium' | 'strong';

const STRENGTH_OPTIONS: { value: RelationshipStrength; label: string; numeric: number }[] = [
  { value: 'weak', label: 'Fraca', numeric: 0.25 },
  { value: 'medium', label: 'Média', numeric: 0.5 },
  { value: 'strong', label: 'Forte', numeric: 0.75 },
];

interface RelationshipStrengthEditorProps {
  edges: Edge[];
  nodes: Variable[];
  strengths: Record<string, RelationshipStrength>;
  onChange: (source: string, target: string, strength: RelationshipStrength) => void;
  readOnly?: boolean;
}

/**
 * Get a composite key for an edge.
 */
function edgeKey(source: string, target: string): string {
  return `${source}__${target}`;
}

/**
 * Get strength from numeric value.
 */
function strengthFromNumeric(value: number | null | undefined): RelationshipStrength {
  if (value == null) return 'medium';
  if (value < 0.4) return 'weak';
  if (value > 0.6) return 'strong';
  return 'medium';
}

/**
 * Filter edges that have high estimated strength (important relationships).
 */
function filterHighStrengthEdges(edges: Edge[]): Edge[] {
  return edges.filter((e) => e.strength_estimated === 'high');
}

/**
 * Step component for editing relationship strengths.
 */
export function RelationshipStrengthEditor({
  edges,
  nodes,
  strengths,
  onChange,
  readOnly = false,
}: RelationshipStrengthEditorProps) {
  const highStrengthEdges = useMemo(() => filterHighStrengthEdges(edges), [edges]);

  // Create lookup for node labels
  const nodeLabels = useMemo(() => {
    const map: Record<string, string> = {};
    for (const node of nodes) {
      map[node.name] = node.label || node.name;
    }
    return map;
  }, [nodes]);

  if (highStrengthEdges.length === 0) {
    return (
      <Card className="border-dashed">
        <CardContent className="py-12 text-center">
          <Link2 className="h-12 w-12 mx-auto text-slate-300 mb-4" />
          <p className="text-sm text-slate-500">
            Nenhum relacionamento de alta importância para configurar.
          </p>
          <p className="text-xs text-slate-400 mt-2">
            Relacionamentos importantes são aqueles que o modelo identificou como tendo impacto
            significativo no resultado.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-start gap-3 p-4 bg-indigo-50 border border-indigo-200 rounded-lg">
        <Info className="h-5 w-5 text-indigo-600 flex-shrink-0 mt-0.5" />
        <div>
          <p className="text-sm font-medium text-indigo-800">Força dos Relacionamentos</p>
          <p className="text-xs text-indigo-700 mt-1">
            Ajuste a força das relações causais mais importantes. Isso afeta quanto uma variável
            influencia a outra na simulação.
          </p>
        </div>
      </div>

      <div className="space-y-3">
        {highStrengthEdges.map((edge) => {
          const key = edgeKey(edge.source, edge.target);
          const currentStrength =
            strengths[key] ||
            strengthFromNumeric(edge.strength_user || edge.strength);
          const sourceLabel = nodeLabels[edge.source] || edge.source;
          const targetLabel = nodeLabels[edge.target] || edge.target;

          return (
            <Card key={key} className="border-slate-200">
              <CardContent className="py-4">
                <div className="flex items-center gap-3 flex-wrap">
                  <span className="text-sm text-slate-600">Uma</span>
                  <span className="font-semibold text-slate-900 font-mono text-sm bg-slate-100 px-2 py-1 rounded">
                    {sourceLabel}
                  </span>
                  <span className="text-sm text-slate-600">implica de forma</span>
                  <Select
                    value={currentStrength}
                    onValueChange={(value) =>
                      onChange(edge.source, edge.target, value as RelationshipStrength)
                    }
                    disabled={readOnly}
                  >
                    <SelectTrigger className="w-32 h-9">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {STRENGTH_OPTIONS.map((opt) => (
                        <SelectItem key={opt.value} value={opt.value}>
                          {opt.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <span className="text-sm text-slate-600">a</span>
                  <span className="font-semibold text-slate-900 font-mono text-sm bg-slate-100 px-2 py-1 rounded">
                    {targetLabel}
                  </span>
                  <ArrowRight className="h-4 w-4 text-slate-400" />
                  <span className="text-xs text-slate-500 font-mono">
                    ({STRENGTH_OPTIONS.find((o) => o.value === currentStrength)?.numeric.toFixed(2)})
                  </span>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      <div className="text-xs text-slate-500 p-3 bg-slate-50 rounded-lg">
        <p className="font-medium mb-1">Interpretação dos valores:</p>
        <ul className="space-y-1">
          <li>
            <strong>Fraca (0.25):</strong> A variável origem tem pequena influência no destino
          </li>
          <li>
            <strong>Média (0.50):</strong> A variável origem tem influência moderada no destino
          </li>
          <li>
            <strong>Forte (0.75):</strong> A variável origem tem grande influência no destino
          </li>
        </ul>
      </div>
    </div>
  );
}

/**
 * Convert strength enum to numeric value.
 */
export function strengthToNumeric(strength: RelationshipStrength): number {
  return STRENGTH_OPTIONS.find((o) => o.value === strength)?.numeric ?? 0.5;
}
