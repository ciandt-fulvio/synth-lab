import { useState, useCallback, useMemo, useRef } from "react";
import * as d3 from "d3";

// ============================================================
// LLM CALLS
// ============================================================
async function callLLM(systemPrompt, userPrompt, model = "claude-sonnet-4-20250514") {
  const resp = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      model,
      max_tokens: 4096,
      system: systemPrompt,
      messages: [{ role: "user", content: userPrompt }],
    }),
  });
  const data = await resp.json();
  return data.content?.map(b => b.type === "text" ? b.text : "").join("") || "";
}

// ============================================================
// SYNTHETIC USERS
// ============================================================
function generateUsers(n = 2000) {
  const users = [];
  const rnorm = (mu, sig) => {
    let u = 0, v = 0;
    while (!u) u = Math.random();
    while (!v) v = Math.random();
    return mu + sig * Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
  };
  const cl = (x, lo, hi) => Math.max(lo, Math.min(hi, x));
  for (let i = 0; i < n; i++) {
    const age = cl(Math.round(rnorm(38, 14)), 18, 80);
    const eduY = cl(Math.round(rnorm(12, 3)), 4, 22);
    const income = cl(Math.round(Math.exp(rnorm(8.5, 0.8))), 1500, 80000);
    const hasCh = Math.random() < (age > 25 ? 0.55 : 0.15);
    const famSz = hasCh ? Math.ceil(Math.random() * 3) + 1 : Math.random() < 0.4 ? 1 : 2;
    const visDis = Math.random() < 0.04;
    const motDis = Math.random() < 0.03;
    const techAff = cl(rnorm(0.5, 0.2) + (age < 35 ? 0.15 : age > 55 ? -0.2 : 0) + (eduY > 16 ? 0.1 : 0), 0, 1);
    const incN = cl((income - 1500) / 78500, 0, 1);
    const eduN = cl((eduY - 4) / 18, 0, 1);
    users.push({
      id: i, age, income, educationYears: eduY, familySize: famSz, hasChildren: hasCh,
      hasVisualDisability: visDis, hasMotorDisability: motDis, techAffinity: techAff,
      incomeNorm: incN, ageNorm: cl((age - 18) / 62, 0, 1), eduNorm: eduN,
      investorProxy: incN * 0.6 + eduN * 0.4,
      planningNeed: (famSz / 5) * 0.5 + cl((age - 18) / 62, 0, 1) * 0.3 + (hasCh ? 0.2 : 0),
      familySizeNorm: famSz / 5,
      hasVisualDisab: visDis ? 1 : 0,
      hasMotorDisab: motDis ? 1 : 0,
    });
  }
  return users;
}

// ============================================================
// USER VAR EXTRACTORS
// ============================================================
const EXTRACTORS = {
  ageNorm: u => u.ageNorm, incomeNorm: u => u.incomeNorm,
  eduNorm: u => u.eduNorm, techAffinity: u => u.techAffinity,
  familySizeNorm: u => u.familySizeNorm, hasVisualDisab: u => u.hasVisualDisab,
  hasMotorDisab: u => u.hasMotorDisab, investorProxy: u => u.investorProxy,
  planningNeed: u => u.planningNeed,
};

// ============================================================
// SIMULATION
// ============================================================
const sigmoid = x => 1 / (1 + Math.exp(-x));
const rnorm = (mu, sig) => {
  let u = 0, v = 0;
  while (!u) u = Math.random();
  while (!v) v = Math.random();
  return mu + sig * Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
};

function runSim(users, experiment, sels, nSims = 3000) {
  const res = [], segR = { young: [], mid: [], senior: [], lowInc: [], midInc: [], highInc: [], lowEdu: [], midEdu: [], highEdu: [] };
  // TOTAL_BUDGET: the maximum total logit swing that ALL edges combined can contribute.
  // With 8 edges, each edge contributes at most BUDGET/nEdges × mu_max × userVar_max.
  // BUDGET=3.0 → total swing [-1.5, +1.5] around intercept → realistic 30-70% range.
  const nEdges = experiment.edges.length;
  const BUDGET = 3.0;
  const perEdgeScale = BUDGET / nEdges;

  for (let s = 0; s < nSims; s++) {
    const bI = rnorm(experiment.interceptMu, experiment.interceptSigma);
    const eCoefs = experiment.edges.map((e, i) => {
      const o = e.options[sels[i]];
      const dir = e.direction || 1;
      // mu is [0,1] coupling strength. Scaled so all edges together fit within BUDGET.
      const betaMu = o.mu * perEdgeScale * dir;
      const betaSigma = o.sigma * perEdgeScale; // sigma is fraction, applied to same scale
      return { uv: e.userVar, c: rnorm(betaMu, betaSigma) };
    });
    let ad = 0;
    const sc = { young: 0, mid: 0, senior: 0, lowInc: 0, midInc: 0, highInc: 0, lowEdu: 0, midEdu: 0, highEdu: 0 };
    const st = { young: 0, mid: 0, senior: 0, lowInc: 0, midInc: 0, highInc: 0, lowEdu: 0, midEdu: 0, highEdu: 0 };
    for (const u of users) {
      let lo = bI;
      for (const ec of eCoefs) { const ext = EXTRACTORS[ec.uv]; lo += ec.c * (ext ? ext(u) : 0); }
      const did = Math.random() < sigmoid(lo) ? 1 : 0;
      ad += did;
      if (u.age < 30) { sc.young += did; st.young++; }
      else if (u.age < 50) { sc.mid += did; st.mid++; }
      else { sc.senior += did; st.senior++; }
      if (u.incomeNorm < 0.33) { sc.lowInc += did; st.lowInc++; }
      else if (u.incomeNorm < 0.66) { sc.midInc += did; st.midInc++; }
      else { sc.highInc += did; st.highInc++; }
      if (u.eduNorm < 0.33) { sc.lowEdu += did; st.lowEdu++; }
      else if (u.eduNorm < 0.66) { sc.midEdu += did; st.midEdu++; }
      else { sc.highEdu += did; st.highEdu++; }
    }
    res.push(ad / users.length);
    for (const k of Object.keys(sc)) segR[k].push(st[k] > 0 ? sc[k] / st[k] : 0);
  }
  return { results: res, segmentResults: segR };
}

function computeStats(arr) {
  const s = [...arr].sort((a, b) => a - b);
  return { mean: d3.mean(s), median: d3.median(s), p10: d3.quantile(s, 0.1), p90: d3.quantile(s, 0.9), std: d3.deviation(s), sorted: s };
}

function runSensitivity(users, exp, sels, nSims = 800) {
  const r = {};
  exp.edges.forEach((edge, i) => {
    const lo = sels.map((s, j) => j === i ? 0 : s);
    const hi = sels.map((s, j) => j === i ? edge.options.length - 1 : s);
    const lM = d3.mean(runSim(users, exp, lo, nSims).results);
    const hM = d3.mean(runSim(users, exp, hi, nSims).results);
    r[edge.id] = {
      question: edge.header || edge.statement || edge.question, from: edge.from, to: edge.to,
      currentLabel: edge.options[sels[i]].text || edge.options[sels[i]].label,
      lowLabel: (edge.options[0].text || edge.options[0].label || "").slice(0, 40),
      highLabel: (edge.options[edge.options.length - 1].text || edge.options[edge.options.length - 1].label || "").slice(0, 40),
      low: lM, high: hM, impact: Math.abs(hM - lM),
    };
  });
  return r;
}

// ============================================================
// RAW INTERPRETATION GENERATORS
// ============================================================
function rawDistInterpretation(stats) {
  return `Com 80% de confiança, a taxa de adoção fica entre ${(stats.p10 * 100).toFixed(1)}% e ${(stats.p90 * 100).toFixed(1)}%. A estimativa central é ${(stats.mean * 100).toFixed(1)}%. ${
    stats.std > 0.03 ? "A dispersão é alta — as premissas têm bastante incerteza. Vale investir em pesquisa primária antes de decidir."
    : stats.std > 0.015 ? "A incerteza é moderada. Refinar as premissas mais impactantes pode estreitar essa faixa."
    : "A incerteza é baixa — premissas consistentes, bom sinal para avançar."
  }`;
}

function rawSegInterpretation(segR) {
  const segs = [
    { key: "young", label: "jovens (18–29)" }, { key: "mid", label: "adultos (30–49)" },
    { key: "senior", label: "sêniores (50+)" }, { key: "lowInc", label: "renda baixa" },
    { key: "midInc", label: "renda média" }, { key: "highInc", label: "renda alta" },
    { key: "lowEdu", label: "escolaridade baixa" }, { key: "midEdu", label: "escolaridade média" },
    { key: "highEdu", label: "escolaridade alta" },
  ];
  const means = segs.map(s => ({ ...s, mean: d3.mean(segR[s.key]) }));
  const best = means.reduce((a, b) => a.mean > b.mean ? a : b);
  const worst = means.reduce((a, b) => a.mean < b.mean ? a : b);
  const ratio = best.mean / Math.max(worst.mean, 0.001);
  const ageS = means.filter(s => ["young", "mid", "senior"].includes(s.key));
  const incS = means.filter(s => ["lowInc", "midInc", "highInc"].includes(s.key));
  const eduS = means.filter(s => ["lowEdu", "midEdu", "highEdu"].includes(s.key));
  const ageSp = Math.max(...ageS.map(s => s.mean)) - Math.min(...ageS.map(s => s.mean));
  const incSp = Math.max(...incS.map(s => s.mean)) - Math.min(...incS.map(s => s.mean));
  const eduSp = Math.max(...eduS.map(s => s.mean)) - Math.min(...eduS.map(s => s.mean));
  let t = `Maior adoção: ${best.label} (${(best.mean * 100).toFixed(1)}%). Menor: ${worst.label} (${(worst.mean * 100).toFixed(1)}%).`;
  if (ratio > 2) t += ` Diferença expressiva — considere piloto focado em ${best.label}.`;
  else if (ratio > 1.3) t += ` Diferença relevante. Lançamento gradual por ${best.label} reduz risco.`;
  else t += ` Adoção uniforme — lançamento amplo pode funcionar.`;
  const maxSp = Math.max(ageSp, incSp, eduSp);
  if (maxSp === ageSp && ageSp > 0.02) t += ` Idade é o fator mais discriminante.`;
  else if (maxSp === incSp && incSp > 0.02) t += ` Renda é o fator mais discriminante.`;
  else if (maxSp === eduSp && eduSp > 0.02) t += ` Escolaridade é o fator mais discriminante.`;
  return t;
}

function rawSensInterpretation(sens) {
  const entries = Object.values(sens).sort((a, b) => b.impact - a.impact);
  if (!entries.length) return "";
  const top = entries[0], bot = entries[entries.length - 1];
  let t = `Premissa mais impactante: "${top.from} → ${top.to}" — variação de ${(top.impact * 100).toFixed(1)}pp. Se há dúvida sobre esta relação, é onde pesquisa adicional mais reduz incerteza.`;
  if (entries.length > 1 && entries[1].impact > top.impact * 0.6)
    t += ` Segundo: "${entries[1].from} → ${entries[1].to}" (${(entries[1].impact * 100).toFixed(1)}pp).`;
  if (bot.impact < top.impact * 0.2)
    t += ` "${bot.from} → ${bot.to}" quase não muda o resultado.`;
  return t;
}

// ============================================================
// LLM PROMPTS
// ============================================================
const DAG_SYSTEM = `You are an expert in causal inference, product experimentation, and behavioral modeling for a Brazilian financial institution.

Given an experiment description, generate a causal DAG where each edge is an ASSERTION about how a variable affects another.

RULES:
- 7-10 nodes, 7-10 edges. Last node = outcome (adoption/conversion/engagement).
- CRITICAL DAG STRUCTURE — 3 layers:
  1. DEMOGRAPHIC ROOTS (left): "Idade", "Renda", "Escolaridade" as root nodes (no incoming edges).
  2. MEDIATING VARIABLES (middle): Behavioral/psychological constructs (e.g., "Confiança", "Percepção de Valor").
  3. OUTCOME (right): Final adoption node.
  Every demographic root must have at least 1 outgoing edge.
- Available userVar values (ONLY): ageNorm, incomeNorm, eduNorm, techAffinity, familySizeNorm, hasVisualDisab, hasMotorDisab, investorProxy, planningNeed
  ALL are normalized [0,1] (Beta(2,2)-like distribution).
- Demographic→Mediator: ageNorm (for Idade), incomeNorm (for Renda), eduNorm (for Escolaridade).

CRITICAL — EDGE FORMAT:
Each edge is an ASSERTION (statement), NOT a question. The PM responds with agreement level.

CRITICAL — EDGE HEADER:
Instead of "statement", each edge has a "header" field. This is a SHORT contextual intro:
  Format: "A respeito de quanto [target] é influenciado(a) por [source concept]"
  Example: "A respeito de quanto a Familiaridade Digital é influenciada pela idade"
  Example: "A respeito de quanto a Percepção de Valor é influenciada pela renda"
  Example: "A respeito de quanto a Confiança no Canal é influenciada pela escolaridade"

CRITICAL — OPTIONS (5 self-contained sentences):
Each option has: text, mu, sigma.
- "text" is a COMPLETE, self-contained sentence that the PM reads and agrees/disagrees with.
  It should make sense on its own without needing the header.
- mu is [0,1] coupling strength. sigma is uncertainty fraction. BOTH ARE HIDDEN from PM.
- The PM sees ONLY the text.

The 5 options MUST follow this exact pattern (strongest agreement first, weakest last):
  Option 0: text = strong effect claim.                      mu=0.80, sigma=0.10
  Option 1: text = significant effect claim.                 mu=0.65, sigma=0.20
  Option 2: text = "Não sei dizer se [X] impacta [Y]"       mu=0.50, sigma=0.40
  Option 3: text = weak/uncertain effect claim.              mu=0.30, sigma=0.20
  Option 4: text = no effect claim.                          mu=0.15, sigma=0.10

THESE mu/sigma VALUES ARE FIXED. Do NOT change them.

Example for edge "Idade → Familiaridade Digital" (direction = -1):
  Option 0: "Idade é barreira crítica para familiaridade digital, quanto mais velho, menor a familiaridade"
  Option 1: "Idade reduz significativamente a familiaridade digital"
  Option 2: "Não sei dizer se a idade impacta a familiaridade digital"
  Option 3: "Não há uma relação forte, mas acredito que idade tem alguma relação com a familiaridade digital"
  Option 4: "Idade não afeta familiaridade digital"

RULES FOR OPTION TEXT:
- Option 0 must be the STRONGEST claim, with specificity (e.g., "quanto mais velho, menor...")
- Option 1 is strong but less absolute
- Option 2 ALWAYS starts with "Não sei dizer se..." — this is the uncertainty option
- Option 3 acknowledges some weak relationship but with hedging language
- Option 4 flatly denies the relationship
- ALL options are complete Portuguese sentences. No abbreviations, no labels.

CRITICAL — "direction" field:
Each edge MUST include a "direction" field: 1 (direct/positive) or -1 (inverse/negative).
- direction = -1: source up → target down. Example: "mais velho → menor familiaridade"
- direction = 1: source up → target up. Example: "maior renda → mais valor percebido"

CRITICAL — VARIED DEFAULTS:
- "default" is NOT always 2. Be OPINIONATED based on common sense about the experiment.
- At least 2 edges should have default != 2. At least 1 should be 0,1 or 3,4.

Node names SHORT (max 25 chars). Portuguese BR.

interceptMu: -0.3 to 0.5. interceptSigma: 0.3 to 0.5.

Respond with ONLY valid JSON:
{
  "label": "string",
  "interceptMu": number,
  "interceptSigma": number,
  "nodes": ["string"...],
  "edges": [{
    "id": "string",
    "from": "string",
    "to": "string",
    "userVar": "string",
    "direction": 1 or -1,
    "header": "string",
    "options": [{"text":"string","mu":number,"sigma":number}...5 items],
    "default": number
  }...]
}`;

const INTERP_SYSTEM = `You are a senior product strategy advisor. You help product managers decide next steps based on simulation results.

You will receive the experiment description, the section type, raw statistics, AND the full sensitivity analysis data.

RULES:
- Write in Portuguese BR. 2-4 sentences max.
- Be SPECIFIC to this experiment — reference the actual product/feature.
- Respond with ONLY the text, no quotes, no markdown.

SECTION-SPECIFIC INSTRUCTIONS:

IF section = "Distribuição":
- ALWAYS start with: "Com 80% de confiança, a taxa de adoção fica entre X% e Y%."
- Then analyze the uncertainty: if high, explain WHICH premisses (from sensitivity data) are driving most uncertainty and what the PM can do about it WITHOUT running a full interview (e.g., desk research, competitor benchmarks, internal data analysis).
- If uncertainty is low, say it's a good sign and suggest next steps.

IF section = "Segmentos":
- Focus on the practical implication: which segment to target first, whether differences justify a phased rollout.
- Reference specific segments by name.

IF section = "Sensibilidade":
- Focus on the top 1-2 premisses and what specific research or data could resolve the uncertainty.
- Be concrete: "Para validar se [premissa], analise dados de uso do app atual filtrado por faixa etária" — not generic advice.`;

const QUESTIONNAIRE_SYSTEM = `You are an expert in marketing research following Naresh Malhotra's "Marketing Research: An Applied Orientation".

CONTEXT: A product manager ran a causal simulation for a product experiment. They need a FIELD QUESTIONNAIRE to validate the most critical assumptions with real users BEFORE running the experiment.

CRITICAL CONSTRAINTS:
- The interview is MEDIATED by a trained interviewer who can adapt and probe as needed.
- Each respondent ALREADY has a complete demographic file (age, income, education, family, disabilities). DO NOT include ANY demographic, screening, or profiling questions.
- Output EXACTLY 3 questions — no more, no less.
- Target the TOP 3 most impactful premisses from the sensitivity analysis.

MALHOTRA METHODOLOGY (apply strictly):
- Ch. 10 (Questionnaire Design): Funnel approach — broad to narrow. With 3 questions:
  * Q1: Open-ended / qualitative (ch.9 unstructured — surfaces natural language, gives interviewer room to probe the most impactful variable)
  * Q2: Scenario-based with forced choice (ch.9 non-comparative scaling — presents a concrete hypothetical, tests the 2nd causal relationship directly)
  * Q3: Behavioral intention scale (ch.9 Likert/intention — captures adoption likelihood, anchored to a specific described experience)
- Ch. 10 (Wording): No leading questions, no double-barreled, no jargon. Simple conversational Portuguese BR.
- Ch. 9 (Triangulation): Each question uses a DIFFERENT measurement technique to cross-validate.

OUTPUT FORMAT (Portuguese BR, Markdown):

For each question:
### Pergunta N
**Texto:** [the question, conversational tone]
**Valida:** [NodeA → NodeB]
**O que escutar:**
- [signal that CONFIRMS the premiss]
- [signal that REFUTES the premiss]
- [ambiguous signal worth probing]
**Dica para o entrevistador:** [one sentence on how to probe deeper]

After the 3 questions:
### Nota para o Entrevistador
- Order rationale (funnel per Malhotra ch.10)
- Key bias to watch for in this specific interview context
- How each answer maps back to the simulation (which Likert premiss to adjust up or down, and what that means for the adoption estimate)

Respond ONLY with the questionnaire in Markdown. No preamble, no meta-commentary.`;

// ============================================================
// UI COLORS
// ============================================================
const C = {
  bg: "#080d14", card: "#0a1019", inner: "#0f1520",
  border: "#1a2332", borderL: "#1e2738",
  tx: "#c8d0dc", txL: "#8892a4", txM: "#5a6578", txB: "#e8ecf2",
  acc: "#4F8EF7", purple: "#7B61FF", orange: "#ff6b35",
  green: "#10B981", red: "#ff6b6b",
};

// ============================================================
// COMPONENTS
// ============================================================
function LikertInput({ edge, selectedIndex, onChange }) {
  const headerText = edge.header || edge.statement || edge.question || `${edge.from} → ${edge.to}`;
  return (
    <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 10, padding: "14px 16px", marginBottom: 10 }}>
      <div style={{ marginBottom: 10 }}>
        <span style={{ fontSize: 9, fontFamily: "monospace", color: C.purple, background: `${C.purple}15`, padding: "2px 8px", borderRadius: 10, whiteSpace: "nowrap" }}>
          {edge.from} → {edge.to}
        </span>
        <div style={{ fontSize: 13, color: C.txM, fontWeight: 400, lineHeight: 1.4, marginTop: 6, fontStyle: "italic" }}>
          {headerText}
        </div>
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: 3 }}>
        {edge.options.map((opt, i) => {
          const sel = i === selectedIndex;
          const text = opt.text || (opt.label ? `${opt.label} — ${opt.desc}` : opt.desc);
          return (
            <button key={i} onClick={() => onChange(i)} style={{
              display: "flex", alignItems: "center", gap: 10, padding: "8px 12px",
              background: sel ? `${C.acc}12` : "transparent",
              border: `1.5px solid ${sel ? C.acc : C.border}`, borderRadius: 7,
              cursor: "pointer", textAlign: "left", transition: "all 0.12s",
            }}
              onMouseOver={e => { if (!sel) e.currentTarget.style.borderColor = C.borderL; }}
              onMouseOut={e => { if (!sel) e.currentTarget.style.borderColor = C.border; }}
            >
              <div style={{ width: 16, height: 16, borderRadius: "50%", flexShrink: 0, border: `2px solid ${sel ? C.acc : C.txM}`, display: "flex", alignItems: "center", justifyContent: "center" }}>
                {sel && <div style={{ width: 7, height: 7, borderRadius: "50%", background: C.acc }} />}
              </div>
              <span style={{ fontSize: 12, color: sel ? C.acc : C.tx, fontWeight: sel ? 500 : 400, lineHeight: 1.4 }}>
                {text}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
}

function DAGView({ experiment, selections }) {
  const { nodes, edges } = experiment;
  const W = 580, H = Math.max(260, nodes.length * 38);
  const NODE_W = 120, NODE_H = 28, PAD = 65;

  const positions = useMemo(() => {
    const pos = {};
    // Compute topological depth (longest path from roots)
    const depths = {};
    const getDepth = (node, vis = new Set()) => {
      if (vis.has(node)) return depths[node] || 0;
      vis.add(node);
      const inE = edges.filter(e => e.to === node);
      if (!inE.length) { depths[node] = 0; return 0; }
      const d = 1 + Math.max(...inE.map(e => getDepth(e.from, new Set(vis))));
      depths[node] = d;
      return d;
    };
    nodes.forEach(n => getDepth(n));

    // Group by depth layer
    const layers = {};
    nodes.forEach(n => {
      const d = depths[n] || 0;
      if (!layers[d]) layers[d] = [];
      layers[d].push(n);
    });
    const maxLayer = Math.max(...Object.keys(layers).map(Number), 0);
    const numLayers = maxLayer + 1;

    // Position: X by layer (left to right), Y distributed within layer
    // For chains (1 node per layer), add vertical zigzag to avoid straight line
    const isChain = Object.values(layers).every(l => l.length <= 1);

    Object.entries(layers).forEach(([layerStr, layerNodes]) => {
      const layer = Number(layerStr);
      const x = PAD + (layer / Math.max(numLayers - 1, 1)) * (W - 2 * PAD);

      if (layerNodes.length === 1) {
        // Single node in layer — apply zigzag or centered
        if (isChain) {
          // Zigzag pattern for chain graphs
          const amplitude = H * 0.28;
          const centerY = H / 2;
          const phase = (layer / Math.max(numLayers - 1, 1)) * Math.PI;
          const y = centerY + Math.sin(phase) * amplitude * (layer % 2 === 0 ? 1 : -1) * 0.5;
          // Actually, use a smooth wave
          const t = layer / Math.max(numLayers - 1, 1);
          const waveY = centerY + Math.sin(t * Math.PI * 1.5) * amplitude * 0.6;
          pos[layerNodes[0]] = { x, y: Math.max(NODE_H, Math.min(H - NODE_H, waveY)) };
        } else {
          pos[layerNodes[0]] = { x, y: H / 2 };
        }
      } else {
        // Multiple nodes: distribute vertically
        const spacing = Math.min(55, (H - 2 * NODE_H) / Math.max(layerNodes.length - 1, 1));
        const totalH = spacing * (layerNodes.length - 1);
        const startY = (H - totalH) / 2;
        layerNodes.forEach((n, i) => {
          pos[n] = { x, y: startY + i * spacing };
        });
      }
    });

    return pos;
  }, [nodes, edges, H]);

  // Edge visuals react to selections
  // Blue = direct (positive mu), Orange = inverse (negative mu), Width = intensity
  const edgeVisuals = useMemo(() => {
    return edges.map((e, i) => {
      const opt = e.options[selections[i]];
      const mu = opt.mu; // [0,1] coupling strength
      const dir = e.direction || 1;
      return {
        width: Math.max(1.5, Math.min(6, 1.5 + mu * 5)),
        opacity: Math.min(1, 0.3 + mu * 0.8),
        color: dir < 0 ? C.orange : C.acc, // orange=inverse, blue=direct
      };
    });
  }, [edges, selections]);

  // Generate curved paths for edges (especially skip-connections)
  const edgePaths = useMemo(() => {
    return edges.map((e) => {
      const f = positions[e.from], t = positions[e.to];
      if (!f || !t) return "";
      const dx = t.x - f.x, dy = t.y - f.y;
      const dist = Math.sqrt(dx * dx + dy * dy);
      // Shorten line by node radius to not overlap boxes
      const shortenF = NODE_W * 0.45, shortenT = NODE_W * 0.45;
      const angle = Math.atan2(dy, dx);
      const sx = f.x + Math.cos(angle) * shortenF;
      const sy = f.y + Math.sin(angle) * shortenF;
      const ex = t.x - Math.cos(angle) * shortenT;
      const ey = t.y - Math.sin(angle) * shortenT;

      // Check if this is a skip-connection (spans > 1 layer)
      const isSkip = Math.abs(dx) > (W - 2 * PAD) / (nodes.length - 1) * 1.8;
      if (isSkip) {
        // Curved path
        const cx = (sx + ex) / 2;
        const cy = (sy + ey) / 2 + (dy > 0 ? -35 : 35);
        return `M${sx},${sy} Q${cx},${cy} ${ex},${ey}`;
      }
      return `M${sx},${sy} L${ex},${ey}`;
    });
  }, [edges, positions, nodes.length]);

  return (
    <svg width={W} height={H} style={{ overflow: "visible", display: "block" }}>
      <defs>
        <marker id="ah-direct" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto"><polygon points="0 0, 8 3, 0 6" fill={C.acc} /></marker>
        <marker id="ah-inverse" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto"><polygon points="0 0, 8 3, 0 6" fill={C.orange} /></marker>
      </defs>
      {edges.map((e, i) => {
        const ev = edgeVisuals[i];
        const path = edgePaths[i];
        if (!path) return null;
        return (
          <path key={e.id} d={path}
            stroke={ev.color} strokeWidth={ev.width} opacity={ev.opacity}
            fill="none"
            markerEnd={ev.color === C.orange ? "url(#ah-inverse)" : "url(#ah-direct)"}
            style={{ transition: "stroke-width 0.3s, opacity 0.3s, stroke 0.3s" }}
          />
        );
      })}
      {nodes.map((n) => {
        const p = positions[n]; if (!p) return null;
        const isOutcome = !edges.some(e => e.from === n);
        const isRoot = !edges.some(e => e.to === n);
        // Wrap text into max 3 lines of ~14 chars
        const maxCharsPerLine = 15;
        const words = n.split(/\s+/);
        const lines = [];
        let current = "";
        for (const w of words) {
          if (current.length + w.length + 1 > maxCharsPerLine && current.length > 0) {
            lines.push(current);
            current = w;
          } else {
            current = current ? current + " " + w : w;
          }
        }
        if (current) lines.push(current);
        const displayLines = lines.slice(0, 3);
        if (lines.length > 3) displayLines[2] = displayLines[2].slice(0, 12) + "…";
        const lineH = 11;
        const boxH = Math.max(NODE_H, displayLines.length * lineH + 10);
        return (
          <g key={n}>
            <rect x={p.x - NODE_W / 2} y={p.y - boxH / 2} width={NODE_W} height={boxH} rx={6}
              fill={C.inner}
              stroke={isOutcome ? C.orange : isRoot ? `${C.acc}88` : C.border}
              strokeWidth={isOutcome ? 2 : 1}
            />
            {displayLines.map((line, li) => (
              <text key={li} x={p.x} y={p.y + (li - (displayLines.length - 1) / 2) * lineH + 3.5}
                textAnchor="middle"
                fill={isOutcome ? C.orange : C.tx}
                fontSize={9} fontFamily="monospace" fontWeight={isOutcome ? 600 : 400}>
                {line}
              </text>
            ))}
          </g>
        );
      })}
    </svg>
  );
}

function Histogram({ data, width = 560, height = 170, color = C.acc }) {
  const stats = useMemo(() => computeStats(data), [data]);
  const bins = useMemo(() => {
    const lo = Math.max(0, stats.p10 * 0.7), hi = stats.p90 * 1.3;
    const x = d3.scaleLinear().domain([lo, hi]).range([50, width - 30]);
    return { bins: d3.bin().domain(x.domain()).thresholds(35)(data), x };
  }, [data, stats, width]);
  const maxC = d3.max(bins.bins, d => d.length);
  const y = d3.scaleLinear().domain([0, maxC]).range([height - 35, 8]);
  return (
    <svg width={width} height={height} style={{ overflow: "visible", display: "block" }}>
      {bins.bins.map((bin, i) => {
        const bx = bins.x(bin.x0), bw = Math.max(1, bins.x(bin.x1) - bins.x(bin.x0) - 1);
        const inCI = bin.x0 >= stats.p10 && bin.x1 <= stats.p90;
        return <rect key={i} x={bx} y={y(bin.length)} width={bw} height={height - 35 - y(bin.length)} fill={inCI ? color : `${color}33`} rx={1} />;
      })}
      <line x1={bins.x(stats.mean)} x2={bins.x(stats.mean)} y1={4} y2={height - 32} stroke={C.orange} strokeWidth={2} strokeDasharray="4,3" />
      <text x={bins.x(stats.mean) + 5} y={14} fill={C.orange} fontSize={10} fontFamily="monospace">média={( stats.mean * 100).toFixed(1)}%</text>
      <line x1={50} x2={width - 30} y1={height - 32} y2={height - 32} stroke={C.border} />
      <text x={bins.x(stats.p10)} y={height - 16} fill={C.txM} fontSize={9} textAnchor="middle" fontFamily="monospace">P10 {(stats.p10 * 100).toFixed(1)}%</text>
      <text x={bins.x(stats.p90)} y={height - 16} fill={C.txM} fontSize={9} textAnchor="middle" fontFamily="monospace">P90 {(stats.p90 * 100).toFixed(1)}%</text>
    </svg>
  );
}

function SensitivityChart({ sensitivity }) {
  const entries = Object.entries(sensitivity).map(([k, v]) => ({ key: k, ...v })).sort((a, b) => b.impact - a.impact);
  const maxI = d3.max(entries, d => d.impact) || 1;
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
      {entries.map(e => (
        <div key={e.key}>
          <div style={{ fontSize: 11, color: C.txL, marginBottom: 3, lineHeight: 1.3 }}>
            <span style={{ color: C.purple, fontFamily: "monospace", fontSize: 9 }}>{e.from}→{e.to}</span> {e.question}
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <div style={{ fontSize: 9, color: C.txM, width: 80, textAlign: "right", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{e.lowLabel}</div>
            <div style={{ flex: 1, height: 20, background: C.inner, borderRadius: 4, position: "relative", overflow: "hidden" }}>
              <div style={{ position: "absolute", left: 0, top: 0, height: "100%", borderRadius: 4, width: `${(e.impact / maxI) * 100}%`, background: `linear-gradient(90deg, ${C.acc}, ${C.purple})`, transition: "width 0.4s" }} />
              <span style={{ position: "absolute", right: 6, top: 3, fontSize: 10, color: "#fff", fontFamily: "monospace" }}>Δ{(e.impact * 100).toFixed(1)}pp</span>
            </div>
            <div style={{ fontSize: 9, color: C.txM, width: 80, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{e.highLabel}</div>
          </div>
        </div>
      ))}
    </div>
  );
}

function SegmentBars({ segmentResults }) {
  const groups = [
    { title: "Idade", segs: [
      { key: "young", label: "18–29" }, { key: "mid", label: "30–49" }, { key: "senior", label: "50+" }
    ]},
    { title: "Renda", segs: [
      { key: "lowInc", label: "Baixa" }, { key: "midInc", label: "Média" }, { key: "highInc", label: "Alta" }
    ]},
    { title: "Escolaridade", segs: [
      { key: "lowEdu", label: "Baixa" }, { key: "midEdu", label: "Média" }, { key: "highEdu", label: "Alta" }
    ]},
  ];
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
      {groups.map(g => (
        <div key={g.title}>
          <div style={{ fontSize: 10, color: C.txM, fontFamily: "monospace", marginBottom: 4 }}>{g.title.toUpperCase()}</div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 8 }}>
            {g.segs.map(s => {
              const st = computeStats(segmentResults[s.key]);
              const c = st.mean > 0.6 ? C.green : st.mean > 0.4 ? C.acc : st.mean > 0.25 ? C.purple : C.red;
              return (
                <div key={s.key} style={{ background: C.inner, borderRadius: 8, padding: "10px 12px", border: `1px solid ${C.border}` }}>
                  <div style={{ fontSize: 11, color: C.txL, marginBottom: 3 }}>{s.label}</div>
                  <div style={{ display: "flex", alignItems: "baseline", gap: 4 }}>
                    <span style={{ fontSize: 20, fontWeight: 700, color: c }}>{(st.mean * 100).toFixed(1)}%</span>
                    <span style={{ fontSize: 9, color: C.txM, fontFamily: "monospace" }}>[{(st.p10 * 100).toFixed(1)}–{(st.p90 * 100).toFixed(1)}]</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}

function Interpretation({ raw, ai, loading }) {
  return (
    <div style={{ marginTop: 14, background: "#0f1923", borderRadius: 8, padding: "12px 16px", borderLeft: `3px solid ${C.acc}`, fontSize: 13, color: "#a8b4c4", lineHeight: 1.65 }}>
      {loading ? (
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <div style={{ width: 14, height: 14, border: `2px solid ${C.border}`, borderTopColor: C.acc, borderRadius: "50%", animation: "spin 0.8s linear infinite", flexShrink: 0 }} />
          <span style={{ color: C.txM, fontSize: 12 }}>Contextualizando com AI...</span>
        </div>
      ) : ai ? (
        <>
          <strong style={{ color: C.txB }}>Interpretação contextualizada: </strong>{ai}
          <details style={{ marginTop: 8 }}>
            <summary style={{ fontSize: 10, color: C.txM, cursor: "pointer" }}>Ver interpretação base (estatística)</summary>
            <div style={{ fontSize: 11, color: C.txM, marginTop: 4 }}>{raw}</div>
          </details>
        </>
      ) : (
        <><strong style={{ color: C.txB }}>Interpretação: </strong>{raw}</>
      )}
    </div>
  );
}

function SectionHeader({ number, color, title, subtitle }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 14 }}>
      <div style={{ width: 22, height: 22, borderRadius: "50%", background: color, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 11, fontWeight: 700, color: "#fff", flexShrink: 0 }}>{number}</div>
      <div>
        <h2 style={{ fontSize: 15, fontWeight: 600, color: C.txB, margin: 0 }}>{title}</h2>
        {subtitle && <div style={{ fontSize: 11, color: C.txM, marginTop: 1 }}>{subtitle}</div>}
      </div>
    </div>
  );
}

// ============================================================
// SIMPLE MARKDOWN RENDERER
// ============================================================
function renderMarkdown(md) {
  if (!md) return "";
  let html = md
    // Escape HTML
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    // Headers
    .replace(/^#### (.+)$/gm, '<h4 style="color:#c8d0dc;font-size:13px;font-weight:600;margin:14px 0 6px;font-family:Space Grotesk,sans-serif">$1</h4>')
    .replace(/^### (.+)$/gm, '<h3 style="color:#E879F9;font-size:14px;font-weight:600;margin:18px 0 8px;font-family:Space Grotesk,sans-serif;border-bottom:1px solid #1a2332;padding-bottom:6px">$1</h3>')
    .replace(/^## (.+)$/gm, '<h2 style="color:#e8ecf2;font-size:15px;font-weight:700;margin:22px 0 10px;font-family:Space Grotesk,sans-serif">$1</h2>')
    .replace(/^# (.+)$/gm, '<h1 style="color:#e8ecf2;font-size:17px;font-weight:700;margin:22px 0 10px;font-family:Space Grotesk,sans-serif">$1</h1>')
    // Bold
    .replace(/\*\*(.+?)\*\*/g, '<strong style="color:#e8ecf2">$1</strong>')
    // Italic
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    // Inline code / tags like [Valida: X → Y]
    .replace(/\[Valida:\s*(.+?)\]/g, '<span style="font-size:10px;font-family:monospace;color:#7B61FF;background:#7B61FF15;padding:1px 6px;border-radius:8px">Valida: $1</span>')
    // Numbered lists
    .replace(/^(\d+)\.\s+(.+)$/gm, '<div style="display:flex;gap:8px;margin:4px 0;padding-left:4px"><span style="color:#8892a4;font-family:monospace;min-width:20px;flex-shrink:0">$1.</span><span>$2</span></div>')
    // Bullet points
    .replace(/^[-•]\s+(.+)$/gm, '<div style="display:flex;gap:8px;margin:3px 0;padding-left:12px"><span style="color:#4F8EF7">•</span><span>$1</span></div>')
    // Line breaks (double newline = paragraph)
    .replace(/\n\n/g, '<div style="margin:10px 0"></div>')
    .replace(/\n/g, '<br/>');
  return html;
}

// ============================================================
// EXAMPLES
// ============================================================
const EXAMPLES = [
  "Quero lançar um pix via WhatsApp para facilitar transferências entre contatos",
  "Experimento de ter uma feature de entrega programada no nosso app de delivery de comida",
  "Push notification sobre subida ou queda de ações com botão de comprar/vender para aumentar negociações",
  "Criar um chatbot de atendimento via IA no app do banco para resolver problemas sem ir à agência",
  "Feature de split de conta automático para grupos no app de pagamentos",
];

// ============================================================
// MAIN APP
// ============================================================
export default function App() {
  const [input, setInput] = useState("");
  const [experiment, setExperiment] = useState(null);
  const [selections, setSelections] = useState([]);
  const [simResults, setSimResults] = useState(null);
  const [sensitivity, setSensitivity] = useState(null);
  const [running, setRunning] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [analyzeError, setAnalyzeError] = useState(null);
  const [step, setStep] = useState(0);
  const [users] = useState(() => generateUsers(2000));

  // AI interpretations state
  const [aiInterps, setAiInterps] = useState({ dist: null, seg: null, sens: null });
  const [aiLoading, setAiLoading] = useState({ dist: false, seg: false, sens: false });
  const [questionnaire, setQuestionnaire] = useState(null);
  const [questionnaireLoading, setQuestionnaireLoading] = useState(false);
  const inputTextRef = useRef("");

  const analyze = useCallback(async (text) => {
    const t = text || input;
    if (!t.trim()) return;
    inputTextRef.current = t;
    setAnalyzing(true);
    setAnalyzeError(null);
    setExperiment(null);
    setSimResults(null);
    setSensitivity(null);
    setAiInterps({ dist: null, seg: null, sens: null });
    setStep(0);
    setQuestionnaire(null);
    setQuestionnaireLoading(false);

    try {
      const result = await callLLM(DAG_SYSTEM, `Generate a causal DAG for this experiment:\n\n"${t}"\n\nRespond with ONLY the JSON object.`, "claude-sonnet-4-20250514");
      if (!result) throw new Error("Empty LLM response");
      const clean = result.replace(/```json\s*/g, "").replace(/```\s*/g, "").trim();
      const parsed = JSON.parse(clean);
      if (!parsed.nodes?.length || !parsed.edges?.length) throw new Error("Invalid DAG structure");
      // Validate & fix
      // Validate & fix
      const FIXED_MU    = [0.80, 0.65, 0.50, 0.30, 0.15];
      const FIXED_SIGMA = [0.10, 0.20, 0.40, 0.20, 0.10];
      for (const edge of parsed.edges) {
        if (!edge.options || edge.options.length !== 5) throw new Error(`Edge ${edge.id} needs 5 options`);
        if (typeof edge.default !== "number") edge.default = 2;
        if (typeof edge.direction !== "number") edge.direction = 1;
        // Ensure header exists (fallback to statement or question)
        if (!edge.header) edge.header = edge.statement || edge.question || `A respeito de ${edge.from} → ${edge.to}`;
        // Force fixed mu/sigma and ensure text field exists
        edge.options.forEach((opt, idx) => {
          opt.mu = FIXED_MU[idx];
          opt.sigma = FIXED_SIGMA[idx];
          // Ensure text field (fallback from label+desc)
          if (!opt.text && opt.label) opt.text = opt.desc ? `${opt.label} — ${opt.desc}` : opt.label;
        });
        if (!EXTRACTORS[edge.userVar]) {
          console.warn(`Unknown userVar "${edge.userVar}", falling back to incomeNorm`);
          edge.userVar = "incomeNorm";
        }
      }
      if (typeof parsed.interceptMu !== "number" || parsed.interceptMu < -1) parsed.interceptMu = 0.1;
      if (typeof parsed.interceptSigma !== "number") parsed.interceptSigma = 0.4;
      setExperiment(parsed);
      setSelections(parsed.edges.map(e => e.default));
      setStep(1);
    } catch (e) {
      console.error("Analyze failed:", e);
      setAnalyzeError(`Erro ao gerar modelo: ${e.message}. Tente reformular a descrição.`);
    } finally {
      setAnalyzing(false);
    }
  }, [input]);

  const handleSelection = useCallback((idx, opt) => {
    setSelections(prev => prev.map((s, i) => i === idx ? opt : s));
  }, []);

  const generateQuestionnaireFromData = useCallback(async (simRes, sens) => {
    if (!experiment) return;
    if (!simRes || !sens) return;
    setQuestionnaireLoading(true);
    setQuestionnaire(null);
    try {
      const st = computeStats(simRes.results);
      const sensEntries = Object.entries(sens);
      const sensRanked = sensEntries.sort(([, a], [, b]) => b.impact - a.impact);
      const top3 = sensRanked.slice(0, 3).map(([edgeId, s], i) => {
        const edgeIdx = experiment.edges.findIndex(e => e.id === edgeId);
        const edge = edgeIdx >= 0 ? experiment.edges[edgeIdx] : null;
        const currentOpt = edge && edgeIdx >= 0 ? edge.options[selections[edgeIdx]] : null;
        return `${i+1}. "${s.from} → ${s.to}" (impacto: ${(s.impact*100).toFixed(1)}pp)
   Afirmação: "${s.question}"
   Nível de concordância do PM: "${s.currentLabel}"
   ${currentOpt ? `Descrição: "${currentOpt.desc}"` : ""}`;
      }).join("\n\n");

      const context = `EXPERIMENT: "${inputTextRef.current}"

SIMULATION RESULT: Mean adoption ${(st.mean*100).toFixed(1)}%, 80% CI [${(st.p10*100).toFixed(1)}%–${(st.p90*100).toFixed(1)}%]

TOP 3 PREMISSES TO VALIDATE (ranked by sensitivity impact):

${top3}

IMPORTANT: The interviewer already has the respondent's demographic file (age, income, education, family, disabilities). Do NOT ask about demographics. Focus the 3 questions ONLY on validating these 3 causal relationships.

Generate the 3-question field questionnaire following Malhotra's methodology.`;

      const result = await callLLM(QUESTIONNAIRE_SYSTEM, context, "claude-sonnet-4-20250514");
      setQuestionnaire(result || "Erro ao gerar questionário.");
    } catch (e) {
      console.error("Questionnaire generation failed:", e);
      setQuestionnaire("Erro ao gerar questionário: " + e.message);
    } finally {
      setQuestionnaireLoading(false);
    }
  }, [experiment, selections]);

  const simulate = useCallback(() => {
    if (!experiment) return;
    setRunning(true);
    setStep(2);
    setAiInterps({ dist: null, seg: null, sens: null });
    setAiLoading({ dist: false, seg: false, sens: false });

    setTimeout(() => {
      const res = runSim(users, experiment, selections, 3000);
      const sens = runSensitivity(users, experiment, selections, 800);
      setSimResults(res);
      setSensitivity(sens);
      setRunning(false);
      setStep(3);

      // Fire 3 AI interpretation calls in parallel
      const stats = computeStats(res.results);
      const rawDist = rawDistInterpretation(stats);
      const rawSeg = rawSegInterpretation(res.segmentResults);
      const rawSens = rawSensInterpretation(sens);
      const expText = inputTextRef.current;

      // Build sensitivity summary for context
      const sensEntries = Object.values(sens).sort((a, b) => b.impact - a.impact);
      const sensSummary = sensEntries.map((s, i) => `${i+1}. "${s.from}→${s.to}": impacto ${(s.impact*100).toFixed(1)}pp (premissa atual: "${s.currentLabel}")`).join("\n");

      setAiLoading({ dist: true, seg: true, sens: true });

      const haikuModel = "claude-haiku-4-5-20241022";

      // Distribution interpretation — includes sensitivity context
      callLLM(INTERP_SYSTEM, `Experiment: "${expText}"\nSection: Distribuição\nRaw stats: ${rawDist}\n\nSensitivity ranking (premisses by impact):\n${sensSummary}`, haikuModel)
        .then(r => setAiInterps(prev => ({ ...prev, dist: r || rawDist })))
        .catch(() => setAiInterps(prev => ({ ...prev, dist: null })))
        .finally(() => setAiLoading(prev => ({ ...prev, dist: false })));

      // Segment interpretation
      callLLM(INTERP_SYSTEM, `Experiment: "${expText}"\nSection: Segmentos\nRaw stats: ${rawSeg}\n\nSensitivity ranking:\n${sensSummary}`, haikuModel)
        .then(r => setAiInterps(prev => ({ ...prev, seg: r || rawSeg })))
        .catch(() => setAiInterps(prev => ({ ...prev, seg: null })))
        .finally(() => setAiLoading(prev => ({ ...prev, seg: false })));

      // Sensitivity interpretation
      callLLM(INTERP_SYSTEM, `Experiment: "${expText}"\nSection: Sensibilidade\nRaw stats: ${rawSens}\n\nFull sensitivity data:\n${sensSummary}`, haikuModel)
        .then(r => setAiInterps(prev => ({ ...prev, sens: r || rawSens })))
        .catch(() => setAiInterps(prev => ({ ...prev, sens: null })))
        .finally(() => setAiLoading(prev => ({ ...prev, sens: false })));

      // Questionnaire NOT auto-fired — user clicks button
    }, 80);
  }, [users, experiment, selections]);

  const stats = useMemo(() => simResults ? computeStats(simResults.results) : null, [simResults]);
  const rawDist = useMemo(() => stats ? rawDistInterpretation(stats) : "", [stats]);
  const rawSeg = useMemo(() => simResults ? rawSegInterpretation(simResults.segmentResults) : "", [simResults]);
  const rawSens = useMemo(() => sensitivity ? rawSensInterpretation(sensitivity) : "", [sensitivity]);

  return (
    <div style={{ minHeight: "100vh", background: C.bg, color: C.tx, fontFamily: "'Inter', -apple-system, sans-serif", padding: "24px 16px" }}>
      <link href="https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Space+Grotesk:wght@400;600;700&family=Inter:wght@400;500;600&display=swap" rel="stylesheet" />
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>

      <div style={{ maxWidth: 660, margin: "0 auto" }}>
        {/* Header */}
        <div style={{ marginBottom: 28 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 4 }}>
            <div style={{ width: 8, height: 8, borderRadius: "50%", background: C.acc, boxShadow: `0 0 12px ${C.acc}66` }} />
            <h1 style={{ fontSize: 21, fontWeight: 700, color: C.txB, fontFamily: "'Space Grotesk', sans-serif", margin: 0 }}>Simulador de Experimentos</h1>
          </div>
          <p style={{ fontSize: 12, color: C.txM, fontFamily: "monospace", margin: 0 }}>
            DAG gerado por Opus · Monte Carlo causal · Interpretações por Haiku · {users.length.toLocaleString()} usuários sintéticos
          </p>
        </div>

        {/* Input */}
        <div style={{ marginBottom: 16 }}>
          <textarea value={input} onChange={e => setInput(e.target.value)}
            placeholder="Descreva o experimento que quer simular — pode ser qualquer feature, produto ou canal..."
            style={{ width: "100%", minHeight: 80, background: C.inner, border: `1px solid ${C.borderL}`, borderRadius: 10, padding: "12px 14px", color: C.txB, fontSize: 14, fontFamily: "Inter, sans-serif", resize: "vertical", outline: "none", boxSizing: "border-box" }}
            onFocus={e => e.target.style.borderColor = C.acc} onBlur={e => e.target.style.borderColor = C.borderL}
          />
          <button onClick={() => analyze()} disabled={!input.trim() || analyzing}
            style={{
              marginTop: 8, padding: "9px 24px", border: "none", borderRadius: 8, fontSize: 13, fontWeight: 600,
              fontFamily: "'Space Grotesk', sans-serif", cursor: input.trim() && !analyzing ? "pointer" : "default",
              background: input.trim() && !analyzing ? `linear-gradient(135deg, ${C.acc}, ${C.purple})` : C.border,
              color: input.trim() && !analyzing ? "#fff" : C.txM,
              display: "flex", alignItems: "center", gap: 8,
            }}>
            {analyzing && <div style={{ width: 14, height: 14, border: `2px solid rgba(255,255,255,0.3)`, borderTopColor: "#fff", borderRadius: "50%", animation: "spin 0.8s linear infinite" }} />}
            {analyzing ? "Opus está gerando o modelo causal..." : "▶ Analisar com AI"}
          </button>
          {analyzeError && <div style={{ marginTop: 8, padding: "8px 12px", background: `${C.red}15`, border: `1px solid ${C.red}33`, borderRadius: 6, fontSize: 12, color: C.red }}>{analyzeError}</div>}
        </div>

        {/* Examples */}
        <div style={{ marginBottom: 24 }}>
          <div style={{ fontSize: 10, color: C.txM, fontFamily: "monospace", marginBottom: 5 }}>EXEMPLOS:</div>
          <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            {EXAMPLES.map((ex, i) => (
              <button key={i} onClick={() => { setInput(ex); analyze(ex); }}
                disabled={analyzing}
                style={{ background: C.inner, border: `1px solid ${C.border}`, borderRadius: 6, padding: "7px 11px", color: C.txL, fontSize: 12, cursor: analyzing ? "default" : "pointer", textAlign: "left", fontFamily: "Inter, sans-serif", transition: "all 0.15s", opacity: analyzing ? 0.5 : 1 }}
                onMouseOver={e => { if (!analyzing) { e.currentTarget.style.borderColor = C.acc; e.currentTarget.style.color = C.tx; } }}
                onMouseOut={e => { e.currentTarget.style.borderColor = C.border; e.currentTarget.style.color = C.txL; }}
              >{ex}</button>
            ))}
          </div>
        </div>

        {/* Step 1: DAG + Likerts */}
        {experiment && step >= 1 && (
          <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 12, padding: 18, marginBottom: 14 }}>
            <SectionHeader number="1" color={C.acc} title="Suas Premissas"
              subtitle={`${experiment.label} · ${experiment.edges.length} afirmações causais · Gerado por Sonnet`} />

            <div style={{ background: C.inner, borderRadius: 8, padding: 10, border: `1px solid ${C.border}`, marginBottom: 14, overflow: "auto" }}>
              <div style={{ fontSize: 10, color: C.txM, fontFamily: "monospace", marginBottom: 4 }}>
                MODELO CAUSAL — espessura reage às suas respostas
              </div>
              <DAGView experiment={experiment} selections={selections} />
              <div style={{ fontSize: 9, color: C.txM, marginTop: 4, fontFamily: "monospace" }}>
                <span style={{ color: `${C.acc}88` }}>□</span> demográfico &nbsp;
                <span style={{ color: C.acc }}>—</span> relação direta &nbsp;
                <span style={{ color: C.orange }}>—</span> relação inversa &nbsp;
                <span style={{ color: C.orange }}>□</span> outcome &nbsp;
                Grossura = intensidade
              </div>
            </div>

            {experiment.edges.map((edge, i) => (
              <LikertInput key={edge.id} edge={edge} selectedIndex={selections[i]} onChange={opt => handleSelection(i, opt)} />
            ))}

            <button onClick={simulate} style={{
              marginTop: 8, padding: "10px 28px",
              background: `linear-gradient(135deg, ${C.orange}, #ff8f65)`,
              border: "none", borderRadius: 8, color: "#fff", fontSize: 13, fontWeight: 600,
              cursor: "pointer", fontFamily: "'Space Grotesk', sans-serif",
            }}>▶ Simular 3.000 Cenários</button>
          </div>
        )}

        {/* Loading sim */}
        {running && (
          <div style={{ textAlign: "center", padding: 36, color: C.acc, fontSize: 13, fontFamily: "monospace" }}>
            <div style={{ width: 28, height: 28, border: `3px solid ${C.border}`, borderTopColor: C.acc, borderRadius: "50%", margin: "0 auto 10px", animation: "spin 0.8s linear infinite" }} />
            Simulando cenários...
          </div>
        )}

        {/* Results */}
        {stats && step >= 3 && (
          <>
            {/* Distribution */}
            <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 12, padding: 18, marginBottom: 14 }}>
              <SectionHeader number="2" color={C.orange} title="Distribuição de Resultados" subtitle="Taxa de adoção em 3.000 cenários" />
              <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 8, marginBottom: 14 }}>
                {[
                  { l: "Média", v: `${(stats.mean * 100).toFixed(1)}%`, c: C.orange },
                  { l: "Mediana", v: `${(stats.median * 100).toFixed(1)}%`, c: C.acc },
                  { l: "IC 80%", v: `${(stats.p10 * 100).toFixed(1)}–${(stats.p90 * 100).toFixed(1)}%`, c: C.purple },
                  { l: "Desvio", v: `${(stats.std * 100).toFixed(2)}pp`, c: C.txL },
                ].map(s => (
                  <div key={s.l} style={{ background: C.inner, borderRadius: 8, padding: "9px 10px", textAlign: "center", border: `1px solid ${C.border}` }}>
                    <div style={{ fontSize: 10, color: C.txM, fontFamily: "monospace" }}>{s.l}</div>
                    <div style={{ fontSize: 17, fontWeight: 700, color: s.c, fontFamily: "'Space Grotesk'", marginTop: 2 }}>{s.v}</div>
                  </div>
                ))}
              </div>
              <div style={{ background: C.bg, borderRadius: 8, padding: 10, border: `1px solid ${C.border}` }}>
                <Histogram data={simResults.results} width={600} height={170} />
              </div>
              <Interpretation raw={rawDist} ai={aiInterps.dist} loading={aiLoading.dist} />
            </div>

            {/* Segments */}
            <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 12, padding: 18, marginBottom: 14 }}>
              <SectionHeader number="3" color={C.green} title="Adoção por Segmento" subtitle="Mesma simulação, recortada por atributos demográficos dos usuários sintéticos" />
              <SegmentBars segmentResults={simResults.segmentResults} />
              <Interpretation raw={rawSeg} ai={aiInterps.seg} loading={aiLoading.seg} />
            </div>

            {/* Sensitivity */}
            {sensitivity && (
              <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 12, padding: 18, marginBottom: 14 }}>
                <SectionHeader number="4" color={C.purple} title="O Que Mais Impacta o Resultado?" subtitle="Qual premissa vale investigar antes de decidir?" />
                <SensitivityChart sensitivity={sensitivity} />
                <Interpretation raw={rawSens} ai={aiInterps.sens} loading={aiLoading.sens} />
              </div>
            )}

            {/* Section 5: Field Questionnaire — auto-generated */}
            {sensitivity && (
              <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 12, padding: 18, marginBottom: 14 }}>
                <SectionHeader number="5" color="#E879F9" title="Questionário de Campo"
                  subtitle="3 perguntas para validar as premissas mais críticas — Malhotra cap. 9-10" />

                {questionnaireLoading && (
                  <div style={{ textAlign: "center", padding: 36, color: "#E879F9", fontSize: 13, fontFamily: "monospace" }}>
                    <div style={{ width: 28, height: 28, border: `3px solid ${C.border}`, borderTopColor: "#E879F9", borderRadius: "50%", margin: "0 auto 10px", animation: "spin 0.8s linear infinite" }} />
                    Sonnet está elaborando as 3 perguntas...
                    <div style={{ fontSize: 11, color: C.txM, marginTop: 6 }}>Baseado nas premissas de maior impacto da sensibilidade</div>
                  </div>
                )}

                {questionnaire && !questionnaireLoading && (
                  <div>
                    <div style={{
                      background: C.inner, border: `1px solid ${C.border}`, borderRadius: 8,
                      padding: "16px 20px", maxHeight: 600, overflowY: "auto",
                      fontSize: 13, color: C.tx, lineHeight: 1.7,
                    }}
                      dangerouslySetInnerHTML={{ __html: renderMarkdown(questionnaire) }}
                    />
                    <div style={{ marginTop: 12, display: "flex", gap: 8 }}>
                      <button onClick={() => {
                        navigator.clipboard?.writeText(questionnaire);
                      }} style={{
                        padding: "8px 20px", background: C.inner, border: `1px solid ${C.border}`,
                        borderRadius: 6, color: C.txL, fontSize: 12, cursor: "pointer",
                        fontFamily: "'Space Grotesk', sans-serif",
                      }}>
                        📋 Copiar Markdown
                      </button>
                      <button onClick={() => generateQuestionnaireFromData(simResults, sensitivity)} style={{
                        padding: "8px 20px", background: C.inner, border: `1px solid ${C.border}`,
                        borderRadius: 6, color: C.txL, fontSize: 12, cursor: "pointer",
                        fontFamily: "'Space Grotesk', sans-serif",
                      }}>
                        🔄 Regenerar
                      </button>
                    </div>
                  </div>
                )}

                {!questionnaire && !questionnaireLoading && (
                  <div style={{ textAlign: "center", padding: "20px 0" }}>
                    <div style={{ fontSize: 12, color: C.txM, marginBottom: 10 }}>
                      Gere um questionário de campo com 3 perguntas para validar as premissas mais críticas com usuários reais.
                    </div>
                    <button onClick={() => generateQuestionnaireFromData(simResults, sensitivity)} style={{
                      padding: "10px 28px",
                      background: `linear-gradient(135deg, #E879F9, #c054e0)`,
                      border: "none", borderRadius: 8, color: "#fff", fontSize: 13, fontWeight: 600,
                      cursor: "pointer", fontFamily: "'Space Grotesk', sans-serif",
                    }}>
                      📝 Gerar Questionário
                    </button>
                  </div>
                )}
              </div>
            )}

            {/* Methodology */}
            <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 12, padding: 18 }}>
              <SectionHeader number="?" color={C.txL} title="Metodologia" />
              <div style={{ fontSize: 12, color: C.txL, lineHeight: 1.7 }}>
                <p style={{ margin: "0 0 8px" }}><strong style={{ color: C.tx }}>Geração do modelo:</strong> Claude Opus gera o DAG causal com afirmações sobre relações entre variáveis. Cada aresta é uma afirmação que você avalia por concordância (Discordo forte → Concordo forte).</p>
                <p style={{ margin: "0 0 8px" }}><strong style={{ color: C.tx }}>Simulação:</strong> 3.000 iterações Monte Carlo × {users.length.toLocaleString()} usuários sintéticos (distribuição Beta(2,2)). Sua concordância define a força do acoplamento entre variáveis. Incerteza maior para respostas moderadas, menor para extremos. P(adoção) = σ(Σ βᵢ×xᵢ).</p>
                <p style={{ margin: "0 0 8px" }}><strong style={{ color: C.tx }}>Interpretações:</strong> Claude Haiku contextualiza os resultados estatísticos para o seu experimento específico. As 3 chamadas rodam em paralelo.</p>
                <p style={{ margin: "0 0 8px" }}><strong style={{ color: C.tx }}>Questionário:</strong> Claude Opus gera 3 perguntas focadas nas premissas de maior impacto (Malhotra cap. 9: escalas Likert, não-comparativa, intenção comportamental; cap. 10: abordagem funil, evitar viés). Entrevista mediada, sem perguntas demográficas.</p>
                <p style={{ margin: 0 }}><strong style={{ color: C.tx }}>Fundamentação:</strong> Malhotra — pesquisa causal por simulação, escalas de mensuração (cap. 9), design de questionário (cap. 10), amostragem (cap. 12). Pearl — inferência causal via DAGs.</p>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
