/**
 * NewExplorationDialog component.
 *
 * Dialog for starting a new scenario exploration from an experiment.
 *
 * References:
 *   - Spec: specs/025-exploration-frontend/spec.md (US1)
 *   - API: POST /explorations
 */

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useStartExploration } from '@/hooks/use-exploration';
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
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Slider } from '@/components/ui/slider';
import { Loader2, TreeDeciduous } from 'lucide-react';
import { toast } from 'sonner';

// Form validation schema
const explorationFormSchema = z.object({
  goal_value: z
    .number()
    .min(1, 'Meta deve ser maior que 0%')
    .max(100, 'Meta deve ser menor ou igual a 100%'),
  beam_width: z
    .number()
    .int()
    .min(1, 'Beam width mínimo é 1')
    .max(10, 'Beam width máximo é 10'),
  max_depth: z
    .number()
    .int()
    .min(1, 'Profundidade mínima é 1')
    .max(10, 'Profundidade máxima é 10'),
});

type ExplorationFormData = z.infer<typeof explorationFormSchema>;

interface NewExplorationDialogProps {
  /** Whether the dialog is open */
  open: boolean;
  /** Callback when the dialog open state changes */
  onOpenChange: (open: boolean) => void;
  /** Experiment ID to link the exploration to */
  experimentId: string;
  /** Current baseline success rate (for context) */
  baselineSuccessRate?: number | null;
  /** Optional callback on successful creation */
  onSuccess?: (explorationId: string) => void;
}

export function NewExplorationDialog({
  open,
  onOpenChange,
  experimentId,
  baselineSuccessRate,
  onSuccess,
}: NewExplorationDialogProps) {
  const { startExploration, isPending, error } = useStartExploration();

  const form = useForm<ExplorationFormData>({
    resolver: zodResolver(explorationFormSchema),
    defaultValues: {
      goal_value: baselineSuccessRate ? Math.min(Math.round((baselineSuccessRate + 0.15) * 100), 100) : 40,
      beam_width: 3,
      max_depth: 5,
    },
  });

  const onSubmit = async (data: ExplorationFormData) => {
    try {
      const exploration = await startExploration({
        experiment_id: experimentId,
        goal_value: data.goal_value / 100, // Convert from % to 0-1
        beam_width: data.beam_width,
        max_depth: data.max_depth,
      });

      toast.success('Exploração iniciada', {
        description: 'A busca por cenários otimizados está em andamento.',
      });

      onOpenChange(false);
      onSuccess?.(exploration.id);
    } catch (err) {
      console.error('Error starting exploration:', err);
      toast.error('Erro ao iniciar exploração', {
        description: err instanceof Error ? err.message : 'Erro desconhecido',
      });
    }
  };

  const goalValue = form.watch('goal_value');

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <div className="icon-box-primary">
              <TreeDeciduous className="h-5 w-5" />
            </div>
            Nova Exploração de Cenários
          </DialogTitle>
          <DialogDescription>
            Configure os parâmetros para explorar cenários otimizados com IA
          </DialogDescription>
        </DialogHeader>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
            {/* Baseline Context */}
            {baselineSuccessRate !== null && baselineSuccessRate !== undefined && (
              <div className="rounded-lg bg-muted/50 p-4">
                <p className="text-sm text-muted-foreground">
                  Taxa de sucesso atual:{' '}
                  <span className="font-medium text-foreground">
                    {(baselineSuccessRate * 100).toFixed(1)}%
                  </span>
                </p>
              </div>
            )}

            {/* Goal Value */}
            <FormField
              control={form.control}
              name="goal_value"
              render={({ field }) => (
                <FormItem>
                  <div className="flex justify-between items-center">
                    <FormLabel>Meta de Success Rate</FormLabel>
                    <div className="flex items-center gap-2">
                      <Input
                        type="number"
                        min={1}
                        max={100}
                        className="w-20 h-8 text-center"
                        value={field.value}
                        onChange={(e) => field.onChange(Number(e.target.value))}
                      />
                      <span className="text-sm text-muted-foreground">%</span>
                    </div>
                  </div>
                  <FormControl>
                    <Slider
                      min={1}
                      max={100}
                      step={1}
                      value={[field.value]}
                      onValueChange={(value) => field.onChange(value[0])}
                    />
                  </FormControl>
                  <FormDescription>
                    Taxa de sucesso desejada para o cenário otimizado
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* Advanced Settings */}
            <div className="space-y-4 border-t pt-4">
              <p className="text-sm font-medium text-muted-foreground">
                Configurações Avançadas
              </p>

              <div className="grid grid-cols-2 gap-4">
                <FormField
                  control={form.control}
                  name="beam_width"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Beam Width</FormLabel>
                      <FormControl>
                        <Input
                          type="number"
                          min={1}
                          max={10}
                          {...field}
                          onChange={(e) => field.onChange(Number(e.target.value))}
                        />
                      </FormControl>
                      <FormDescription className="text-xs">
                        Cenários por iteração
                      </FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="max_depth"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Profundidade Máxima</FormLabel>
                      <FormControl>
                        <Input
                          type="number"
                          min={1}
                          max={10}
                          {...field}
                          onChange={(e) => field.onChange(Number(e.target.value))}
                        />
                      </FormControl>
                      <FormDescription className="text-xs">
                        Níveis na árvore
                      </FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>
            </div>

            {/* Error Display */}
            {error && (
              <div className="rounded-lg bg-destructive/10 p-3 text-sm text-destructive">
                {error.message}
              </div>
            )}

            {/* Actions */}
            <div className="flex justify-end gap-3 pt-2">
              <Button
                type="button"
                variant="outline"
                onClick={() => onOpenChange(false)}
                disabled={isPending}
              >
                Cancelar
              </Button>
              <Button type="submit" disabled={isPending} className="btn-primary">
                {isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Iniciar Exploração
              </Button>
            </div>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}
