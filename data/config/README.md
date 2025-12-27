# Configurações do Sistema

Este diretório contém arquivos de configuração estáticos do sistema.

## Arquivos

### scenarios.json

Define os cenários pré-configurados para simulações Monte Carlo.

**Cenários disponíveis:**

- **baseline** - Condições típicas de uso
  - Valores neutros (modifiers = 0.0)
  - Task criticality: 0.5 (média)

- **crisis** - Situação de urgência
  - Motivation: +0.2 (maior urgência)
  - Trust: -0.1 (menos confiança sob pressão)
  - Friction: -0.15 (tolera menos fricção)
  - Task criticality: 0.85 (alta)

- **first-use** - Primeira experiência com o produto
  - Motivation: +0.1 (curiosidade)
  - Trust: -0.2 (desconfiança inicial)
  - Friction: 0.0 (neutro)
  - Task criticality: 0.2 (baixa - apenas explorando)

**Formato:**

```json
{
  "scenario_id": {
    "id": "scenario_id",
    "name": "Nome do Cenário",
    "description": "Descrição",
    "motivation_modifier": 0.0,
    "trust_modifier": 0.0,
    "friction_modifier": 0.0,
    "task_criticality": 0.5
  }
}
```

**Como adicionar novos cenários:**

1. Edite `scenarios.json`
2. Adicione um novo objeto com os campos acima
3. Ajuste os modificadores conforme necessário:
   - Modifiers: valores entre -1.0 e +1.0
   - Task criticality: entre 0.0 (nada crítico) e 1.0 (muito crítico)
4. Reinicie o servidor API

**Não é necessário alterar o banco de dados** - os cenários são carregados automaticamente do arquivo JSON.
