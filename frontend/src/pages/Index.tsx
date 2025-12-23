// src/pages/Index.tsx

import { useState } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { InterviewList } from "@/components/interviews/InterviewList";
import { SynthList } from "@/components/synths/SynthList";
import { FileText, Users } from "lucide-react";

export default function Index() {
  const [activeTab, setActiveTab] = useState("interviews");

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center gap-3">
            <img
              src="/synthlab-log.png"
              alt="SynthLab Logo"
              className="h-8 w-auto"
            />
            <h1 className="text-3xl font-bold text-gray-900">
              SynthLab
            </h1>
          </div>
          <p className="mt-2 text-sm text-gray-600 mb-6">
            Plataforma de pesquisa com personas sintéticas
          </p>
          <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="interviews" className="flex items-center gap-2">
                <FileText className="w-4 h-4" />
                Interviews
              </TabsTrigger>
              <TabsTrigger value="synths" className="flex items-center gap-2">
                <Users className="w-4 h-4" />
                Synths
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
