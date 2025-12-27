/**
 * T025 ExperimentForm component.
 *
 * Form for creating/editing experiments.
 *
 * References:
 *   - Spec: specs/018-experiment-hub/spec.md (US2)
 *   - Types: src/types/experiment.ts
 */

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Loader2 } from 'lucide-react';
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
}

export function ExperimentForm({
  initialData,
  onSubmit,
  onCancel,
  isSubmitting = false,
}: ExperimentFormProps) {
  const [name, setName] = useState(initialData?.name ?? '');
  const [hypothesis, setHypothesis] = useState(initialData?.hypothesis ?? '');
  const [description, setDescription] = useState(initialData?.description ?? '');
  const [errors, setErrors] = useState<FormErrors>({});

  const validate = (): boolean => {
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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validate()) {
      return;
    }

    await onSubmit({
      name: name.trim(),
      hypothesis: hypothesis.trim(),
      description: description.trim() || undefined,
    });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
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
        {errors.name && (
          <p className="text-sm text-red-500">{errors.name}</p>
        )}
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
        {errors.hypothesis && (
          <p className="text-sm text-red-500">{errors.hypothesis}</p>
        )}
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
          rows={4}
          disabled={isSubmitting}
          className={errors.description ? 'border-red-500' : ''}
        />
        {errors.description && (
          <p className="text-sm text-red-500">{errors.description}</p>
        )}
        <p className="text-xs text-gray-500">{description.length}/2000</p>
      </div>

      <div className="flex justify-end gap-2 pt-4">
        <Button
          type="button"
          variant="outline"
          onClick={onCancel}
          disabled={isSubmitting}
        >
          Cancelar
        </Button>
        <Button type="submit" disabled={isSubmitting}>
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
