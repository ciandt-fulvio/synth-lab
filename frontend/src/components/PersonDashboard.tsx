import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Users, GitBranch, Mail } from "lucide-react";

const PersonDashboard = () => {
  const mockPeople = [
    {
      id: "person-1",
      name: "nome-pessoa-1",
      role: "cargo-pessoa-1",
      email: "email-pessoa-1@exemplo.com",
      contributions: "contribuições-pessoa-1",
      projects: "projetos-pessoa-1",
    },
    {
      id: "person-2",
      name: "nome-pessoa-2",
      role: "cargo-pessoa-2",
      email: "email-pessoa-2@exemplo.com",
      contributions: "contribuições-pessoa-2",
      projects: "projetos-pessoa-2",
    },
    {
      id: "person-3",
      name: "nome-pessoa-3",
      role: "cargo-pessoa-3",
      email: "email-pessoa-3@exemplo.com",
      contributions: "contribuições-pessoa-3",
      projects: "projetos-pessoa-3",
    },
  ];

  return (
    <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
      {mockPeople.map((person) => (
        <Card key={person.id}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">{person.name}</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{person.role}</div>
            <p className="text-xs text-muted-foreground mt-2">
              <div className="flex items-center gap-1">
                <Mail className="h-3 w-3" /> {person.email}
              </div>
              <div className="flex items-center gap-1">
                <GitBranch className="h-3 w-3" /> {person.contributions} Contribuições
              </div>
              <div className="flex items-center gap-1">
                <Users className="h-3 w-3" /> {person.projects} Projetos
              </div>
            </p>
          </CardContent>
        </Card>
      ))}
    </div>
  );
};

export default PersonDashboard;