/**
 * Index page - Landing page with CTA to create experiment.
 */

import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { FlaskConical, Plus, Users } from 'lucide-react';
import { SynthLabHeader } from '@/components/shared/SynthLabHeader';

export default function Index() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 via-white to-slate-50">
      <SynthLabHeader
        actions={
          <Button
            variant="outline"
            size="sm"
            onClick={() => navigate('/synths')}
            className="btn-secondary"
          >
            <Users className="h-4 w-4 mr-2" />
            Synths
          </Button>
        }
      />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="flex flex-col items-center justify-center text-center">
          <div className="p-4 bg-gradient-to-br from-purple-500 to-blue-500 rounded-2xl text-white shadow-lg shadow-purple-200 mb-8">
            <FlaskConical className="h-12 w-12" />
          </div>

          <h1 className="text-4xl font-bold text-slate-900 mb-4">
            Synth Lab
          </h1>
          <p className="text-lg text-slate-500 max-w-md mb-8">
            Crie experimentos e entreviste synths para validar suas hipóteses de produto.
          </p>

          <div className="flex gap-4">
            <Button
              onClick={() => navigate('/new-experiment/')}
              className="btn-primary text-lg px-8 py-6"
            >
              <Plus className="w-5 h-5 mr-2" />
              Criar Experimento
            </Button>
            <Button
              variant="outline"
              onClick={() => navigate('/old-home/')}
              className="btn-secondary text-lg px-8 py-6"
            >
              Ver Experimentos
            </Button>
          </div>
        </div>
      </main>
    </div>
  );
}
