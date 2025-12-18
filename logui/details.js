/**
 * Detail Panel - Step inspection UI (Inline Collapsible)
 *
 * Handles:
 * - Rendering step details as inline collapsible content
 * - Rendering different step types (LLM calls, tool calls, errors, logic)
 * - Content truncation for long text (prompts, responses)
 */

// State
let currentStep = null;
let expandedSections = new Set();

/**
 * Render step details into a container (new inline system)
 */
function renderStepDetails(container, step) {
    currentStep = step;
    expandedSections.clear();
    container.innerHTML = '';

    // Create detail wrapper
    const detailWrapper = document.createElement('div');
    detailWrapper.className = 'step-detail-wrapper';

    // Render appropriate details based on step type
    const contentElement = document.createElement('div');
    contentElement.className = 'step-detail-body';

    switch (step.type) {
        case 'llm_call':
            renderLLMCallDetails(step.attributes, contentElement);
            break;
        case 'tool_call':
            renderToolCallDetails(step.attributes, contentElement);
            break;
        case 'error':
            renderErrorDetails(step.attributes, contentElement);
            break;
        case 'logic':
            renderLogicDetails(step.attributes, contentElement);
            break;
        default:
            renderGenericDetails(step, contentElement);
    }

    detailWrapper.appendChild(contentElement);
    container.appendChild(detailWrapper);
}

/**
 * Show detail panel with step information (legacy)
 */
function showDetails(step) {
    currentStep = step;
    expandedSections.clear();
    // New system uses renderStepDetails instead
    selectStep(step);
}

/**
 * Hide detail panel (legacy)
 */
function hideDetailPanel() {
    currentStep = null;
    expandedSections.clear();
    document.querySelectorAll('.step-detail-content').forEach(el => {
        el.style.display = 'none';
        el.classList.add('collapsed');
    });
}

/**
 * Format step title based on type
 */
function formatStepTitle(step) {
    const typeLabels = {
        'llm_call': '🤖 LLM Call',
        'tool_call': '🔧 Tool Call',
        'logic': '⚙️ Logic',
        'error': '❌ Error'
    };

    return typeLabels[step.type] || '📍 Step Details';
}

/**
 * Render LLM call details
 */
function renderLLMCallDetails(attributes, container) {
    const sections = [];

    // Model information
    if (attributes.model) {
        sections.push({
            label: 'Model',
            value: attributes.model,
            type: 'text'
        });
    }

    // Speaker
    if (attributes.speaker) {
        sections.push({
            label: 'Speaker',
            value: attributes.speaker,
            type: 'text'
        });
    }

    // Prompt
    if (attributes.prompt) {
        sections.push({
            label: 'Prompt',
            value: attributes.prompt,
            type: 'long-text',
            id: 'prompt'
        });
    }

    // Response
    if (attributes.response) {
        sections.push({
            label: 'Response',
            value: attributes.response,
            type: 'long-text',
            id: 'response'
        });
    }

    // Raw response
    if (attributes.raw_response) {
        sections.push({
            label: 'Raw Response',
            value: attributes.raw_response,
            type: 'long-text',
            id: 'raw_response'
        });
    }

    // Final response
    if (attributes.final_response) {
        sections.push({
            label: 'Final Response',
            value: attributes.final_response,
            type: 'long-text',
            id: 'final_response'
        });
    }

    // Token counts
    if (attributes.tokens_input !== undefined || attributes.tokens_output !== undefined) {
        const tokenInfo = [];
        if (attributes.tokens_input !== undefined) {
            tokenInfo.push(`Input: ${attributes.tokens_input}`);
        }
        if (attributes.tokens_output !== undefined) {
            tokenInfo.push(`Output: ${attributes.tokens_output}`);
        }
        sections.push({
            label: 'Tokens',
            value: tokenInfo.join(', '),
            type: 'text'
        });
    }

    renderDetailSections(sections, container);
}

/**
 * Render tool call details
 */
function renderToolCallDetails(attributes, container) {
    const sections = [];

    // Tool name
    if (attributes.tool_name) {
        sections.push({
            label: 'Tool',
            value: attributes.tool_name,
            type: 'text'
        });
    }

    // Arguments
    if (attributes.arguments) {
        sections.push({
            label: 'Arguments',
            value: JSON.stringify(attributes.arguments, null, 2),
            type: 'code',
            id: 'arguments'
        });
    }

    // Result
    if (attributes.result) {
        sections.push({
            label: 'Result',
            value: JSON.stringify(attributes.result, null, 2),
            type: 'code',
            id: 'result'
        });
    }

    // Error message if present
    if (attributes.error_message) {
        sections.push({
            label: 'Error',
            value: attributes.error_message,
            type: 'error-text',
            id: 'error'
        });
    }

    renderDetailSections(sections, container);
}

/**
 * Render error details
 */
function renderErrorDetails(attributes, container) {
    const sections = [];

    // Error type
    if (attributes.error_type) {
        sections.push({
            label: 'Error Type',
            value: attributes.error_type,
            type: 'error-text'
        });
    }

    // Error message
    if (attributes.error_message) {
        sections.push({
            label: 'Message',
            value: attributes.error_message,
            type: 'error-text',
            id: 'error-message'
        });
    }

    // Stack trace if available
    if (attributes.stack_trace) {
        sections.push({
            label: 'Stack Trace',
            value: attributes.stack_trace,
            type: 'code',
            id: 'stack-trace'
        });
    }

    renderDetailSections(sections, container);
}

/**
 * Render logic step details
 */
function renderLogicDetails(attributes, container) {
    console.log('[DEBUG] renderLogicDetails called with:', attributes);
    console.log('[DEBUG] Attribute keys:', Object.keys(attributes));

    const sections = [];

    // Operation first
    if (attributes.operation) {
        sections.push({
            label: 'Operation',
            value: attributes.operation,
            type: 'text'
        });
    }

    // Render ALL other attributes dynamically
    for (const [key, value] of Object.entries(attributes)) {
        // Skip operation (already rendered)
        if (key === 'operation') continue;

        console.log(`[DEBUG] Processing attribute: ${key}, type: ${typeof value}, length: ${typeof value === 'string' ? value.length : 'N/A'}`);

        const displayValue = typeof value === 'string'
            ? value
            : JSON.stringify(value, null, 2);

        // Format key for display (snake_case to Title Case)
        const label = key.split('_').map(word =>
            word.charAt(0).toUpperCase() + word.slice(1)
        ).join(' ');

        sections.push({
            label: label,
            value: displayValue,
            type: typeof value === 'string' && value.length > 100 ? 'long-text' : (typeof value === 'object' ? 'code' : 'text'),
            id: key
        });
    }

    console.log('[DEBUG] Total sections created:', sections.length, sections.map(s => s.label));
    renderDetailSections(sections, container);
}

/**
 * Render generic details for unknown types
 */
function renderGenericDetails(step, container) {
    const sections = [];

    // Add all attributes as key-value pairs
    for (const [key, value] of Object.entries(step.attributes || {})) {
        const displayValue = typeof value === 'string'
            ? value
            : JSON.stringify(value, null, 2);

        sections.push({
            label: key,
            value: displayValue,
            type: typeof value === 'string' ? 'text' : 'code',
            id: key
        });
    }

    renderDetailSections(sections, container);
}

/**
 * Render detail sections
 */
function renderDetailSections(sections, container) {
    // Use provided container or fall back to detailContent (for legacy compatibility)
    const target = container || (typeof detailContent !== 'undefined' ? detailContent : null);

    if (!target) {
        console.error('[ERROR] No container provided for renderDetailSections');
        return;
    }

    target.innerHTML = '';

    if (sections.length === 0) {
        const placeholder = document.createElement('p');
        placeholder.className = 'detail-placeholder';
        placeholder.textContent = 'No details available';
        target.appendChild(placeholder);
        return;
    }

    sections.forEach(section => {
        const sectionElement = document.createElement('div');
        sectionElement.className = 'detail-section';

        // Label
        const label = document.createElement('div');
        label.className = 'detail-label';
        label.textContent = section.label;
        sectionElement.appendChild(label);

        // Value (with truncation if needed)
        const valueContainer = document.createElement('div');
        valueContainer.className = `detail-value ${section.type || 'text'}`;

        if (section.type === 'long-text' || section.type === 'code') {
            const { element, needsTruncation } = truncateContent(section.value, 500, section.id);
            valueContainer.appendChild(element);
        } else {
            valueContainer.textContent = section.value;
        }

        sectionElement.appendChild(valueContainer);
        target.appendChild(sectionElement);
    });
}

/**
 * Truncate content with "Show More" toggle
 */
function truncateContent(text, maxLength = 500, contentId) {
    const needsTruncation = text.length > maxLength;
    const container = document.createElement('div');
    container.className = 'truncatable-content';

    if (!needsTruncation) {
        const content = document.createElement('div');
        content.className = 'content-text';
        content.textContent = text;
        container.appendChild(content);
        return { element: container, needsTruncation: false };
    }

    const isExpanded = expandedSections.has(contentId);
    const displayText = isExpanded ? text : text.substring(0, maxLength);

    const content = document.createElement('div');
    content.className = 'content-text';
    content.textContent = displayText;

    if (!isExpanded) {
        const ellipsis = document.createElement('span');
        ellipsis.className = 'ellipsis';
        ellipsis.textContent = '...';
        content.appendChild(ellipsis);
    }

    container.appendChild(content);

    // Toggle button
    const toggleButton = document.createElement('button');
    toggleButton.className = 'toggle-content';
    toggleButton.textContent = isExpanded ? 'Show Less' : 'Show More';
    toggleButton.addEventListener('click', () => {
        if (expandedSections.has(contentId)) {
            expandedSections.delete(contentId);
        } else {
            expandedSections.add(contentId);
        }
        showDetails(currentStep); // Re-render with new expansion state
    });

    container.appendChild(toggleButton);

    return { element: container, needsTruncation: true };
}

// No initialization needed for new inline system
