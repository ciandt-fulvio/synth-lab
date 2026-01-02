# Research: PDF Download for Document Viewer

**Feature**: 027-pdf-download
**Date**: 2026-01-01
**Phase**: 0 - Research

## Overview

This document captures research findings for implementing PDF download functionality using html2canvas and jsPDF libraries.

## Research Tasks

### 1. html2canvas Best Practices

**Decision**: Use html2canvas v1.4.1 with 2x scale factor for high-quality rendering

**Rationale**:
- Version 1.4.1 is already installed and stable
- 2x scale factor provides good balance between quality and performance
- Supports rendering complex markdown content including tables and formatted text
- Can target specific DOM elements via ref

**Key Implementation Details**:
```typescript
// Recommended configuration
html2canvas(element, {
  scale: 2,              // 2x for high quality
  useCORS: true,         // Allow cross-origin images if any
  logging: false,        // Disable console logs in production
  backgroundColor: '#ffffff'  // White background for PDFs
})
```

**Alternatives Considered**:
- Scale factor 3x: Rejected - too slow, minimal quality improvement
- Scale factor 1x: Rejected - poor quality, text pixelation
- dom-to-image library: Rejected - less maintained, more compatibility issues

**Sources**:
- html2canvas documentation: https://html2canvas.hertzen.com/configuration
- Best practices for React: https://github.com/niklasvh/html2canvas/wiki/React-specific-usage

---

### 2. jsPDF Best Practices

**Decision**: Use jsPDF v3.0.4 with A4 format and automatic page handling

**Rationale**:
- Version 3.0.4 is already installed and latest stable
- A4 format is standard for document export
- `addImage()` method handles canvas-to-PDF conversion efficiently
- Automatic page breaking for long documents

**Key Implementation Details**:
```typescript
import jsPDF from 'jspdf';

const pdf = new jsPDF({
  orientation: 'portrait',
  unit: 'mm',
  format: 'a4'
});

// Calculate dimensions to fit A4 width
const imgWidth = 210; // A4 width in mm
const imgHeight = (canvas.height * imgWidth) / canvas.width;

// Add image to PDF
pdf.addImage(
  canvas.toDataURL('image/png'),
  'PNG',
  0,
  0,
  imgWidth,
  imgHeight
);

// Trigger download
pdf.save(filename);
```

**Alternatives Considered**:
- Letter format: Rejected - A4 is more universal outside US
- Manual page breaking: Rejected - adds complexity, auto-breaking sufficient for MVP
- PDF compression: Deferred - out of scope for MVP, can add later if file sizes become issue

**Sources**:
- jsPDF documentation: https://github.com/parallax/jsPDF
- Image handling: https://raw.githack.com/MrRio/jsPDF/master/docs/module-addImage.html

---

### 3. Filename Sanitization Strategy

**Decision**: Replace spaces with hyphens, remove special characters except underscores and hyphens

**Rationale**:
- Cross-platform compatibility (Windows, Mac, Linux)
- URL-safe filenames for potential future sharing features
- Preserves readability while ensuring no file system issues

**Implementation Pattern**:
```typescript
function sanitizeFilename(text: string): string {
  return text
    .toLowerCase()
    .replace(/\s+/g, '-')           // spaces to hyphens
    .replace(/[^a-z0-9\-_]/g, '')   // remove special chars
    .replace(/-+/g, '-')            // collapse multiple hyphens
    .replace(/^-|-$/g, '');         // trim leading/trailing hyphens
}
```

**Edge Cases Handled**:
- Empty title suffix: Use document type only
- Very long titles: Truncate to 50 characters to avoid OS limits
- Non-ASCII characters: Removed for maximum compatibility

**Alternatives Considered**:
- Keep spaces: Rejected - causes issues in URLs and some file systems
- Use URL encoding: Rejected - results in ugly %20 filenames
- Keep accents/unicode: Rejected - potential compatibility issues across systems

---

### 4. Error Handling Strategy

**Decision**: Try-catch around PDF generation with user-friendly error messages

**Rationale**:
- html2canvas can fail on complex CSS or large DOM
- jsPDF can fail on memory constraints
- Users need actionable feedback, not technical stack traces

**Implementation Pattern**:
```typescript
const handleDownloadPdf = async () => {
  setIsGeneratingPdf(true);

  try {
    if (!contentRef.current) {
      throw new Error('Conteúdo não encontrado');
    }

    const canvas = await html2canvas(contentRef.current, { scale: 2 });
    const pdf = new jsPDF(...);
    // ... PDF generation
    pdf.save(filename);

  } catch (error) {
    console.error('PDF generation failed:', error);
    toast.error('Erro ao gerar PDF', {
      description: 'Tente novamente ou reduza o tamanho do documento.'
    });
  } finally {
    setIsGeneratingPdf(false);
  }
};
```

**Error Scenarios**:
1. Element not found: User sees "Conteúdo não encontrado"
2. Canvas generation fails: User sees generic error with retry suggestion
3. PDF save fails: User sees browser-specific download help

**Alternatives Considered**:
- Silent failure: Rejected - user needs feedback
- Detailed technical errors: Rejected - confusing for non-technical users
- Retry logic: Deferred - adds complexity, manual retry sufficient for MVP

---

### 5. Button State Management

**Decision**: Use local component state (useState) for isGeneratingPdf flag

**Rationale**:
- Simple boolean state sufficient for this feature
- No need for global state or React Query
- Follows React best practices for UI state

**Implementation Pattern**:
```typescript
const [isGeneratingPdf, setIsGeneratingPdf] = useState(false);

// Button disabled conditions
const isButtonDisabled = isGenerating || isFailed || !hasContent || isGeneratingPdf;
```

**State Transitions**:
1. Initial: `isGeneratingPdf = false`, button enabled (if content ready)
2. User clicks: `isGeneratingPdf = true`, button shows spinner
3. Success/Error: `isGeneratingPdf = false`, button returns to normal

**Alternatives Considered**:
- useReducer: Rejected - overkill for single boolean
- Context API: Rejected - state doesn't need to be shared
- React Query mutation: Rejected - not a server operation

---

### 6. React Component Integration

**Decision**: Add button to DialogHeader with conditional rendering

**Rationale**:
- Dialog header is the standard location for action buttons
- Lucide React Download icon provides clear visual affordance
- Button component from shadcn/ui maintains design consistency

**Implementation Pattern**:
```tsx
<DialogHeader>
  <div className="flex items-center justify-between">
    <DialogTitle className="flex items-center gap-2">
      {icon}
      {fullTitle}
    </DialogTitle>
    <Button
      variant="ghost"
      size="icon"
      onClick={handleDownloadPdf}
      disabled={isButtonDisabled}
    >
      {isGeneratingPdf ? (
        <Loader2 className="h-4 w-4 animate-spin" />
      ) : (
        <Download className="h-4 w-4" />
      )}
    </Button>
  </div>
</DialogHeader>
```

**Design Decisions**:
- Ghost variant: Less visual weight, doesn't compete with content
- Icon-only button: Compact, universally understood download symbol
- Right alignment: Standard position for action buttons in dialogs

**Alternatives Considered**:
- Primary button: Rejected - too prominent, download is secondary action
- Text button "Download PDF": Rejected - takes more space, redundant with icon
- Footer placement: Rejected - header is more accessible, standard pattern

---

## Summary

All research tasks completed with clear decisions and rationale. No additional research required. Ready to proceed to Phase 1 (Design & Contracts).

**Key Technologies Confirmed**:
- html2canvas ^1.4.1 (already installed)
- jsPDF ^3.0.4 (already installed)
- React 18.3.1 (local state management)
- Lucide React (Download icon)
- Sonner (error toast notifications)

**No New Dependencies Required**
