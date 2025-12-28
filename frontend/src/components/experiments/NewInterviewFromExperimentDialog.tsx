/**
 * NewInterviewFromExperimentDialog component.
 *
 * Dialog for creating a new interview linked to an experiment.
 * Uses the experiment's interview guide for context.
 *
 * References:
 *   - Spec: specs/018-experiment-hub/spec.md (US5)
 *   - API: POST /experiments/{id}/interviews
 */

import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useCreateInterviewForExperiment } from '@/hooks/use-experiments';
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
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import { Loader2 } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

// Schema for interview creation (topic comes from experiment's interview guide)
const interviewFormSchema = z.object({
  additional_context: z.string().optional(),
  synth_count: z.number().min(1).max(50),
  max_turns: z.number().min(1).max(20),
  generate_summary: z.boolean(),
});

type InterviewFormData = z.infer<typeof interviewFormSchema>;

interface NewInterviewFromExperimentDialogProps {
  /** Whether the dialog is open */
  open: boolean;
  /** Callback when the dialog open state changes */
  onOpenChange: (open: boolean) => void;
  /** Experiment ID to link the interview to */
  experimentId: string;
}

export function NewInterviewFromExperimentDialog({
  open,
  onOpenChange,
  experimentId,
}: NewInterviewFromExperimentDialogProps) {
  const navigate = useNavigate();
  const { toast } = useToast();
  const createMutation = useCreateInterviewForExperiment();

  const form = useForm<InterviewFormData>({
    resolver: zodResolver(interviewFormSchema),
    defaultValues: {
      additional_context: '',
      synth_count: 5,
      max_turns: 6,
      generate_summary: true,
    },
  });

  useEffect(() => {
    if (!open) {
      form.reset();
    }
  }, [open, form]);

  const onSubmit = async (data: InterviewFormData) => {
    try {
      const response = await createMutation.mutateAsync({
        experimentId,
        data: {
          additional_context: data.additional_context || undefined,
          synth_count: data.synth_count,
          max_turns: data.max_turns,
          generate_summary: data.generate_summary,
        },
      });

      toast({
        title: 'Entrevista iniciada',
        description: 'A entrevista foi criada e esta em execucao.',
      });

      onOpenChange(false);
      // Navigate to interview detail page
      navigate(`/experiments/${experimentId}/interviews/${response.exec_id}`);
    } catch (error) {
      console.error('Error creating interview:', error);
      toast({
        title: 'Erro ao criar entrevista',
        description: error instanceof Error ? error.message : 'Erro desconhecido',
        variant: 'destructive',
      });
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Nova Entrevista</DialogTitle>
          <DialogDescription>
            Configure os parametros para iniciar uma nova entrevista.
            O guia de entrevista do experimento sera utilizado.
          </DialogDescription>
        </DialogHeader>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="additional_context"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Contexto Adicional (Opcional)</FormLabel>
                  <FormControl>
                    <Textarea
                      placeholder="Adicione informacoes complementares sobre o cenario da pesquisa..."
                      rows={2}
                      {...field}
                    />
                  </FormControl>
                  <FormDescription>
                    Complemente o guia de entrevista com contexto adicional
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="synth_count"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Entrevistar quantos Synths</FormLabel>
                  <FormControl>
                    <Input
                      type="number"
                      {...field}
                      onChange={(e) => field.onChange(parseInt(e.target.value))}
                    />
                  </FormControl>
                  <FormDescription>Quantidade de synths para entrevistar (1-50)</FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="max_turns"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Maximo de Turnos</FormLabel>
                  <FormControl>
                    <Input
                      type="number"
                      {...field}
                      onChange={(e) => field.onChange(parseInt(e.target.value))}
                    />
                  </FormControl>
                  <FormDescription>Numero maximo de perguntas por synth (1-20)</FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

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
                Iniciar Entrevista
              </Button>
            </div>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}
