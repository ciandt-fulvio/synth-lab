import { Toaster } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { ProtectedRoute } from "./components/auth/ProtectedRoute";
import Index from "./pages/Index";
import LoginPage from "./pages/LoginPage";
import ExperimentDetail from "./pages/ExperimentDetail";
import ExplorationDetail from "./pages/ExplorationDetail";
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
          {/* Public Routes */}
          <Route path="/login" element={<LoginPage />} />

          {/* Protected Routes */}
          <Route path="/" element={<ProtectedRoute><Index /></ProtectedRoute>} />
          <Route path="/experiments/:id" element={<ProtectedRoute><ExperimentDetail /></ProtectedRoute>} />
          <Route path="/experiments/:id/simulations/:simId" element={<ProtectedRoute><SimulationDetail /></ProtectedRoute>} />
          <Route path="/experiments/:id/explorations/:explorationId" element={<ProtectedRoute><ExplorationDetail /></ProtectedRoute>} />
          <Route path="/interviews/:execId" element={<ProtectedRoute><InterviewDetail /></ProtectedRoute>} />
          <Route path="/experiments/:expId/interviews/:execId" element={<ProtectedRoute><InterviewDetail /></ProtectedRoute>} />
          <Route path="/synths" element={<ProtectedRoute><Synths /></ProtectedRoute>} />

          {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
