export interface Repository {
  id: string;
  name: string;
  description: string;
  lastCommit: string;
  totalCommits: number;
  contributors: number;
  activity: "high" | "medium" | "low" | "stale";
  knowledgeConcentration: number;
  topContributors: Array<{
    name: string;
    percentage: number;
  }>;
  hotspots: Array<{
    path: string;
    changes: number;
  }>;
  dependencies: string[];
  alerts: Array<{
    type: "warning" | "danger" | "info";
    message: string;
  }>;
}

export interface Person {
  id: string;
  name: string;
  email: string;
  avatar: string;
  repositories: Array<{
    name: string;
    commits: number;
    lastActivity: string;
    expertise: number;
  }>;
  technologies: Array<{
    name: string;
    level: number;
  }>;
  domains: string[];
  recentActivity: number;
  alerts: Array<{
    type: "warning" | "danger" | "info";
    message: string;
  }>;
}

export const repositories: Repository[] = [
  {
    id: "1",
    name: "reports-service",
    description: "Serviço de geração e exportação de relatórios",
    lastCommit: "2024-01-15",
    totalCommits: 847,
    contributors: 8,
    activity: "high",
    knowledgeConcentration: 45,
    topContributors: [
      { name: "Ana Silva", percentage: 32 },
      { name: "Carlos Santos", percentage: 28 },
      { name: "Beatriz Lima", percentage: 18 },
    ],
    hotspots: [
      { path: "src/exporters/pdf.ts", changes: 124 },
      { path: "src/generators/financial.ts", changes: 98 },
      { path: "src/api/reports.controller.ts", changes: 87 },
    ],
    dependencies: ["finance-core", "analytics-service"],
    alerts: [
      {
        type: "info",
        message: "Alta atividade recente - 47 commits nos últimos 30 dias",
      },
      {
        type: "warning",
        message: "Forte dependência com analytics-service - mudanças costumam ocorrer juntas",
      },
    ],
  },
  {
    id: "2",
    name: "finance-core",
    description: "Núcleo de lógica financeira e contábil",
    lastCommit: "2023-03-22",
    totalCommits: 1243,
    contributors: 5,
    activity: "stale",
    knowledgeConcentration: 75,
    topContributors: [
      { name: "Marcos Oliveira", percentage: 75 },
      { name: "Paula Costa", percentage: 15 },
      { name: "Roberto Alves", percentage: 10 },
    ],
    hotspots: [
      { path: "src/ledger/transactions.ts", changes: 203 },
      { path: "src/models/account.ts", changes: 156 },
      { path: "src/calculations/balance.ts", changes: 134 },
    ],
    dependencies: ["database-layer"],
    alerts: [
      {
        type: "danger",
        message: "Repositório sem alterações há 10 meses - risco de conhecimento obsoleto",
      },
      {
        type: "danger",
        message: "Marcos Oliveira responsável por 75% das alterações - concentração crítica",
      },
      {
        type: "warning",
        message: "Módulo ledger/ tem apenas 1 pessoa ativa historicamente",
      },
    ],
  },
  {
    id: "3",
    name: "ui-dashboard",
    description: "Interface web do dashboard principal",
    lastCommit: "2024-01-18",
    totalCommits: 2156,
    contributors: 12,
    activity: "high",
    knowledgeConcentration: 38,
    topContributors: [
      { name: "Clara Mendes", percentage: 38 },
      { name: "Diego Ferreira", percentage: 24 },
      { name: "Elena Rodrigues", percentage: 19 },
    ],
    hotspots: [
      { path: "src/pages/Reports.tsx", changes: 178 },
      { path: "src/components/Charts/FinancialChart.tsx", changes: 145 },
      { path: "src/components/Filters/DateRangePicker.tsx", changes: 132 },
    ],
    dependencies: ["reports-service", "auth-service"],
    alerts: [
      {
        type: "info",
        message: "Boa distribuição de conhecimento entre 12 contribuidores",
      },
      {
        type: "warning",
        message: "Componente FinancialChart.tsx modificado frequentemente - possível hotspot de bugs",
      },
    ],
  },
  {
    id: "4",
    name: "analytics-service",
    description: "Processamento e análise de dados",
    lastCommit: "2024-01-10",
    totalCommits: 634,
    contributors: 6,
    activity: "medium",
    knowledgeConcentration: 52,
    topContributors: [
      { name: "Fernando Souza", percentage: 52 },
      { name: "Gabriela Martins", percentage: 28 },
      { name: "Hugo Pereira", percentage: 20 },
    ],
    hotspots: [
      { path: "src/processors/metrics.ts", changes: 89 },
      { path: "src/aggregators/daily.ts", changes: 76 },
      { path: "src/api/analytics.controller.ts", changes: 68 },
    ],
    dependencies: ["database-layer", "cache-service"],
    alerts: [
      {
        type: "warning",
        message: "Fernando Souza é responsável por mais de 50% das alterações",
      },
      {
        type: "info",
        message: "Atividade moderada - 18 commits nos últimos 30 dias",
      },
    ],
  },
  {
    id: "5",
    name: "auth-service",
    description: "Autenticação e autorização",
    lastCommit: "2023-11-30",
    totalCommits: 456,
    contributors: 4,
    activity: "low",
    knowledgeConcentration: 68,
    topContributors: [
      { name: "Igor Nascimento", percentage: 68 },
      { name: "Julia Campos", percentage: 22 },
      { name: "Lucas Barbosa", percentage: 10 },
    ],
    hotspots: [
      { path: "src/strategies/jwt.ts", changes: 94 },
      { path: "src/middleware/auth.ts", changes: 82 },
      { path: "src/services/token.service.ts", changes: 71 },
    ],
    dependencies: ["database-layer"],
    alerts: [
      {
        type: "warning",
        message: "Sem commits há 2 meses - atividade baixa",
      },
      {
        type: "danger",
        message: "Igor Nascimento detém 68% do conhecimento - risco de concentração",
      },
    ],
  },
];

export const people: Person[] = [
  {
    id: "1",
    name: "Ana Silva",
    email: "ana.silva@company.com",
    avatar: "AS",
    repositories: [
      { name: "reports-service", commits: 271, lastActivity: "2024-01-15", expertise: 95 },
      { name: "ui-dashboard", commits: 89, lastActivity: "2024-01-12", expertise: 65 },
      { name: "analytics-service", commits: 34, lastActivity: "2023-12-20", expertise: 40 },
    ],
    technologies: [
      { name: "TypeScript", level: 95 },
      { name: "Node.js", level: 90 },
      { name: "React", level: 75 },
      { name: "PostgreSQL", level: 70 },
    ],
    domains: ["Relatórios", "Exportação de Dados", "APIs REST"],
    recentActivity: 47,
    alerts: [
      {
        type: "info",
        message: "Principal especialista em reports-service com 271 commits",
      },
      {
        type: "warning",
        message: "Conhecimento concentrado em poucos repositórios - considerar diversificação",
      },
    ],
  },
  {
    id: "2",
    name: "Marcos Oliveira",
    email: "marcos.oliveira@company.com",
    avatar: "MO",
    repositories: [
      { name: "finance-core", commits: 932, lastActivity: "2023-03-22", expertise: 98 },
      { name: "database-layer", commits: 156, lastActivity: "2023-04-10", expertise: 75 },
      { name: "reports-service", commits: 45, lastActivity: "2023-02-15", expertise: 35 },
    ],
    technologies: [
      { name: "Java", level: 98 },
      { name: "Spring Boot", level: 95 },
      { name: "SQL", level: 92 },
      { name: "Contabilidade", level: 88 },
    ],
    domains: ["Finanças", "Contabilidade", "Transações", "Ledger"],
    recentActivity: 0,
    alerts: [
      {
        type: "danger",
        message: "Único especialista em finance-core - risco crítico de concentração",
      },
      {
        type: "danger",
        message: "Sem atividade há 10 meses - conhecimento pode estar desatualizado",
      },
      {
        type: "warning",
        message: "Responsável por 75% das alterações em finance-core",
      },
    ],
  },
  {
    id: "3",
    name: "Clara Mendes",
    email: "clara.mendes@company.com",
    avatar: "CM",
    repositories: [
      { name: "ui-dashboard", commits: 819, lastActivity: "2024-01-18", expertise: 96 },
      { name: "design-system", commits: 234, lastActivity: "2024-01-16", expertise: 85 },
      { name: "reports-service", commits: 67, lastActivity: "2024-01-10", expertise: 45 },
    ],
    technologies: [
      { name: "React", level: 98 },
      { name: "TypeScript", level: 95 },
      { name: "CSS/Tailwind", level: 92 },
      { name: "UX/UI", level: 88 },
    ],
    domains: ["Interface", "Componentes", "Visualização de Dados", "UX"],
    recentActivity: 52,
    alerts: [
      {
        type: "info",
        message: "Principal desenvolvedora frontend com alta atividade recente",
      },
      {
        type: "info",
        message: "Boa distribuição entre ui-dashboard e design-system",
      },
    ],
  },
  {
    id: "4",
    name: "Fernando Souza",
    email: "fernando.souza@company.com",
    avatar: "FS",
    repositories: [
      { name: "analytics-service", commits: 330, lastActivity: "2024-01-10", expertise: 92 },
      { name: "data-pipeline", commits: 178, lastActivity: "2024-01-08", expertise: 80 },
      { name: "reports-service", commits: 89, lastActivity: "2023-12-28", expertise: 55 },
    ],
    technologies: [
      { name: "Python", level: 95 },
      { name: "Node.js", level: 85 },
      { name: "Data Analysis", level: 92 },
      { name: "SQL", level: 88 },
    ],
    domains: ["Analytics", "Processamento de Dados", "Métricas", "ETL"],
    recentActivity: 28,
    alerts: [
      {
        type: "warning",
        message: "Responsável por 52% das alterações em analytics-service",
      },
      {
        type: "info",
        message: "Especialista em processamento e análise de dados",
      },
    ],
  },
  {
    id: "5",
    name: "Diego Ferreira",
    email: "diego.ferreira@company.com",
    avatar: "DF",
    repositories: [
      { name: "ui-dashboard", commits: 517, lastActivity: "2024-01-17", expertise: 88 },
      { name: "mobile-app", commits: 298, lastActivity: "2024-01-14", expertise: 82 },
      { name: "auth-service", commits: 45, lastActivity: "2023-11-20", expertise: 40 },
    ],
    technologies: [
      { name: "React", level: 90 },
      { name: "React Native", level: 88 },
      { name: "TypeScript", level: 85 },
      { name: "GraphQL", level: 75 },
    ],
    domains: ["Frontend", "Mobile", "Componentes", "State Management"],
    recentActivity: 41,
    alerts: [
      {
        type: "info",
        message: "Forte atuação em frontend web e mobile",
      },
      {
        type: "info",
        message: "Bom complemento de conhecimento com Clara Mendes",
      },
    ],
  },
];

export interface FeatureAnalysis {
  feature: string;
  impactedRepos: Array<{
    name: string;
    confidence: number;
    reasoning: string;
    modules: string[];
  }>;
  recommendedPeople: Array<{
    name: string;
    relevance: number;
    reasoning: string;
  }>;
  risks: Array<{
    type: "high" | "medium" | "low";
    message: string;
  }>;
  suggestedOrder: Array<{
    step: number;
    action: string;
    repository: string;
    reasoning: string;
  }>;
  additionalRecommendations: string[];
}

export const exampleAnalysis: FeatureAnalysis = {
  feature: "Implementar suporte a exportação de relatórios financeiros consolidados",
  impactedRepos: [
    {
      name: "reports-service",
      confidence: 95,
      reasoning: "Forte histórico de commits contendo 'report', 'export', 'finance'. Responsável pela geração e exportação de relatórios.",
      modules: ["src/exporters/", "src/generators/financial.ts", "src/api/reports.controller.ts"],
    },
    {
      name: "finance-core",
      confidence: 88,
      reasoning: "Contém estruturas de dados financeiros e lógica de consolidação usadas em relatórios.",
      modules: ["src/ledger/", "src/calculations/balance.ts", "src/models/account.ts"],
    },
    {
      name: "ui-dashboard",
      confidence: 82,
      reasoning: "Interface responsável por telas de relatórios, filtros e visualização de dados financeiros.",
      modules: ["src/pages/Reports.tsx", "src/components/Charts/", "src/components/Filters/"],
    },
    {
      name: "analytics-service",
      confidence: 65,
      reasoning: "Pode ser necessário para agregação de dados consolidados antes da exportação.",
      modules: ["src/aggregators/", "src/processors/metrics.ts"],
    },
  ],
  recommendedPeople: [
    {
      name: "Ana Silva",
      relevance: 95,
      reasoning: "Principal especialista em reports-service com 271 commits. Mexeu 14 vezes no módulo de exportação nos últimos 6 meses.",
    },
    {
      name: "Marcos Oliveira",
      relevance: 92,
      reasoning: "Único especialista em finance-core, responsável por 75% das alterações. Conhecimento crítico sobre estruturas financeiras.",
    },
    {
      name: "Clara Mendes",
      relevance: 85,
      reasoning: "Principal autora das últimas alterações em ui-dashboard. Especialista em componentes de visualização de dados.",
    },
    {
      name: "Fernando Souza",
      relevance: 70,
      reasoning: "Especialista em analytics-service. Pode auxiliar na agregação de dados consolidados.",
    },
  ],
  risks: [
    {
      type: "high",
      message: "finance-core não recebe mudanças há 10 meses - risco de conhecimento obsoleto e possíveis incompatibilidades",
    },
    {
      type: "high",
      message: "Apenas Marcos Oliveira fez 75% das alterações no módulo ledger/ - concentração crítica de conhecimento",
    },
    {
      type: "medium",
      message: "reports-service tem forte dependência histórica com analytics-service - mudanças podem impactar ambos",
    },
    {
      type: "medium",
      message: "Módulo de exportação em reports-service é um hotspot com 124 alterações - área sensível a bugs",
    },
    {
      type: "low",
      message: "ui-dashboard tem boa distribuição de conhecimento, mas componente FinancialChart.tsx é frequentemente modificado",
    },
  ],
  suggestedOrder: [
    {
      step: 1,
      action: "Revisão e atualização do modelo de dados financeiros",
      repository: "finance-core",
      reasoning: "Dependência ascendente - outros serviços dependem destas estruturas. Necessário garantir compatibilidade antes de prosseguir.",
    },
    {
      step: 2,
      action: "Implementar lógica de consolidação e agregação",
      repository: "analytics-service",
      reasoning: "Preparar dados consolidados que serão consumidos pelo serviço de relatórios.",
    },
    {
      step: 3,
      action: "Desenvolver nova funcionalidade de exportação consolidada",
      repository: "reports-service",
      reasoning: "Implementar a lógica principal de exportação usando dados consolidados.",
    },
    {
      step: 4,
      action: "Criar interface e componentes de visualização",
      repository: "ui-dashboard",
      reasoning: "Última camada - interface depende dos serviços backend estarem prontos.",
    },
  ],
  additionalRecommendations: [
    "Criar documentação técnica do módulo ledger/ em finance-core antes de iniciar alterações",
    "Realizar pair programming entre Ana Silva e Marcos Oliveira para transferência de conhecimento sobre finance-core",
    "Considerar code review cruzado entre Fernando Souza e Ana Silva para reduzir concentração de conhecimento",
    "Implementar testes de integração entre reports-service e analytics-service devido à forte dependência",
    "Agendar sessão de alinhamento técnico com Clara Mendes antes de iniciar trabalho no frontend",
  ],
};