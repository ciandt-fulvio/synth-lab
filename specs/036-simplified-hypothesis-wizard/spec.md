# Feature Specification: Simplified Hypothesis Selection Wizard

**Feature Branch**: `036-simplified-hypothesis-wizard`
**Created**: 2026-01-28
**Status**: Draft
**Input**: User description: "Vamos simplificar o process de escolha de hipoteses, pra facilitar o uso. Depois do DAG, o sistema mostra cenários (Conservador/Realista/Otimista). Após escolha do cenário, LLM cria hipóteses levando em conta o cenário. LLM analisa incertezas críticas e pergunta só o essencial (max 3-5 perguntas). Sistema mapeia respostas subjetivas (mais/menos/igual/não sei) para ajustes internos. 4 LLMs: entende pergunta, constrói DAG, escolhe variáveis críticas, explica resultado."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Select General Scenario Profile (Priority: P1)

After the causal DAG is created and validated, users need to quickly set the overall tone for their simulation without dealing with statistical parameters. They should be able to choose from three predefined scenario profiles (Conservative, Realistic, Optimistic) that automatically configure distribution types and parameters for all variables in the DAG.

**Why this priority**: This is the foundation of the simplified workflow. Without this, users must manually configure each hypothesis, which is complex and time-consuming. This single choice provides immediate value by generating a complete set of hypotheses that can be used for simulation.

**Independent Test**: Can be fully tested by creating a DAG, selecting a scenario profile, and verifying that all variables receive appropriate distribution configurations matching the selected profile. Delivers a complete, runnable simulation without any additional user input.

**Acceptance Scenarios**:

1. **Given** a validated causal DAG exists, **When** the user views the scenario selection screen, **Then** three options are presented: Conservative, Realistic, and Optimistic, each with a clear description of what it represents
2. **Given** the user selects "Conservative" scenario, **When** the system generates hypotheses, **Then** all variables receive conservative distribution parameters (e.g., lower means, higher variance for uncertainties)
3. **Given** the user selects "Realistic" scenario, **When** the system generates hypotheses, **Then** all variables receive market-average distribution parameters
4. **Given** the user selects "Optimistic" scenario, **When** the system generates hypotheses, **Then** all variables receive optimistic distribution parameters (e.g., higher means, lower variance)
5. **Given** a scenario profile is selected, **When** hypotheses are generated, **Then** distribution_type, distrib_params, range_min, and range_max are automatically determined for each variable based on the profile

---

### User Story 2 - Answer Targeted Clarification Questions (Priority: P2)

After selecting a general scenario profile, users may still have high uncertainty in a few critical variables. The system should identify 3-5 critical variables with the highest uncertainty and ask simple, qualitative questions to refine the distributions. Users answer in plain language (more/less/equal/don't know) rather than providing statistical parameters.

**Why this priority**: This adds precision to the most impactful variables without overwhelming the user. The P1 story already provides a working simulation, and this story enhances accuracy where it matters most. It's independent because it operates on the hypotheses created in P1.

**Independent Test**: Can be tested by selecting a scenario profile, receiving clarification questions, answering them with qualitative responses, and verifying that the affected variables' distributions are adjusted accordingly. Delivers improved simulation accuracy for critical variables.

**Acceptance Scenarios**:

1. **Given** a scenario profile has been selected and initial hypotheses generated, **When** the system analyzes variable uncertainty, **Then** 3-5 critical variables with highest uncertainty are identified
2. **Given** critical variables are identified for a simple decision context, **When** clarification questions are generated, **Then** no more than 3 questions are asked
3. **Given** critical variables are identified for a complex decision context, **When** clarification questions are generated, **Then** no more than 5 questions are asked
4. **Given** a clarification question is presented, **When** the user sees the question, **Then** it is phrased in plain language asking about relative frequency or magnitude (e.g., "Is logistic failure more common or rare in your context?")
5. **Given** a clarification question is presented, **When** the user responds, **Then** four response options are available: "more", "less", "equal", "don't know"
6. **Given** the user selects "more" for a variable, **When** distributions are updated, **Then** the system adjusts distribution parameters to reflect higher frequency/magnitude (e.g., increase mean or shift distribution)
7. **Given** the user selects "less" for a variable, **When** distributions are updated, **Then** the system adjusts distribution parameters to reflect lower frequency/magnitude
8. **Given** the user selects "equal" for a variable, **When** distributions are updated, **Then** the distribution remains at the scenario profile default
9. **Given** the user selects "don't know" for a variable, **When** distributions are updated, **Then** the system increases variance to reflect higher uncertainty while keeping the mean at the scenario profile default
10. **Given** the user has answered all clarification questions (or skipped them), **When** final hypotheses are generated, **Then** all variables have complete distribution configurations ready for simulation

---

### User Story 3 - Proceed with Simulation Despite Uncertainty (Priority: P3)

Users should be able to run simulations even when they haven't answered all clarification questions or when some uncertainty remains. The system should explicitly communicate which variables have high uncertainty and still produce simulation results with appropriate confidence indicators.

**Why this priority**: This ensures the system is always usable, even with incomplete information. Users can get directional insights quickly and refine later. It's lower priority because P1 and P2 already provide a complete, runnable simulation.

**Independent Test**: Can be tested by skipping clarification questions and running a simulation, verifying that results are produced with clear uncertainty indicators. Delivers immediate value even with incomplete data.

**Acceptance Scenarios**:

1. **Given** clarification questions are presented, **When** the user chooses to skip them, **Then** the system proceeds with simulation using scenario profile defaults for those variables
2. **Given** a simulation is run with unanswered clarification questions, **When** results are displayed, **Then** the system clearly indicates which variables had high uncertainty
3. **Given** a simulation is run with unanswered clarification questions, **When** results are displayed, **Then** confidence intervals or uncertainty ranges reflect the higher uncertainty in those variables
4. **Given** the question limit is reached (3 for simple, 5 for complex), **When** additional uncertainties remain, **Then** the system proceeds with simulation and documents remaining uncertainties in the results

---

### Edge Cases

- What happens when the DAG has no variables with significant uncertainty? (System skips clarification questions and proceeds directly to simulation)
- What happens when a user changes their scenario profile after answering clarification questions? (System regenerates all hypotheses from scratch, discarding previous clarification answers)
- What happens when the system cannot classify a decision as "simple" or "complex"? (Default to 5 questions - the more permissive limit)
- What happens when LLM fails to generate appropriate distributions for a scenario profile? (System logs error, falls back to Realistic profile defaults, and notifies user)
- What happens when a user provides conflicting answers to clarification questions? (System uses most recent answer and adjusts distributions accordingly)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST present three scenario profile options after DAG validation: Conservative, Realistic, and Optimistic
- **FR-002**: System MUST display clear descriptions for each scenario profile explaining what it represents in plain language
- **FR-003**: System MUST generate complete hypothesis configurations (distribution_type, distrib_params, range_min, range_max) for all DAG variables based on selected scenario profile
- **FR-004**: System MUST use LLM to analyze the selected scenario profile and determine appropriate distribution parameters for each variable type
- **FR-005**: System MUST identify 3-5 critical variables with highest impact and uncertainty after scenario profile selection
- **FR-006**: System MUST classify the decision context as "simple" or "complex" to determine question limit (3 or 5 questions)
- **FR-007**: System MUST generate clarification questions in plain language asking about relative frequency or magnitude of critical variables
- **FR-008**: System MUST provide exactly four response options for each clarification question: "more", "less", "equal", "don't know"
- **FR-009**: System MUST adjust distribution parameters based on qualitative responses (more/less/equal/don't know)
- **FR-010**: System MUST enforce question limit: maximum 3 questions for simple decisions, maximum 5 questions for complex decisions
- **FR-011**: System MUST allow users to skip clarification questions and proceed with scenario profile defaults
- **FR-012**: System MUST produce simulation results even when clarification questions are skipped or unanswered
- **FR-013**: System MUST document which variables had high uncertainty in simulation results
- **FR-014**: System MUST use four distinct LLM roles: (1) understand user question, (2) construct DAG, (3) identify critical variables and generate clarification questions, (4) explain simulation results
- **FR-015**: System MUST apply clamps (range_min/range_max) when necessary to ensure distributions remain within realistic bounds
- **FR-016**: System MUST increase distribution variance for variables marked as "don't know" to reflect higher uncertainty
- **FR-017**: System MUST regenerate all hypotheses from scratch if user changes scenario profile after answering clarification questions

### Key Entities

- **Scenario Profile**: Represents a predefined set of distribution parameter strategies (Conservative, Realistic, Optimistic). Contains mapping rules for how to configure distributions for different variable types.
- **Clarification Question**: A plain-language question about a critical variable's frequency or magnitude. Contains the variable reference, question text, and mapping logic for qualitative responses to distribution adjustments.
- **Hypothesis Configuration**: Complete statistical specification for a DAG variable. Includes distribution_type, distrib_params, range_min, range_max, and metadata about how it was configured (scenario profile, clarification responses).
- **Variable Uncertainty**: Measure of how critical and uncertain a variable is. Used to prioritize which variables need clarification questions. Contains uncertainty score, impact score, and combined criticality ranking.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can complete hypothesis configuration for a 10-variable DAG in under 3 minutes (from scenario selection to ready-to-simulate state)
- **SC-002**: 90% of users successfully generate simulation-ready hypotheses using only scenario profile selection (no clarification questions needed)
- **SC-003**: No more than 5 clarification questions are presented to any user, regardless of DAG complexity
- **SC-004**: Users receive simulation results within 10 seconds of completing hypothesis configuration
- **SC-005**: 100% of generated hypotheses have valid distribution configurations (no missing or invalid parameters)
- **SC-006**: System reduces hypothesis configuration time by at least 70% compared to manual parameter specification
- **SC-007**: Users can understand and answer clarification questions without statistical or technical knowledge (measured by task completion rate)
- **SC-008**: Simulation results clearly communicate uncertainty levels for variables with unanswered clarification questions (measured by user comprehension in testing)

## Assumptions

- Users understand the qualitative meaning of "Conservative", "Realistic", and "Optimistic" in the context of their business scenario
- LLM can reliably classify decision contexts as "simple" or "complex" based on DAG structure and variable types
- Market-average distribution parameters exist or can be inferred for common business variables (conversion rates, failure rates, time delays, etc.)
- Qualitative responses ("more", "less", "equal", "don't know") can be consistently mapped to quantitative distribution adjustments using predefined rules or LLM interpretation
- Users prefer quick, approximate hypothesis generation over precise, time-consuming manual configuration
- 3-5 clarification questions are sufficient to significantly improve simulation accuracy for critical variables
- The four LLM roles (understand, construct, clarify, explain) can operate sequentially with outputs from one feeding into the next
- Users can make relative judgments ("more common or rare") more easily than absolute judgments ("happens 5% of the time")

## Dependencies

- Existing causal DAG construction feature must be functional
- DAG validation feature must confirm DAG is ready for hypothesis generation
- Variable metadata must include enough context for LLM to determine appropriate distribution types
- Simulation engine must accept distribution configurations in the format generated by this feature
- Tracing/observability infrastructure (Arize Phoenix) must be available for monitoring LLM calls
- LLM service (OpenAI) must be accessible and responsive for four sequential LLM operations

## Out of Scope

- Manual distribution parameter editing (users who need precise control should use advanced mode, if available)
- Importing distribution parameters from external data sources
- Collaborative hypothesis configuration (multiple users working on same scenario)
- Version history or comparison of different scenario profiles
- Custom scenario profiles beyond the three predefined options
- Sensitivity analysis showing how clarification responses impact results
- Learning from user behavior to improve default scenario profiles over time
- Integration with external data sources to auto-populate realistic distributions
