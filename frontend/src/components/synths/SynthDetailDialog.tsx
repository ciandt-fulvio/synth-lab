// src/components/synths/SynthDetailDialog.tsx

import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Avatar, AvatarImage, AvatarFallback } from '@/components/ui/avatar';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Loader2, User, Monitor, Wrench, Activity, Clock, BookOpen } from 'lucide-react';
import { useSynthDetail } from '@/hooks/use-synths';
import { getSynthAvatarUrl } from '@/services/synths-api';

// Helper to get color based on value
function getValueColor(value: number): { bg: string; text: string; label: string } {
  if (value < 0.4) {
    return { bg: 'bg-red-500', text: 'text-red-600', label: 'Baixo' };
  } else if (value < 0.7) {
    return { bg: 'bg-amber-500', text: 'text-amber-600', label: 'Médio' };
  } else {
    return { bg: 'bg-emerald-500', text: 'text-emerald-600', label: 'Alto' };
  }
}

// Observable attribute configuration
const OBSERVABLE_CONFIG = [
  { key: 'digital_literacy', label: 'Familiaridade com tecnologia', icon: Monitor },
  { key: 'similar_tool_experience', label: 'Experiência com ferramentas similares', icon: Wrench },
  { key: 'motor_ability', label: 'Habilidade física', icon: Activity },
  { key: 'time_availability', label: 'Disponibilidade de Tempo', icon: Clock },
  { key: 'domain_expertise', label: 'Conhecimento do assunto', icon: BookOpen },
] as const;

interface SynthDetailDialogProps {
  synthId: string | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function SynthDetailDialog({ synthId, open, onOpenChange }: SynthDetailDialogProps) {
  const { data: synth, isLoading } = useSynthDetail(synthId);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin" />
          </div>
        ) : synth ? (
          <>
            <DialogHeader>
              <div className="flex items-center gap-4">
                <Avatar className="h-20 w-20">
                  <AvatarImage
                    src={synth.avatar_path ? getSynthAvatarUrl(synth.id) : undefined}
                    alt={synth.nome}
                  />
                  <AvatarFallback>
                    <User className="h-10 w-10" />
                  </AvatarFallback>
                </Avatar>
                <div>
                  <DialogTitle className="text-2xl">{synth.nome}</DialogTitle>
                  {synth.descricao && (
                    <p className="text-sm text-muted-foreground">{synth.descricao}</p>
                  )}
                </div>
              </div>
            </DialogHeader>

            <Tabs defaultValue="demographics" className="mt-4">
              <TabsList className="grid w-full grid-cols-3">
                <TabsTrigger value="demographics">Demografia</TabsTrigger>
                <TabsTrigger value="psychographics">Psicografia</TabsTrigger>
                <TabsTrigger value="tech">Capacidades Técnicas</TabsTrigger>
              </TabsList>

              <TabsContent value="demographics" className="space-y-4">
                {synth.demografia && (
                  <Card>
                    <CardHeader>
                      <CardTitle>Informações Demográficas</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-2 text-sm">
                      {synth.demografia.idade && (
                        <div><span className="font-semibold">Idade:</span> {synth.demografia.idade} anos</div>
                      )}
                      {synth.demografia.genero_biologico && (
                        <div><span className="font-semibold">Gênero Biológico:</span> {synth.demografia.genero_biologico}</div>
                      )}
                      {synth.demografia.raca_etnia && (
                        <div><span className="font-semibold">Raça/Etnia:</span> {synth.demografia.raca_etnia}</div>
                      )}
                      {synth.demografia.escolaridade && (
                        <div><span className="font-semibold">Escolaridade:</span> {synth.demografia.escolaridade}</div>
                      )}
                      {synth.demografia.ocupacao && (
                        <div><span className="font-semibold">Ocupação:</span> {synth.demografia.ocupacao}</div>
                      )}
                      {synth.demografia.renda_mensal && (
                        <div><span className="font-semibold">Renda Mensal:</span> R$ {synth.demografia.renda_mensal.toLocaleString('pt-BR')}</div>
                      )}
                      {synth.demografia.estado_civil && (
                        <div><span className="font-semibold">Estado Civil:</span> {synth.demografia.estado_civil}</div>
                      )}
                      {synth.demografia.localizacao && (
                        <div>
                          <span className="font-semibold">Localização:</span>{' '}
                          {[
                            synth.demografia.localizacao.cidade,
                            synth.demografia.localizacao.estado,
                            synth.demografia.localizacao.pais,
                          ].filter(Boolean).join(', ')}
                        </div>
                      )}
                    </CardContent>
                  </Card>
                )}
              </TabsContent>

              <TabsContent value="psychographics" className="space-y-4">
                {synth.psicografia?.interesses && synth.psicografia.interesses.length > 0 && (
                  <Card>
                    <CardHeader>
                      <CardTitle>Interesses</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="flex flex-wrap gap-2">
                        {synth.psicografia.interesses.map((interesse, idx) => (
                          <span key={idx} className="px-3 py-1 bg-secondary text-secondary-foreground rounded-full text-sm">
                            {interesse}
                          </span>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                )}

                {synth.psicografia?.contrato_cognitivo && (
                  <Card>
                    <CardHeader>
                      <CardTitle>Contrato Cognitivo</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-2 text-sm">
                      {synth.psicografia.contrato_cognitivo.tipo && (
                        <div><span className="font-semibold">Tipo:</span> {synth.psicografia.contrato_cognitivo.tipo}</div>
                      )}
                      {synth.psicografia.contrato_cognitivo.perfil_cognitivo && (
                        <div><span className="font-semibold">Perfil:</span> {synth.psicografia.contrato_cognitivo.perfil_cognitivo}</div>
                      )}
                      {synth.psicografia.contrato_cognitivo.efeito_esperado && (
                        <div><span className="font-semibold">Efeito Esperado:</span> {synth.psicografia.contrato_cognitivo.efeito_esperado}</div>
                      )}
                    </CardContent>
                  </Card>
                )}
              </TabsContent>

              <TabsContent value="tech" className="space-y-4">
                {synth.observables && (
                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-base">Atributos Observáveis</CardTitle>
                      <p className="text-xs text-muted-foreground">
                        Características que podem ser identificadas ou medidas externamente
                      </p>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      {OBSERVABLE_CONFIG.map(({ key, label, icon: Icon }) => {
                        const value = synth.observables?.[key as keyof typeof synth.observables] ?? 0;
                        const percentage = value * 100;
                        const colors = getValueColor(value);

                        return (
                          <div key={key} className="space-y-1.5">
                            <div className="flex items-center justify-between">
                              <div className="flex items-center gap-2">
                                <div className={`p-1.5 rounded-md bg-slate-100`}>
                                  <Icon className="h-4 w-4 text-slate-600" />
                                </div>
                                <span className="text-sm font-medium text-slate-700">{label}</span>
                              </div>
                              <div className="flex items-center gap-2">
                                <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${colors.bg} bg-opacity-15 ${colors.text}`}>
                                  {colors.label}
                                </span>
                                <span className="text-sm font-semibold text-slate-800 w-12 text-right">
                                  {percentage.toFixed(0)}%
                                </span>
                              </div>
                            </div>
                            <div className="h-2 w-full bg-slate-100 rounded-full overflow-hidden">
                              <div
                                className={`h-full rounded-full transition-all duration-500 ${colors.bg}`}
                                style={{ width: `${percentage}%` }}
                              />
                            </div>
                          </div>
                        );
                      })}
                    </CardContent>
                  </Card>
                )}
              </TabsContent>
            </Tabs>
          </>
        ) : (
          <div className="text-center py-12">Synth não encontrado</div>
        )}
      </DialogContent>
    </Dialog>
  );
}
