/**
 * Tests for PDF utility functions
 * Following TDD approach - tests verify implementation correctness
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import {
  sanitizeFilename,
  generatePdfFilename,
  generatePdfFromElement,
} from '../../src/lib/pdf-utils';

// Mock html2canvas and jsPDF at the module level
vi.mock('html2canvas');
vi.mock('jspdf');

describe('sanitizeFilename', () => {
  it('should convert spaces to hyphens', () => {
    expect(sanitizeFilename('Pix via WhatsApp')).toBe('pix-via-whatsapp');
    expect(sanitizeFilename('Multiple   Spaces')).toBe('multiple-spaces');
  });

  it('should remove special characters', () => {
    expect(sanitizeFilename('Test@Feature#123')).toBe('testfeature123');
    expect(sanitizeFilename('Hello! World?')).toBe('hello-world');
  });

  it('should handle empty/undefined input', () => {
    expect(sanitizeFilename('')).toBe('document');
    expect(sanitizeFilename(undefined)).toBe('document');
    expect(sanitizeFilename('   ')).toBe('document');
  });

  it('should remove unicode/non-ASCII characters', () => {
    expect(sanitizeFilename('Café São Paulo')).toBe('caf-so-paulo');
    expect(sanitizeFilename('日本語')).toBe('document');
  });

  it('should truncate to 50 characters', () => {
    const longTitle = 'This is a very long title that definitely exceeds fifty characters limit for filenames';
    const result = sanitizeFilename(longTitle);
    expect(result.length).toBeLessThanOrEqual(50);
  });

  it('should collapse multiple hyphens', () => {
    expect(sanitizeFilename('test---multiple---hyphens')).toBe('test-multiple-hyphens');
  });

  it('should trim leading/trailing hyphens', () => {
    expect(sanitizeFilename('---test---')).toBe('test');
  });
});

describe('generatePdfFilename', () => {
  it('should generate filename for prfaq documents', () => {
    expect(generatePdfFilename('prfaq', 'Pix via WhatsApp')).toBe('prfaq_pix-via-whatsapp.pdf');
  });

  it('should generate filename for executive_summary documents', () => {
    expect(generatePdfFilename('executive_summary', 'Test Feature')).toBe('executive_summary_test-feature.pdf');
  });

  it('should generate filename for summary documents', () => {
    expect(generatePdfFilename('summary', 'Another Test')).toBe('summary_another-test.pdf');
  });

  it('should handle undefined titleSuffix', () => {
    expect(generatePdfFilename('prfaq', undefined)).toBe('prfaq_document.pdf');
    expect(generatePdfFilename('summary')).toBe('summary_document.pdf');
  });

  it('should sanitize special characters in titleSuffix', () => {
    expect(generatePdfFilename('prfaq', 'Test@#$%^')).toBe('prfaq_test.pdf');
  });
});

describe('generatePdfFromElement', () => {
  it('should throw error if element is null', async () => {
    await expect(generatePdfFromElement(null as unknown as HTMLElement, 'test.pdf')).rejects.toThrow('Conteúdo não encontrado');
  });

  it('should throw error if element is undefined', async () => {
    await expect(generatePdfFromElement(undefined as unknown as HTMLElement, 'test.pdf')).rejects.toThrow('Conteúdo não encontrado');
  });

  // Note: Full integration tests with html2canvas and jsPDF would require complex mocking
  // These are better tested manually or with E2E tests
  // The function is verified to work through manual testing
});
