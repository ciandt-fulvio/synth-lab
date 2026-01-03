# Feature Specification: Exploration Summary and PRFAQ Generation

**Feature Branch**: `028-exploration-summary`
**Created**: 2026-01-02
**Status**: Draft
**Input**: User description: "quero criar um summary e um PRFAQ que funcionarão de maneira analoga ao que rola hoje nas entrevistas:

- deve comecar com os botões de gerar na tela, desabilitados
- assim que uma explocarao terminar (por atingimento de meta ou pq chegou em algum limite -- ou seja, por qq motivo menos termino por erros), deve ser iniciaada a criacao de um summary
- o summary deve usar uma LLM para contar a história que deu melhor resultado em uma explocacao. Na imagem em anexo, é a história que passa por 'tutorial interativo, tooltip de seguranca, mensagem de erros clarar a valor default inteligente' (ou seja, é o caminho que leva do nó até a folha que teve o melhor reultado. por enquanto vamos olhar só pra uma caminho, no futuro poderemos expandir para outros caminhos de resultados tbm altos.
- dentro de cada nós é possível ver a acao aplicada e a justificativa, o quero é um bom prompt que conte essa história. Veja que o prompt não precisa falar comeca assim, depois assado, etc. basta ele pegar o cenário original do problema, todas as acoes, as justificativas e montar como ficaria o experimento após tudo que foi explorado nesse caminho"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - View Generated Summary After Exploration Completes (Priority: P1)

A researcher completes an exploration session (either by achieving the goal or hitting depth/cost limits) and wants to understand the best performing path discovered by the system. The system automatically generates a narrative summary that tells the story of the winning path from root to best leaf node.

**Why this priority**: This is the core value proposition - converting tree exploration data into actionable insights. Without this, users cannot easily understand what the exploration discovered.

**Independent Test**: Can be fully tested by running an exploration to completion and verifying that a narrative summary is automatically generated describing the winning path's actions and rationale.

**Acceptance Scenarios**:

1. **Given** an exploration has completed with status=GOAL_ACHIEVED, **When** the user views the exploration details, **Then** a "Generate Summary" button is visible and enabled
2. **Given** an exploration has completed with status=DEPTH_LIMIT_REACHED, **When** the system identifies the best performing leaf node, **Then** it automatically initiates summary generation
3. **Given** an exploration has completed with status=COST_LIMIT_REACHED, **When** the system finds the path with highest success rate, **Then** it generates a narrative describing all actions and rationales along that path
4. **Given** an exploration has status=RUNNING, **When** the user views the exploration details, **Then** the "Generate Summary" button is disabled
5. **Given** an exploration has status=NO_VIABLE_PATHS, **When** the user views the exploration details, **Then** the "Generate Summary" button remains disabled (no valid path to summarize)

---

### User Story 2 - View Generated PRFAQ After Exploration Completes (Priority: P2)

A researcher wants a structured Press Release/FAQ document that formalizes the winning path's recommendations in a business-friendly format, similar to how interview guides are generated for experiments.

**Why this priority**: Builds on the summary (P1) to provide a more formal deliverable. Users need the summary first to understand the path, then the PRFAQ to communicate findings to stakeholders.

**Independent Test**: Can be fully tested by triggering PRFAQ generation on a completed exploration and verifying the output follows the PRFAQ structure with sections for press release, FAQ, and recommendations.

**Acceptance Scenarios**:

1. **Given** an exploration has completed successfully, **When** the user clicks "Generate PRFAQ", **Then** the system creates a structured document with press release section describing the winning path
2. **Given** an exploration summary has been generated, **When** PRFAQ generation runs, **Then** it includes FAQ section addressing common questions about the proposed changes
3. **Given** a completed exploration with best path identified, **When** PRFAQ is generated, **Then** it includes recommendations section listing all actions from the winning path

---

### User Story 3 - Manual Summary Regeneration (Priority: P3)

A researcher who has already generated a summary wants to regenerate it (perhaps after understanding more context or if generation failed previously).

**Why this priority**: Nice-to-have for error recovery and iteration, but not essential for the core value. Initial generation (P1) must work first.

**Independent Test**: Can be fully tested by clicking "Generate Summary" button multiple times and verifying each generation creates a new summary artifact.

**Acceptance Scenarios**:

1. **Given** a summary already exists for an exploration, **When** the user clicks "Generate Summary" again, **Then** a new summary is generated and replaces the previous one
2. **Given** a previous summary generation failed, **When** the user clicks "Generate Summary", **Then** the system retries generation using the same winning path

---

### Edge Cases

- What happens when an exploration has multiple paths with identical success rates (tie for best path)?
  - System should select the path with lowest depth (shortest path to success)
  - If still tied, select the path created first (earlier timestamp)

- How does the system handle explorations that terminate due to errors (not completed successfully)?
  - "Generate Summary" button remains disabled
  - User sees message: "Summary not available - exploration did not complete successfully"

- What if the winning path has no action nodes (root node is the best)?
  - Summary should describe the baseline scenario only
  - Indicate that no improvements were found that outperformed the baseline

- How should the system handle very long paths (e.g., depth = 10)?
  - LLM prompt should handle up to max_depth (currently 10) nodes
  - Summary should remain concise while covering all actions

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST enable "Generate Summary" and "Generate PRFAQ" buttons only when exploration has completed (status is GOAL_ACHIEVED, DEPTH_LIMIT_REACHED, or COST_LIMIT_REACHED)
- **FR-002**: System MUST keep "Generate Summary" and "Generate PRFAQ" buttons disabled when exploration status is RUNNING or NO_VIABLE_PATHS
- **FR-003**: System MUST automatically identify the winning path (root to best leaf node) by finding the leaf node with highest success_rate
- **FR-004**: System MUST retrieve all nodes along the winning path from root to best leaf, preserving order
- **FR-005**: System MUST extract from each node: action_applied, rationale, action_category, and scorecard impacts
- **FR-006**: System MUST construct an LLM prompt that includes:
  - Original experiment scenario description
  - All actions applied along the winning path (in order)
  - Rationale for each action
  - Final scorecard parameters
  - Final success rate achieved
- **FR-007**: System MUST use LLM to generate a narrative summary that describes the winning path as a coherent story
- **FR-008**: Summary MUST NOT be a sequential "first do X, then do Y" format - instead it should describe the final state after all actions are applied
- **FR-009**: System MUST persist generated summary content linked to the exploration_id
- **FR-010**: System MUST persist generated PRFAQ content linked to the exploration_id
- **FR-011**: Users MUST be able to regenerate summary/PRFAQ, which overwrites previous version
- **FR-012**: System MUST display generation errors to users if LLM call fails
- **FR-013**: Summary generation MUST complete within reasonable time (target: 30 seconds for typical paths with 5 nodes)

### Key Entities

- **ExplorationSummary**: Represents the generated narrative summary
  - exploration_id: Reference to parent exploration
  - winning_path_nodes: List of node IDs from root to best leaf
  - summary_content: Generated narrative text from LLM
  - generated_at: Timestamp of generation
  - generation_status: Status (generating, completed, failed)

- **ExplorationPRFAQ**: Represents the generated PRFAQ document
  - exploration_id: Reference to parent exploration
  - winning_path_nodes: List of node IDs from root to best leaf
  - prfaq_content: Generated PRFAQ text from LLM
  - generated_at: Timestamp of generation
  - generation_status: Status (generating, completed, failed)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can generate a summary for any completed exploration in under 30 seconds
- **SC-002**: Generated summaries accurately describe all actions and rationales from the winning path
- **SC-003**: 95% of summary generations complete successfully without errors
- **SC-004**: Users can regenerate summaries multiple times for the same exploration
- **SC-005**: Generate buttons are correctly enabled/disabled based on exploration status in 100% of cases
- **SC-006**: Generated PRFAQ documents follow the structured format (press release + FAQ + recommendations sections)
