/**
 * Trace Renderer - JSON loading and parsing
 *
 * Handles:
 * - File upload via input or drag-and-drop
 * - JSON parsing and validation
 * - Error handling for invalid files
 * - UI state updates
 */

// Global state
let currentTrace = null;

// DOM Elements
const fileInput = document.getElementById('trace-file-input');
const dropZone = document.getElementById('drop-zone');
const fileStatus = document.getElementById('file-status');
const errorMessage = document.getElementById('error-message');
const errorText = document.getElementById('error-text');
const errorClose = document.getElementById('error-close');
const traceInfo = document.getElementById('trace-info');
const waterfallSection = document.getElementById('waterfall-section');
const exportButton = document.getElementById('export-trace');

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    fileInput.addEventListener('change', handleFileSelect);
    dropZone.addEventListener('dragover', handleDragOver);
    dropZone.addEventListener('dragleave', handleDragLeave);
    dropZone.addEventListener('drop', handleDrop);
    errorClose.addEventListener('click', hideError);
    exportButton.addEventListener('click', exportTrace);
});

/**
 * Handle file selection via input
 */
function handleFileSelect(event) {
    const file = event.target.files[0];
    if (file) {
        loadTraceFile(file);
    }
}

/**
 * Handle drag over event
 */
function handleDragOver(event) {
    event.preventDefault();
    event.stopPropagation();
    dropZone.classList.add('drag-over');
}

/**
 * Handle drag leave event
 */
function handleDragLeave(event) {
    event.preventDefault();
    event.stopPropagation();
    dropZone.classList.remove('drag-over');
}

/**
 * Handle file drop
 */
function handleDrop(event) {
    event.preventDefault();
    event.stopPropagation();
    dropZone.classList.remove('drag-over');

    const file = event.dataTransfer.files[0];
    if (file) {
        // Verify it's a JSON file
        if (!file.name.endsWith('.json') && !file.name.endsWith('.trace.json')) {
            showError('Arquivo inválido. Por favor, selecione um arquivo .json ou .trace.json');
            return;
        }

        loadTraceFile(file);
    }
}

/**
 * Load and parse trace file
 */
function loadTraceFile(file) {
    fileStatus.textContent = `Carregando ${file.name}...`;

    const reader = new FileReader();

    reader.onload = (event) => {
        try {
            const jsonText = event.target.result;
            const trace = parseJSON(jsonText);

            // Validate trace structure
            if (!validateTrace(trace)) {
                showError('Arquivo trace inválido: estrutura JSON não corresponde ao schema esperado');
                fileStatus.textContent = '';
                return;
            }

            // Store trace
            currentTrace = trace;

            // Update UI
            fileStatus.textContent = `✅ ${file.name} carregado`;
            displayTraceInfo(trace);
            renderWaterfall(trace);

        } catch (error) {
            showError(`Erro ao carregar trace: ${error.message}`);
            fileStatus.textContent = '';
        }
    };

    reader.onerror = () => {
        showError('Erro ao ler arquivo. Verifique as permissões.');
        fileStatus.textContent = '';
    };

    reader.readAsText(file);
}

/**
 * Parse JSON text
 */
function parseJSON(text) {
    try {
        return JSON.parse(text);
    } catch (error) {
        throw new Error(`JSON inválido: ${error.message}`);
    }
}

/**
 * Validate trace structure
 */
function validateTrace(trace) {
    // Check required fields
    if (!trace.trace_id || !trace.turns || !Array.isArray(trace.turns)) {
        return false;
    }

    // Check turns have required fields
    for (const turn of trace.turns) {
        if (!turn.turn_id || !turn.turn_number || !turn.steps || !Array.isArray(turn.steps)) {
            return false;
        }

        // Check steps have required fields
        for (const step of turn.steps) {
            if (!step.span_id || !step.type || !step.status) {
                return false;
            }
        }
    }

    return true;
}

/**
 * Display trace information
 */
function displayTraceInfo(trace) {
    // Calculate total steps
    const totalSteps = trace.turns.reduce((sum, turn) => sum + turn.steps.length, 0);

    // Update info panel
    document.getElementById('info-trace-id').textContent = trace.trace_id;
    document.getElementById('info-duration').textContent = `${trace.duration_ms}ms`;
    document.getElementById('info-turns').textContent = trace.turns.length;
    document.getElementById('info-steps').textContent = totalSteps;

    // Show info panel and export button
    traceInfo.classList.remove('hidden');
    exportButton.classList.remove('hidden');
}

/**
 * Show error message
 */
function showError(message) {
    errorText.textContent = message;
    errorMessage.classList.remove('hidden');
}

/**
 * Hide error message
 */
function hideError() {
    errorMessage.classList.add('hidden');
}

/**
 * Get current trace
 */
function getCurrentTrace() {
    return currentTrace;
}

/**
 * Export trace as .trace.json file
 */
function exportTrace() {
    if (!currentTrace) {
        showError('Nenhum trace carregado para exportar');
        return;
    }

    // Generate filename with trace ID and timestamp
    const filename = generateTraceFilename(currentTrace);

    // Convert trace to JSON
    const jsonString = JSON.stringify(currentTrace, null, 2);

    // Create Blob
    const blob = new Blob([jsonString], { type: 'application/json' });

    // Create download link
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;

    // Trigger download
    document.body.appendChild(link);
    link.click();

    // Cleanup
    document.body.removeChild(link);
    URL.revokeObjectURL(url);

    fileStatus.textContent = `✅ ${filename} exportado`;
    setTimeout(() => {
        fileStatus.textContent = '';
    }, 3000);
}

/**
 * Generate filename for trace export
 */
function generateTraceFilename(trace) {
    // Use trace_id as base
    const baseId = trace.trace_id || 'trace';

    // Add timestamp
    const now = new Date();
    const timestamp = now.toISOString()
        .replace(/[:.]/g, '-')
        .replace('T', '_')
        .substring(0, 19);

    return `${baseId}_${timestamp}.trace.json`;
}
