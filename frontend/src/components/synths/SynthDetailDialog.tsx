// src/components/synths/SynthDetailDialog.tsx

import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Avatar, AvatarImage, AvatarFallback } from '@/components/ui/avatar';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Loader2, User } from 'lucide-react';
import { ObservablesDisplay } from './ObservablesDisplay';
import { useSynthDetail } from '@/hooks/use-synths';
import { getSynthAvatarUrl } from '@/services/synths-api';

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

            <Tabs defaultValue="capabilities" className="mt-4">
              <TabsList className="grid w-full grid-cols-4">
                <TabsTrigger value="capabilities">Capacidades</TabsTrigger>
                <TabsTrigger value="demographics">Demografia</TabsTrigger>
                <TabsTrigger value="psychographics">Psicografia</TabsTrigger>
                <TabsTrigger value="tech">Tecnologia</TabsTrigger>
              </TabsList>

              <TabsContent value="capabilities" className="space-y-4">
                <ObservablesDisplay simulationAttributes={synth.simulation_attributes} />
              </TabsContent>

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
                    <CardHeader>
                      <CardTitle>Atributos Observáveis</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-3">
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <span className="font-semibold">Literacia Digital:</span>{' '}
                          {((synth.observables.digital_literacy ?? 0) * 100).toFixed(0)}%
                        </div>
                        <div>
                          <span className="font-semibold">Experiência com Ferramentas:</span>{' '}
                          {((synth.observables.similar_tool_experience ?? 0) * 100).toFixed(0)}%
                        </div>
                        <div>
                          <span className="font-semibold">Habilidade Motora:</span>{' '}
                          {((synth.observables.motor_ability ?? 0) * 100).toFixed(0)}%
                        </div>
                        <div>
                          <span className="font-semibold">Disponibilidade de Tempo:</span>{' '}
                          {((synth.observables.time_availability ?? 0) * 100).toFixed(0)}%
                        </div>
                        <div>
                          <span className="font-semibold">Expertise no Domínio:</span>{' '}
                          {((synth.observables.domain_expertise ?? 0) * 100).toFixed(0)}%
                        </div>
                      </div>
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
