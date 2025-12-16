# Feature Specification: Topic Guides with Multi-Modal Context

**Feature Branch**: `006-topic-guides`
**Created**: 2025-12-16
**Status**: Draft
**Input**: User description: "contexto para topicos 1. Estrutura de diretórios para topic guides: - Cada topic guide vira um diretório: data/topic_guides/<nome_do_guia>/ - Dentro desse diretório podem ter documentos (PDFs, markdown, texto) e imagens 2. Arquivo summary.md obrigatório: - Cada diretório de topic guide deve ter um summary.md - Esse arquivo deve: - Ajudar a entender o contexto geral - Ter uma seção ## FILE DESCRIPTION que descreve cada arquivo do diretório 3. Contexto para os synths: - Os synths devem poder acessar esses documentos e imagens - Exemplo: para entrevista sobre Amazon, synth poderia 'ver' as telas da Amazon 4. Comando CLI para criar/atualizar summary.md: - Recebe --topic-guide <nome> como parâmetro Se o diretório não existir: - Cria o diretório data/topic_guides/<nome>/ - Cria summary.md com: 'contexto para o guide: <nome>' Se o diretório já existir: - Lista todos os arquivos do diretório (exceto o próprio summary.md) - Verifica se cada arquivo já consta na seção ## FILE DESCRIPTION - Para cada arquivo que NÃO consta: - Submete o arquivo à LLM (OpenAI) - Pede descrição (10-50 palavras) - Tipos suportados: PNG, JPEG, PDF, MD, TXT ou qualquer arquivo texto - Appenda nome do arquivo + descrição na ## FILE DESCRIPTION"

## Clarifications

### Session 2025-12-16

- Q: When a user has files in their topic guide directory that are NOT in the supported list (PNG, JPEG, PDF, MD, TXT), what should the system do? → A: Skip unsupported files but log a warning message listing which files were skipped
- Q: When the LLM API call fails during file description generation (network timeout, API error, rate limit), what should the system do for that specific file? → A: Skip the file, log a warning, and add a placeholder entry in FILE DESCRIPTION indicating the file needs manual documentation
- Q: How should the system identify whether a file is "already documented" in the FILE DESCRIPTION section to avoid re-processing? → A: Match by file content hash (MD5/SHA) to detect if the file content has changed since last documentation
- Q: When the system encounters a file it cannot read (corrupted file, permission denied, or binary file that fails to process), what should happen? → A: Skip silently and continue processing other files
- Q: When summary.md exists but is missing the `## FILE DESCRIPTION` section, what should the system do? → A: Automatically append the missing `## FILE DESCRIPTION` section to the existing summary.md file

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Create New Topic Guide Directory (Priority: P1)

A researcher wants to create a new topic guide for conducting synth interviews about a specific subject (e.g., Amazon e-commerce). They need a structured directory to organize all contextual materials (screenshots, documents, PDFs) that synths will reference during interviews.

**Why this priority**: This is the foundation of the feature. Without the ability to create and initialize topic guide directories, no other functionality can work. It provides immediate value by establishing the organizational structure.

**Independent Test**: Can be fully tested by running the CLI command with a new topic guide name and verifying that the directory structure and initial summary.md file are created correctly. Delivers a working organizational structure for topic-specific content.

**Acceptance Scenarios**:

1. **Given** the topic guide "amazon-ecommerce" does not exist, **When** user runs the command with `--topic-guide amazon-ecommerce`, **Then** the system creates directory `data/topic_guides/amazon-ecommerce/` and file `summary.md` with content "contexto para o guide: amazon-ecommerce"
2. **Given** the parent directory `data/topic_guides/` does not exist, **When** user runs the command with any topic guide name, **Then** the system creates the parent directory before creating the topic guide directory
3. **Given** a valid topic guide name, **When** the directory is created, **Then** the summary.md file includes the required section headers (context description and ## FILE DESCRIPTION)

---

### User Story 2 - Auto-Document Existing Files (Priority: P2)

A researcher has manually added several files (screenshots, PDFs, markdown notes) to an existing topic guide directory. They want the system to automatically analyze these files and generate descriptions without manual documentation work.

**Why this priority**: This automates the tedious work of documenting context files and ensures synths have clear descriptions of all available materials. It significantly reduces manual effort and improves consistency.

**Independent Test**: Can be tested by creating a topic guide, adding various file types (PNG, PDF, TXT, MD), running the update command, and verifying that each file gets an AI-generated description in the summary.md. Delivers automated documentation of context materials.

**Acceptance Scenarios**:

1. **Given** topic guide "amazon-ecommerce" exists with 3 PNG screenshots and 2 PDF documents not yet documented, **When** user runs the update command, **Then** the system analyzes each file and appends descriptions to the ## FILE DESCRIPTION section
2. **Given** a topic guide with files already documented in summary.md with matching content hashes, **When** user runs the update command, **Then** the system skips files with unchanged content and only processes new or modified files
3. **Given** a file that is summary.md itself, **When** scanning the directory, **Then** the system excludes summary.md from the files to be documented
4. **Given** a supported file type (PNG, JPEG, PDF, MD, TXT), **When** sending to LLM for description, **Then** the system requests a description between 10-50 words

---

### User Story 3 - Access Context During Interviews (Priority: P3)

During a UX research interview, a synth needs to reference visual materials (e.g., Amazon product page screenshots) and documents (e.g., feature specifications) to provide informed responses about their experience with the interface.

**Why this priority**: This enables synths to provide contextual, grounded responses during interviews by accessing relevant materials. It's the ultimate goal but depends on the previous stories being complete.

**Independent Test**: Can be tested by conducting a synth interview about a topic with prepared context files and verifying that the synth can access and reference the documented materials in their responses. Delivers the complete user experience of context-aware interviews.

**Acceptance Scenarios**:

1. **Given** a topic guide "amazon-ecommerce" with documented screenshots and PDFs, **When** a synth interview is conducted about Amazon shopping, **Then** the synth can access the file descriptions from summary.md
2. **Given** visual materials (PNG/JPEG) in a topic guide, **When** the synth references these materials, **Then** the synth's responses reflect understanding of the visual content (e.g., "I can see the product image shows...")
3. **Given** text-based materials (PDF, MD, TXT) in a topic guide, **When** the synth is asked about specific topics, **Then** the synth can reference information from those documents

---

### Edge Cases

- Unsupported file types: System skips files not in the supported list and logs a warning listing skipped files
- Corrupted or unreadable files: System skips silently and continues processing other files
- LLM API failures: System skips the failed file, logs a warning, and adds a placeholder entry in FILE DESCRIPTION indicating manual documentation needed
- Missing FILE DESCRIPTION section: System automatically appends the missing section to existing summary.md
- How does the system handle very large files (e.g., 100MB PDF)?
- What happens when file names contain special characters or spaces?
- How does the system handle permission issues (read-only directories, write-protected files)?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST create a directory structure `data/topic_guides/<topic_name>/` when a new topic guide is initialized
- **FR-002**: System MUST create a `summary.md` file in each topic guide directory with the initial content "contexto para o guide: <topic_name>"
- **FR-003**: System MUST include a ## FILE DESCRIPTION section in every summary.md file
- **FR-004**: System MUST scan all files in a topic guide directory (excluding summary.md itself) when updating documentation
- **FR-005**: System MUST identify files not yet documented in the ## FILE DESCRIPTION section by comparing file content hashes (MD5 or SHA)
- **FR-006**: System MUST send undocumented files to an LLM for description generation
- **FR-007**: System MUST support the following file types: PNG, JPEG, PDF, MD, TXT, and any plain text files
- **FR-008**: System MUST request descriptions between 10-50 words from the LLM
- **FR-009**: System MUST append file name, content hash, and description to the ## FILE DESCRIPTION section for each newly documented file
- **FR-010**: System MUST provide a CLI command that accepts `--topic-guide <name>` parameter
- **FR-011**: CLI command MUST create new topic guide if the directory does not exist
- **FR-012**: CLI command MUST update existing topic guide documentation if the directory already exists
- **FR-013**: System MUST skip files whose content hash matches an existing entry in the ## FILE DESCRIPTION section during updates
- **FR-014**: Summary.md file MUST help users understand the general context of the topic guide
- **FR-015**: Synths MUST be able to access documents and images from topic guides during interviews
- **FR-016**: System MUST silently skip files that cannot be read (corrupted, permission denied, unreadable binary files) and continue processing other files
- **FR-017**: System MUST skip files with unsupported file types and log a warning message listing which files were skipped
- **FR-018**: When LLM API calls fail for a file, system MUST skip that file, log a warning, and add a placeholder entry in FILE DESCRIPTION indicating manual documentation is needed
- **FR-019**: When summary.md exists but is missing the ## FILE DESCRIPTION section, system MUST automatically append the missing section to preserve existing content

### Key Entities

- **Topic Guide**: A named collection of contextual materials organized in a dedicated directory, includes a summary.md with context description and file catalog
- **Summary File (summary.md)**: A markdown file containing general context about the topic and a FILE DESCRIPTION section cataloging all materials in the directory
- **Context File**: Any document or image (PNG, JPEG, PDF, MD, TXT) stored in a topic guide directory that provides background information for synth interviews
- **File Description**: A 10-50 word AI-generated description of a context file's content, stored in the summary.md

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can create a new topic guide directory with initialized summary.md in under 10 seconds via a single CLI command
- **SC-002**: System can automatically document 20 mixed files (images and documents) in under 2 minutes
- **SC-003**: 95% of AI-generated file descriptions accurately capture the file's key content in 10-50 words
- **SC-004**: Synths conducting interviews can access and reference contextual materials from topic guides in their responses
- **SC-005**: Update command successfully identifies and documents only new or modified files (based on content hash), skipping unchanged files with 100% accuracy
- **SC-006**: System handles all supported file types (PNG, JPEG, PDF, MD, TXT) without errors in file processing

## Assumptions

- The LLM API (OpenAI) is available and accessible with appropriate credentials configured
- Users have write permissions to the `data/topic_guides/` directory
- File names follow standard filesystem naming conventions (no illegal characters)
- The system has sufficient disk space to store topic guide materials
- Network connectivity is available for LLM API calls during file description generation
- Standard markdown formatting is acceptable for the summary.md structure
- Synths have a mechanism to read and parse summary.md files during interview sessions (integration point to be defined in planning phase)
