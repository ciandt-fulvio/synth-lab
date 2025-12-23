// src/pages/Index.tsx

import { useState } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { InterviewList } from "@/components/interviews/InterviewList";
import { SynthList } from "@/components/synths/SynthList";
import { useResearchList } from "@/hooks/use-research";
import { useSynthsList } from "@/hooks/use-synths";
import { FileText, Users } from "lucide-react";

export default function Index() {
  const [activeTab, setActiveTab] = useState("interviews");

  // [TABS-COUNTER] Fetch data for tab counters
  const { data: researchData } = useResearchList();
  const { data: synthsData } = useSynthsList();
  const interviewCount = researchData?.data?.length ?? 0;
  const synthCount = synthsData?.data?.length ?? 0;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* [HEADER-BG] Gradiente sutil no fundo */}
      <header className="bg-gradient-to-r from-slate-50 via-white to-blue-50/30 border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center gap-3">
            {/* [HEADER-LOGO-ANIMATION] Animação pulse com clareamento a cada 2s */}
            <img
              src="/synthlab-log.png"
              alt="SynthLab Logo"
              className="h-8 w-auto logo-pulse-loop"
            />
            {/* [HEADER-TITLE-GRADIENT] Gradiente no título */}
            <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
              SynthLab
            </h1>
            {/* [HEADER-BADGE] Badge Beta */}
            <Badge variant="secondary" className="bg-purple-100 text-purple-700 hover:bg-purple-100">
              Beta
            </Badge>
          </div>
          {/* [HEADER-TAGLINE] Nova tagline */}
          <p className="mt-2 text-sm font-semibold text-gray-600 mb-6">
            Pesquisa sintética, insights reais
          </p>
          {/* [TABS-STYLED] Tabs com ícones coloridos, gradiente, hover e contador */}
          <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
            <TabsList className="grid w-full grid-cols-2 bg-gray-100/80 p-1">
              <TabsTrigger
                value="interviews"
                className={`
                  flex items-center gap-2 transition-all duration-200
                  hover:shadow-md
                  data-[state=active]:bg-gradient-to-r data-[state=active]:from-blue-500 data-[state=active]:to-purple-500
                  data-[state=active]:text-white data-[state=active]:shadow-lg
                `}
              >
                <FileText className={`w-4 h-4 ${activeTab === "interviews" ? "text-white" : "text-gray-400"}`} />
                Interviews
                <span className={`text-xs px-1.5 py-0.5 rounded-full ${
                  activeTab === "interviews"
                    ? "bg-white/20 text-white"
                    : "bg-gray-200 text-gray-500"
                }`}>
                  {interviewCount}
                </span>
              </TabsTrigger>
              <TabsTrigger
                value="synths"
                className={`
                  flex items-center gap-2 transition-all duration-200
                  hover:shadow-md
                  data-[state=active]:bg-gradient-to-r data-[state=active]:from-blue-500 data-[state=active]:to-purple-500
                  data-[state=active]:text-white data-[state=active]:shadow-lg
                `}
              >
                <Users className={`w-4 h-4 ${activeTab === "synths" ? "text-white" : "text-gray-400"}`} />
                Synths
                <span className={`text-xs px-1.5 py-0.5 rounded-full ${
                  activeTab === "synths"
                    ? "bg-white/20 text-white"
                    : "bg-gray-200 text-gray-500"
                }`}>
                  {synthCount}
                </span>
              </TabsTrigger>
            </TabsList>
          </Tabs>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsContent value="interviews">
            <InterviewList />
          </TabsContent>

          <TabsContent value="synths">
            <SynthList />
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}
