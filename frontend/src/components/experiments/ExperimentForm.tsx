/**
 * ExperimentForm component (Refactored).
 *
 * Two-step form for creating/editing experiments with embedded scorecard sliders.
 * Step 1: Basic info (name, hypothesis, description)
 * Step 2: Scorecard sliders with LLM estimation
 *
 * References:
 *   - Spec: specs/019-experiment-refactor/spec.md
 *   - Types: src/types/experiment.ts
 */

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Slider } from '@/components/ui/slider';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Loader2, Sparkles, ArrowRight, ArrowLeft, Users } from 'lucide-react';
import { useEstimateScorecardFromText } from '@/hooks/use-experiments';
import { useSynthGroups } from '@/hooks/use-synth-groups';
import { useToast } from '@/hooks/use-toast';
import type { ExperimentCreate, ExperimentUpdate, ScorecardData } from '@/types/experiment';

interface ExperimentFormProps {
  /** Initial values for edit mode */
  initialData?: ExperimentUpdate & { scorecard_data?: ScorecardData | null };
  /** Submit handler */
  onSubmit: (data: ExperimentCreate) => void | Promise<void>;
  /** Cancel handler */
  onCancel: () => void;
  /** Whether the form is submitting */
  isSubmitting?: boolean;
  /** Whether to show scorecard sliders (default: true for new experiments) */
  showScorecard?: boolean;
}

interface FormErrors {
  name?: string;
  hypothesis?: string;
  description?: string;
}

interface ScorecardSliders {
  complexity: number;
  initial_effort: number;
  perceived_risk: number;
  time_to_value: number;
}

const DIMENSION_LABELS = {
  complexity: 'Complexidade',
  initial_effort: 'Esforço Inicial',
  perceived_risk: 'Risco Percebido',
  time_to_value: 'Tempo até Valor',
} as const;

const DIMENSION_DESCRIPTIONS = {
  complexity: '0 = simples, 1 = complexo',
  initial_effort: '0 = imediato, 1 = muito esforço',
  perceived_risk: '0 = seguro, 1 = arriscado',
  time_to_value: '0 = imediato, 1 = demorado',
} as const;

export function ExperimentForm({
  initialData,
  onSubmit,
  onCancel,
  isSubmitting = false,
  showScorecard = true,
}: ExperimentFormProps) {
  const { toast } = useToast();
  const estimateMutation = useEstimateScorecardFromText();
  const { data: synthGroupsData, isLoading: isLoadingSynthGroups } = useSynthGroups();

  // Step management (1 = basic info, 2 = scorecard)
  const [step, setStep] = useState(1);

  const [name, setName] = useState(initialData?.name ?? '');
  const [hypothesis, setHypothesis] = useState(initialData?.hypothesis ?? '');
  const [description, setDescription] = useState(initialData?.description ?? '');
  const [selectedSynthGroupId, setSelectedSynthGroupId] = useState<string>('grp_00000001');
  const [errors, setErrors] = useState<FormErrors>({});

  // Initialize sliders from existing scorecard or defaults
  const [sliders, setSliders] = useState<ScorecardSliders>(() => {
    if (initialData?.scorecard_data) {
      return {
        complexity: initialData.scorecard_data.complexity.score,
        initial_effort: initialData.scorecard_data.initial_effort.score,
        perceived_risk: initialData.scorecard_data.perceived_risk.score,
        time_to_value: initialData.scorecard_data.time_to_value.score,
      };
    }
    return {
      complexity: 0.5,
      initial_effort: 0.5,
      perceived_risk: 0.5,
      time_to_value: 0.5,
    };
  });

  const validateStep1 = (): boolean => {
    const newErrors: FormErrors = {};

    // Name validation
    if (!name.trim()) {
      newErrors.name = 'Nome é obrigatório';
    } else if (name.length > 100) {
      newErrors.name = 'Nome deve ter no máximo 100 caracteres';
    }

    // Hypothesis validation
    if (!hypothesis.trim()) {
      newErrors.hypothesis = 'Hipótese é obrigatória';
    } else if (hypothesis.length > 500) {
      newErrors.hypothesis = 'Hipótese deve ter no máximo 500 caracteres';
    }

    // Description validation (optional)
    if (description && description.length > 2000) {
      newErrors.description = 'Descrição deve ter no máximo 2000 caracteres';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleNextStep = () => {
    if (validateStep1()) {
      setStep(2);
    }
  };

  const handlePrevStep = () => {
    setStep(1);
  };

  const handleEstimate = async () => {
    try {
      const estimate = await estimateMutation.mutateAsync({
        name: name.trim(),
        hypothesis: hypothesis.trim(),
        description: description.trim() || undefined,
      });

      // Update sliders with AI estimates
      setSliders({
        complexity: estimate.complexity.score,
        initial_effort: estimate.initial_effort.score,
        perceived_risk: estimate.perceived_risk.score,
        time_to_value: estimate.time_to_value.score,
      });

      toast({
        title: 'Estimativa gerada',
        description: 'Os valores foram atualizados com base na análise de IA.',
      });
    } catch (err) {
      toast({
        title: 'Erro na estimativa',
        description: err instanceof Error ? err.message : 'Erro desconhecido',
        variant: 'destructive',
      });
    }
  };

  const handleSliderChange = (dimension: keyof ScorecardSliders, value: number[]) => {
    setSliders((prev) => ({
      ...prev,
      [dimension]: value[0],
    }));
  };

  const handleSubmit = async () => {
    // Build experiment data with embedded scorecard
    const experimentData: ExperimentCreate = {
      name: name.trim(),
      hypothesis: hypothesis.trim(),
      description: description.trim() || undefined,
      synth_group_id: selectedSynthGroupId,
    };

    // Include scorecard data if showing sliders
    if (showScorecard) {
      experimentData.scorecard_data = {
        feature_name: name.trim(),
        description_text: hypothesis.trim(),
        complexity: { score: sliders.complexity },
        initial_effort: { score: sliders.initial_effort },
        perceived_risk: { score: sliders.perceived_risk },
        time_to_value: { score: sliders.time_to_value },
      };
    }

    await onSubmit(experimentData);
  };

  // If not showing scorecard, render single-step form
  if (!showScorecard) {
    return (
      <form
        onSubmit={async (e) => {
          e.preventDefault();
          if (validateStep1()) {
            await handleSubmit();
          }
        }}
        className="space-y-4"
      >
        <div className="space-y-2">
          <Label htmlFor="name">
            Nome <span className="text-red-500">*</span>
          </Label>
          <Input
            id="name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Ex: Checkout Simplificado"
            maxLength={100}
            disabled={isSubmitting}
            className={errors.name ? 'border-red-500' : ''}
          />
          {errors.name && <p className="text-sm text-red-500">{errors.name}</p>}
          <p className="text-xs text-gray-500">{name.length}/100</p>
        </div>

        <div className="space-y-2">
          <Label htmlFor="hypothesis">
            Hipótese <span className="text-red-500">*</span>
          </Label>
          <Textarea
            id="hypothesis"
            value={hypothesis}
            onChange={(e) => setHypothesis(e.target.value)}
            placeholder="Ex: Usuários completam mais compras com checkout de uma página"
            maxLength={500}
            rows={3}
            disabled={isSubmitting}
            className={errors.hypothesis ? 'border-red-500' : ''}
          />
          {errors.hypothesis && <p className="text-sm text-red-500">{errors.hypothesis}</p>}
          <p className="text-xs text-gray-500">{hypothesis.length}/500</p>
        </div>

        <div className="space-y-2">
          <Label htmlFor="description">Descrição (opcional)</Label>
          <Textarea
            id="description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Contexto adicional, links, referências..."
            maxLength={2000}
            rows={3}
            disabled={isSubmitting}
            className={errors.description ? 'border-red-500' : ''}
          />
          {errors.description && <p className="text-sm text-red-500">{errors.description}</p>}
          <p className="text-xs text-gray-500">{description.length}/2000</p>
        </div>

        <div className="space-y-2">
          <Label htmlFor="synth-group">
            <Users className="inline h-4 w-4 mr-1" />
            Grupo de Synths
          </Label>
          <Select
            value={selectedSynthGroupId}
            onValueChange={setSelectedSynthGroupId}
            disabled={isSubmitting || isLoadingSynthGroups}
          >
            <SelectTrigger id="synth-group">
              <SelectValue placeholder="Selecione um grupo..." />
            </SelectTrigger>
            <SelectContent>
              {synthGroupsData?.data.map((group) => (
                <SelectItem key={group.id} value={group.id}>
                  {group.name} ({group.synth_count} synths)
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <p className="text-xs text-gray-500">
            Synths deste grupo serão usados em simulações, entrevistas e explorações
          </p>
        </div>

        <div className="flex justify-end gap-2 pt-4">
          <Button type="button" variant="outline" onClick={onCancel} disabled={isSubmitting} className="btn-secondary">
            Cancelar
          </Button>
          <Button type="submit" disabled={isSubmitting} className="btn-primary">
            {isSubmitting ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Salvando...
              </>
            ) : (
              'Salvar'
            )}
          </Button>
        </div>
      </form>
    );
  }

  // Two-step form for creating experiments with scorecard
  return (
    <div className="space-y-4">
      {/* Step indicator */}
      <div className="flex items-center justify-center gap-2 mb-4">
        <div
          className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
            step === 1 ? 'bg-primary text-primary-foreground' : 'bg-gray-200 text-gray-600'
          }`}
        >
          1
        </div>
        <div className="w-8 h-0.5 bg-gray-200" />
        <div
          className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
            step === 2 ? 'bg-primary text-primary-foreground' : 'bg-gray-200 text-gray-600'
          }`}
        >
          2
        </div>
      </div>

      {/* Step 1: Basic Info */}
      {step === 1 && (
        <div className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="name">
              Nome <span className="text-red-500">*</span>
            </Label>
            <Input
              id="name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Ex: Checkout Simplificado"
              maxLength={100}
              disabled={isSubmitting}
              className={errors.name ? 'border-red-500' : ''}
            />
            {errors.name && <p className="text-sm text-red-500">{errors.name}</p>}
            <p className="text-xs text-gray-500">{name.length}/100</p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="hypothesis">
              Hipótese <span className="text-red-500">*</span>
            </Label>
            <Textarea
              id="hypothesis"
              value={hypothesis}
              onChange={(e) => setHypothesis(e.target.value)}
              placeholder="Ex: Usuários completam mais compras com checkout de uma página"
              maxLength={500}
              rows={3}
              disabled={isSubmitting}
              className={errors.hypothesis ? 'border-red-500' : ''}
            />
            {errors.hypothesis && <p className="text-sm text-red-500">{errors.hypothesis}</p>}
            <p className="text-xs text-gray-500">{hypothesis.length}/500</p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="description">Descrição (opcional)</Label>
            <Textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Contexto adicional, links, referências..."
              maxLength={2000}
              rows={3}
              disabled={isSubmitting}
              className={errors.description ? 'border-red-500' : ''}
            />
            {errors.description && <p className="text-sm text-red-500">{errors.description}</p>}
            <p className="text-xs text-gray-500">{description.length}/2000</p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="synth-group-step1">
              <Users className="inline h-4 w-4 mr-1" />
              Grupo de Synths
            </Label>
            <Select
              value={selectedSynthGroupId}
              onValueChange={setSelectedSynthGroupId}
              disabled={isSubmitting || isLoadingSynthGroups}
            >
              <SelectTrigger id="synth-group-step1">
                <SelectValue placeholder="Selecione um grupo..." />
              </SelectTrigger>
              <SelectContent>
                {synthGroupsData?.data.map((group) => (
                  <SelectItem key={group.id} value={group.id}>
                    {group.name} ({group.synth_count} synths)
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <p className="text-xs text-gray-500">
              Synths deste grupo serão usados em simulações, entrevistas e explorações
            </p>
          </div>

          <div className="flex justify-end gap-2 pt-4">
            <Button type="button" variant="outline" onClick={onCancel} className="btn-secondary">
              Cancelar
            </Button>
            <Button type="button" onClick={handleNextStep} className="btn-primary">
              Próximo
              <ArrowRight className="w-4 h-4 ml-2" />
            </Button>
          </div>
        </div>
      )}

      {/* Step 2: Scorecard Sliders */}
      {step === 2 && (
        <div className="space-y-4">
          <div className="text-center mb-2">
            <h3 className="font-medium text-gray-900">Scorecard</h3>
            <p className="text-sm text-gray-500">
              Ajuste os valores ou use IA para estimar
            </p>
          </div>

          {/* Sliders for each dimension */}
          {(Object.keys(DIMENSION_LABELS) as Array<keyof ScorecardSliders>).map((dimension) => (
            <div key={dimension} className="space-y-1">
              <div className="flex items-center justify-between">
                <Label htmlFor={dimension} className="text-sm">
                  {DIMENSION_LABELS[dimension]}
                </Label>
                <span className="text-sm font-mono text-gray-600">
                  {sliders[dimension].toFixed(2)}
                </span>
              </div>
              <Slider
                id={dimension}
                min={0}
                max={1}
                step={0.05}
                value={[sliders[dimension]]}
                onValueChange={(value) => handleSliderChange(dimension, value)}
                disabled={isSubmitting || estimateMutation.isPending}
                className="w-full"
              />
              <p className="text-xs text-gray-400">{DIMENSION_DESCRIPTIONS[dimension]}</p>
            </div>
          ))}

          {/* Action buttons */}
          <div className="flex justify-between gap-2 pt-4">
            <Button
              type="button"
              variant="ghost"
              size="icon"
              onClick={handlePrevStep}
              disabled={isSubmitting || estimateMutation.isPending}
              className="btn-ghost-icon"
            >
              <ArrowLeft className="w-4 h-4" />
            </Button>

            <div className="flex gap-2">
              <Button
                type="button"
                variant="outline"
                onClick={onCancel}
                disabled={isSubmitting || estimateMutation.isPending}
                className="btn-secondary"
              >
                Cancelar
              </Button>
              <Button
                type="button"
                onClick={handleEstimate}
                disabled={isSubmitting || estimateMutation.isPending}
                className="btn-primary"
              >
                {estimateMutation.isPending ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Estimando...
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4 mr-2" />
                    Estimar com IA
                  </>
                )}
              </Button>
              <Button
                type="button"
                onClick={async () => await handleSubmit()}
                disabled={isSubmitting || estimateMutation.isPending}
                className="btn-primary"
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Salvando...
                  </>
                ) : (
                  'Salvar'
                )}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
