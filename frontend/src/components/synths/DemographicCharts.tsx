/**
 * DemographicCharts component.
 *
 * Renders demographic statistics as bar charts (age, income)
 * and pie charts (education, family composition, disability).
 *
 * References:
 *   - Types: src/types/synthGroup.ts (DemographicStats)
 *   - Charts: recharts v2.15
 */

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
} from 'recharts';
import type { DemographicStats } from '@/types/synthGroup';

const BAR_COLOR = '#4f46e5'; // indigo-600

const PIE_COLORS = [
  '#4f46e5', // indigo-600
  '#7c3aed', // violet-600
  '#2563eb', // blue-600
  '#0891b2', // cyan-600
  '#059669', // emerald-600
  '#d97706', // amber-600
  '#dc2626', // red-600
];

const EDUCATION_LABELS: Record<string, string> = {
  sem_instrucao: 'Sem instrução',
  fundamental: 'Fundamental',
  medio: 'Médio',
  superior: 'Superior',
};

const FAMILY_LABELS: Record<string, string> = {
  unipessoal: 'Unipessoal',
  casal_sem_filhos: 'Casal s/ filhos',
  casal_com_filhos: 'Casal c/ filhos',
  monoparental: 'Monoparental',
  multigeracional: 'Multigeracional',
};

interface StatsAnnotationProps {
  mean: number;
  stdDev: number;
  prefix?: string;
}

function StatsAnnotation({ mean, stdDev, prefix = '' }: StatsAnnotationProps) {
  return (
    <p className="text-xs text-slate-500 mt-1">
      Média: {prefix}{mean.toLocaleString('pt-BR', { maximumFractionDigits: 1 })} | Desvio: {prefix}{stdDev.toLocaleString('pt-BR', { maximumFractionDigits: 1 })}
    </p>
  );
}

interface DemographicChartsProps {
  data: DemographicStats;
}

export function DemographicCharts({ data }: DemographicChartsProps) {
  const ageBuckets = data.age.buckets.map((b) => ({
    name: b.label,
    count: b.count,
    percentage: b.percentage,
  }));

  const incomeBuckets = data.income.buckets.map((b) => ({
    name: b.label,
    count: b.count,
    percentage: b.percentage,
  }));

  const educationData = data.education.map((c) => ({
    name: EDUCATION_LABELS[c.label] ?? c.label,
    value: c.count,
    percentage: c.percentage,
  }));

  const familyData = data.family_composition.map((c) => ({
    name: FAMILY_LABELS[c.label] ?? c.label,
    value: c.count,
    percentage: c.percentage,
  }));

  const disabilityData = [
    { name: 'PcD', value: data.disability.pcd_count, percentage: data.disability.pcd_percentage },
    { name: 'Sem deficiência', value: data.disability.non_pcd_count, percentage: data.disability.non_pcd_percentage },
  ];

  return (
    <div className="space-y-6">
      <h3 className="text-lg font-semibold text-slate-900">Demografia</h3>

      {/* Bar charts row */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Age histogram */}
        <div className="bg-white rounded-lg border border-slate-200 p-4">
          <h4 className="text-sm font-medium text-slate-700 mb-1">Distribuição de Idade</h4>
          <StatsAnnotation mean={data.age.mean} stdDev={data.age.std_dev} />
          <div className="h-52 mt-2">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={ageBuckets}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} allowDecimals={false} />
                <Tooltip
                  formatter={(value: number, _name: string, props: { payload: { percentage: number } }) => [
                    `${value} synths (${props.payload.percentage}%)`,
                    '',
                  ]}
                />
                <Bar dataKey="count" fill={BAR_COLOR} radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Income histogram */}
        <div className="bg-white rounded-lg border border-slate-200 p-4">
          <h4 className="text-sm font-medium text-slate-700 mb-1">Distribuição de Renda</h4>
          <StatsAnnotation mean={data.income.mean} stdDev={data.income.std_dev} prefix="R$ " />
          <div className="h-52 mt-2">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={incomeBuckets}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} allowDecimals={false} />
                <Tooltip
                  formatter={(value: number, _name: string, props: { payload: { percentage: number } }) => [
                    `${value} synths (${props.payload.percentage}%)`,
                    '',
                  ]}
                />
                <Bar dataKey="count" fill="#7c3aed" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Pie charts row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <PieChartCard title="Escolaridade" data={educationData} />
        <PieChartCard title="Composição Familiar" data={familyData} />
        <PieChartCard title="Deficiência (PcD)" data={disabilityData} />
      </div>
    </div>
  );
}

interface PieChartCardProps {
  title: string;
  data: { name: string; value: number; percentage: number }[];
}

function PieChartCard({ title, data }: PieChartCardProps) {
  if (data.length === 0 || data.every((d) => d.value === 0)) {
    return (
      <div className="bg-white rounded-lg border border-slate-200 p-4">
        <h4 className="text-sm font-medium text-slate-700 mb-3">{title}</h4>
        <div className="flex items-center justify-center h-48 text-xs text-slate-400">
          Sem dados
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg border border-slate-200 p-4">
      <h4 className="text-sm font-medium text-slate-700 mb-3">{title}</h4>
      <div className="h-48">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius={35}
              outerRadius={65}
              paddingAngle={2}
              dataKey="value"
            >
              {data.map((_, index) => (
                <Cell key={index} fill={PIE_COLORS[index % PIE_COLORS.length]} />
              ))}
            </Pie>
            <Tooltip
              formatter={(value: number, name: string, props: { payload: { percentage: number } }) => [
                `${value} (${props.payload.percentage.toFixed(1)}%)`,
                name,
              ]}
            />
            <Legend
              layout="vertical"
              align="right"
              verticalAlign="middle"
              iconSize={8}
              wrapperStyle={{ fontSize: '11px', lineHeight: '18px' }}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
