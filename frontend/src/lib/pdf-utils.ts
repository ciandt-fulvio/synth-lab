/**
 * PDF Generation Utilities
 *
 * Provides functions for generating PDF files from DOM elements using html2canvas and jsPDF.
 * Used by DocumentViewer component to export documents as PDFs.
 *
 * Dependencies:
 * - html2canvas: https://html2canvas.hertzen.com/
 * - jsPDF: https://github.com/parallax/jsPDF
 */

import html2canvas from 'html2canvas';
import jsPDF from 'jspdf';
import type { DocumentType } from '@/types/document';

/**
 * Sanitizes a string to create a valid, cross-platform filename.
 *
 * Rules:
 * - Converts to lowercase
 * - Replaces spaces with hyphens
 * - Removes all non-alphanumeric characters except hyphens and underscores
 * - Collapses multiple consecutive hyphens into one
 * - Removes leading/trailing hyphens
 * - Truncates to 50 characters maximum
 * - Returns "document" if result is empty
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
export function sanitizeFilename(text: string | undefined): string {
  if (!text || !text.trim()) {
    return 'document';
  }

  const sanitized = text
    .toLowerCase()
    .trim()
    .replace(/\s+/g, '-')            // Replace spaces with hyphens
    .replace(/[^a-z0-9\-_]/g, '')    // Remove special chars (keep alphanumeric, hyphens, underscores)
    .replace(/-+/g, '-')             // Collapse multiple hyphens
    .replace(/^-|-$/g, '')           // Remove leading/trailing hyphens
    .substring(0, 50);               // Truncate to 50 chars

  return sanitized || 'document';    // Fallback if empty after sanitization
}

/**
 * Generates a standardized PDF filename from document type and title suffix.
 *
 * Format: {documentType}_{sanitized_suffix}.pdf
 *
 * @param documentType - The type of document ('prfaq' | 'executive_summary' | 'summary')
 * @param titleSuffix - Optional custom title suffix
 * @returns A filename in format: {documentType}_{sanitized_title}.pdf
 *
 * @example
 * generatePdfFilename('prfaq', 'Pix via WhatsApp') // → "prfaq_pix-via-whatsapp.pdf"
 * generatePdfFilename('summary', undefined) // → "summary_document.pdf"
 * generatePdfFilename('executive_summary', 'Test Feature') // → "executive_summary_test-feature.pdf"
 */
export function generatePdfFilename(
  documentType: DocumentType,
  titleSuffix?: string
): string {
  const sanitizedSuffix = sanitizeFilename(titleSuffix);
  return `${documentType}_${sanitizedSuffix}.pdf`;
}

/**
 * Generates a PDF file from a DOM element and triggers browser download.
 *
 * Process:
 * 1. Captures the element using html2canvas (2x scale for quality)
 * 2. Converts canvas to PNG data URL
 * 3. Creates a jsPDF document (A4, portrait)
 * 4. Calculates dimensions with 10mm margins on all sides
 * 5. Automatically splits content across multiple pages if needed
 * 6. Adds paginated images to PDF
 * 7. Triggers browser download
 *
 * Page specifications:
 * - Format: A4 (210mm x 297mm)
 * - Margins: 10mm on all sides
 * - Usable area: 190mm x 277mm per page
 * - Auto-pagination: Content flows across multiple pages as needed
 *
 * @param element - The HTML element to capture (typically the markdown content container)
 * @param filename - The filename for the downloaded PDF
 * @returns Promise that resolves when PDF is generated and download initiated
 * @throws Error if element is null, canvas generation fails, or PDF creation fails
 *
 * @example
 * const contentElement = contentRef.current;
 * await generatePdfFromElement(contentElement, "prfaq_example.pdf");
 */
export async function generatePdfFromElement(
  element: HTMLElement,
  filename: string
): Promise<void> {
  // Validate element
  if (!element) {
    throw new Error('Conteúdo não encontrado');
  }

  try {
    // Capture element as canvas with high quality (2x scale)
    const canvas = await html2canvas(element, {
      scale: 2,                    // 2x for high quality
      useCORS: true,              // Allow cross-origin images if any
      logging: false,             // Disable console logs
      backgroundColor: '#ffffff'  // White background for PDFs
    });

    // Create jsPDF instance (A4, portrait, mm units)
    const pdf = new jsPDF({
      orientation: 'portrait',
      unit: 'mm',
      format: 'a4'
    });

    // PDF page dimensions with margins
    const pageWidth = 210;           // A4 width in mm
    const pageHeight = 297;          // A4 height in mm
    const margin = 10;               // 10mm margins on all sides
    const contentWidth = pageWidth - (2 * margin);   // 190mm usable width
    const contentHeight = pageHeight - (2 * margin); // 277mm usable height

    // Convert mm to pixels for canvas calculations (assuming 96 DPI)
    const mmToPixel = (mm: number) => (mm * 96) / 25.4;
    const contentWidthPx = mmToPixel(contentWidth);
    const contentHeightPx = mmToPixel(contentHeight);

    // Calculate scale factor to fit canvas width to content width
    const scaleFactor = contentWidthPx / canvas.width;
    const scaledCanvasHeight = canvas.height * scaleFactor;

    // Calculate how many pages are needed
    const totalPages = Math.ceil(scaledCanvasHeight / contentHeightPx);

    // Create a temporary canvas for slicing
    const sliceCanvas = document.createElement('canvas');
    const sliceCtx = sliceCanvas.getContext('2d');
    if (!sliceCtx) {
      throw new Error('Não foi possível criar contexto do canvas');
    }

    // Set slice canvas dimensions to match content area
    sliceCanvas.width = canvas.width;
    sliceCanvas.height = Math.min(
      canvas.height,
      Math.ceil(contentHeightPx / scaleFactor)
    );

    // Add pages with content slices
    for (let page = 0; page < totalPages; page++) {
      // Add new page for all pages except the first
      if (page > 0) {
        pdf.addPage();
      }

      // Calculate source Y position in original canvas
      const sourceY = page * (contentHeightPx / scaleFactor);
      const sourceHeight = Math.min(
        sliceCanvas.height,
        canvas.height - sourceY
      );

      // Clear the slice canvas
      sliceCtx.fillStyle = '#ffffff';
      sliceCtx.fillRect(0, 0, sliceCanvas.width, sliceCanvas.height);

      // Draw the slice from the original canvas
      sliceCtx.drawImage(
        canvas,
        0,              // source x
        sourceY,        // source y (offset for this page)
        canvas.width,   // source width
        sourceHeight,   // source height
        0,              // destination x
        0,              // destination y
        canvas.width,   // destination width
        sourceHeight    // destination height
      );

      // Convert slice to image data
      const sliceImgData = sliceCanvas.toDataURL('image/png');

      // Add the slice to the PDF
      pdf.addImage(
        sliceImgData,
        'PNG',
        margin,        // x position (with left margin)
        margin,        // y position (with top margin)
        contentWidth,  // image width (fits content area)
        Math.min(contentHeight, (sourceHeight * scaleFactor * 25.4) / 96) // image height in mm
      );
    }

    // Clean up
    sliceCanvas.remove();

    // Trigger download
    pdf.save(filename);

  } catch (error) {
    console.error('PDF generation failed:', error);
    throw new Error('Falha ao gerar PDF. Tente novamente.');
  }
}
