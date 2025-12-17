/**
 * Detail Panel - Step inspection UI
 *
 * Handles:
 * - Click events on steps to show details
 * - Rendering different step types (LLM calls, tool calls, errors, logic)
 * - Content truncation for long text (prompts, responses)
 * - Panel open/close state
 */

// DOM Elements
const detailPanel = document.getElementById('detail-panel');
const detailTitle = document.getElementById('detail-title');
const detailContent = document.getElementById('detail-content');
const detailClose = document.getElementById('detail-close');

// State
let currentStep = null;
let expandedSections = new Set();

/**
 * Initialize detail panel event listeners
 */
function initializeDetailPanel() {
    detailClose.addEventListener('click', hideDetailPanel);
}

/**
 * Show detail panel with step information
 */
function showDetails(step) {
    currentStep = step;
    expandedSections.clear();

    // Update title based on step type
    detailTitle.textContent = formatStepTitle(step);

    // Render appropriate details based on step type
    switch (step.type) {
        case 'llm_call':
            renderLLMCallDetails(step.attributes);
            break;
        case 'tool_call':
            renderToolCallDetails(step.attributes);
            break;
        case 'error':
            renderErrorDetails(step.attributes);
            break;
        case 'logic':
            renderLogicDetails(step.attributes);
            break;
        default:
            renderGenericDetails(step);
    }

    // Show panel
    detailPanel.classList.remove('hidden');
}

/**
 * Hide detail panel
 */
function hideDetailPanel() {
    detailPanel.classList.add('hidden');
    currentStep = null;
    expandedSections.clear();
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
function renderLLMCallDetails(attributes) {
    const sections = [];

    // Model information
    if (attributes.model) {
        sections.push({
            label: 'Model',
            value: attributes.model,
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

    renderDetailSections(sections);
}

/**
 * Render tool call details
 */
function renderToolCallDetails(attributes) {
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

    renderDetailSections(sections);
}

/**
 * Render error details
 */
function renderErrorDetails(attributes) {
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

    renderDetailSections(sections);
}

/**
 * Render logic step details
 */
function renderLogicDetails(attributes) {
    const sections = [];

    // Operation
    if (attributes.operation) {
        sections.push({
            label: 'Operation',
            value: attributes.operation,
            type: 'text'
        });
    }

    // Input
    if (attributes.input !== undefined) {
        const inputValue = typeof attributes.input === 'string'
            ? attributes.input
            : JSON.stringify(attributes.input, null, 2);

        sections.push({
            label: 'Input',
            value: inputValue,
            type: typeof attributes.input === 'string' ? 'long-text' : 'code',
            id: 'input'
        });
    }

    // Output
    if (attributes.output !== undefined) {
        const outputValue = typeof attributes.output === 'string'
            ? attributes.output
            : JSON.stringify(attributes.output, null, 2);

        sections.push({
            label: 'Output',
            value: outputValue,
            type: typeof attributes.output === 'string' ? 'long-text' : 'code',
            id: 'output'
        });
    }

    renderDetailSections(sections);
}

/**
 * Render generic details for unknown types
 */
function renderGenericDetails(step) {
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

    renderDetailSections(sections);
}

/**
 * Render detail sections
 */
function renderDetailSections(sections) {
    detailContent.innerHTML = '';

    if (sections.length === 0) {
        detailContent.innerHTML = '<p class="detail-placeholder">No details available</p>';
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
        detailContent.appendChild(sectionElement);
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

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    initializeDetailPanel();
});
