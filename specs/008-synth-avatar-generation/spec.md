# Feature Specification: Synth Avatar Generation

**Feature Branch**: `008-synth-avatar-generation`
**Created**: 2025-12-16
**Status**: Draft
**Input**: User description: "Geração de Avatares para Synths - Adicionar funcionalidade de geração de avatares ao comando gensynth usando API OpenAI para criar imagens 3x3 com 9 avatares diversificados"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Generate avatars in batches during synth creation (Priority: P1)

Users want to automatically generate visual avatars for newly created synths in batches of 9, making the synthetic personas more realistic and usable for research, prototyping, and presentations.

**Why this priority**: This is the core functionality. Without batch avatar generation, users cannot efficiently create visual representations for their synths, which is the main purpose of this feature.

**Independent Test**: Can be fully tested by running `gensynth -n 9 --avatar` and verifying that 9 avatar images are created in `data/synths/avatar/` directory, with each image correctly mapped to a synth ID.

**Acceptance Scenarios**:

1. **Given** user wants to generate 9 synths with avatars, **When** user runs `gensynth -n 9 --avatar`, **Then** system generates 9 synths, creates one 1024x1024 image via OpenAI API with 9 distinct avatars in 3x3 grid, splits the image into 9 individual avatar files, and saves each as `data/synths/avatar/{synth-id}.png`

2. **Given** user wants to generate 18 synths with avatars, **When** user runs `gensynth -n 18 --avatar`, **Then** system processes 2 blocks (9 synths each), makes 2 API calls to OpenAI, and generates 18 individual avatar files

3. **Given** user generates synths with avatars enabled, **When** avatars are created, **Then** each avatar image displays appropriate diversity in visual filters (no filter, B&W, sepia, warm, cold, 3D style), backgrounds matching profession context, varied clothing/accessories, and realistic Brazilian demographics

---

### User Story 2 - Control number of avatar blocks to generate (Priority: P2)

Users want to control how many blocks of avatars to generate separately from the number of synths, allowing batch generation of avatars for existing synths or pre-generation of avatar batches.

**Why this priority**: This provides flexibility for advanced use cases like generating avatars for existing synths or pre-creating avatar batches, but is not essential for basic functionality.

**Independent Test**: Can be fully tested by running `gensynth --avatar -b 3` and verifying that exactly 3 blocks (27 avatars total) are generated regardless of synth count.

**Acceptance Scenarios**:

1. **Given** user wants to generate 3 blocks of avatars without creating new synths, **When** user runs `gensynth --avatar -b 3`, **Then** system generates 27 avatars (3 blocks × 9 avatars) and saves them to the avatar directory

2. **Given** user runs avatar generation with block parameter, **When** -b parameter is omitted, **Then** system defaults to 1 block (9 avatars)

3. **Given** user specifies both synth count and block count, **When** block count doesn't match synth count, **Then** system uses synth count to determine number of blocks needed (rounded up to nearest multiple of 9)

---

### User Story 3 - Generate avatars for existing synths (Priority: P3)

Users want to generate avatars for synths that were created earlier without avatars, filling gaps in their synthetic persona database.

**Why this priority**: This is a convenience feature for maintaining consistency in synth databases but not critical for initial adoption.

**Independent Test**: Can be fully tested by creating synths without avatars, then running a command to generate avatars for specific synth IDs, and verifying the avatar files are created correctly.

**Acceptance Scenarios**:

1. **Given** user has existing synths without avatars, **When** user runs avatar generation for specific synth IDs, **Then** system loads synth data, generates appropriate avatar based on synth demographics, and saves to correct location

2. **Given** user requests avatars for synths that already have avatars, **When** generation runs, **Then** system overwrites existing avatar files with newly generated ones

---

### Edge Cases

- What happens when OpenAI API request fails (rate limit, network error, API error)?
A: Just fail gracefully with an error message.
- How does system handle partial block generation (e.g., 10 synths when blocks are groups of 9)?
A: Generate only the required number of avatars for the last block.
- What happens when the avatar directory doesn't exist?
/data/synths/avatar/ should be created automatically.
- How does system handle duplicate synth IDs during avatar filename generation?
A: Synth IDs are unique by design; if duplicates occur, it indicates a deeper issue in synth generation.
- What happens when image splitting fails or produces corrupted images?
A: System should log an error and skip saving those avatars, notifying the user.
- How does system handle malformed synth data (missing demographics fields needed for prompts)?
A: System should validate synth data before making API calls and skip invalid entries with a warning.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST add `--avatar` flag to `gensynth` command to enable avatar generation during synth creation
- **FR-002**: System MUST add `-b <number>` parameter to specify number of avatar blocks to generate (default: 1 block)
- **FR-003**: System MUST group synths into blocks of exactly 9 for batch avatar generation via OpenAI API
- **FR-004**: System MUST construct prompts for OpenAI image generation API that include only visually relevant synth data: idade (age), gênero (gender), raça_etnia (ethnicity), ocupação (occupation)
- **FR-005**: System MUST exclude from image prompts non-visual data such as interesses (interests), traços de personalidade (personality traits), cidade específica (specific city), income, education level
- **FR-006**: System MUST randomly apply visual filters with equal probability across the 9 avatars: no filter, B&W, sepia, warm, cold, or 3D movie character style
- **FR-007**: System MUST request backgrounds related to the person's profession, preferably with bokeh/defocused effect
- **FR-008**: System MUST request varied clothing colors, patterns, and accessories (glasses, earrings, hair accessories), occasionally profession-related
- **FR-009**: System MUST call OpenAI API using model "gpt-image-1-mini", size="1024x1024", quality="high"
- **FR-010**: System MUST split received 1024x1024 image into 9 equal squares (3 rows × 3 columns, each approximately 341x341 pixels)
- **FR-011**: System MUST save each split avatar image as `data/synths/avatar/{synth-id}.png` where synth-id is the 6-character ID
- **FR-012**: System MUST create `data/synths/avatar/` directory if it doesn't exist before saving images
- **FR-013**: System MUST handle cases where synth count is not a multiple of 9 by generating only the required number of avatars from the final block
- **FR-014**: System MUST provide clear error messages when OpenAI API calls fail (network errors, rate limits, authentication issues)
- **FR-015**: System MUST validate that required synth demographic fields exist before constructing image prompts

### Key Entities *(include if feature involves data)*

- **Avatar Image**: Visual representation of a synth, 341x341 PNG file stored with synth ID as filename, generated from 1024x1024 grid split
- **Avatar Block**: Group of 9 avatars generated in a single OpenAI API call via 3x3 grid image
- **Image Prompt**: Text instruction sent to OpenAI containing descriptions of 9 synths with visual characteristics (age, gender, ethnicity, profession) and styling directives (filters, backgrounds, clothing variety)
- **Synths Directory**: File system location `data/synths/` where synth data and avatars are stored
- **Avatar Directory**: File system location `data/synths/avatar/` where all avatar images are stored

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can generate avatar images for 9 synths in under 30 seconds per block (dependent on OpenAI API response time)
- **SC-002**: Generated avatars accurately reflect synth demographics (age range, gender, ethnicity) as verified by visual inspection
- **SC-003**: Avatar visual variety is achieved with at least 5 different filter styles distributed across generated batches
- **SC-004**: System successfully handles avatar generation for batches of 1-100 synths without failures
- **SC-005**: Avatar files are correctly mapped to synth IDs with 100% accuracy (no mismatched IDs)
- **SC-006**: System gracefully handles API failures with informative error messages and no data corruption

## Assumptions *(include if applicable)*

- **A-001**: OpenAI API credentials are configured and available in environment variables
- **A-002**: Users have sufficient OpenAI API quota/credits for image generation requests
- **A-003**: Image processing library (e.g., Pillow/PIL) is available for splitting 1024x1024 images into 9 parts
- **A-004**: File system has write permissions for `data/synths/avatar/` directory
- **A-005**: Synth generation (via `assemble_synth()`) already provides all necessary demographic fields
- **A-006**: Generated 1024x1024 images from OpenAI will consistently use a 3x3 grid layout as specified in the prompt
- **A-007**: Each grid cell in the 1024x1024 image will be centered and suitable for 341x341 extraction
- **A-008**: The OpenAI API "gpt-image-1-mini" model is suitable for generating diverse, realistic avatars with Brazilian demographics

## Out of Scope *(include if applicable)*

- Avatar regeneration with different styles for existing synths
- Custom avatar upload or manual avatar assignment
- Avatar editing or post-processing features
- Avatar validation to ensure demographic accuracy
- Caching or reuse of generated avatars
- Avatar generation for synths from external sources (non-gensynth created)
- Integration with other image generation services beyond OpenAI
- Avatar preview before saving
- Batch processing of existing synth databases to add avatars retroactively

## Dependencies *(include if applicable)*

- **D-001**: OpenAI Python SDK for API calls to image generation endpoint
- **D-002**: Image processing library (Pillow) for splitting 1024x1024 images into 9 parts
- **D-003**: Environment variable configuration for OpenAI API key
- **D-004**: Existing synth generation system (`gen_synth.py`, `synth_builder.py`) providing demographic data

## Open Questions *(include if unresolved)*

None - all clarifications resolved with reasonable defaults.
