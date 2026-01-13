/**
 * T031 SynthGroupDetail component.
 *
 * Displays detailed information about a synth group including its configuration.
 *
 * References:
 *   - Spec: specs/030-custom-synth-groups/spec.md (US3)
 *   - Types: src/types/synthGroup.ts
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { DistributionDisplay } from './DistributionDisplay';
import {
  Users,
  Calendar,
  AlertCircle,
  Heart,
  GraduationCap,
  Home,
  Brain,
} from 'lucide-react';
import { formatDistanceToNow, format } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import type { SynthGroupDetail as SynthGroupDetailType } from '@/types/synthGroup';
import {
  IDADE_LABELS,
  ESCOLARIDADE_LABELS,
  COMPOSICAO_FAMILIAR_LABELS,
  IDADE_ORDER,
  ESCOLARIDADE_ORDER,
  COMPOSICAO_FAMILIAR_ORDER,
  DOMAIN_EXPERTISE_PRESETS,
  type DomainExpertiseLevel,
} from '@/types/synthGroup';

interface SynthGroupDetailProps {
  group: SynthGroupDetailType;
}

function getDomainExpertiseLevel(
  alpha: number,
  beta: number
): DomainExpertiseLevel | null {
  for (const [level, config] of Object.entries(DOMAIN_EXPERTISE_PRESETS)) {
    if (config.alpha === alpha && config.beta === beta) {
      return level as DomainExpertiseLevel;
    }
  }
  return null;
}

const DOMAIN_EXPERTISE_DISPLAY: Record<DomainExpertiseLevel, string> = {
  baixo: 'Baixo (maioria leigos)',
  regular: 'Regular (equilibrado)',
  alto: 'Alto (maioria especialistas)',
};

export function SynthGroupDetailSkeleton() {
  return (
    <Card>
      <CardHeader className="pb-4">
        <div className="flex items-center justify-between">
          <Skeleton className="h-6 w-48" />
          <Skeleton className="h-5 w-20" />
        </div>
        <Skeleton className="h-4 w-3/4 mt-2" />
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="space-y-2">
          <Skeleton className="h-4 w-24" />
          <Skeleton className="h-3 w-full" />
          <Skeleton className="h-3 w-full" />
        </div>
        <div className="space-y-2">
          <Skeleton className="h-4 w-24" />
          <Skeleton className="h-3 w-full" />
          <Skeleton className="h-3 w-full" />
        </div>
      </CardContent>
    </Card>
  );
}

export function SynthGroupDetailView({ group }: SynthGroupDetailProps) {
  const formattedDate = formatDistanceToNow(new Date(group.created_at), {
    addSuffix: true,
    locale: ptBR,
  });

  const fullDate = format(new Date(group.created_at), "dd 'de' MMMM 'de' yyyy", {
    locale: ptBR,
  });

  const isDefaultGroup = group.id === 'grp_default';
  const config = group.config;

  return (
    <Card>
      <CardHeader className="pb-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div
              className={`p-1.5 rounded-lg ${
                isDefaultGroup
                  ? 'bg-slate-100 text-slate-600'
                  : 'bg-gradient-to-br from-indigo-500 to-violet-500 text-white'
              }`}
            >
              <Users className="h-4 w-4" />
            </div>
            <CardTitle className="text-lg">{group.name}</CardTitle>
          </div>
          <Badge variant="secondary" className="text-xs">
            {group.synth_count} synths
          </Badge>
        </div>
        {group.description && (
          <p className="text-sm text-slate-600 mt-1">{group.description}</p>
        )}
        <div className="flex items-center gap-4 text-xs text-slate-500 mt-2">
          <div className="flex items-center gap-1" title={fullDate}>
            <Calendar className="h-3 w-3" />
            <span>{formattedDate}</span>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {!config ? (
          <div className="flex items-start gap-3 p-4 bg-slate-50 rounded-lg">
            <AlertCircle className="h-5 w-5 text-slate-400 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-slate-700">
                Grupo legado sem configuração
              </p>
              <p className="text-xs text-slate-500 mt-1">
                Este grupo foi criado antes da funcionalidade de configuração customizada.
                Os synths foram gerados com as distribuições padrão do IBGE.
              </p>
            </div>
          </div>
        ) : (
          <>
            {/* Age Distribution */}
            <div className="flex items-start gap-3">
              <Users className="h-4 w-4 text-indigo-500 mt-0.5" />
              <div className="flex-1">
                <DistributionDisplay
                  title="Idade"
                  items={IDADE_ORDER.map((key) => ({
                    label: IDADE_LABELS[key],
                    value: config.distributions.idade[key],
                  }))}
                />
              </div>
            </div>

            {/* Education Distribution */}
            <div className="flex items-start gap-3">
              <GraduationCap className="h-4 w-4 text-indigo-500 mt-0.5" />
              <div className="flex-1">
                <DistributionDisplay
                  title="Escolaridade"
                  items={ESCOLARIDADE_ORDER.map((key) => ({
                    label: ESCOLARIDADE_LABELS[key],
                    value: config.distributions.escolaridade[key],
                  }))}
                />
              </div>
            </div>

            {/* Disability Rate */}
            <div className="flex items-start gap-3">
              <Heart className="h-4 w-4 text-indigo-500 mt-0.5" />
              <div className="flex-1">
                <h4 className="text-sm font-medium text-slate-700 mb-2">
                  PcD
                </h4>
                <div className="flex items-center gap-2">
                  <div className="flex-1 h-3 rounded-full bg-slate-100 overflow-hidden">
                    <div
                      className="h-full bg-indigo-500 transition-all duration-300"
                      style={{
                        width: `${config.distributions.deficiencias.taxa_com_deficiencia * 100}%`,
                      }}
                    />
                  </div>
                  <span className="text-sm font-medium text-slate-700 tabular-nums">
                    {(config.distributions.deficiencias.taxa_com_deficiencia * 100).toFixed(1)}%
                  </span>
                </div>
              </div>
            </div>

            {/* Family Composition */}
            <div className="flex items-start gap-3">
              <Home className="h-4 w-4 text-indigo-500 mt-0.5" />
              <div className="flex-1">
                <DistributionDisplay
                  title="Família"
                  items={COMPOSICAO_FAMILIAR_ORDER.map((key) => ({
                    label: COMPOSICAO_FAMILIAR_LABELS[key],
                    value: config.distributions.composicao_familiar[key],
                  }))}
                />
              </div>
            </div>

            {/* Domain Expertise */}
            <div className="flex items-start gap-3">
              <Brain className="h-4 w-4 text-indigo-500 mt-0.5" />
              <div className="flex-1">
                <h4 className="text-sm font-medium text-slate-700 mb-2">
                  Conhecimento
                </h4>
                {(() => {
                  const expertiseLevel = getDomainExpertiseLevel(
                    config.distributions.domain_expertise.alpha,
                    config.distributions.domain_expertise.beta
                  );
                  return expertiseLevel ? (
                    <Badge
                      variant="secondary"
                      className={`text-xs ${
                        expertiseLevel === 'alto'
                          ? 'bg-green-100 text-green-700'
                          : expertiseLevel === 'baixo'
                            ? 'bg-amber-100 text-amber-700'
                            : 'bg-slate-100 text-slate-700'
                      }`}
                    >
                      {DOMAIN_EXPERTISE_DISPLAY[expertiseLevel]}
                    </Badge>
                  ) : (
                    <span className="text-sm text-slate-600">
                      Beta(α={config.distributions.domain_expertise.alpha}, β=
                      {config.distributions.domain_expertise.beta})
                    </span>
                  );
                })()}
              </div>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}
