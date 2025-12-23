// src/components/synths/SynthCard.tsx

import { Card, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Avatar, AvatarImage, AvatarFallback } from '@/components/ui/avatar';
import { User } from 'lucide-react';
import { getSynthAvatarUrl } from '@/services/synths-api';
import type { SynthSummary } from '@/types';

interface SynthCardProps {
  synth: SynthSummary;
  onClick: (synthId: string) => void;
}

export function SynthCard({ synth, onClick }: SynthCardProps) {
  const initials = synth.nome
    .split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2);

  return (
    <Card
      className="cursor-pointer hover:shadow-lg transition-shadow"
      onClick={() => onClick(synth.id)}
    >
      <CardHeader className="flex flex-row items-center gap-4">
        <Avatar className="h-16 w-16">
          <AvatarImage
            src={getSynthAvatarUrl(synth.id)}
            alt={synth.nome}
          />
          <AvatarFallback>
            <User className="h-8 w-8" />
          </AvatarFallback>
        </Avatar>
        <div className="flex-1">
          <CardTitle className="text-lg">{synth.nome}</CardTitle>
          {synth.descricao && (
            <CardDescription className="text-sm line-clamp-2">{synth.descricao}</CardDescription>
          )}
        </div>
      </CardHeader>
    </Card>
  );
}
