# Component Interface Contract: PDF Download

**Feature**: 027-pdf-download
**Type**: Frontend Component Interface
**Date**: 2026-01-01

## Overview

This document defines the interface contract for the PDF download feature. Since this is a client-side only feature with no API endpoints, the contract describes the component's public interface and utility function signatures.

## Component Props Contract

No changes to existing DocumentViewer component props. The component maintains backward compatibility.

### DocumentViewerProps (Unchanged)

```typescript
interface DocumentViewerProps {
  /** Whether the dialog is open */
  isOpen: boolean;

  /** Callback when dialog is closed */
  onClose: () => void;

  /** Document type for title and icon */
  documentType: DocumentType;

  /** Markdown content to display */
  markdownContent?: string;

  /** Whether content is loading */
  isLoading?: boolean;

  /** Current document status */
  status?: DocumentStatus;

  /** Error message if failed */
  errorMessage?: string;

  /** Optional custom title suffix */
  titleSuffix?: string;
}
```

**Constraints**:
- All existing prop contracts remain unchanged
- Component remains compatible with all current call sites
- No breaking changes to props interface

## Utility Function Contracts

### sanitizeFilename

Converts a string into a safe, cross-platform filename.

```typescript
/**
 * Sanitizes a string to create a valid, cross-platform filename.
 *
 * @param text - The text to sanitize (typically titleSuffix)
 * @returns A sanitized filename string (lowercase, alphanumeric + hyphens/underscores only)
 *
 * @example
 * sanitizeFilename("Pix via WhatsApp") // → "pix-via-whatsapp"
 * sanitizeFilename("Test@Feature#123") // → "testfeature123"
 * sanitizeFilename(undefined) // → "document"
 * sanitizeFilename("") // → "document"
 */
export function sanitizeFilename(text: string | undefined): string;
```

**Contract**:
- Input: `string | undefined`
- Output: `string` (always returns a valid filename, never empty string)
- Side effects: None (pure function)
- Performance: O(n) where n is input length

**Behavior**:
1. If input is `undefined` or empty after sanitization → return `"document"`
2. Convert to lowercase
3. Replace spaces with hyphens
4. Remove all non-alphanumeric characters except hyphens and underscores
5. Collapse multiple consecutive hyphens into one
6. Remove leading/trailing hyphens
7. Truncate to 50 characters maximum
8. If result is empty → return `"document"`

### generatePdfFilename

Generates a standardized PDF filename from document type and title suffix.

```typescript
/**
 * Generates a standardized PDF filename.
 *
 * @param documentType - The type of document ('prfaq' | 'executive_summary' | 'summary')
 * @param titleSuffix - Optional custom title suffix
 * @returns A filename in format: {documentType}_{sanitized_title}.pdf
 *
 * @example
 * generatePdfFilename('prfaq', 'Pix via WhatsApp') // → "prfaq_pix-via-whatsapp.pdf"
 * generatePdfFilename('summary', undefined) // → "summary_document.pdf"
 */
export function generatePdfFilename(
  documentType: DocumentType,
  titleSuffix?: string
): string;
```

**Contract**:
- Input: `DocumentType`, `string | undefined`
- Output: `string` (always ends with `.pdf`)
- Side effects: None (pure function)
- Performance: O(n) where n is titleSuffix length

**Format**: `{documentType}_{sanitized_suffix}.pdf`

### generatePdfFromElement

Generates a PDF file from a DOM element and triggers download.

```typescript
/**
 * Generates a PDF file from a DOM element and triggers browser download.
 *
 * @param element - The HTML element to capture (typically the markdown content container)
 * @param filename - The filename for the downloaded PDF
 * @returns Promise that resolves when PDF is generated and download initiated
 * @throws Error if element is null, canvas generation fails, or PDF creation fails
 *
 * @example
 * await generatePdfFromElement(contentRef.current, "prfaq_example.pdf");
 */
export async function generatePdfFromElement(
  element: HTMLElement,
  filename: string
): Promise<void>;
```

**Contract**:
- Input: `HTMLElement`, `string`
- Output: `Promise<void>` (async operation)
- Side effects: Triggers browser file download
- Performance: 1-5 seconds depending on content size
- Errors: Throws `Error` with user-friendly message on failure

**Behavior**:
1. Validate element is not null (throw if null)
2. Call `html2canvas(element, { scale: 2, ... })`
3. Convert canvas to PNG data URL
4. Create jsPDF instance (A4, portrait)
5. Calculate dimensions to fit A4 width
6. Add image to PDF
7. Trigger download via `pdf.save(filename)`
8. On error: throw with message suitable for user display

## Internal State Contract

These are implementation details but documented for clarity:

```typescript
// Internal component state (not exposed as props)
interface InternalState {
  isGeneratingPdf: boolean;        // PDF generation in progress
  contentRef: RefObject<HTMLDivElement>;  // Ref to markdown container
}
```

**State Transitions**:
- Initial: `isGeneratingPdf = false`
- User clicks download: `isGeneratingPdf = true`
- PDF generation completes (success or error): `isGeneratingPdf = false`

## Component Behavior Contract

### Download Button Visibility
- Always visible in dialog header
- Positioned to the right of the dialog title
- Uses Lucide React `Download` icon
- Uses shadcn/ui `Button` component (variant: ghost, size: icon)

### Download Button States

```typescript
type ButtonState = 'enabled' | 'disabled' | 'loading';

// Button state logic
const buttonState: ButtonState =
  isGeneratingPdf ? 'loading' :
  (isGenerating || isFailed || !hasContent) ? 'disabled' :
  'enabled';
```

**Enabled** (clickable):
- Document status is 'completed'
- Has valid markdown content (non-empty string)
- Not currently generating PDF
- Icon: `<Download />`

**Disabled** (not clickable):
- Document status is 'generating' or 'failed'
- No content or empty content
- Icon: `<Download />` (grayed out)

**Loading** (not clickable):
- PDF generation in progress
- Icon: `<Loader2 className="animate-spin" />`

### Error Handling Contract

```typescript
// Error handling behavior
try {
  await generatePdfFromElement(element, filename);
} catch (error) {
  // 1. Log to console for debugging
  console.error('PDF generation failed:', error);

  // 2. Show user-friendly toast notification
  toast.error('Erro ao gerar PDF', {
    description: 'Tente novamente ou reduza o tamanho do documento.'
  });

  // 3. Reset loading state
  setIsGeneratingPdf(false);
}
```

**Error Contract**:
- All errors result in user-friendly toast notification (Portuguese)
- Technical error details logged to console only
- Component remains functional (can retry)
- Dialog remains open (does not close on error)

## No API Contracts

This feature does not involve:
- REST API endpoints
- GraphQL queries/mutations
- WebSocket connections
- Server-side operations

All contracts are client-side TypeScript interfaces and function signatures.

## Testing Contract

For testing purposes, the following behaviors are guaranteed:

1. **Button Render**: Button is always present in dialog header when dialog is open
2. **State Management**: Button correctly reflects document state (enabled/disabled/loading)
3. **PDF Generation**: Calls `generatePdfFromElement` with correct parameters
4. **Error Handling**: Errors result in toast notification and state reset
5. **Filename Format**: Filenames follow pattern `{type}_{sanitized}.pdf`
6. **No Side Effects**: Utility functions are pure (sanitizeFilename, generatePdfFilename)

## Backward Compatibility

**Guarantee**: No breaking changes to existing DocumentViewer usage.

All existing code using DocumentViewer will continue to work unchanged:
```typescript
// Existing usage (still works)
<DocumentViewer
  isOpen={isOpen}
  onClose={onClose}
  documentType="prfaq"
  markdownContent={content}
  status="completed"
/>

// New feature is automatically available (no prop changes needed)
```
