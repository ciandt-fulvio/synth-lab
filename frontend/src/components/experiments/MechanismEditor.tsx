// frontend/src/components/experiments/MechanismEditor.tsx
// Editor component for feature mechanisms with 9 sliders

import { Info } from 'lucide-react';
import { Slider } from '@/components/ui/slider';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import type { FeatureMechanisms } from '@/types/simulation';

/** Mechanism field configuration */
interface MechanismConfig {
  key: keyof FeatureMechanisms;
  label: string;
  description: string;
  example: string;
}

/** All mechanism configurations */
const MECHANISM_CONFIGS: MechanismConfig[] = [
  {
    key: 'irreversibility',
    label: 'Irreversibilidade',
    description: 'Grau em que as ações são permanentes e não podem ser desfeitas',
    example: 'Transferência Pix, exclusão de dados',
  },
  {
    key: 'network_effect',
    label: 'Efeito de Rede',
    description: 'Grau em que o valor depende de outros usuários também usarem',
    example: 'WhatsApp, redes sociais',
  },
  {
    key: 'institutional_trust',
    label: 'Confiança Institucional',
    description: 'Grau em que a feature requer confiança na instituição',
    example: 'Banco digital, investimentos',
  },
  {
    key: 'habit_displacement',
    label: 'Substituição de Hábito',
    description: 'Grau em que a feature substitui hábitos existentes',
    example: 'Migrar de cartão para Pix',
  },
  {
    key: 'learning_curve',
    label: 'Curva de Aprendizado',
    description: 'Grau em que a feature requer aprender novas habilidades',
    example: 'Nova interface, novo fluxo',
  },
  {
    key: 'social_visibility',
    label: 'Visibilidade Social',
    description: 'Grau em que o uso é visível para outros',
    example: 'Compra em grupo, posts públicos',
  },
  {
    key: 'valor_intrinseco',
    label: 'Valor Intrínseco',
    description: 'Grau em que a feature melhora a vida real do usuário',
    example: 'Agendamento automático, alerta de fraude',
  },
  {
    key: 'friccao_operacional',
    label: 'Fricção Operacional',
    description: 'Grau de fricção, etapas ou erros no uso cotidiano',
    example: 'Múltiplas confirmações, timeout, erros frequentes',
  },
  {
    key: 'frequencia_de_uso',
    label: 'Frequência de Uso',
    description: 'Frequência esperada de uso da feature',
    example: 'Diário (saldo), mensal (extrato), raro (portabilidade)',
  },
];

interface MechanismEditorProps {
  /** Current mechanism values */
  value: FeatureMechanisms;
  /** Called when any mechanism value changes */
  onChange: (mechanisms: FeatureMechanisms) => void;
  /** Whether the editor is in read-only mode */
  disabled?: boolean;
}

/**
 * Editor component for feature mechanisms.
 *
 * Displays 9 sliders for mechanism values [0, 1] with descriptions
 * and examples to help PMs understand each mechanism.
 */
export function MechanismEditor({ value, onChange, disabled = false }: MechanismEditorProps) {
  const handleSliderChange = (key: keyof FeatureMechanisms, newValue: number[]) => {
    onChange({
      ...value,
      [key]: newValue[0],
    });
  };

  return (
    <TooltipProvider>
      <div className="space-y-6">
        <div className="flex items-center gap-2 mb-4">
          <h3 className="text-sm font-medium text-slate-700">Mecanismos da Feature</h3>
          <Tooltip>
            <TooltipTrigger asChild>
              <Info className="h-4 w-4 text-slate-400 cursor-help" />
            </TooltipTrigger>
            <TooltipContent className="max-w-xs">
              <p>
                Mecanismos estruturais que determinam como a feature interage com diferentes
                perfis de usuários na simulação.
              </p>
            </TooltipContent>
          </Tooltip>
        </div>

        <div className="grid gap-6">
          {MECHANISM_CONFIGS.map((config) => (
            <MechanismSlider
              key={config.key}
              config={config}
              value={value[config.key]}
              onChange={(newValue) => handleSliderChange(config.key, newValue)}
              disabled={disabled}
            />
          ))}
        </div>
      </div>
    </TooltipProvider>
  );
}

interface MechanismSliderProps {
  config: MechanismConfig;
  value: number;
  onChange: (value: number[]) => void;
  disabled: boolean;
}

function MechanismSlider({ config, value, onChange, disabled }: MechanismSliderProps) {
  const displayValue = Math.round(value * 100);

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <label className="text-sm font-medium text-slate-700">{config.label}</label>
          <Tooltip>
            <TooltipTrigger asChild>
              <Info className="h-3.5 w-3.5 text-slate-400 cursor-help" />
            </TooltipTrigger>
            <TooltipContent className="max-w-xs">
              <p className="font-medium mb-1">{config.description}</p>
              <p className="text-xs text-slate-400">Ex: {config.example}</p>
            </TooltipContent>
          </Tooltip>
        </div>
        <span className="text-sm font-mono text-slate-600">{displayValue}%</span>
      </div>

      <Slider
        value={[value]}
        onValueChange={onChange}
        min={0}
        max={1}
        step={0.05}
        disabled={disabled}
        className="w-full"
      />

      <div className="flex justify-between text-xs text-slate-400">
        <span>Baixo</span>
        <span>Alto</span>
      </div>
    </div>
  );
}

/** Default mechanism values (all zeros) */
export const DEFAULT_MECHANISMS: FeatureMechanisms = {
  irreversibility: 0,
  network_effect: 0,
  institutional_trust: 0,
  habit_displacement: 0,
  learning_curve: 0,
  social_visibility: 0,
  valor_intrinseco: 0,
  friccao_operacional: 0,
  frequencia_de_uso: 0,
};

/** Check if mechanisms have any non-zero values */
export function hasMechanisms(mechanisms: FeatureMechanisms | null | undefined): boolean {
  if (!mechanisms) return false;
  return Object.values(mechanisms).some((v) => v > 0);
}
