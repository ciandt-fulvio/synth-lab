import { Toaster } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Index from "./pages/Index";
import ExperimentDetail from "./pages/ExperimentDetail";
import ExplorationDetail from "./pages/ExplorationDetail";
import ExplorationPreview from "./pages/ExplorationPreview";
import SimulationDetail from "./pages/SimulationDetail";
import InterviewDetail from "./pages/InterviewDetail";
import Synths from "./pages/Synths";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <BrowserRouter>
        <Routes>
          {/* Home - Experiment List */}
          <Route path="/" element={<Index />} />

          {/* Experiment Detail */}
          <Route path="/experiments/:id" element={<ExperimentDetail />} />

          {/* Simulation Detail (within experiment) */}
          <Route path="/experiments/:id/simulations/:simId" element={<SimulationDetail />} />

          {/* Exploration Detail (within experiment) */}
          <Route path="/experiments/:id/explorations/:explorationId" element={<ExplorationDetail />} />

          {/* Exploration Preview - React Flow (within experiment) */}
          <Route path="/experiments/:id/explorations-preview/:explorationId" element={<ExplorationPreview />} />

          {/* Interview Detail (legacy route) */}
          <Route path="/interviews/:execId" element={<InterviewDetail />} />

          {/* Interview Detail (new route within experiment) */}
          <Route path="/experiments/:expId/interviews/:execId" element={<InterviewDetail />} />

          {/* Synths Catalog */}
          <Route path="/synths" element={<Synths />} />

          {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
