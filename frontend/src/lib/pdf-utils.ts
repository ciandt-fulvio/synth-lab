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
 * 1. Captures the element using html2canvas (high quality)
 * 2. Creates a jsPDF document (A4, portrait)
 * 3. Calculates dimensions with margins
 * 4. Splits image across pages with proper positioning
 * 5. Triggers browser download
 *
 * Page specifications:
 * - Format: A4 (210mm x 297mm)
 * - Margins: 15mm on all sides (for safer page breaks)
 * - Usable area: 180mm x 267mm per page
 *
 * @param element - The HTML element to capture (typically the markdown content container)
 * @param filename - The filename for the downloaded PDF
 * @returns Promise that resolves when PDF is generated and download initiated
 * @throws Error if element is null or PDF generation fails
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
    // Capture element as canvas with high quality
    const canvas = await html2canvas(element, {
      scale: 2,
      useCORS: true,
      logging: false,
      backgroundColor: '#ffffff'
    });

    // Create jsPDF instance (A4, portrait, mm units)
    const pdf = new jsPDF({
      orientation: 'portrait',
      unit: 'mm',
      format: 'a4',
      compress: true
    });

    // PDF dimensions
    const pageWidth = 210;  // A4 width in mm
    const pageHeight = 297; // A4 height in mm
    const margin = 15;      // 15mm margins for safer breaks

    // Content area (with margins)
    const contentWidth = pageWidth - (2 * margin);   // 180mm
    const contentHeight = pageHeight - (2 * margin); // 267mm

    // Calculate image dimensions to fit content width
    const imgWidth = contentWidth;
    const imgHeight = (canvas.height * contentWidth) / canvas.width;

    // Calculate number of pages needed
    const totalPages = Math.ceil(imgHeight / contentHeight);

    // Convert canvas to image
    const imgData = canvas.toDataURL('image/png', 1.0);

    // Add each page
    for (let page = 0; page < totalPages; page++) {
      if (page > 0) {
        pdf.addPage();
      }

      // Calculate position for this page
      const position = -(page * contentHeight);

      // Add image positioned for this page
      pdf.addImage(
        imgData,
        'PNG',
        margin,           // x (with left margin)
        margin + position, // y (with top margin + page offset)
        imgWidth,
        imgHeight
      );
    }

    // Download PDF
    pdf.save(filename);

  } catch (error) {
    console.error('PDF generation failed:', error);
    throw new Error('Falha ao gerar PDF. Tente novamente.');
  }
}
