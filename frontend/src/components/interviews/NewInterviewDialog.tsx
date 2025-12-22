// src/components/interviews/NewInterviewDialog.tsx

import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useTopicsList } from '@/hooks/use-topics';
import { useExecuteResearch } from '@/hooks/use-research';
import { newInterviewSchema, type NewInterviewFormData } from '@/lib/schemas';
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import { Loader2 } from 'lucide-react';

interface NewInterviewDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function NewInterviewDialog({ open, onOpenChange }: NewInterviewDialogProps) {
  const navigate = useNavigate();
  const { data: topics, isLoading: topicsLoading } = useTopicsList();
  const executeResearchMutation = useExecuteResearch();

  const form = useForm<NewInterviewFormData>({
    resolver: zodResolver(newInterviewSchema),
    defaultValues: {
      topic_name: '',
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

  const onSubmit = async (data: NewInterviewFormData) => {
    try {
      const response = await executeResearchMutation.mutateAsync(data);
      onOpenChange(false);
      navigate(`/interviews/${response.exec_id}`);
    } catch (error) {
      console.error('Error executing research:', error);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Nova Entrevista</DialogTitle>
          <DialogDescription>
            Configure os parâmetros para iniciar uma nova pesquisa
          </DialogDescription>
        </DialogHeader>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="topic_name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Tópico</FormLabel>
                  <Select onValueChange={field.onChange} value={field.value}>
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="Selecione um tópico" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      {topicsLoading ? (
                        <div className="flex items-center justify-center py-6">
                          <Loader2 className="h-4 w-4 animate-spin" />
                        </div>
                      ) : (
                        topics?.data.map((topic) => (
                          <SelectItem key={topic.name} value={topic.name}>
                            {topic.name}
                          </SelectItem>
                        ))
                      )}
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="additional_context"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Contexto Adicional (Opcional)</FormLabel>
                  <FormControl>
                    <Textarea
                      placeholder="Adicione informações complementares sobre o cenário da pesquisa..."
                      rows={2}
                      {...field}
                    />
                  </FormControl>
                  <FormDescription>
                    Complemente o tópico com contexto adicional para a pesquisa
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
                  <FormLabel>Máximo de Turnos</FormLabel>
                  <FormControl>
                    <Input
                      type="number"
                      {...field}
                      onChange={(e) => field.onChange(parseInt(e.target.value))}
                    />
                  </FormControl>
                  <FormDescription>Número máximo de perguntas por synth (1-20)</FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            <div className="flex justify-end gap-3 pt-4">
              <Button
                type="button"
                variant="outline"
                onClick={() => onOpenChange(false)}
                disabled={executeResearchMutation.isPending}
              >
                Cancelar
              </Button>
              <Button type="submit" disabled={executeResearchMutation.isPending}>
                {executeResearchMutation.isPending && (
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
