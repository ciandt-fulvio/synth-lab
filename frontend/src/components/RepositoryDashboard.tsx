import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { GitBranch, Star, Users } from "lucide-react";

const RepositoryDashboard = () => {
  const mockRepositories = [
    {
      id: "repo-1",
      name: "titulo-card-1",
      description: "Descrição genérica do componente A.",
      stars: "data-card-1",
      forks: "data-card-2",
      contributors: "data-card-3",
      lastUpdate: "data-card-4",
    },
    {
      id: "repo-2",
      name: "titulo-card-2",
      description: "Descrição genérica do componente B.",
      stars: "data-card-5",
      forks: "data-card-6",
      contributors: "data-card-7",
      lastUpdate: "data-card-8",
    },
    {
      id: "repo-3",
      name: "titulo-card-3",
      description: "Descrição genérica do componente C.",
      stars: "data-card-9",
      forks: "data-card-10",
      contributors: "data-card-11",
      lastUpdate: "data-card-12",
    },
  ];

  return (
    <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
      {mockRepositories.map((repo) => (
        <Card key={repo.id}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">{repo.name}</CardTitle>
            <GitBranch className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{repo.description}</div>
            <p className="text-xs text-muted-foreground mt-2">
              <div className="flex items-center gap-1">
                <Star className="h-3 w-3" /> {repo.stars} Estrelas
              </div>
              <div className="flex items-center gap-1">
                <GitBranch className="h-3 w-3" /> {repo.forks} Forks
              </div>
              <div className="flex items-center gap-1">
                <Users className="h-3 w-3" /> {repo.contributors} Contribuidores
              </div>
              <div className="mt-1">Última atualização: {repo.lastUpdate}</div>
            </p>
          </CardContent>
        </Card>
      ))}
    </div>
  );
};

export default RepositoryDashboard;