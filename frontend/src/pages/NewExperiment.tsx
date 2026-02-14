/**
 * NewExperiment page - Full page for creating a new experiment.
 */

import { useNavigate } from 'react-router-dom';
import { ExperimentForm } from '@/components/experiments/ExperimentForm';
import { useCreateExperiment } from '@/hooks/use-experiments';
import { SynthLabHeader } from '@/components/shared/SynthLabHeader';
import { useToast } from '@/hooks/use-toast';
import type { ExperimentCreate } from '@/types/experiment';

export default function NewExperiment() {
  const navigate = useNavigate();
  const { toast } = useToast();
  const createMutation = useCreateExperiment();

  const handleSubmit = async (formData: ExperimentCreate) => {
    try {
      const created = await createMutation.mutateAsync(formData);
      toast({
        title: 'Experimento criado',
        description: `"${formData.name}" foi criado com sucesso.`,
      });
      navigate(`/experiments/${created.id}`);
    } catch (err) {
      toast({
        title: 'Erro ao criar experimento',
        description: err instanceof Error ? err.message : 'Erro desconhecido',
        variant: 'destructive',
      });
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 via-white to-slate-50">
      <SynthLabHeader subtitle="Novo Experimento" backTo="/" />

      <main className="max-w-xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
          <h2 className="text-xl font-bold text-slate-900 mb-6">
            Criar Experimento
          </h2>
          <ExperimentForm
            onSubmit={handleSubmit}
            onCancel={() => navigate('/')}
            isSubmitting={createMutation.isPending}
          />
        </div>
      </main>
    </div>
  );
}
