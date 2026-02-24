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
import { Loader2, Shuffle, TrendingUp, TrendingDown, Minus, Zap } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { cn } from '@/lib/utils';

// Schema for interview creation (topic comes from experiment's interview guide)
const interviewFormSchema = z.object({
  additional_context: z.string().optional(),
  synth_count: z.number().min(1).max(50),
  max_turns: z.number().min(1).max(10),
  synth_selection_type: z.string().default('random'),
});

type InterviewFormData = z.infer<typeof interviewFormSchema>;

interface SelectionOption {
  value: string;
  label: string;
  description: string;
  icon: React.ReactNode;
  colorClass: string;
}

const SELECTION_OPTIONS: SelectionOption[] = [
  {
    value: 'random',
    label: 'Aleatório',
    description: 'Amostra representativa da população',
    icon: <Shuffle className="h-4 w-4" />,
    colorClass: 'border-slate-300 data-[selected=true]:border-indigo-500 data-[selected=true]:bg-indigo-50',
  },
  {
    value: 'propensos',
    label: 'Propensos',
    description: 'Alta probabilidade de adoção',
    icon: <TrendingUp className="h-4 w-4" />,
    colorClass: 'border-slate-300 data-[selected=true]:border-emerald-500 data-[selected=true]:bg-emerald-50',
  },
  {
    value: 'indecisos',
    label: 'Indecisos',
    description: 'Probabilidade próxima a 50%',
    icon: <Minus className="h-4 w-4" />,
    colorClass: 'border-slate-300 data-[selected=true]:border-amber-500 data-[selected=true]:bg-amber-50',
  },
  {
    value: 'resistentes',
    label: 'Resistentes',
    description: 'Baixa probabilidade de adoção',
    icon: <TrendingDown className="h-4 w-4" />,
    colorClass: 'border-slate-300 data-[selected=true]:border-red-400 data-[selected=true]:bg-red-50',
  },
  {
    value: 'sensiveis',
    label: 'Sensíveis',
    description: 'Maior variação entre cenários',
    icon: <Zap className="h-4 w-4" />,
    colorClass: 'border-slate-300 data-[selected=true]:border-violet-500 data-[selected=true]:bg-violet-50',
  },
];

const ICON_COLOR: Record<string, string> = {
  random: 'text-indigo-500',
  propensos: 'text-emerald-500',
  indecisos: 'text-amber-500',
  resistentes: 'text-red-400',
  sensiveis: 'text-violet-500',
};

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
      synth_count: 9,
      max_turns: 5,
      synth_selection_type: 'random',
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
          synth_selection_type: data.synth_selection_type,
        },
      });

      toast({
        title: 'Entrevista iniciada',
        description: 'A entrevista foi criada e esta em execucao.',
      });

      onOpenChange(false);
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

  const selectedType = form.watch('synth_selection_type');

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[520px]">
        <DialogHeader>
          <DialogTitle>Nova Entrevista</DialogTitle>
          <DialogDescription>
            Configure os parametros para iniciar uma nova entrevista.
            O guia de entrevista do experimento sera utilizado.
          </DialogDescription>
        </DialogHeader>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-5">

            {/* Synth selection type */}
            <FormField
              control={form.control}
              name="synth_selection_type"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Tipo de Synths</FormLabel>
                  <div className="grid grid-cols-5 gap-1.5 mt-1">
                    {SELECTION_OPTIONS.map((opt) => (
                      <button
                        key={opt.value}
                        type="button"
                        data-selected={field.value === opt.value}
                        onClick={() => field.onChange(opt.value)}
                        className={cn(
                          'flex flex-col items-center gap-1.5 rounded-lg border p-2.5 text-center transition-all cursor-pointer',
                          'hover:border-slate-400 hover:bg-slate-50',
                          opt.colorClass,
                        )}
                      >
                        <span className={cn(
                          'transition-colors',
                          field.value === opt.value
                            ? ICON_COLOR[opt.value]
                            : 'text-slate-400',
                        )}>
                          {opt.icon}
                        </span>
                        <span className={cn(
                          'text-xs font-medium leading-tight transition-colors',
                          field.value === opt.value ? 'text-slate-800' : 'text-slate-500',
                        )}>
                          {opt.label}
                        </span>
                      </button>
                    ))}
                  </div>
                  <FormDescription className="text-xs">
                    {SELECTION_OPTIONS.find(o => o.value === selectedType)?.description}
                    {selectedType !== 'random' && (
                      <span className="text-slate-400"> · usa dados da última simulação</span>
                    )}
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
                  <FormLabel>Quantos Synths</FormLabel>
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
                  <FormDescription>Numero maximo de perguntas por synth (1-10)</FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="additional_context"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Contexto Adicional <span className="text-slate-400 font-normal">(Opcional)</span></FormLabel>
                  <FormControl>
                    <Textarea
                      placeholder="Adicione informacoes complementares sobre o cenario da pesquisa..."
                      rows={2}
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <div className="flex justify-end gap-3 pt-2">
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
