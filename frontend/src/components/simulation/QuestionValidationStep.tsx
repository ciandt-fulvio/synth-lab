/**
 * QuestionValidationStep component for simulation wizard.
 *
 * Displays the parsed problem decomposition for user review and editing.
 *
 * References:
 *   - Spec: specs/035-causal-simulation/spec.md
 */

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { ArrowRight, Edit2, Loader2, Save, X } from 'lucide-react';
import { toast } from 'sonner';
import type { ProblemDecomposition } from '@/services/simulations-api';
import {
  ScenarioProfileSelector,
  type ScenarioProfile,
} from '@/components/simulation/hypothesis/ScenarioProfileSelector';

interface QuestionValidationStepProps {
  problemDecomposition: ProblemDecomposition;
  onConfirm: () => void;
  onUpdate: (update: Partial<ProblemDecomposition>) => Promise<void>;
  isConfirming: boolean;
  isUpdating: boolean;
  /** When true, hides edit/confirm buttons for reviewing completed steps */
  readOnly?: boolean;
  /** Selected scenario profile */
  scenarioProfile?: ScenarioProfile;
  /** Callback when scenario profile changes */
  onScenarioProfileChange?: (profile: ScenarioProfile) => void;
}

const DECISION_TYPES = [
  { value: 'product_launch', label: 'Lançamento de Produto' },
  { value: 'feature_rollout', label: 'Rollout de Feature' },
  { value: 'pricing_change', label: 'Mudança de Preço' },
  { value: 'process_improvement', label: 'Melhoria de Processo' },
  { value: 'capacity_planning', label: 'Planejamento de Capacidade' },
  { value: 'market_entry', label: 'Entrada em Mercado' },
];

const UNIT_OF_ANALYSIS = [
  { value: 'user', label: 'Usuário' },
  { value: 'customer', label: 'Cliente' },
  { value: 'transaction', label: 'Transação' },
  { value: 'account', label: 'Conta' },
  { value: 'session', label: 'Sessão' },
  { value: 'cohort', label: 'Coorte' },
];

/**
 * Step component for validating the parsed question/problem decomposition.
 */
export function QuestionValidationStep({
  problemDecomposition,
  onConfirm,
  onUpdate,
  isConfirming,
  isUpdating,
  readOnly = false,
  scenarioProfile,
  onScenarioProfileChange,
}: QuestionValidationStepProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [editedData, setEditedData] = useState(problemDecomposition);

  const handleStartEdit = () => {
    setEditedData(problemDecomposition);
    setIsEditing(true);
  };

  const handleCancelEdit = () => {
    setEditedData(problemDecomposition);
    setIsEditing(false);
  };

  const handleSaveEdit = async () => {
    try {
      await onUpdate(editedData);
      setIsEditing(false);
      toast.success('Alterações salvas');
    } catch (error) {
      toast.error('Erro ao salvar alterações');
    }
  };

  const handleSecondaryOutcomeChange = (index: number, value: string) => {
    const updated = [...editedData.secondary_outcomes];
    updated[index] = value;
    setEditedData({ ...editedData, secondary_outcomes: updated });
  };

  const handleAddSecondaryOutcome = () => {
    setEditedData({
      ...editedData,
      secondary_outcomes: [...editedData.secondary_outcomes, ''],
    });
  };

  const handleRemoveSecondaryOutcome = (index: number) => {
    const updated = editedData.secondary_outcomes.filter((_, i) => i !== index);
    setEditedData({ ...editedData, secondary_outcomes: updated });
  };

  if (isEditing) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-slate-900">
            Editar Estruturação da Pergunta
          </h2>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={handleCancelEdit}>
              <X className="h-4 w-4 mr-1" />
              Cancelar
            </Button>
            <Button
              size="sm"
              onClick={handleSaveEdit}
              disabled={isUpdating}
              className="btn-primary"
            >
              {isUpdating ? (
                <Loader2 className="h-4 w-4 mr-1 animate-spin" />
              ) : (
                <Save className="h-4 w-4 mr-1" />
              )}
              Salvar
            </Button>
          </div>
        </div>

        <div className="grid gap-4">
          <div>
            <Label htmlFor="intervention">Intervenção</Label>
            <Textarea
              id="intervention"
              value={editedData.intervention}
              onChange={(e) =>
                setEditedData({ ...editedData, intervention: e.target.value })
              }
              placeholder="Qual ação/mudança está sendo avaliada?"
              rows={2}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="primary_outcome">Resultado Principal</Label>
              <Input
                id="primary_outcome"
                value={editedData.primary_outcome}
                onChange={(e) =>
                  setEditedData({ ...editedData, primary_outcome: e.target.value })
                }
                placeholder="ex: taxa_de_adocao"
              />
            </div>

            <div>
              <Label htmlFor="time_horizon">Horizonte de Tempo</Label>
              <Input
                id="time_horizon"
                value={editedData.time_horizon}
                onChange={(e) =>
                  setEditedData({ ...editedData, time_horizon: e.target.value })
                }
                placeholder="ex: 6 meses"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="unit_of_analysis">Unidade de Análise</Label>
              <Select
                value={editedData.unit_of_analysis}
                onValueChange={(value) =>
                  setEditedData({ ...editedData, unit_of_analysis: value })
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {UNIT_OF_ANALYSIS.map((unit) => (
                    <SelectItem key={unit.value} value={unit.value}>
                      {unit.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label htmlFor="decision_type">Tipo de Decisão</Label>
              <Select
                value={editedData.decision_type}
                onValueChange={(value) =>
                  setEditedData({ ...editedData, decision_type: value })
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {DECISION_TYPES.map((type) => (
                    <SelectItem key={type.value} value={type.value}>
                      {type.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div>
            <Label>Resultados Secundários</Label>
            <div className="space-y-2 mt-1">
              {editedData.secondary_outcomes.map((outcome, idx) => (
                <div key={idx} className="flex gap-2">
                  <Input
                    value={outcome}
                    onChange={(e) => handleSecondaryOutcomeChange(idx, e.target.value)}
                    placeholder="ex: satisfacao_cliente"
                  />
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => handleRemoveSecondaryOutcome(idx)}
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>
              ))}
              <Button
                variant="outline"
                size="sm"
                onClick={handleAddSecondaryOutcome}
              >
                + Adicionar Resultado
              </Button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-slate-900">
          {readOnly ? 'Estruturação da Pergunta' : 'Validar Estruturação da Pergunta'}
        </h2>
        {!readOnly && (
          <Button variant="outline" size="sm" onClick={handleStartEdit}>
            <Edit2 className="h-4 w-4 mr-1" />
            Editar
          </Button>
        )}
      </div>

      {!readOnly && (
        <p className="text-sm text-slate-600">
          Revise a estruturação abaixo. Após confirmar, o modelo causal será gerado automaticamente.
        </p>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="space-y-1">
          <h3 className="text-sm font-semibold text-slate-700">Intervenção</h3>
          <p className="text-sm text-slate-600">{problemDecomposition.intervention}</p>
        </div>

        <div className="space-y-1">
          <h3 className="text-sm font-semibold text-slate-700">Resultado Principal</h3>
          <p className="text-sm text-slate-600">{problemDecomposition.primary_outcome}</p>
        </div>

        <div className="space-y-1">
          <h3 className="text-sm font-semibold text-slate-700">Horizonte de Tempo</h3>
          <p className="text-sm text-slate-600">{problemDecomposition.time_horizon}</p>
        </div>

        <div className="space-y-1">
          <h3 className="text-sm font-semibold text-slate-700">Unidade de Análise</h3>
          <p className="text-sm text-slate-600">
            {UNIT_OF_ANALYSIS.find((u) => u.value === problemDecomposition.unit_of_analysis)?.label ||
              problemDecomposition.unit_of_analysis}
          </p>
        </div>

        <div className="space-y-1">
          <h3 className="text-sm font-semibold text-slate-700">Tipo de Decisão</h3>
          <p className="text-sm text-slate-600">
            {DECISION_TYPES.find((d) => d.value === problemDecomposition.decision_type)?.label ||
              problemDecomposition.decision_type}
          </p>
        </div>

        {problemDecomposition.secondary_outcomes.length > 0 && (
          <div className="md:col-span-2 space-y-1">
            <h3 className="text-sm font-semibold text-slate-700">Resultados Secundários</h3>
            <div className="flex flex-wrap gap-2">
              {problemDecomposition.secondary_outcomes.map((outcome, idx) => (
                <span
                  key={idx}
                  className="px-3 py-1 rounded-full bg-indigo-50 text-indigo-700 text-sm"
                >
                  {outcome}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      {!readOnly && scenarioProfile && onScenarioProfileChange && (
        <ScenarioProfileSelector
          value={scenarioProfile}
          onChange={onScenarioProfileChange}
          disabled={isConfirming}
        />
      )}

      {!readOnly && (
        <div className="flex justify-end pt-4 border-t">
          <Button
            onClick={onConfirm}
            disabled={isConfirming}
            className="btn-primary"
          >
            {isConfirming ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Gerando Modelo...
              </>
            ) : (
              <>
                Confirmar e Gerar Modelo
                <ArrowRight className="h-4 w-4 ml-2" />
              </>
            )}
          </Button>
        </div>
      )}
    </div>
  );
}
