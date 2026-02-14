/**
 * ExperimentForm component.
 *
 * Form for creating/editing experiments with basic info.
 *
 * References:
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
import { Loader2, Users } from 'lucide-react';
import { useSynthGroups } from '@/hooks/use-synth-groups';
import type { ExperimentCreate, ExperimentUpdate } from '@/types/experiment';

interface ExperimentFormProps {
  /** Initial values for edit mode */
  initialData?: ExperimentUpdate;
  /** Submit handler */
  onSubmit: (data: ExperimentCreate) => void | Promise<void>;
  /** Cancel handler */
  onCancel: () => void;
  /** Whether the form is submitting */
  isSubmitting?: boolean;
}

interface FormErrors {
  name?: string;
  hypothesis?: string;
  description?: string;
  synth_group_id?: string;
}

export function ExperimentForm({
  initialData,
  onSubmit,
  onCancel,
  isSubmitting = false,
}: ExperimentFormProps) {
  const { data: synthGroupsData, isLoading: isLoadingSynthGroups } = useSynthGroups();

  const [name, setName] = useState(initialData?.name ?? '');
  const [hypothesis, setHypothesis] = useState(initialData?.hypothesis ?? '');
  const [description, setDescription] = useState(initialData?.description ?? '');
  const [selectedSynthGroupId, setSelectedSynthGroupId] = useState<string>('');
  const [errors, setErrors] = useState<FormErrors>({});

  const validate = (): boolean => {
    const newErrors: FormErrors = {};

    if (!name.trim()) {
      newErrors.name = 'Nome é obrigatório';
    } else if (name.length > 100) {
      newErrors.name = 'Nome deve ter no máximo 100 caracteres';
    }

    if (!hypothesis.trim()) {
      newErrors.hypothesis = 'Hipótese é obrigatória';
    } else if (hypothesis.length > 500) {
      newErrors.hypothesis = 'Hipótese deve ter no máximo 500 caracteres';
    }

    if (description && description.length > 2000) {
      newErrors.description = 'Descrição deve ter no máximo 2000 caracteres';
    }

    if (!selectedSynthGroupId) {
      newErrors.synth_group_id = 'Grupo de Synths é obrigatório';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async () => {
    const experimentData: ExperimentCreate = {
      name: name.trim(),
      hypothesis: hypothesis.trim(),
      description: description.trim() || undefined,
      synth_group_id: selectedSynthGroupId,
    };

    await onSubmit(experimentData);
  };

  return (
    <form
      onSubmit={async (e) => {
        e.preventDefault();
        if (validate()) {
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
          Synths deste grupo serão usados em entrevistas
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
            'Criar Experimento'
          )}
        </Button>
      </div>
    </form>
  );
}
