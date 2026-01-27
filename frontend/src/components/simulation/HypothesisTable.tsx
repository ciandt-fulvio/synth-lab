/**
 * HypothesisTable component for displaying and editing hypotheses.
 *
 * Editable table with distribution parameters and correlations.
 *
 * References:
 *   - Types: types/hypothesis.ts
 *   - Hook: hooks/use-hypotheses.ts
 */

import { useState } from 'react';
import { Edit2, Save, X, Info } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { DistributionPicker, getDistributionLabel } from './DistributionPicker';
import type {
  Hypothesis,
  HypothesisUpdateRequest,
  DistributionParameters,
  DistributionType,
} from '@/types/hypothesis';

interface HypothesisTableProps {
  /**
   * List of hypotheses to display.
   */
  hypotheses: Hypothesis[];

  /**
   * Callback when a hypothesis is updated.
   */
  onUpdate?: (variableName: string, request: HypothesisUpdateRequest) => void;

  /**
   * Whether table is in read-only mode.
   */
  readOnly?: boolean;

  /**
   * Whether updates are being processed.
   */
  isUpdating?: boolean;
}

interface EditState {
  variableName: string;
  params: DistributionParameters;
}

/**
 * Format parameter value for display.
 */
function formatParam(value: number | null | undefined): string {
  if (value === null || value === undefined) return '-';
  return value.toFixed(2);
}

/**
 * HypothesisTable component.
 *
 * @example
 * <HypothesisTable
 *   hypotheses={hypotheses}
 *   onUpdate={handleUpdate}
 * />
 */
export function HypothesisTable({
  hypotheses,
  onUpdate,
  readOnly = false,
  isUpdating = false,
}: HypothesisTableProps) {
  const [editState, setEditState] = useState<EditState | null>(null);

  const handleEdit = (hyp: Hypothesis) => {
    setEditState({
      variableName: hyp.variable_name,
      params: { ...hyp.parameters },
    });
  };

  const handleCancel = () => {
    setEditState(null);
  };

  const handleSave = () => {
    if (!editState || !onUpdate) return;

    onUpdate(editState.variableName, {
      parameters: editState.params,
    });
    setEditState(null);
  };

  const updateParam = (key: keyof DistributionParameters, value: string) => {
    if (!editState) return;

    setEditState({
      ...editState,
      params: {
        ...editState.params,
        [key]: value === '' ? null : parseFloat(value),
      },
    });
  };

  const updateDistType = (type: DistributionType) => {
    if (!editState) return;

    setEditState({
      ...editState,
      params: {
        ...editState.params,
        distribution_type: type,
      },
    });
  };

  if (hypotheses.length === 0) {
    return (
      <div className="text-center text-slate-500 py-8">
        No hypotheses available
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-slate-200 overflow-hidden">
      <Table>
        <TableHeader>
          <TableRow className="bg-slate-50">
            <TableHead className="w-[200px]">Variable</TableHead>
            <TableHead>Distribution</TableHead>
            <TableHead className="text-right">Min</TableHead>
            <TableHead className="text-right">Max</TableHead>
            <TableHead className="text-right">Mean/Mode</TableHead>
            <TableHead className="text-right">Std Dev</TableHead>
            <TableHead className="text-center">Version</TableHead>
            {!readOnly && <TableHead className="w-[100px]">Actions</TableHead>}
          </TableRow>
        </TableHeader>
        <TableBody>
          {hypotheses.map((hyp) => {
            const isEditing = editState?.variableName === hyp.variable_name;
            const params = isEditing ? editState.params : hyp.parameters;

            return (
              <TableRow key={hyp.variable_name}>
                <TableCell>
                  <div className="flex items-center gap-2">
                    <span className="font-medium">{hyp.variable_name}</span>
                    {hyp.rationale && (
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <Info className="h-4 w-4 text-slate-400 cursor-help" />
                        </TooltipTrigger>
                        <TooltipContent className="max-w-xs">
                          <p className="text-sm">{hyp.rationale}</p>
                        </TooltipContent>
                      </Tooltip>
                    )}
                  </div>
                </TableCell>
                <TableCell>
                  {isEditing ? (
                    <DistributionPicker
                      value={params.distribution_type}
                      onChange={updateDistType}
                    />
                  ) : (
                    <span className="text-sm">
                      {getDistributionLabel(params.distribution_type)}
                    </span>
                  )}
                </TableCell>
                <TableCell className="text-right">
                  {isEditing ? (
                    <Input
                      type="number"
                      value={params.min_value ?? ''}
                      onChange={(e) => updateParam('min_value', e.target.value)}
                      className="w-20 text-right"
                    />
                  ) : (
                    <span className="font-mono text-sm">
                      {formatParam(params.min_value)}
                    </span>
                  )}
                </TableCell>
                <TableCell className="text-right">
                  {isEditing ? (
                    <Input
                      type="number"
                      value={params.max_value ?? ''}
                      onChange={(e) => updateParam('max_value', e.target.value)}
                      className="w-20 text-right"
                    />
                  ) : (
                    <span className="font-mono text-sm">
                      {formatParam(params.max_value)}
                    </span>
                  )}
                </TableCell>
                <TableCell className="text-right">
                  {isEditing ? (
                    <Input
                      type="number"
                      value={params.mean ?? params.mode ?? ''}
                      onChange={(e) =>
                        updateParam(
                          params.distribution_type === 'triangular' ? 'mode' : 'mean',
                          e.target.value
                        )
                      }
                      className="w-20 text-right"
                    />
                  ) : (
                    <span className="font-mono text-sm">
                      {formatParam(params.mean ?? params.mode)}
                    </span>
                  )}
                </TableCell>
                <TableCell className="text-right">
                  {isEditing ? (
                    <Input
                      type="number"
                      value={params.std_dev ?? ''}
                      onChange={(e) => updateParam('std_dev', e.target.value)}
                      className="w-20 text-right"
                      disabled={
                        params.distribution_type === 'uniform' ||
                        params.distribution_type === 'triangular'
                      }
                    />
                  ) : (
                    <span className="font-mono text-sm">
                      {formatParam(params.std_dev)}
                    </span>
                  )}
                </TableCell>
                <TableCell className="text-center">
                  <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-slate-100 text-slate-700 text-xs font-medium">
                    {hyp.version}
                  </span>
                </TableCell>
                {!readOnly && (
                  <TableCell>
                    <div className="flex items-center gap-1">
                      {isEditing ? (
                        <>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={handleSave}
                            disabled={isUpdating}
                            className="h-8 w-8 p-0 text-green-600"
                          >
                            <Save className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={handleCancel}
                            className="h-8 w-8 p-0 text-slate-600"
                          >
                            <X className="h-4 w-4" />
                          </Button>
                        </>
                      ) : (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleEdit(hyp)}
                          className="h-8 w-8 p-0"
                        >
                          <Edit2 className="h-4 w-4" />
                        </Button>
                      )}
                    </div>
                  </TableCell>
                )}
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    </div>
  );
}
