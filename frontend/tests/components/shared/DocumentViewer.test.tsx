/**
 * Tests for DocumentViewer component PDF download functionality
 * Following TDD/BDD approach per Constitution Principle I
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { DocumentViewer } from '../../../src/components/shared/DocumentViewer';
import * as pdfUtils from '../../../src/lib/pdf-utils';

// Mock toast notifications
vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

// Mock PDF utilities
vi.mock('../../../src/lib/pdf-utils', () => ({
  generatePdfFromElement: vi.fn(),
  generatePdfFilename: vi.fn(),
}));

describe('DocumentViewer - PDF Download Button', () => {
  const defaultProps = {
    isOpen: true,
    onClose: vi.fn(),
    documentType: 'prfaq' as const,
    markdownContent: '# Test Document\n\nThis is a test.',
    status: 'completed' as const,
    titleSuffix: 'Test Feature',
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  // T015: Download button renders in dialog header
  it('should render download button in dialog header when dialog is open', () => {
    render(<DocumentViewer {...defaultProps} />);

    const downloadButton = screen.getByRole('button', { name: /download pdf/i });
    expect(downloadButton).toBeInTheDocument();
  });

  // T016: Download button shows Download icon when not generating
  it('should show Download icon when not generating PDF', () => {
    render(<DocumentViewer {...defaultProps} />);

    const downloadButton = screen.getByRole('button', { name: /download pdf/i });
    // Download icon is present (lucide-react Download component)
    expect(downloadButton).toBeInTheDocument();
  });

  // T018: Download button is enabled when status is 'completed' and has content
  it('should enable download button when status is completed and has content', () => {
    render(<DocumentViewer {...defaultProps} />);

    const downloadButton = screen.getByRole('button', { name: /download pdf/i });
    expect(downloadButton).not.toBeDisabled();
  });

  // T019: onClick calls handleDownloadPdf function
  it('should call handleDownloadPdf when download button is clicked', async () => {
    const user = userEvent.setup();
    const mockGeneratePdfFilename = vi.spyOn(pdfUtils, 'generatePdfFilename');
    const mockGeneratePdfFromElement = vi.spyOn(pdfUtils, 'generatePdfFromElement').mockResolvedValue();

    mockGeneratePdfFilename.mockReturnValue('prfaq_test-feature.pdf');

    render(<DocumentViewer {...defaultProps} />);

    const downloadButton = screen.getByRole('button', { name: /download pdf/i });
    await user.click(downloadButton);

    await waitFor(() => {
      expect(mockGeneratePdfFilename).toHaveBeenCalledWith('prfaq', 'Test Feature');
    });
  });

  // T020: handleDownloadPdf generates correct filename for prfaq documents
  it('should generate correct filename for prfaq documents', async () => {
    const user = userEvent.setup();
    const mockGeneratePdfFilename = vi.spyOn(pdfUtils, 'generatePdfFilename');
    vi.spyOn(pdfUtils, 'generatePdfFromElement').mockResolvedValue();

    mockGeneratePdfFilename.mockReturnValue('prfaq_test-feature.pdf');

    render(<DocumentViewer {...defaultProps} documentType="prfaq" />);

    const downloadButton = screen.getByRole('button', { name: /download pdf/i });
    await user.click(downloadButton);

    await waitFor(() => {
      expect(mockGeneratePdfFilename).toHaveBeenCalledWith('prfaq', 'Test Feature');
    });
  });

  // T021: handleDownloadPdf generates correct filename for executive_summary documents
  it('should generate correct filename for executive_summary documents', async () => {
    const user = userEvent.setup();
    const mockGeneratePdfFilename = vi.spyOn(pdfUtils, 'generatePdfFilename');
    vi.spyOn(pdfUtils, 'generatePdfFromElement').mockResolvedValue();

    mockGeneratePdfFilename.mockReturnValue('executive_summary_test-feature.pdf');

    render(<DocumentViewer {...defaultProps} documentType="executive_summary" />);

    const downloadButton = screen.getByRole('button', { name: /download pdf/i });
    await user.click(downloadButton);

    await waitFor(() => {
      expect(mockGeneratePdfFilename).toHaveBeenCalledWith('executive_summary', 'Test Feature');
    });
  });

  // T022: handleDownloadPdf generates correct filename for summary documents
  it('should generate correct filename for summary documents', async () => {
    const user = userEvent.setup();
    const mockGeneratePdfFilename = vi.spyOn(pdfUtils, 'generatePdfFilename');
    vi.spyOn(pdfUtils, 'generatePdfFromElement').mockResolvedValue();

    mockGeneratePdfFilename.mockReturnValue('summary_test-feature.pdf');

    render(<DocumentViewer {...defaultProps} documentType="summary" />);

    const downloadButton = screen.getByRole('button', { name: /download pdf/i });
    await user.click(downloadButton);

    await waitFor(() => {
      expect(mockGeneratePdfFilename).toHaveBeenCalledWith('summary', 'Test Feature');
    });
  });

  // T023: handleDownloadPdf calls generatePdfFromElement with contentRef.current
  it('should call generatePdfFromElement with the markdown content element', async () => {
    const user = userEvent.setup();
    const mockGeneratePdfFromElement = vi.spyOn(pdfUtils, 'generatePdfFromElement').mockResolvedValue();
    vi.spyOn(pdfUtils, 'generatePdfFilename').mockReturnValue('test.pdf');

    render(<DocumentViewer {...defaultProps} />);

    const downloadButton = screen.getByRole('button', { name: /download pdf/i });
    await user.click(downloadButton);

    await waitFor(() => {
      expect(mockGeneratePdfFromElement).toHaveBeenCalled();
      // First argument should be an HTMLElement (the content ref)
      expect(mockGeneratePdfFromElement.mock.calls[0][0]).toBeInstanceOf(HTMLElement);
      // Second argument should be the filename
      expect(mockGeneratePdfFromElement.mock.calls[0][1]).toBe('test.pdf');
    });
  });
});

// T040-T045: User Story 2 tests - Button state management
describe('DocumentViewer - Button State Management (US2)', () => {
  const baseProps = {
    isOpen: true,
    onClose: vi.fn(),
    documentType: 'prfaq' as const,
    titleSuffix: 'Test',
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  // T040: Download button is disabled when status is 'generating'
  it('should disable download button when status is generating', () => {
    render(<DocumentViewer {...baseProps} status="generating" markdownContent="# Test" />);

    const downloadButton = screen.getByRole('button', { name: /download pdf/i });
    expect(downloadButton).toBeDisabled();
  });

  // T041: Download button is disabled when status is 'failed'
  it('should disable download button when status is failed', () => {
    render(<DocumentViewer {...baseProps} status="failed" markdownContent="# Test" />);

    const downloadButton = screen.getByRole('button', { name: /download pdf/i });
    expect(downloadButton).toBeDisabled();
  });

  // T042: Download button is disabled when markdownContent is empty string
  it('should disable download button when markdownContent is empty string', () => {
    render(<DocumentViewer {...baseProps} status="completed" markdownContent="" />);

    const downloadButton = screen.getByRole('button', { name: /download pdf/i });
    expect(downloadButton).toBeDisabled();
  });

  // T043: Download button is disabled when markdownContent is undefined
  it('should disable download button when markdownContent is undefined', () => {
    render(<DocumentViewer {...baseProps} status="completed" markdownContent={undefined} />);

    const downloadButton = screen.getByRole('button', { name: /download pdf/i });
    expect(downloadButton).toBeDisabled();
  });

  // T045: Download button is enabled when status is 'completed' and has valid content
  it('should enable download button when status is completed and has content', () => {
    render(<DocumentViewer {...baseProps} status="completed" markdownContent="# Valid Content" />);

    const downloadButton = screen.getByRole('button', { name: /download pdf/i });
    expect(downloadButton).not.toBeDisabled();
  });
});
