/**
 * T046 NewSimulationDialog component.
 *
 * Dialog for creating a new scorecard/simulation linked to an experiment.
 *
 * References:
 *   - Spec: specs/018-experiment-hub/spec.md (US4)
 *   - API: POST /experiments/{id}/scorecards
 */

import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import {
  useCreateScorecardForExperiment,
  useEstimateScorecardForExperiment,
} from '@/hooks/use-experiments';
import { newScorecardSchema, type NewScorecardFormData } from '@/lib/schemas';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog';
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
  FormDescription,
} from '@/components/ui/form';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import { Slider } from '@/components/ui/slider';
import { Loader2, Sparkles } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

interface ExperimentInfo {
  name: string;
  hypothesis: string;
  description?: string | null;
}

interface NewSimulationDialogProps {
  /** Whether the dialog is open */
  open: boolean;
  /** Callback when the dialog open state changes */
  onOpenChange: (open: boolean) => void;
  /** Experiment ID to link the scorecard to */
  experimentId: string;
  /** Experiment information for pre-filling */
  experiment: ExperimentInfo;
  /** Optional callback on successful creation */
  onSuccess?: () => void;
}

export function NewSimulationDialog({
  open,
  onOpenChange,
  experimentId,
  experiment,
  onSuccess,
}: NewSimulationDialogProps) {
  const { toast } = useToast();
  const createMutation = useCreateScorecardForExperiment();
  const estimateMutation = useEstimateScorecardForExperiment();

  const form = useForm<NewScorecardFormData>({
    resolver: zodResolver(newScorecardSchema),
    defaultValues: {
      feature_name: '',
      use_scenario: '',
      description_text: '',
      evaluators: [],
      complexity: { score: 0.5 },
      initial_effort: { score: 0.5 },
      perceived_risk: { score: 0.5 },
      time_to_value: { score: 0.5 },
    },
  });

  // Pre-fill form with experiment data when dialog opens
  useEffect(() => {
    if (open && experiment) {
      form.reset({
        feature_name: experiment.name,
        use_scenario: experiment.hypothesis,
        description_text: experiment.description || '',
        evaluators: [],
        complexity: { score: 0.5 },
        initial_effort: { score: 0.5 },
        perceived_risk: { score: 0.5 },
        time_to_value: { score: 0.5 },
      });
    }
  }, [open, experiment, form]);

  const handleEstimateWithAI = async () => {
    try {
      const estimate = await estimateMutation.mutateAsync(experimentId);

      // Update form with AI estimates
      form.setValue('complexity.score', estimate.complexity.value);
      form.setValue('initial_effort.score', estimate.initial_effort.value);
      form.setValue('perceived_risk.score', estimate.perceived_risk.value);
      form.setValue('time_to_value.score', estimate.time_to_value.value);

      toast({
        title: 'Estimativa gerada',
        description: 'Os scores foram preenchidos com base na análise da IA.',
      });
    } catch (error) {
      console.error('Error estimating scorecard:', error);
      toast({
        title: 'Erro na estimativa',
        description: error instanceof Error ? error.message : 'Erro desconhecido',
        variant: 'destructive',
      });
    }
  };

  const onSubmit = async (data: NewScorecardFormData) => {
    try {
      await createMutation.mutateAsync({
        experimentId,
        data: {
          feature_name: data.feature_name,
          use_scenario: data.use_scenario,
          description_text: data.description_text,
          evaluators: data.evaluators,
          complexity: data.complexity,
          initial_effort: data.initial_effort,
          perceived_risk: data.perceived_risk,
          time_to_value: data.time_to_value,
        },
      });

      toast({
        title: 'Simulacao criada',
        description: 'O scorecard foi criado com sucesso.',
      });

      onOpenChange(false);
      onSuccess?.();
    } catch (error) {
      console.error('Error creating scorecard:', error);
      toast({
        title: 'Erro ao criar simulacao',
        description: error instanceof Error ? error.message : 'Erro desconhecido',
        variant: 'destructive',
      });
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px] max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Nova Simulacao</DialogTitle>
          <DialogDescription>
            Configure o scorecard para iniciar uma nova simulacao
          </DialogDescription>
        </DialogHeader>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            {/* Experiment Info (read-only display) */}
            <div className="space-y-3 rounded-lg bg-muted/50 p-4">
              <h4 className="text-sm font-medium text-muted-foreground">
                Dados do Experimento
              </h4>
              <div className="space-y-2">
                <div>
                  <span className="text-xs text-muted-foreground">Nome</span>
                  <p className="text-sm font-medium">{experiment.name}</p>
                </div>
                <div>
                  <span className="text-xs text-muted-foreground">Hipótese</span>
                  <p className="text-sm">{experiment.hypothesis}</p>
                </div>
                {experiment.description && (
                  <div>
                    <span className="text-xs text-muted-foreground">Descrição</span>
                    <p className="text-sm text-muted-foreground">
                      {experiment.description}
                    </p>
                  </div>
                )}
              </div>
            </div>

            {/* Hidden fields that mirror experiment data */}
            <input type="hidden" {...form.register('feature_name')} />
            <input type="hidden" {...form.register('use_scenario')} />

            <FormField
              control={form.control}
              name="description_text"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Descrição Adicional (opcional)</FormLabel>
                  <FormControl>
                    <Textarea
                      placeholder="Adicione detalhes específicos para esta simulação..."
                      rows={2}
                      {...field}
                    />
                  </FormControl>
                  <FormDescription>
                    Contexto adicional para a simulação além dos dados do experimento
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* Dimension Sliders */}
            <div className="space-y-4 pt-2">
              <div className="flex items-center justify-between">
                <h4 className="text-sm font-medium text-gray-700">
                  Dimensoes do Scorecard
                </h4>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={handleEstimateWithAI}
                  disabled={estimateMutation.isPending}
                >
                  {estimateMutation.isPending ? (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  ) : (
                    <Sparkles className="mr-2 h-4 w-4" />
                  )}
                  Estimar com IA
                </Button>
              </div>

              <FormField
                control={form.control}
                name="complexity.score"
                render={({ field }) => (
                  <FormItem>
                    <div className="flex justify-between">
                      <FormLabel>Complexidade</FormLabel>
                      <span className="text-sm text-gray-500">
                        {(field.value * 100).toFixed(0)}%
                      </span>
                    </div>
                    <FormControl>
                      <Slider
                        min={0}
                        max={1}
                        step={0.05}
                        value={[field.value]}
                        onValueChange={(value) => field.onChange(value[0])}
                      />
                    </FormControl>
                    <FormDescription>
                      Quao complexo e o recurso para os usuarios
                    </FormDescription>
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="initial_effort.score"
                render={({ field }) => (
                  <FormItem>
                    <div className="flex justify-between">
                      <FormLabel>Esforco Inicial</FormLabel>
                      <span className="text-sm text-gray-500">
                        {(field.value * 100).toFixed(0)}%
                      </span>
                    </div>
                    <FormControl>
                      <Slider
                        min={0}
                        max={1}
                        step={0.05}
                        value={[field.value]}
                        onValueChange={(value) => field.onChange(value[0])}
                      />
                    </FormControl>
                    <FormDescription>
                      Quanto esforco o usuario precisa investir inicialmente
                    </FormDescription>
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="perceived_risk.score"
                render={({ field }) => (
                  <FormItem>
                    <div className="flex justify-between">
                      <FormLabel>Risco Percebido</FormLabel>
                      <span className="text-sm text-gray-500">
                        {(field.value * 100).toFixed(0)}%
                      </span>
                    </div>
                    <FormControl>
                      <Slider
                        min={0}
                        max={1}
                        step={0.05}
                        value={[field.value]}
                        onValueChange={(value) => field.onChange(value[0])}
                      />
                    </FormControl>
                    <FormDescription>
                      Quanto risco o usuario percebe ao usar o recurso
                    </FormDescription>
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="time_to_value.score"
                render={({ field }) => (
                  <FormItem>
                    <div className="flex justify-between">
                      <FormLabel>Tempo ate Valor</FormLabel>
                      <span className="text-sm text-gray-500">
                        {(field.value * 100).toFixed(0)}%
                      </span>
                    </div>
                    <FormControl>
                      <Slider
                        min={0}
                        max={1}
                        step={0.05}
                        value={[field.value]}
                        onValueChange={(value) => field.onChange(value[0])}
                      />
                    </FormControl>
                    <FormDescription>
                      Quanto tempo ate o usuario perceber valor
                    </FormDescription>
                  </FormItem>
                )}
              />
            </div>

            <div className="flex justify-end gap-3 pt-4">
              <Button
                type="button"
                variant="outline"
                onClick={() => onOpenChange(false)}
                disabled={createMutation.isPending}
              >
                Cancelar
              </Button>
              <Button type="submit" disabled={createMutation.isPending}>
                {createMutation.isPending && (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                )}
                Criar Scorecard
              </Button>
            </div>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}
