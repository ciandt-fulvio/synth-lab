/**
 * Waterfall Visualization
 *
 * Renders trace as horizontal waterfall chart with:
 * - Turns as expandable/collapsible rows
 * - Steps as horizontal bars scaled by duration
 * - Color coding by span type
 * - Click to select (future: detail panel)
 */

/**
 * Render complete waterfall from trace
 */
function renderWaterfall(trace) {
    const container = document.getElementById('waterfall-container');
    const section = document.getElementById('waterfall-section');

    // Clear existing content
    container.innerHTML = '';

    // Calculate max duration for scaling
    const maxDuration = calculateMaxDuration(trace);

    // Render each turn
    trace.turns.forEach((turn, index) => {
        const turnElement = renderTurn(turn, index, maxDuration);
        container.appendChild(turnElement);
    });

    // Show waterfall section
    section.classList.remove('hidden');
}

/**
 * Calculate maximum duration for scaling bars
 */
function calculateMaxDuration(trace) {
    let max = 0;

    for (const turn of trace.turns) {
        if (turn.duration_ms > max) {
            max = turn.duration_ms;
        }

        for (const step of turn.steps) {
            if (step.duration_ms > max) {
                max = step.duration_ms;
            }
        }
    }

    return max;
}

/**
 * Render a single turn
 */
function renderTurn(turn, index, maxDuration) {
    const turnContainer = document.createElement('div');
    turnContainer.className = 'turn-container';
    turnContainer.dataset.turnId = turn.turn_id;

    // Turn header (clickable to expand/collapse)
    const turnHeader = document.createElement('div');
    turnHeader.className = 'turn-header';
    turnHeader.innerHTML = `
        <span class="turn-toggle">▶</span>
        <span class="turn-label">Turn ${turn.turn_number}</span>
        <span class="turn-duration">${turn.duration_ms}ms</span>
        <span class="turn-steps">${turn.steps.length} steps</span>
    `;

    // Turn bar (duration visualization)
    const turnBar = document.createElement('div');
    turnBar.className = 'turn-bar';
    const turnWidth = (turn.duration_ms / maxDuration) * 100;
    turnBar.style.width = `${turnWidth}%`;

    // Steps container (initially collapsed)
    const stepsContainer = document.createElement('div');
    stepsContainer.className = 'steps-container collapsed';

    // Render each step
    turn.steps.forEach((step, stepIndex) => {
        const stepElement = renderStep(step, stepIndex, maxDuration);
        stepsContainer.appendChild(stepElement);
    });

    // Click to toggle expand/collapse
    turnHeader.addEventListener('click', () => {
        toggleTurn(turnContainer, stepsContainer);
    });

    // Assemble turn
    turnContainer.appendChild(turnHeader);
    turnContainer.appendChild(turnBar);
    turnContainer.appendChild(stepsContainer);

    return turnContainer;
}

/**
 * Render a single step
 */
function renderStep(step, index, maxDuration) {
    const stepContainer = document.createElement('div');
    stepContainer.className = 'step-container';

    // Step row (header + bar)
    const stepElement = document.createElement('div');
    stepElement.className = 'step-row';
    stepElement.dataset.spanId = step.span_id;

    // Step label
    const stepLabel = document.createElement('div');
    stepLabel.className = 'step-label';

    // Format step name based on type
    let stepName = formatStepName(step);
    stepLabel.innerHTML = `
        <span class="step-toggle">▶</span>
        <span class="step-index">${index + 1}.</span>
        <span class="step-name">${stepName}</span>
        <span class="step-duration">${step.duration_ms}ms</span>
    `;

    // Step bar (duration visualization with color coding)
    const stepBar = document.createElement('div');
    stepBar.className = `step-bar step-bar-${step.type}`;

    // Apply status styling
    if (step.status === 'error') {
        stepBar.classList.add('step-bar-error');
    }

    const stepWidth = (step.duration_ms / maxDuration) * 100;
    stepBar.style.width = `${stepWidth}%`;

    // Detail content container (initially collapsed)
    const detailContent = document.createElement('div');
    detailContent.className = 'step-detail-content collapsed';
    detailContent.style.display = 'none';

    // Click handler to toggle details
    stepElement.addEventListener('click', (e) => {
        e.stopPropagation();
        toggleStepDetails(stepContainer, stepElement, detailContent, step);
    });

    // Assemble step row
    stepElement.appendChild(stepLabel);
    stepElement.appendChild(stepBar);

    // Assemble step container
    stepContainer.appendChild(stepElement);
    stepContainer.appendChild(detailContent);

    return stepContainer;
}

/**
 * Format step name based on type and attributes
 */
function formatStepName(step) {
    switch (step.type) {
        case 'llm_call':
            return `🤖 LLM Call: ${step.attributes.model || 'unknown'}`;
        case 'tool_call':
            return `🔧 Tool: ${step.attributes.tool_name || 'unknown'}`;
        case 'logic':
            return `⚙️ Logic: ${step.attributes.operation || 'processing'}`;
        case 'error':
            return `❌ Error: ${step.attributes.error_type || 'unknown'}`;
        default:
            return `📍 ${step.type}`;
    }
}

/**
 * Toggle turn expansion
 */
function toggleTurn(turnContainer, stepsContainer) {
    const toggle = turnContainer.querySelector('.turn-toggle');
    const isExpanded = !stepsContainer.classList.contains('collapsed');

    if (isExpanded) {
        // Collapse
        stepsContainer.classList.add('collapsed');
        toggle.textContent = '▶';
    } else {
        // Expand
        stepsContainer.classList.remove('collapsed');
        toggle.textContent = '▼';
    }
}

/**
 * Toggle step details expansion
 */
function toggleStepDetails(stepContainer, stepElement, detailContent, step) {
    const toggle = stepElement.querySelector('.step-toggle');
    const isExpanded = detailContent.style.display !== 'none';

    if (isExpanded) {
        // Collapse
        detailContent.style.display = 'none';
        detailContent.classList.add('collapsed');
        toggle.textContent = '▶';
        stepElement.classList.remove('selected');
    } else {
        // Expand - close all other steps first
        document.querySelectorAll('.step-detail-content').forEach(el => {
            el.style.display = 'none';
            el.classList.add('collapsed');
        });
        document.querySelectorAll('.step-toggle').forEach(el => {
            el.textContent = '▶';
        });
        document.querySelectorAll('.step-row.selected').forEach(el => {
            el.classList.remove('selected');
        });

        // Open this step
        detailContent.style.display = 'block';
        detailContent.classList.remove('collapsed');
        toggle.textContent = '▼';
        stepElement.classList.add('selected');

        // Populate details
        if (typeof renderStepDetails === 'function') {
            renderStepDetails(detailContent, step);
        }
    }
}

/**
 * Select a step (for legacy compatibility)
 */
function selectStep(step) {
    // This is called from details.js but we'll use the new toggle system
    const stepElement = document.querySelector(`[data-span-id="${step.span_id}"]`);
    if (stepElement && stepElement.parentElement) {
        const stepRow = stepElement;
        const stepContainer = stepElement.parentElement;
        const detailContent = stepContainer.querySelector('.step-detail-content');
        if (detailContent) {
            toggleStepDetails(stepContainer, stepRow, detailContent, step);
        }
    }
}
