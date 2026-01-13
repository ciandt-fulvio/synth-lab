030 - Grupos de Synths Customizados                                                                                          
                                                                                                                                                    
  1. Objetivo                                                                                                                                       
                                                                                                                                                    
  Permitir que PMs criem grupos de synths com distribuições customizadas dos Fatores Raiz para simular públicos específicos (ex: aposentados, PcD,  
  universitários, especialistas).                                                                                                                   
                                                                                                                                                    
  ---                                                                                                                                               
  2. Fatores Raiz Configuráveis                                                                                                                     
  
  │        Fator        │    Controle     │                        Opções                         │  Default  │                                       
  │ Idade               │ Sliders de peso │ 4 faixas: 15-29, 30-44, 45-59, 60+                    │ IBGE      │                                       
  │ Escolaridade        │ Sliders de peso │ 4 níveis: Sem instrução, Fundamental, Médio, Superior │ IBGE      │                                       
  │ Deficiências        │ Slider único    │ 0% a 100%                                             │ 8% (IBGE) │                                       
  │ Composição Familiar │ Sliders de peso │ 5 tipos                                               │ IBGE      │                                       
  │ Domain Expertise    │ Radio buttons   │ Baixo, Regular, Alto                                  │ Regular   │                                     
  └─────────────────────┴─────────────────┴───────────────────────────────────────────────────────┴───────────┘                                     
  ---                                                                                                                                               
  3. Fluxo UX                                                                                                                                       
                                                                                                                                                    
  3.1 Modal de Criação                                                                                                                              
                                                                                                                                                    
  ┌──────────────────────────────────────────────────────────────┐                                                                                  
  │  Criar Grupo de Synths                                       │                                                                                  
  │                                                              │                                                                                  
  │  Baseado em: [Default ▼]                                     │                                                                                  
  │                                                              │                                                                                  
  │  Nome*: [___________________]                                │                                                                                  
  │  Descrição: [______________________________] 0/50            │                                                                                  
  │                                                              │                                                                                  
  │  ─── Idade ───────────────────────────────────────────────   │                                                                                  
  │                                                              │                                                                                  
  │  15-29   ████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░  26%      │                                                                                   
  │  30-44   █████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░  27%      │                                                                                   
  │  45-59   ███████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  24%      │                                                                                   
  │  60+     ██████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  23%      │                                                                                   
  │                                        [Resetar para IBGE]   │                                                                                  
  │                                                              │                                                                                  
  │  ─── Escolaridade ────────────────────────────────────────   │                                                                                  
  │                                                              │                                                                                  
  │  Sem instrução   ███░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░   7%  │                                                                                  
  │  Fundamental     ████████████████░░░░░░░░░░░░░░░░░░░░░  33%  │                                                                                  
  │  Médio           ███████████████░░░░░░░░░░░░░░░░░░░░░░  31%  │                                                                                  
  │  Superior        ██████████████░░░░░░░░░░░░░░░░░░░░░░░  29%  │                                                                                  
  │                                        [Resetar para IBGE]   │                                                                                  
  │                                                              │                                                                                  
  │  ─── Deficiências ────────────────────────────────────────   │                                                                                  
  │                                                              │                                                                                  
  │  % com deficiência   ████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  8%  │                                                                                  
  │                                        [Resetar para IBGE]   │                                                                                  
  │                                                              │                                                                                  
  │  ─── Composição Familiar ─────────────────────────────────   │                                                                                  
  │                                                              │                                                                                  
  │  Unipessoal          ███████░░░░░░░░░░░░░░░░░░░░░░░░░░  15%  │                                                                                  
  │  Casal sem filhos    █████████░░░░░░░░░░░░░░░░░░░░░░░░  20%  │                                                                                  
  │  Casal com filhos    █████████████████░░░░░░░░░░░░░░░░  35%  │                                                                                  
  │  Monoparental        ████████░░░░░░░░░░░░░░░░░░░░░░░░░  18%  │                                                                                  
  │  Multigeracional     █████░░░░░░░░░░░░░░░░░░░░░░░░░░░░  12%  │                                                                                  
  │                                        [Resetar para IBGE]   │                                                                                  
  │                                                              │                                                                                  
  │  ─── Conhecimento no Assunto ─────────────────────────────   │                                                                                  
  │                                                              │                                                                                  
  │  ( ) Baixo (maioria leigos)                                  │                                                                                  
  │  (●) Regular (distribuição equilibrada)                      │                                                                                  
  │  ( ) Alto (maioria especialistas)                            │                                                                                  
  │                                                              │                                                                                  
  │                                                              │                                                                                  
  │  [Cancelar]                              [Gerar Synths]      │                                                                                  
  │                                                              │                                                                                  
  └──────────────────────────────────────────────────────────────┘                                                                                  
                                                                                                                                                    
  3.2 Visual do Slider-Histograma                                                                                                                   
                                                                                                                                                    
  Label      [████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░]  XX%                                                                                        
             ↑                                        ↑                                                                                             
             Cor forte (preenchido)     Cor pastel/background                                                                                       
                                                                                                                                                    
             O usuário arrasta a borda entre as cores                                                                                               
                                                                                                                                                    
  3.3 Loading State                                                                                                                                 
                                                                                                                                                    
  ┌──────────────────────────────────────────────────────────────┐                                                                                  
  │                                                              │                                                                                  
  │                    ◐ Gerando synths...                       │                                                                                  
  │                                                              │                                                                                  
  │                    Isso pode levar alguns segundos.          │                                                                                  
  │                                                              │                                                                                  
  └──────────────────────────────────────────────────────────────┘                                                                                  
                                                                                                                                                    
  3.4 Comportamento dos Sliders                                                                                                                     
  ┌────────────────────┬─────────────────────────────────────────────────────────────────────────┐                                                  
  │   Comportamento    │                                Descrição                                │                                                    
  │ Redistribuição     │ Ao ajustar um slider, os outros se redistribuem para manter soma = 100% │                                                    
  │ Mínimo             │ Cada faixa pode ir até 0%                                               │                                                    
  │ Máximo             │ Cada faixa pode ir até 100%                                             │                                                    
  │ Atualização visual │ Histograma atualiza em tempo real                                       │                                                    
  │ "Baseado em"       │ Carrega config do grupo selecionado como ponto de partida               │                                                  
  └────────────────────┴─────────────────────────────────────────────────────────────────────────┘                                                  
  ---                                                                                                                                               
  4. Escolaridade - Mapeamento Interno                                                                                                              
                                                                                                                                                    
  4.1 UI → Interno                                                                                                                                  
  ┌───────────────┬─────────────────────────────────────────────────────────┐                                                                       
  │   Opção UI    │                   Agrupa Internamente                   │                                                                       
  │ Sem instrução │ sem_instrucao                                           │                                                                       
  │ Fundamental   │ fundamental_incompleto + fundamental_completo           │                                                                       
  │ Médio         │ medio_incompleto + medio_completo                       │                                                                       
  │ Superior      │ superior_incompleto + superior_completo + pos_graduacao │                                                                       
  └───────────────┴─────────────────────────────────────────────────────────┘                                                                       
  4.2 Proporções Internas (IBGE)                                                                                                                    
                                                                                                                                                    
  ESCOLARIDADE_INTERNAL_RATIOS = {                                                                                                                  
      "fundamental": {                                                                                                                              
          "fundamental_incompleto": 0.763,  # 25.1 / (25.1 + 7.8)                                                                                   
          "fundamental_completo": 0.237     # 7.8 / (25.1 + 7.8)                                                                                    
      },                                                                                                                                            
      "medio": {                                                                                                                                    
          "medio_incompleto": 0.134,        # 4.2 / (4.2 + 27.2)                                                                                    
          "medio_completo": 0.866           # 27.2 / (4.2 + 27.2)                                                                                   
      },                                                                                                                                            
      "superior": {                                                                                                                                 
          "superior_incompleto": 0.183,     # 5.3 / (5.3 + 17.5 + 6.1)                                                                              
          "superior_completo": 0.606,       # 17.5 / (5.3 + 17.5 + 6.1)                                                                             
          "pos_graduacao": 0.211            # 6.1 / (5.3 + 17.5 + 6.1)                                                                              
      }                                                                                                                                             
  }                                                                                                                                                 
                                                                                                                                                    
  4.3 Exemplo                                                                                                                                       
                                                                                                                                                    
  Se o usuário define "Fundamental = 40%", internamente:                                                                                            
  - fundamental_incompleto: 40% × 0.763 = 30.5%                                                                                                     
  - fundamental_completo: 40% × 0.237 = 9.5%                                                                                                        
                                                                                                                                                    
  ---                                                                                                                                               
  5. Deficiências - Lógica de Geração                                                                                                               
                                                                                                                                                    
  5.1 Comportamento por Faixa do Slider                                                                                                             
  ┌─────────────┬──────────────────────┬──────────────────────┬─────────────────────────┐                                                           
  │    Faixa    │ taxa_com_deficiencia │ "nenhuma" no sorteio │ Distribuição Severidade │                                                           
  │ ≤ 8% (IBGE) │ valor do slider      │ Sim                  │ Uniforme (20% cada)     │                                                           
  │ > 8%        │ valor do slider      │ Não                  │ Pesada em severos       │                                                           
  └─────────────┴──────────────────────┴──────────────────────┴─────────────────────────┘                                                           
  5.2 Distribuições de Severidade                                                                                                                   
                                                                                                                                                    
  IBGE (slider ≤ 8%)                                                                                                                                
  {                                                                                                                                                 
    "nenhuma": 0.20,                                                                                                                                
    "leve": 0.20,                                                                                                                                   
    "moderada": 0.20,                                                                                                                               
    "severa": 0.20,                                                                                                                                 
    "total": 0.20                                                                                                                                   
  }                                                                                                                                                 
                                                                                                                                                    
  Pesada (slider > 8%)                                                                                                                              
  {                                                                                                                                                 
    "nenhuma": 0.00,                                                                                                                                
    "leve": 0.10,                                                                                                                                   
    "moderada": 0.25,                                                                                                                               
    "severa": 0.30,                                                                                                                                 
    "total": 0.35                                                                                                                                   
  }                                                                                                                                                 
                                                                                                                                                    
  5.3 Mapeamento de "total"                                                                                                                         
  ┌───────────┬─────────────────────────────┐                                                                                                       
  │ Categoria │     "total" mapeia para     │                                                                                                       
  │ Visual    │ cegueira                    │                                                                                                       
  │ Auditiva  │ surdez                      │                                                                                                       
  │ Motora    │ severa (não existe "total") │                                                                                                       
  │ Cognitiva │ severa (não existe "total") │                                                                                                       
  └───────────┴─────────────────────────────┘                                                                                                       
  5.4 Pseudocódigo                                                                                                                                  
                                                                                                                                                    
  def generate_disabilities(config: dict) -> dict:                                                                                                  
      taxa = config["taxa_com_deficiencia"]                                                                                                         
      dist_severidade = config["distribuicao_severidade"]                                                                                           
                                                                                                                                                    
      tem_deficiencia = random.random() < taxa                                                                                                      
                                                                                                                                                    
      if not tem_deficiencia:                                                                                                                       
          return todas_nenhuma()                                                                                                                    
                                                                                                                                                    
      def sample_severidade(incluir_total: bool):                                                                                                   
          opcoes = ["nenhuma", "leve", "moderada", "severa"]                                                                                        
          pesos = [dist_severidade[o] for o in opcoes]                                                                                              
          if incluir_total:                                                                                                                         
              opcoes.append("total")                                                                                                                
              pesos.append(dist_severidade["total"])                                                                                                
          # Normaliza e sorteia                                                                                                                     
          return weighted_choice(opcoes, pesos)                                                                                                     
                                                                                                                                                    
      visual_sev = sample_severidade(incluir_total=True)                                                                                            
      auditiva_sev = sample_severidade(incluir_total=True)                                                                                          
      motora_sev = sample_severidade(incluir_total=False)                                                                                           
      cognitiva_sev = sample_severidade(incluir_total=False)                                                                                        
                                                                                                                                                    
      return {                                                                                                                                      
          "visual": {"tipo": "cegueira" if visual_sev == "total" else visual_sev},                                                                  
          "auditiva": {"tipo": "surdez" if auditiva_sev == "total" else auditiva_sev},                                                              
          "motora": {"tipo": motora_sev},                                                                                                           
          "cognitiva": {"tipo": cognitiva_sev},                                                                                                     
      }                                                                                                                                             
                                                                                                                                                    
  ---                                                                                                                                               
  6. Domain Expertise - Parâmetros Beta                                                                                                             
  ┌──────────┬───────┬──────┬────────────────┐                                                                                                      
  │ Opção UI │ Alpha │ Beta │ Média Esperada │                                                                                                      
  │ Baixo    │ 2     │ 5    │ ~0.29          │                                                                                                      
  │ Regular  │ 3     │ 3    │ ~0.50          │                                                                                                      
  │ Alto     │ 5     │ 2    │ ~0.71          │                                                                                                      
  └──────────┴───────┴──────┴────────────────┘                                                                                                      
  ---                                                                                                                                               
  7. Persistência                                                                                                                                   
                                                                                                                                                    
  7.1 Tabela synth_groups                                                                                                                           
  ┌─────────────┬───────────────┬─────────────────────────────┐                                                                                     
  │    Campo    │     Tipo      │          Descrição          │                                                                                     
                                                                                       
  │ id          │ string (UUID) │ PK                          │                                                                                     
                                                                                       
  │ name        │ string        │ Nome do grupo (obrigatório) │                                                                                     
                                                                                       
  │ description │ string | null │ Descrição (max 50 chars)    │                                                                                     
                                                                                       
  │ created_at  │ datetime      │ Data de criação             │                                                                                     
                                                                                       
  │ config      │ JSONB         │ Parâmetros de geração       │                                                                                     
  └─────────────┴───────────────┴─────────────────────────────┘                                                                                     
  7.2 Estrutura do config JSON                                                                                                                      
                                                                                                                                                    
  {                                                                                                                                                 
    "n_synths": 500,                                                                                                                                
    "distributions": {                                                                                                                              
      "idade": {                                                                                                                                    
        "15-29": 0.26,                                                                                                                              
        "30-44": 0.27,                                                                                                                              
        "45-59": 0.24,                                                                                                                              
        "60+": 0.23                                                                                                                                 
      },                                                                                                                                            
      "escolaridade": {                                                                                                                             
        "sem_instrucao": 0.068,                                                                                                                     
        "fundamental": 0.329,                                                                                                                       
        "medio": 0.314,                                                                                                                             
        "superior": 0.289                                                                                                                           
      },                                                                                                                                            
      "deficiencias": {                                                                                                                             
        "taxa_com_deficiencia": 0.084,                                                                                                              
        "distribuicao_severidade": {                                                                                                                
          "nenhuma": 0.20,                                                                                                                          
          "leve": 0.20,                                                                                                                             
          "moderada": 0.20,                                                                                                                         
          "severa": 0.20,                                                                                                                           
          "total": 0.20                                                                                                                             
        }                                                                                                                                           
      },                                                                                                                                            
      "composicao_familiar": {                                                                                                                      
        "unipessoal": 0.15,                                                                                                                         
        "casal_sem_filhos": 0.20,                                                                                                                   
        "casal_com_filhos": 0.35,                                                                                                                   
        "monoparental": 0.18,                                                                                                                       
        "multigeracional": 0.12                                                                                                                     
      },                                                                                                                                            
      "domain_expertise": {                                                                                                                         
        "alpha": 3,                                                                                                                                 
        "beta": 3                                                                                                                                   
      }                                                                                                                                             
    }                                                                                                                                               
  }                                                                                                                                                 
                                                                                                                                                    
  7.3 Seed do Grupo Default                                                                                                                         
                                                                                                                                                    
  O grupo default deve ter config preenchido com valores IBGE explícitos:                                                                           
                                                                                                                                                    
  {                                                                                                                                                 
    "id": "default",                                                                                                                                
    "name": "Default",                                                                                                                              
    "description": "Distribuição IBGE",                                                                                                             
    "created_at": "2024-01-01T00:00:00Z",                                                                                                           
    "config": {                                                                                                                                     
      "n_synths": 500,                                                                                                                              
      "distributions": {                                                                                                                            
        "idade": {                                                                                                                                  
          "15-29": 0.26,                                                                                                                            
          "30-44": 0.27,                                                                                                                            
          "45-59": 0.24,                                                                                                                            
          "60+": 0.23                                                                                                                               
        },                                                                                                                                          
        "escolaridade": {                                                                                                                           
          "sem_instrucao": 0.068,                                                                                                                   
          "fundamental": 0.329,                                                                                                                     
          "medio": 0.314,                                                                                                                           
          "superior": 0.289                                                                                                                         
        },                                                                                                                                          
        "deficiencias": {                                                                                                                           
          "taxa_com_deficiencia": 0.084,                                                                                                            
          "distribuicao_severidade": {                                                                                                              
            "nenhuma": 0.20,                                                                                                                        
            "leve": 0.20,                                                                                                                           
            "moderada": 0.20,                                                                                                                       
            "severa": 0.20,                                                                                                                         
            "total": 0.20                                                                                                                           
          }                                                                                                                                         
        },                                                                                                                                          
        "composicao_familiar": {                                                                                                                    
          "unipessoal": 0.15,                                                                                                                       
          "casal_sem_filhos": 0.20,                                                                                                                 
          "casal_com_filhos": 0.35,                                                                                                                 
          "monoparental": 0.18,                                                                                                                     
          "multigeracional": 0.12                                                                                                                   
        },                                                                                                                                          
        "domain_expertise": {                                                                                                                       
          "alpha": 3,                                                                                                                               
          "beta": 3                                                                                                                                 
        }                                                                                                                                           
      }                                                                                                                                             
    }                                                                                                                                               
  }                                                                                                                                                 
                                                                                                                                                    
  ---                                                                                                                                               
  8. API                                                                                                                                            
                                                                                                                                                    
  8.1 Endpoints                                                                                                                                     
  ┌────────┬────────────────────────┬──────────────────────────────────────┐                                                                        
  │ Método │          Rota          │              Descrição               │                                                                        
  │ GET    │ /api/synth-groups      │ Lista todos os grupos                │                                                                        
  │ GET    │ /api/synth-groups/{id} │ Detalhes de um grupo (inclui config) │                                                                        
  │ POST   │ /api/synth-groups      │ Cria novo grupo + gera synths        │                                                                        
  └────────┴────────────────────────┴──────────────────────────────────────┘                                                                        
  8.2 Request POST /api/synth-groups                                                                                                                
                                                                                                                                                    
  {                                                                                                                                                 
    "name": "Aposentados 60+",                                                                                                                      
    "description": "Grupo para simular previdência",                                                                                                
    "config": {                                                                                                                                     
      "n_synths": 500,                                                                                                                              
      "distributions": {                                                                                                                            
        "idade": {                                                                                                                                  
          "15-29": 0.05,                                                                                                                            
          "30-44": 0.05,                                                                                                                            
          "45-59": 0.10,                                                                                                                            
          "60+": 0.80                                                                                                                               
        },                                                                                                                                          
        "escolaridade": {                                                                                                                           
          "sem_instrucao": 0.10,                                                                                                                    
          "fundamental": 0.40,                                                                                                                      
          "medio": 0.30,                                                                                                                            
          "superior": 0.20                                                                                                                          
        },                                                                                                                                          
        "deficiencias": {                                                                                                                           
          "taxa_com_deficiencia": 0.25,                                                                                                             
          "distribuicao_severidade": {                                                                                                              
            "nenhuma": 0.00,                                                                                                                        
            "leve": 0.10,                                                                                                                           
            "moderada": 0.25,                                                                                                                       
            "severa": 0.30,                                                                                                                         
            "total": 0.35                                                                                                                           
          }                                                                                                                                         
        },                                                                                                                                          
        "composicao_familiar": {                                                                                                                    
          "unipessoal": 0.30,                                                                                                                       
          "casal_sem_filhos": 0.40,                                                                                                                 
          "casal_com_filhos": 0.10,                                                                                                                 
          "monoparental": 0.10,                                                                                                                     
          "multigeracional": 0.10                                                                                                                   
        },                                                                                                                                          
        "domain_expertise": {                                                                                                                       
          "alpha": 2,                                                                                                                               
          "beta": 5                                                                                                                                 
        }                                                                                                                                           
      }                                                                                                                                             
    }                                                                                                                                               
  }                                                                                                                                                 
                                                                                                                                                    
  8.3 Response POST                                                                                                                                 
                                                                                                                                                    
  {                                                                                                                                                 
    "id": "abc123",                                                                                                                                 
    "name": "Aposentados 60+",                                                                                                                      
    "description": "Grupo para simular previdência",                                                                                                
    "created_at": "2026-01-12T10:30:00Z",                                                                                                           
    "synths_count": 500                                                                                                                             
  }                                                                                                                                                 
                                                                                                                                                    
  ---                                                                                                                                               
  10. Regras de Negócio                                                                                                                             
  ┌─────────────────────────────┬─────────────────────────────────────────────────┐                                                                 
  │            Regra            │                  Comportamento                  │                                                                 
  │ Grupos são imutáveis        │ Após criação, não pode editar                   │                                                                 
  │ "Baseado em" carrega config │ Facilita duplicação/variação                    │                                                                 
  │ Grupo default é fixo        │ Sempre existe, distribuições IBGE               │                                                                 
  │ Synths gerados na criação   │ 500 synths criados junto com grupo              │                                                                 
  │ n_synths fixo               │ Sempre 500 (pode ser parametrizado futuramente) │                                                                 
  └─────────────────────────────┴─────────────────────────────────────────────────┘                                                                 
  ---                                                                                                                                               
  11. Impacto na Simulação                                                                                                                          
  ┌──────────────────────┬───────────────────────────────────┬──────────────────────────────────────┐                                               
  │    Grupo Exemplo     │          Característica           │      Impacto nos Latent Traits       │                                               
  │ "Aposentados 60+"    │ idade 60+ = 80%                   │ time_availability ↑, motor_ability ↓ │                                               
  │ "PcD 50%"            │ 50% com deficiência               │ motor_ability ↓↓, capability_mean ↓  │                                               
  │ "Especialistas"      │ domain_expertise alto             │ capability_mean ↑ (peso 0.10)        │                                               
  │ "Universitários"     │ escolaridade superior = 80%       │ digital_literacy ↑, trust_mean ↑     │                                               
  │ "Baixa escolaridade" │ fundamental + sem instrução = 70% │ digital_literacy ↓, trust_mean ↓     │                                               
  └──────────────────────┴───────────────────────────────────┴──────────────────────────────────────┘                                              