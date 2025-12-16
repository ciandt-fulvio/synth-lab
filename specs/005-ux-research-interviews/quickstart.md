# Quickstart: Entrevistas de Pesquisa UX com Synths

## Visão Geral

O comando `synthlab research` permite executar entrevistas de pesquisa UX simuladas com personas sintéticas (synths). Duas LLMs conversam em tempo real: uma como entrevistador profissional de UX e outra como o synth, respondendo de acordo com sua personalidade, demografia e vieses.

## Pré-requisitos

1. **API Key da OpenAI**: Configure a variável de ambiente:
   ```bash
   export OPENAI_API_KEY="sua-chave-aqui"
   ```

2. **Synths gerados**: Certifique-se de ter synths em `data/synths/synths.json`:
   ```bash
   synthlab gensynth -n 5  # Gera 5 synths
   ```

3. **Guia de tópicos** (opcional): Crie um arquivo com os temas da entrevista.

## Uso Básico

### Entrevista com synth específico

```bash
# Listar synths disponíveis
synthlab listsynth

# Executar entrevista com synth específico
synthlab research fhynws
```

### Com guia de tópicos personalizado

```bash
synthlab research fhynws --topic-guide data/topic_guides/ecommerce.md
```

### Configurando número de turnos

```bash
# Entrevista curta (5 turnos)
synthlab research fhynws --max-rounds 5

# Entrevista longa (20 turnos)
synthlab research fhynws --max-rounds 20
```

## Parâmetros do Comando

| Parâmetro | Tipo | Obrigatório | Default | Descrição |
|-----------|------|-------------|---------|-----------|
| synth_id | str | Sim | - | ID do synth (6 caracteres) |
| --topic-guide | str | Não | None | Caminho para arquivo de guia de tópicos |
| --max-rounds | int | Não | 10 | Máximo de turnos de conversa |
| --model | str | Não | gpt-4.1 | Modelo LLM a usar |
| --output-dir | str | Não | data/transcripts/ | Diretório para salvar transcrições |

## Criando um Guia de Tópicos

O guia de tópicos direciona a entrevista. Crie um arquivo Markdown:

```markdown
# Guia: Experiência de Compra Mobile

## Objetivos
- Entender hábitos de compra pelo celular
- Identificar frustrações no checkout
- Explorar preferências de pagamento

## Perguntas Principais
1. Com que frequência você faz compras pelo celular?
2. O que mais te frustra no processo de compra?
3. Como você prefere pagar?

## Temas para Aprofundar
- Segurança e confiança
- Comparação de preços
- Experiências de devolução
```

## Exemplos Práticos

### Exemplo 1: Pesquisa sobre E-commerce

```bash
# Criar guia de tópicos
cat > data/topic_guides/ecommerce.md << 'EOF'
# Pesquisa: E-commerce Mobile

## Objetivos
- Comportamento de compra
- Barreiras de conversão
- Métodos de pagamento preferidos

## Perguntas
1. Conte sobre sua última compra online
2. O que te faz desistir de uma compra?
3. Qual forma de pagamento você prefere?
EOF

# Executar entrevista
synthlab research fhynws --topic-guide data/topic_guides/ecommerce.md
```

### Exemplo 2: Pesquisa sobre App de Banco

```bash
synthlab research abc123 \
  --topic-guide data/topic_guides/banco-digital.md \
  --max-rounds 15
```

## Output da Entrevista

### Visualização em Tempo Real

Durante a entrevista, você verá mensagens formatadas:

```
╭─ Entrevistador ───────────────────────────────────────╮
│ Olá! Obrigado por participar. Podemos começar        │
│ falando sobre seus hábitos de compra online?         │
╰───────────────────────────────────────────────────────╯

╭─ João Lucas (fhynws) ─────────────────────────────────╮
│ Bom, eu costumo fazer compras pelo celular quando    │
│ estou no ônibus voltando do trabalho. É prático.     │
╰───────────────────────────────────────────────────────╯
```

### Transcrição Salva

Ao final, uma transcrição JSON é salva:

```
✓ Entrevista concluída!
  Transcrição salva em: data/transcripts/fhynws_20251216_143052.json
  Duração: 4m 32s
  Turnos: 10
```

## Estrutura da Transcrição

```json
{
  "session": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "synth_id": "fhynws",
    "topic_guide_path": "data/topic_guides/ecommerce.md",
    "max_rounds": 10,
    "actual_rounds": 10,
    "start_time": "2025-12-16T14:30:52.123Z",
    "end_time": "2025-12-16T14:35:24.456Z",
    "duration_seconds": 272.333,
    "status": "completed",
    "model_used": "gpt-4.1",
    "termination_reason": "interviewer_signal"
  },
  "synth_snapshot": { /* dados completos do synth */ },
  "messages": [
    {
      "speaker": "interviewer",
      "content": "Olá! Obrigado por participar...",
      "timestamp": "2025-12-16T14:30:52.123Z",
      "round_number": 1
    },
    {
      "speaker": "synth",
      "content": "Bom, eu costumo fazer compras...",
      "timestamp": "2025-12-16T14:31:15.456Z",
      "round_number": 1
    }
  ],
  "metadata": {
    "version": "1.0.0",
    "created_at": "2025-12-16T14:35:24.789Z"
  }
}
```

## Tratamento de Erros

### Synth não encontrado

```bash
$ synthlab research xyz123
Erro: Synth com ID 'xyz123' não encontrado.
Use 'synthlab listsynth' para ver IDs disponíveis.
```

### API Key não configurada

```bash
$ synthlab research fhynws
Erro: OPENAI_API_KEY não configurada.
Configure: export OPENAI_API_KEY="sua-chave"
```

### Guia de tópicos não encontrado

```bash
$ synthlab research fhynws --topic-guide arquivo-inexistente.md
Erro: Arquivo não encontrado: arquivo-inexistente.md
```

## Dicas de Uso

1. **Escolha synths variados**: Entreviste synths com diferentes perfis demográficos e de personalidade para obter insights diversos.

2. **Guias de tópicos focados**: Guias mais específicos geram entrevistas mais direcionadas e úteis.

3. **Ajuste max_rounds**: Use menos turnos para exploração rápida, mais turnos para profundidade.

4. **Revise as transcrições**: As `internal_notes` do entrevistador contêm insights valiosos sobre o comportamento do synth.

5. **Compare personalidades**: O mesmo guia com synths diferentes revela como personalidade afeta respostas.

## Próximos Passos

- Explore os synths disponíveis: `synthlab listsynth`
- Gere mais synths: `synthlab gensynth -n 10`
- Analise transcrições para insights de pesquisa
