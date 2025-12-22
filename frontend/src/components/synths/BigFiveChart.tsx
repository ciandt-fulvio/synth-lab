// src/components/synths/BigFiveChart.tsx

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import type { BigFivePersonality } from '@/types';

interface BigFiveChartProps {
  personality: BigFivePersonality;
}

export function BigFiveChart({ personality }: BigFiveChartProps) {
  const data = [
    { trait: 'Abertura', value: personality.abertura || 0 },
    { trait: 'Conscienciosidade', value: personality.conscienciosidade || 0 },
    { trait: 'Extroversão', value: personality.extroversao || 0 },
    { trait: 'Amabilidade', value: personality.amabilidade || 0 },
    { trait: 'Neuroticismo', value: personality.neuroticismo || 0 },
  ];

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={data} layout="vertical" margin={{ top: 5, right: 30, left: 100, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis type="number" domain={[0, 100]} />
        <YAxis dataKey="trait" type="category" />
        <Tooltip />
        <Bar dataKey="value" fill="hsl(var(--primary))" />
      </BarChart>
    </ResponsiveContainer>
  );
}
