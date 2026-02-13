/**
 * ExperimentForm component (Refactored).
 *
 * Two-step form for creating/editing experiments with narrative mechanism configuration.
 * Step 1: Basic info (name, hypothesis, description)
 * Step 2: Narrative-based mechanism configuration via LLM (039-narrative-mechanism-config)
 *
 * References:
 *   - Spec: specs/039-narrative-mechanism-config/spec.md
 *   - Types: src/types/experiment.ts
 */

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Loader2, ArrowRight, Users } from 'lucide-react';
import { useSynthGroups } from '@/hooks/use-synth-groups';
import { NarrativeStep } from './NarrativeStep';
import type { ExperimentCreate, ExperimentUpdate, ScorecardData } from '@/types/experiment';
import type { MechanismValues } from '@/types/mechanisms';
import type { FeatureMechanisms } from '@/types/simulation';

interface ExperimentFormProps {
  /** Initial values for edit mode */
  initialData?: ExperimentUpdate & { scorecard_data?: ScorecardData | null };
  /** Submit handler */
  onSubmit: (data: ExperimentCreate) => void | Promise<void>;
  /** Cancel handler */
  onCancel: () => void;
  /** Whether the form is submitting */
  isSubmitting?: boolean;
  /** Whether to show narrative mechanism configuration (default: true for new experiments) */
  showScorecard?: boolean;
}

interface FormErrors {
  name?: string;
  hypothesis?: string;
  description?: string;
  synth_group_id?: string;
}

/**
 * Convert MechanismValues to FeatureMechanisms format for storage.
 * Maps mechanism keys to scorecard_data.mechanisms structure.
 */
function mechanismValuesToFeatureMechanisms(values: MechanismValues): FeatureMechanisms {
  return {
    irreversibility: values.irreversibility ?? 0.5,
    network_effect: values.network_effect ?? 0.5,
    institutional_trust: values.institutional_trust ?? 0.5,
    habit_displacement: values.habit_displacement ?? 0.5,
    learning_curve: values.learning_curve ?? 0.5,
    social_visibility: values.social_visibility ?? 0.5,
    intrinsic_value: values.intrinsic_value ?? 0.5,
    operational_friction: values.operational_friction ?? 0.5,
    frequency_of_use: values.frequency_of_use ?? 0.5,
  };
}

export function ExperimentForm({
  initialData,
  onSubmit,
  onCancel,
  isSubmitting = false,
  showScorecard = true,
}: ExperimentFormProps) {
  const { data: synthGroupsData, isLoading: isLoadingSynthGroups } = useSynthGroups();

  // Step management (1 = basic info, 2 = narrative mechanism config)
  const [step, setStep] = useState(1);

  const [name, setName] = useState(initialData?.name ?? '');
  const [hypothesis, setHypothesis] = useState(initialData?.hypothesis ?? '');
  const [description, setDescription] = useState(initialData?.description ?? '');
  const [selectedSynthGroupId, setSelectedSynthGroupId] = useState<string>('');
  const [errors, setErrors] = useState<FormErrors>({});

  // Store mechanism values from narrative step (T028)
  const [mechanismValues, setMechanismValues] = useState<MechanismValues | null>(null);
  const [inferredTypes, setInferredTypes] = useState<string[]>([]);

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

    // Synth group validation
    if (!selectedSynthGroupId) {
      newErrors.synth_group_id = 'Grupo de Synths é obrigatório';
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

  /**
   * Handle continue from NarrativeStep.
   * Stores mechanism values and submits the form (T028).
   */
  const handleNarrativeContinue = async (values: MechanismValues, types: string[]) => {
    setMechanismValues(values);
    setInferredTypes(types);

    // Build experiment data with narrative-based mechanism configuration
    const experimentData: ExperimentCreate = {
      name: name.trim(),
      hypothesis: hypothesis.trim(),
      description: description.trim() || undefined,
      synth_group_id: selectedSynthGroupId,
    };

    // Include scorecard data with mechanisms (T028)
    experimentData.scorecard_data = {
      feature_name: name.trim(),
      description_text: hypothesis.trim(),
      // Store mechanism values from narrative configuration
      mechanisms: mechanismValuesToFeatureMechanisms(values),
      // Store inferred feature types
      feature_types: types,
    };

    await onSubmit(experimentData);
  };

  const handleSubmit = async () => {
    // Build experiment data without scorecard (for single-step form)
    const experimentData: ExperimentCreate = {
      name: name.trim(),
      hypothesis: hypothesis.trim(),
      description: description.trim() || undefined,
      synth_group_id: selectedSynthGroupId,
    };

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
            Grupo de Synths <span className="text-red-500">*</span>
          </Label>
          <Select
            value={selectedSynthGroupId}
            onValueChange={setSelectedSynthGroupId}
            disabled={isSubmitting || isLoadingSynthGroups}
          >
            <SelectTrigger id="synth-group" className={errors.synth_group_id ? 'border-red-500' : ''}>
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
          {errors.synth_group_id && <p className="text-sm text-red-500">{errors.synth_group_id}</p>}
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
              Grupo de Synths <span className="text-red-500">*</span>
            </Label>
            <Select
              value={selectedSynthGroupId}
              onValueChange={setSelectedSynthGroupId}
              disabled={isSubmitting || isLoadingSynthGroups}
            >
              <SelectTrigger id="synth-group-step1" className={errors.synth_group_id ? 'border-red-500' : ''}>
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
            {errors.synth_group_id && <p className="text-sm text-red-500">{errors.synth_group_id}</p>}
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

      {/* Step 2: Narrative Mechanism Configuration (039-narrative-mechanism-config) */}
      {step === 2 && (
        <NarrativeStep
          name={name.trim()}
          hypothesis={hypothesis.trim()}
          description={description.trim() || undefined}
          onContinue={handleNarrativeContinue}
          onBack={handlePrevStep}
          isSubmitting={isSubmitting}
        />
      )}
    </div>
  );
}
