import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Progress } from "@/components/ui/progress";
import { exampleAnalysis, type FeatureAnalysis } from "@/data/mockData";
import { Sparkles, Send, GitBranch, Users, AlertTriangle, ListOrdered, Lightbulb, Loader2 } from "lucide-react";
import { showSuccess } from "@/utils/toast";

const PlanningAssistant = () => {
  const [input, setInput] = useState("");
  const [analysis, setAnalysis] = useState<FeatureAnalysis | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const handleAnalyze = () => {
    if (!input.trim()) return;

    setIsAnalyzing(true);
    
    // Simulate AI processing
    setTimeout(() => {
      setAnalysis({
        ...exampleAnalysis,
        feature: input,
      });
      setIsAnalyzing(false);
      showSuccess("Análise concluída com sucesso!");
    }, 2000);
  };

  const getRiskColor = (type: string) => {
    switch (type) {
      case "high": return "border-red-500 bg-red-50 text-red-900";
      case "medium": return "border-yellow-500 bg-yellow-50 text-yellow-900";
      case "low": return "border-blue-500 bg-blue-50 text-blue-900";
      default: return "border-gray-500 bg-gray-50 text-gray-900";
    }
  };

  const getRiskBadge = (type: string) => {
    switch (type) {
      case "high": return <Badge variant="destructive">Alto Risco</Badge>;
      case "medium": return <Badge className="bg-yellow-500">Risco Médio</Badge>;
      case "low": return <Badge className="bg-blue-500">Risco Baixo</Badge>;
      default: return <Badge variant="secondary">Desconhecido</Badge>;
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Sparkles className="w-6 h-6 text-purple-500" />
            Assistente de Planejamento com IA
          </CardTitle>
          <CardDescription>
            Descreva a funcionalidade que deseja implementar e receba uma análise completa de impacto, riscos e recomendações
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium">Descrição da Funcionalidade</label>
            <Textarea
              placeholder="Ex: Precisamos implementar suporte a exportação de relatórios financeiros consolidados..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              rows={4}
              className="resize-none"
            />
          </div>
          <Button
            onClick={handleAnalyze}
            disabled={!input.trim() || isAnalyzing}
            className="w-full"
            size="lg"
          >
            {isAnalyzing ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Analisando...
              </>
            ) : (
              <>
                <Send className="w-4 h-4 mr-2" />
                Analisar Funcionalidade
              </>
            )}
          </Button>
        </CardContent>
      </Card>

      {analysis && (
        <div className="space-y-6 animate-in fade-in duration-500">
          <Card className="border-purple-200 bg-purple-50">
            <CardHeader>
              <CardTitle className="text-purple-900">Funcionalidade Analisada</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-purple-800 font-medium">{analysis.feature}</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <GitBranch className="w-5 h-5 text-blue-500" />
                Repositórios Impactados
              </CardTitle>
              <CardDescription>
                Análise de impacto baseada em histórico e semântica
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {analysis.impactedRepos.map((repo, index) => (
                <div key={index} className="space-y-3 p-4 bg-gray-50 rounded-lg border">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h4 className="font-semibold text-lg">{repo.name}</h4>
                      <p className="text-sm text-gray-600 mt-1">{repo.reasoning}</p>
                    </div>
                    <div className="text-right ml-4">
                      <div className="text-2xl font-bold text-blue-600">{repo.confidence}%</div>
                      <div className="text-xs text-gray-500">confiança</div>
                    </div>
                  </div>
                  <div>
                    <Progress value={repo.confidence} className="h-2" />
                  </div>
                  <div>
                    <h5 className="text-xs font-semibold text-gray-700 mb-2">Módulos Afetados:</h5>
                    <div className="flex flex-wrap gap-2">
                      {repo.modules.map((module, idx) => (
                        <Badge key={idx} variant="outline" className="text-xs font-mono">
                          {module}
                        </Badge>
                      ))}
                    </div>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Users className="w-5 h-5 text-green-500" />
                Pessoas Recomendadas
              </CardTitle>
              <CardDescription>
                Especialistas com conhecimento relevante para esta funcionalidade
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {analysis.recommendedPeople.map((person, index) => (
                <div key={index} className="flex items-start gap-4 p-3 bg-gray-50 rounded-lg">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <h4 className="font-semibold">{person.name}</h4>
                      <Badge variant="secondary" className="text-xs">
                        {person.relevance}% relevância
                      </Badge>
                    </div>
                    <p className="text-sm text-gray-600">{person.reasoning}</p>
                  </div>
                  <Progress value={person.relevance} className="w-20 h-2 mt-2" />
                </div>
              ))}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-orange-500" />
                Riscos Identificados
              </CardTitle>
              <CardDescription>
                Potenciais problemas e pontos de atenção
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {analysis.risks.map((risk, index) => (
                <Alert key={index} className={getRiskColor(risk.type)}>
                  <div className="flex items-start justify-between gap-3">
                    <AlertDescription className="text-sm flex-1">
                      {risk.message}
                    </AlertDescription>
                    {getRiskBadge(risk.type)}
                  </div>
                </Alert>
              ))}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <ListOrdered className="w-5 h-5 text-purple-500" />
                Ordem Sugerida de Implementação
              </CardTitle>
              <CardDescription>
                Sequência lógica baseada em dependências e histórico
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {analysis.suggestedOrder.map((step, index) => (
                <div key={index} className="flex gap-4">
                  <div className="flex-shrink-0">
                    <div className="w-10 h-10 rounded-full bg-purple-500 text-white flex items-center justify-center font-bold">
                      {step.step}
                    </div>
                  </div>
                  <div className="flex-1 pb-4 border-l-2 border-gray-200 pl-4 -ml-5">
                    <h4 className="font-semibold text-lg mb-1">{step.action}</h4>
                    <Badge variant="outline" className="mb-2">
                      {step.repository}
                    </Badge>
                    <p className="text-sm text-gray-600">{step.reasoning}</p>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>

          <Card className="border-green-200 bg-green-50">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-green-900">
                <Lightbulb className="w-5 h-5 text-green-600" />
                Recomendações Adicionais
              </CardTitle>
              <CardDescription className="text-green-700">
                Sugestões para reduzir riscos e melhorar a execução
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2">
                {analysis.additionalRecommendations.map((rec, index) => (
                  <li key={index} className="flex items-start gap-2 text-sm text-green-900">
                    <span className="text-green-600 font-bold mt-0.5">•</span>
                    <span>{rec}</span>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        </div>
      )}

      {!analysis && !isAnalyzing && (
        <Card className="border-dashed border-2">
          <CardContent className="py-12">
            <div className="text-center text-gray-500">
              <Sparkles className="w-12 h-12 mx-auto mb-4 text-gray-400" />
              <p className="text-lg font-medium mb-2">Pronto para Analisar</p>
              <p className="text-sm">
                Digite a descrição de uma funcionalidade acima e clique em "Analisar" para receber insights detalhados
              </p>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default PlanningAssistant;