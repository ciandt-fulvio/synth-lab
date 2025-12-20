// src/components/synths/SynthList.tsx

import { useState } from 'react';
import { SynthCard } from './SynthCard';
import { SynthDetailDialog } from './SynthDetailDialog';
import { useSynthsList } from '@/hooks/use-synths';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2, Users } from 'lucide-react';

export function SynthList() {
  const [selectedSynthId, setSelectedSynthId] = useState<string | null>(null);
  const { data, isLoading, error } = useSynthsList();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertDescription>
          Erro ao carregar synths: {error.message}
        </AlertDescription>
      </Alert>
    );
  }

  if (!data || data.data.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <Users className="h-12 w-12 text-muted-foreground mb-4" />
        <h3 className="text-lg font-semibold mb-2">Nenhum synth encontrado</h3>
        <p className="text-sm text-muted-foreground">
          Não há synths disponíveis no momento
        </p>
      </div>
    );
  }

  return (
    <>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {data.data.map((synth) => (
          <SynthCard
            key={synth.id}
            synth={synth}
            onClick={(id) => setSelectedSynthId(id)}
          />
        ))}
      </div>

      <SynthDetailDialog
        synthId={selectedSynthId}
        open={!!selectedSynthId}
        onOpenChange={(open) => {
          if (!open) setSelectedSynthId(null);
        }}
      />
    </>
  );
}
