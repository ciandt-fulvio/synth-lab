/**
 * QuestionInput component for natural language business question input.
 *
 * Allows users to input business questions for causal simulation.
 *
 * References:
 *   - Spec: specs/035-causal-simulation/spec.md
 *   - Hook: hooks/use-simulations.ts
 */

import { useState } from 'react';
import { Loader2, Sparkles } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { useCreateSimulation } from '@/hooks/use-simulations';
import { toast } from 'sonner';

interface QuestionInputProps {
  /**
   * Callback when simulation is created successfully.
   */
  onSimulationCreated?: (simulationId: string) => void;

  /**
   * Optional default question text.
   */
  defaultQuestion?: string;

  /**
   * Optional random seed for reproducibility.
   */
  randomSeed?: number;

  /**
   * Optional number of worlds to simulate.
   */
  nWorlds?: number;
}

/**
 * QuestionInput component.
 *
 * Provides textarea for business question input and submit button.
 *
 * @example
 * <QuestionInput
 *   onSimulationCreated={(id) => navigate(`/simulations/${id}`)}
 * />
 */
export function QuestionInput({
  onSimulationCreated,
  defaultQuestion = '',
  randomSeed = 42,
  nWorlds = 500,
}: QuestionInputProps) {
  const [question, setQuestion] = useState(defaultQuestion);
  const { mutate: createSimulation, isPending } = useCreateSimulation();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    const trimmedQuestion = question.trim();
    if (trimmedQuestion.length < 10) {
      toast.error('Pergunta muito curta', {
        description: 'A pergunta deve ter pelo menos 10 caracteres.',
      });
      return;
    }

    if (trimmedQuestion.length > 2000) {
      toast.error('Pergunta muito longa', {
        description: 'A pergunta deve ter no máximo 2000 caracteres.',
      });
      return;
    }

    createSimulation(
      {
        question_text: trimmedQuestion,
        random_seed: randomSeed,
        n_worlds: nWorlds,
      },
      {
        onSuccess: (data) => {
          toast.success('Simulação criada', {
            description: 'Analisando pergunta e construindo modelo causal...',
          });
          onSimulationCreated?.(data.id);
        },
        onError: (error) => {
          toast.error('Erro ao criar simulação', {
            description: error.message || 'Tente novamente.',
          });
        },
      }
    );
  };

  const exampleQuestions = [
    'Qual será a taxa de adoção de um serviço de assinatura semanal de refeições?',
    'Quantos usuários vão converter do plano gratuito para o pago no Q1 2026?',
    'Qual é a receita esperada do lançamento de uma nova feature premium?',
  ];

  const handleExampleClick = (example: string) => {
    setQuestion(example);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="space-y-2">
        <Label htmlFor="question" className="text-section-title">
          Pergunta de Negócio
        </Label>
        <Textarea
          id="question"
          placeholder="Exemplo: Qual será a taxa de adoção de um serviço de assinatura semanal de refeições?"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          rows={4}
          className="resize-none text-base"
          disabled={isPending}
        />
        <p className="text-sm text-slate-500">
          {question.length}/2000 caracteres
        </p>
      </div>

      {/* Example questions */}
      <div className="space-y-2">
        <p className="text-sm font-medium text-slate-700">Perguntas de exemplo:</p>
        <div className="flex flex-wrap gap-2">
          {exampleQuestions.map((example, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => handleExampleClick(example)}
              className="text-xs px-3 py-1.5 rounded-full bg-indigo-50 text-indigo-700 hover:bg-indigo-100 transition-colors"
              disabled={isPending}
            >
              {example}
            </button>
          ))}
        </div>
      </div>

      {/* Submit button */}
      <Button
        type="submit"
        disabled={isPending || question.trim().length < 10}
        className="w-full btn-primary"
      >
        {isPending ? (
          <>
            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            Criando Simulação...
          </>
        ) : (
          <>
            <Sparkles className="h-4 w-4 mr-2" />
            Criar Simulação
          </>
        )}
      </Button>

      {/* Info message */}
      <div className="rounded-lg bg-blue-50 border border-blue-200 p-4">
        <p className="text-sm text-blue-800">
          <strong>Como funciona:</strong> O sistema vai analisar sua pergunta, construir um
          modelo causal com 8-20 variáveis e gerar {nWorlds} mundos sintéticos para projetar resultados.
        </p>
      </div>
    </form>
  );
}
