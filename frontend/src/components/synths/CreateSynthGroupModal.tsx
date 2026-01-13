/**
 * CreateSynthGroupModal component.
 *
 * Dialog for creating a new synth group with custom demographic distributions.
 *
 * References:
 *   - Spec: specs/030-custom-synth-groups/spec.md
 *   - Types: src/types/synthGroup.ts
 */

import { useState, useCallback, useMemo } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Slider } from '@/components/ui/slider';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { DistributionSlider } from './DistributionSlider';
import { useCreateSynthGroupWithConfig } from '@/hooks/use-synth-groups';
import { toast } from 'sonner';
import {
  Loader2,
  Users,
  GraduationCap,
  Heart,
  Home,
  Brain,
  Sparkles,
  AlertCircle,
  RotateCcw,
} from 'lucide-react';
import type {
  GroupConfig,
  IdadeDistribution,
  EscolaridadeDistribution,
  ComposicaoFamiliarDistribution,
  DomainExpertiseLevel,
  SliderItem,
} from '@/types/synthGroup';
import {
  DEFAULT_IDADE_DISTRIBUTION,
  DEFAULT_ESCOLARIDADE_DISTRIBUTION,
  DEFAULT_COMPOSICAO_FAMILIAR,
  DEFAULT_DEFICIENCIAS_CONFIG,
  DOMAIN_EXPERTISE_PRESETS,
  DOMAIN_EXPERTISE_LABELS,
  IDADE_LABELS,
  ESCOLARIDADE_LABELS,
  COMPOSICAO_FAMILIAR_LABELS,
} from '@/types/synthGroup';

interface CreateSynthGroupModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess?: () => void;
}

// Convert distribution object to slider items
function distributionToSliderItems<T extends Record<string, number>>(
  dist: T,
  labels: Record<keyof T, string>
): SliderItem[] {
  return Object.entries(dist).map(([key, value]) => ({
    key,
    label: labels[key as keyof T] || key,
    value: value as number,
  }));
}

// Convert slider items back to distribution object
function sliderItemsToDistribution<T extends Record<string, number>>(
  items: SliderItem[]
): T {
  return items.reduce((acc, item) => {
    acc[item.key as keyof T] = item.value as T[keyof T];
    return acc;
  }, {} as T);
}

export function CreateSynthGroupModal({
  open,
  onOpenChange,
  onSuccess,
}: CreateSynthGroupModalProps) {
  const createMutation = useCreateSynthGroupWithConfig();

  // Form state
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [nSynths, setNSynths] = useState(500);
  const [activeTab, setActiveTab] = useState('idade');

  // Distribution states
  const [idadeItems, setIdadeItems] = useState<SliderItem[]>(() =>
    distributionToSliderItems(DEFAULT_IDADE_DISTRIBUTION, IDADE_LABELS)
  );
  const [escolaridadeItems, setEscolaridadeItems] = useState<SliderItem[]>(() =>
    distributionToSliderItems(DEFAULT_ESCOLARIDADE_DISTRIBUTION, ESCOLARIDADE_LABELS)
  );
  const [composicaoItems, setComposicaoItems] = useState<SliderItem[]>(() =>
    distributionToSliderItems(DEFAULT_COMPOSICAO_FAMILIAR, COMPOSICAO_FAMILIAR_LABELS)
  );
  const [deficienciaTaxa, setDeficienciaTaxa] = useState(
    DEFAULT_DEFICIENCIAS_CONFIG.taxa_com_deficiencia
  );
  const [domainExpertiseLevel, setDomainExpertiseLevel] =
    useState<DomainExpertiseLevel>('regular');

  // Validation
  const isValid = useMemo(() => {
    if (!name.trim()) return false;
    if (nSynths < 1) return false;

    // Check all distributions sum to ~1.0
    const idadeSum = idadeItems.reduce((sum, item) => sum + item.value, 0);
    const escolaridadeSum = escolaridadeItems.reduce((sum, item) => sum + item.value, 0);
    const composicaoSum = composicaoItems.reduce((sum, item) => sum + item.value, 0);

    return (
      Math.abs(idadeSum - 1.0) < 0.01 &&
      Math.abs(escolaridadeSum - 1.0) < 0.01 &&
      Math.abs(composicaoSum - 1.0) < 0.01
    );
  }, [name, nSynths, idadeItems, escolaridadeItems, composicaoItems]);

  // Reset individual distributions
  const resetIdade = useCallback(() => {
    setIdadeItems(distributionToSliderItems(DEFAULT_IDADE_DISTRIBUTION, IDADE_LABELS));
  }, []);

  const resetEscolaridade = useCallback(() => {
    setEscolaridadeItems(
      distributionToSliderItems(DEFAULT_ESCOLARIDADE_DISTRIBUTION, ESCOLARIDADE_LABELS)
    );
  }, []);

  const resetComposicao = useCallback(() => {
    setComposicaoItems(
      distributionToSliderItems(DEFAULT_COMPOSICAO_FAMILIAR, COMPOSICAO_FAMILIAR_LABELS)
    );
  }, []);

  const resetDeficiencias = useCallback(() => {
    setDeficienciaTaxa(DEFAULT_DEFICIENCIAS_CONFIG.taxa_com_deficiencia);
  }, []);

  // Reset form
  const resetForm = useCallback(() => {
    setName('');
    setDescription('');
    setNSynths(500);
    setActiveTab('idade');
    resetIdade();
    resetEscolaridade();
    resetComposicao();
    resetDeficiencias();
    setDomainExpertiseLevel('regular');
  }, [resetIdade, resetEscolaridade, resetComposicao, resetDeficiencias]);

  // Handle form submission
  const handleSubmit = async () => {
    if (!isValid) return;

    const config: GroupConfig = {
      n_synths: nSynths,
      distributions: {
        idade: sliderItemsToDistribution<IdadeDistribution>(idadeItems),
        escolaridade: sliderItemsToDistribution<EscolaridadeDistribution>(escolaridadeItems),
        deficiencias: {
          taxa_com_deficiencia: deficienciaTaxa,
          distribuicao_severidade: DEFAULT_DEFICIENCIAS_CONFIG.distribuicao_severidade,
        },
        composicao_familiar:
          sliderItemsToDistribution<ComposicaoFamiliarDistribution>(composicaoItems),
        domain_expertise: DOMAIN_EXPERTISE_PRESETS[domainExpertiseLevel],
      },
    };

    try {
      await createMutation.mutateAsync({
        name: name.trim(),
        description: description.trim() || null,
        config,
      });

      toast.success('Grupo criado com sucesso', {
        description: `${nSynths} synths foram gerados`,
      });

      resetForm();
      onOpenChange(false);
      onSuccess?.();
    } catch (error) {
      toast.error('Erro ao criar grupo', {
        description: error instanceof Error ? error.message : 'Erro desconhecido',
      });
    }
  };

  const handleOpenChange = (newOpen: boolean) => {
    if (!newOpen) {
      resetForm();
    }
    onOpenChange(newOpen);
  };

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-[700px] max-h-[95vh] p-0 gap-0 overflow-hidden">
        {/* Header */}
        <DialogHeader className="px-6 pt-3 pb-2 border-b border-slate-100 bg-gradient-to-br from-slate-50 to-white">
          <div className="flex items-center gap-2.5">
            <div className="p-2 bg-gradient-to-br from-indigo-500 to-violet-500 rounded-lg text-white shadow-lg shadow-indigo-200/50">
              <Sparkles className="h-4 w-4" />
            </div>
            <div>
              <DialogTitle className="text-lg font-bold text-slate-900">
                Novo Grupo de Synths
              </DialogTitle>
              <DialogDescription className="text-slate-500 text-xs">
                Configure as distribuicoes demograficas
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>

        <ScrollArea className="max-h-[calc(95vh-130px)]">
          <div className="px-6 py-6 space-y-2">
            {/* Basic Info */}
            <div className="grid grid-cols-3 gap-3">
              <div>
                <Label htmlFor="name" className="text-sm font-medium text-slate-700">
                  Nome do Grupo *
                </Label>
                <Input
                  id="name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Ex: Aposentados 60+"
                  maxLength={23}
                  className="mt-1"
                />
              </div>
              <div>
                <Label htmlFor="description" className="text-sm font-medium text-slate-700">
                  Descricao
                </Label>
                <Input
                  id="description"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Ex: Grupo para simular previdencia"
                  maxLength={50}
                  className="mt-1"
                />
              </div>
              <div>
                <Label htmlFor="n-synths" className="text-sm font-medium text-slate-700">
                  Quantidade
                </Label>
                <Select
                  value={nSynths.toString()}
                  onValueChange={(value) => setNSynths(Number(value))}
                >
                  <SelectTrigger id="n-synths" className="mt-1">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="100">100 synths</SelectItem>
                    <SelectItem value="300">300 synths</SelectItem>
                    <SelectItem value="500">500 synths</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Distribution Tabs */}
            <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
              <TabsList className="grid w-full grid-cols-5 h-auto p-1 bg-slate-100 rounded-lg">
                <TabsTrigger
                  value="idade"
                  className="flex flex-col items-center gap-0.5 py-1.5 px-1 text-xs data-[state=active]:bg-white data-[state=active]:shadow-sm rounded-md"
                >
                  <Users className="h-4 w-4" />
                  <span className="hidden sm:inline">Idade</span>
                </TabsTrigger>
                <TabsTrigger
                  value="escolaridade"
                  className="flex flex-col items-center gap-0.5 py-1.5 px-1 text-xs data-[state=active]:bg-white data-[state=active]:shadow-sm rounded-md"
                >
                  <GraduationCap className="h-4 w-4" />
                  <span className="hidden sm:inline">Escolaridade</span>
                </TabsTrigger>
                <TabsTrigger
                  value="deficiencias"
                  className="flex flex-col items-center gap-0.5 py-1.5 px-1 text-xs data-[state=active]:bg-white data-[state=active]:shadow-sm rounded-md"
                >
                  <Heart className="h-4 w-4" />
                  <span className="hidden sm:inline">PcD</span>
                </TabsTrigger>
                <TabsTrigger
                  value="composicao"
                  className="flex flex-col items-center gap-0.5 py-1.5 px-1 text-xs data-[state=active]:bg-white data-[state=active]:shadow-sm rounded-md"
                >
                  <Home className="h-4 w-4" />
                  <span className="hidden sm:inline">Família</span>
                </TabsTrigger>
                <TabsTrigger
                  value="expertise"
                  className="flex flex-col items-center gap-0.5 py-1.5 px-1 text-xs data-[state=active]:bg-white data-[state=active]:shadow-sm rounded-md"
                >
                  <Brain className="h-4 w-4" />
                  <span className="hidden sm:inline">Conhecimento</span>
                </TabsTrigger>
              </TabsList>

              <div className="mt-2 px-6 pt-4 pb-6 rounded-xl border border-slate-200 bg-white">
                <TabsContent value="idade" className="mt-0">
                  <DistributionSlider
                    label="Faixa Etária"
                    items={idadeItems}
                    onChange={setIdadeItems}
                    colorScheme="indigo"
                    onReset={resetIdade}
                  />
                </TabsContent>

                <TabsContent value="escolaridade" className="mt-0">
                  <DistributionSlider
                    label="Escolaridade"
                    items={escolaridadeItems}
                    onChange={setEscolaridadeItems}
                    colorScheme="emerald"
                    onReset={resetEscolaridade}
                  />
                </TabsContent>

                <TabsContent value="deficiencias" className="mt-0">
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <h4 className="text-sm font-semibold text-indigo-700 flex-1">
                        Taxa de PcD
                      </h4>
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={resetDeficiencias}
                        className="h-6 px-2 text-xs text-slate-500 hover:text-indigo-600"
                        title="Resetar para padrão IBGE"
                      >
                        <RotateCcw className="h-3 w-3" />
                      </Button>
                      <div className="px-2 py-0.5 rounded-md text-xs font-medium border bg-indigo-50 text-indigo-700 border-indigo-200">
                        {(deficienciaTaxa * 100).toFixed(1)}%
                      </div>
                    </div>
                    <Select
                      value={deficienciaTaxa.toString()}
                      onValueChange={(value) => setDeficienciaTaxa(Number(value))}
                    >
                      <SelectTrigger className="w-full">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="0.084">Padrão IBGE (8,4%)</SelectItem>
                        <SelectItem value="0.5">50% de PcD</SelectItem>
                        <SelectItem value="1.0">Apenas PcD</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </TabsContent>

                <TabsContent value="composicao" className="mt-0">
                  <DistributionSlider
                    label="Composição Familiar"
                    items={composicaoItems}
                    onChange={setComposicaoItems}
                    colorScheme="amber"
                    onReset={resetComposicao}
                  />
                </TabsContent>

                <TabsContent value="expertise" className="mt-0">
                  <div className="space-y-2">
                    <h4 className="text-sm font-semibold text-indigo-700">
                      Conhecimento do assunto
                    </h4>

                    <Select
                      value={domainExpertiseLevel}
                      onValueChange={(value) =>
                        setDomainExpertiseLevel(value as DomainExpertiseLevel)
                      }
                    >
                      <SelectTrigger className="w-full">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {(Object.keys(DOMAIN_EXPERTISE_LABELS) as DomainExpertiseLevel[]).map(
                          (level) => (
                            <SelectItem key={level} value={level}>
                              {DOMAIN_EXPERTISE_LABELS[level]}
                            </SelectItem>
                          )
                        )}
                      </SelectContent>
                    </Select>
                  </div>
                </TabsContent>
              </div>
            </Tabs>
          </div>
        </ScrollArea>

        {/* Footer */}
        <div className="px-6 py-2.5 border-t border-slate-100 bg-slate-50 flex items-center justify-between gap-4">
          <div className="text-xs text-slate-500">
            {!isValid && (
              <span className="text-amber-600 flex items-center gap-1">
                <AlertCircle className="h-3 w-3" />
                {!name.trim()
                  ? 'Nome e obrigatorio'
                  : 'Verifique se as distribuicoes somam 100%'}
              </span>
            )}
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleOpenChange(false)}
              disabled={createMutation.isPending}
            >
              Cancelar
            </Button>
            <Button
              size="sm"
              onClick={handleSubmit}
              disabled={!isValid || createMutation.isPending}
              className="bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-700 hover:to-violet-700 text-white shadow-lg shadow-indigo-200/50"
            >
              {createMutation.isPending ? (
                <>
                  <Loader2 className="mr-2 h-3.5 w-3.5 animate-spin" />
                  Gerando {nSynths} synths...
                </>
              ) : (
                <>
                  <Sparkles className="mr-2 h-3.5 w-3.5" />
                  Criar Grupo
                </>
              )}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
