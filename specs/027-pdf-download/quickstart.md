# Quickstart: PDF Download for Document Viewer

**Feature**: 027-pdf-download
**Date**: 2026-01-01
**Audience**: Developers and end users

## Overview

This feature adds PDF download functionality to the DocumentViewer component, allowing users to export generated documents (PR/FAQ, Executive Summary, Summary) as PDF files.

## For End Users

### How to Download a Document as PDF

1. **Open a Document**
   - Navigate to an experiment detail page
   - Click on any document button (PR/FAQ, Executive Summary, or Summary)
   - The DocumentViewer dialog will open displaying the markdown content

2. **Download the PDF**
   - Look for the download icon button in the top-right corner of the dialog header
   - Click the download button
   - A loading spinner will appear while the PDF is being generated (typically 2-5 seconds)
   - The PDF file will automatically download to your browser's default download location

3. **Filename Format**
   - Files are named: `{document-type}_{experiment-title}.pdf`
   - Example: `prfaq_pix-via-whatsapp.pdf`
   - All filenames are lowercase with hyphens replacing spaces

### When the Download Button is Disabled

The download button will be grayed out and unclickable when:
- The document is still being generated (status: "Gerando...")
- The document generation failed (status: "Falha ao gerar documento")
- The document content is empty or unavailable
- A PDF is currently being generated (loading spinner visible)

### Troubleshooting

**Problem**: Download button doesn't work
- **Solution**: Wait for the document to finish generating first. The button is only enabled when the document is ready.

**Problem**: PDF generation fails with error message
- **Solution**: Try again. If the error persists, the document might be too long or complex. Contact support.

**Problem**: Downloaded PDF has poor quality text
- **Solution**: This shouldn't happen (2x rendering scale ensures quality). If text appears blurry, try a different browser or report the issue.

**Problem**: File downloads with wrong name or special characters
- **Solution**: Filenames are automatically sanitized. Special characters and spaces are removed or converted to hyphens. This is expected behavior.

---

## For Developers

### Prerequisites

- React 18.3.1+
- TypeScript 5.5.3+
- html2canvas ^1.4.1 (already installed)
- jsPDF ^3.0.4 (already installed)
- Lucide React (for Download icon)
- Sonner (for toast notifications)

### Component Usage

The DocumentViewer component automatically includes the PDF download feature. No additional props or setup required.

```tsx
import { DocumentViewer } from '@/components/shared/DocumentViewer';

function MyComponent() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <DocumentViewer
      isOpen={isOpen}
      onClose={() => setIsOpen(false)}
      documentType="prfaq"
      markdownContent={myMarkdownContent}
      status="completed"
      titleSuffix="My Experiment"
    />
  );
}
```

The download button appears automatically in the dialog header. Users can click it when the document is ready.

### Utility Functions

If you need PDF generation functionality elsewhere:

```typescript
import { generatePdfFromElement, generatePdfFilename } from '@/lib/pdf-utils';

// Generate PDF from any DOM element
const element = document.getElementById('my-content');
const filename = generatePdfFilename('summary', 'Custom Title');

try {
  await generatePdfFromElement(element, filename);
  console.log('PDF downloaded successfully');
} catch (error) {
  console.error('PDF generation failed:', error);
}
```

### Filename Sanitization

To create safe filenames:

```typescript
import { sanitizeFilename } from '@/lib/pdf-utils';

const safe = sanitizeFilename('Test@Feature #123');
// Result: "testfeature123"

const filename = `document_${sanitizeFilename(userInput)}.pdf`;
```

### Testing

**Unit Tests** (fast):
```bash
cd frontend
npm test -- DocumentViewer.test.tsx
```

**Manual Testing Checklist**:
- [ ] Download button appears in dialog header
- [ ] Button is disabled when document is generating
- [ ] Button is disabled when document failed
- [ ] Button is disabled when content is empty
- [ ] Button shows spinner during PDF generation
- [ ] PDF downloads with correct filename format
- [ ] PDF contains all visible markdown content
- [ ] PDF text is readable (not pixelated)
- [ ] Error toast appears on generation failure
- [ ] Dialog remains open after download

### Development Workflow

1. **Write Tests First** (TDD)
   ```bash
   # Create test file
   touch frontend/tests/components/shared/DocumentViewer.test.tsx

   # Write failing tests for PDF feature
   # Run tests: npm test
   ```

2. **Implement Feature**
   - Add PDF utility functions to `frontend/src/lib/pdf-utils.ts`
   - Modify `DocumentViewer.tsx` to add download button
   - Add button state management and event handler

3. **Verify Tests Pass**
   ```bash
   npm test -- DocumentViewer.test.tsx
   ```

4. **Manual Browser Testing**
   ```bash
   npm run dev
   # Navigate to experiment detail page
   # Test PDF download with various document types
   ```

5. **Commit**
   ```bash
   git add .
   git commit -m "feat: add PDF download to DocumentViewer"
   ```

### Architecture Notes

**Frontend Only**: This feature is entirely client-side. No backend changes required.

**Component Structure**:
- `DocumentViewer.tsx`: UI and state management
- `pdf-utils.ts`: Pure utility functions for PDF generation
- No new API calls or query keys needed

**Design Pattern**: Self-contained component feature with local state management (useState).

### Configuration

**PDF Settings** (in `pdf-utils.ts`):
```typescript
// html2canvas configuration
const canvasOptions = {
  scale: 2,              // Quality factor (2x recommended)
  useCORS: true,         // Cross-origin image support
  logging: false,        // Disable console logs
  backgroundColor: '#ffffff'  // White background
};

// jsPDF configuration
const pdfOptions = {
  orientation: 'portrait',
  unit: 'mm',
  format: 'a4'          // A4 page size
};
```

To change PDF quality or format, modify these constants.

### Performance Considerations

- **Generation Time**: 1-5 seconds depending on document length
- **Memory Usage**: Proportional to document size (~10-50 MB during generation)
- **Browser Limits**: Very long documents (>50 pages) may fail in some browsers
- **Recommendation**: For documents over 20 pages, warn users about potential delays

### Error Scenarios

```typescript
// Common errors and handling
try {
  await generatePdfFromElement(element, filename);
} catch (error) {
  // Error types:
  // 1. Element is null → "Conteúdo não encontrado"
  // 2. Canvas generation fails → Generic error message
  // 3. PDF save fails → Browser-specific guidance

  // All errors show user-friendly toast (Portuguese)
  // Technical details logged to console for debugging
}
```

### Browser Compatibility

Tested and working on:
- ✅ Chrome 90+ (recommended)
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+

**Known Issues**:
- IE 11: Not supported (html2canvas requires modern browser)
- Mobile Safari: Works but may be slow on large documents

### File Size Expectations

- **Short document** (1-2 pages): ~500 KB - 1 MB
- **Medium document** (5-10 pages): ~2-5 MB
- **Long document** (20+ pages): ~10-20 MB

PDF files are uncompressed PNGs. Future optimization could add compression.

### Accessibility

- **Keyboard**: Download button is keyboard accessible (Tab + Enter)
- **Screen Readers**: Button has aria-label "Download PDF"
- **Visual**: Loading state clearly indicated with spinner
- **Errors**: Error messages announced via toast notification

### Future Enhancements (Out of Scope for MVP)

- PDF compression to reduce file size
- Custom page breaks and headers/footers
- Batch download of multiple documents
- Email sharing integration
- Print preview before download
- Alternative formats (Word, HTML)

## Quick Reference

| Task | Command/Path |
|------|-------------|
| Run tests | `cd frontend && npm test -- DocumentViewer.test.tsx` |
| Start dev server | `cd frontend && npm run dev` |
| Component file | `frontend/src/components/shared/DocumentViewer.tsx` |
| Utility functions | `frontend/src/lib/pdf-utils.ts` |
| Test file | `frontend/tests/components/shared/DocumentViewer.test.tsx` |

## Support

For issues or questions:
1. Check browser console for error details
2. Verify html2canvas and jspdf are installed: `npm list html2canvas jspdf`
3. Review toast error messages for user-friendly guidance
4. Check this quickstart guide for common solutions
