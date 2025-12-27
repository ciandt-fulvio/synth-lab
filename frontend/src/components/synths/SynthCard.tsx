// src/components/synths/SynthCard.tsx

import { Card, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Avatar, AvatarImage, AvatarFallback } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { User, Users } from 'lucide-react';
import { getSynthAvatarUrl } from '@/services/synths-api';
import type { SynthSummary } from '@/types';

interface SynthCardProps {
  synth: SynthSummary;
  onClick: (synthId: string) => void;
  groupName?: string;
}

export function SynthCard({ synth, onClick, groupName }: SynthCardProps) {
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
          <div className="flex items-center gap-2">
            <CardTitle className="text-lg">{synth.nome}</CardTitle>
          </div>
          {synth.descricao && (
            <CardDescription className="text-sm line-clamp-2">{synth.descricao}</CardDescription>
          )}
          {groupName && (
            <div className="flex items-center gap-1 mt-1">
              <Users className="h-3 w-3 text-muted-foreground" />
              <Badge variant="secondary" className="text-xs">
                {groupName}
              </Badge>
            </div>
          )}
        </div>
      </CardHeader>
    </Card>
  );
}
