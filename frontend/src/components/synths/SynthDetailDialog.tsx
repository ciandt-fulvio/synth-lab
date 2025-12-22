// src/components/synths/SynthDetailDialog.tsx

import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Avatar, AvatarImage, AvatarFallback } from '@/components/ui/avatar';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Loader2, User } from 'lucide-react';
import { BigFiveChart } from './BigFiveChart';
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
                  {synth.arquetipo && (
                    <p className="text-sm text-muted-foreground">{synth.arquetipo}</p>
                  )}
                </div>
              </div>
            </DialogHeader>

            <Tabs defaultValue="demographics" className="mt-4">
              <TabsList className="grid w-full grid-cols-4">
                <TabsTrigger value="demographics">Demografia</TabsTrigger>
                <TabsTrigger value="psychographics">Psicografia</TabsTrigger>
                <TabsTrigger value="behavior">Comportamento</TabsTrigger>
                <TabsTrigger value="tech">Tecnologia</TabsTrigger>
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
                      {synth.demografia.identidade_genero && (
                        <div><span className="font-semibold">Identidade de Gênero:</span> {synth.demografia.identidade_genero}</div>
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
                {synth.psicografia?.personalidade_big_five && (
                  <Card>
                    <CardHeader>
                      <CardTitle>Personalidade Big Five</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <BigFiveChart personality={synth.psicografia.personalidade_big_five} />
                    </CardContent>
                  </Card>
                )}

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

              <TabsContent value="behavior" className="space-y-4">
                {synth.comportamento?.habitos_consumo && (
                  <Card>
                    <CardHeader>
                      <CardTitle>Hábitos de Consumo</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-2 text-sm">
                      {synth.comportamento.habitos_consumo.frequencia_compras && (
                        <div><span className="font-semibold">Frequência:</span> {synth.comportamento.habitos_consumo.frequencia_compras}</div>
                      )}
                      {synth.comportamento.habitos_consumo.preferencia_canal && (
                        <div><span className="font-semibold">Canal Preferido:</span> {synth.comportamento.habitos_consumo.preferencia_canal}</div>
                      )}
                      {synth.comportamento.habitos_consumo.categorias_preferidas && (
                        <div>
                          <span className="font-semibold">Categorias:</span>{' '}
                          {synth.comportamento.habitos_consumo.categorias_preferidas.join(', ')}
                        </div>
                      )}
                    </CardContent>
                  </Card>
                )}

                {synth.comportamento?.engajamento_redes_sociais && (
                  <Card>
                    <CardHeader>
                      <CardTitle>Redes Sociais</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-2 text-sm">
                      {synth.comportamento.engajamento_redes_sociais.plataformas && (
                        <div>
                          <span className="font-semibold">Plataformas:</span>{' '}
                          {synth.comportamento.engajamento_redes_sociais.plataformas.join(', ')}
                        </div>
                      )}
                      {synth.comportamento.engajamento_redes_sociais.frequencia_posts && (
                        <div>
                          <span className="font-semibold">Frequência de Posts:</span>{' '}
                          {synth.comportamento.engajamento_redes_sociais.frequencia_posts}
                        </div>
                      )}
                    </CardContent>
                  </Card>
                )}

                {synth.comportamento?.lealdade_marca !== undefined && (
                  <Card>
                    <CardHeader>
                      <CardTitle>Lealdade de Marca</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold">{synth.comportamento.lealdade_marca}/100</div>
                    </CardContent>
                  </Card>
                )}
              </TabsContent>

              <TabsContent value="tech" className="space-y-4">
                {synth.capacidades_tecnologicas && (
                  <>
                    {synth.capacidades_tecnologicas.alfabetizacao_digital !== undefined && (
                      <Card>
                        <CardHeader>
                          <CardTitle>Alfabetização Digital</CardTitle>
                        </CardHeader>
                        <CardContent>
                          <div className="text-2xl font-bold">{synth.capacidades_tecnologicas.alfabetizacao_digital}/100</div>
                        </CardContent>
                      </Card>
                    )}

                    {synth.capacidades_tecnologicas.dispositivos && (
                      <Card>
                        <CardHeader>
                          <CardTitle>Dispositivos</CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-2 text-sm">
                          {synth.capacidades_tecnologicas.dispositivos.principal && (
                            <div><span className="font-semibold">Principal:</span> {synth.capacidades_tecnologicas.dispositivos.principal}</div>
                          )}
                          {synth.capacidades_tecnologicas.dispositivos.qualidade && (
                            <div><span className="font-semibold">Qualidade:</span> {synth.capacidades_tecnologicas.dispositivos.qualidade}</div>
                          )}
                        </CardContent>
                      </Card>
                    )}

                    {synth.capacidades_tecnologicas.familiaridade_plataformas && (
                      <Card>
                        <CardHeader>
                          <CardTitle>Familiaridade com Plataformas</CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-2 text-sm">
                          {synth.capacidades_tecnologicas.familiaridade_plataformas.e_commerce !== undefined && (
                            <div><span className="font-semibold">E-commerce:</span> {synth.capacidades_tecnologicas.familiaridade_plataformas.e_commerce}/100</div>
                          )}
                          {synth.capacidades_tecnologicas.familiaridade_plataformas.banco_digital !== undefined && (
                            <div><span className="font-semibold">Banco Digital:</span> {synth.capacidades_tecnologicas.familiaridade_plataformas.banco_digital}/100</div>
                          )}
                          {synth.capacidades_tecnologicas.familiaridade_plataformas.redes_sociais !== undefined && (
                            <div><span className="font-semibold">Redes Sociais:</span> {synth.capacidades_tecnologicas.familiaridade_plataformas.redes_sociais}/100</div>
                          )}
                        </CardContent>
                      </Card>
                    )}
                  </>
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
