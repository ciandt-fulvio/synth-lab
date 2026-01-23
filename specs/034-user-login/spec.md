# Feature Specification: User Login with Google SSO and Access Control

**Feature Branch**: `034-user-login`
**Created**: 2026-01-22
**Status**: Draft
**Input**: User description: "034 user login criar login SSO / login social via GOOGLE cada experimento e synth_group deve pertencer a um usuário o usuário pode compartilhar o experimento e/ou o synth_group com outro usuário qdo tiver compartilhando o experimento, automaticamente compartilha também o synth_group dele deve ter uma whitelist que tem o email permitido e/ou o dominio permitido"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - First-time Login via Google (Priority: P1)

A new user visits the application and wants to access experiments. They click "Sign in with Google", are redirected to Google's authentication page, authorize the application, and are redirected back to the application where they can now create their first experiment.

**Why this priority**: This is the core authentication mechanism. Without it, users cannot access any features of the application. This is the absolute minimum viable functionality.

**Independent Test**: Can be fully tested by navigating to the login page, clicking the Google sign-in button, completing OAuth flow, and verifying the user is redirected to the main application with an authenticated session. Delivers immediate value by allowing users to access the platform.

**Acceptance Scenarios**:

1. **Given** a user is on the login page, **When** they click "Sign in with Google", **Then** they are redirected to Google's OAuth consent screen
2. **Given** a user completes Google authentication successfully, **When** they are redirected back to the application, **Then** their user account is created and they are logged in
3. **Given** a user's email is not on the whitelist, **When** they attempt to sign in with Google, **Then** they see an error message indicating they are not authorized to access the application
4. **Given** a user's email domain is on the whitelist, **When** they sign in with Google, **Then** they are granted access even if their specific email is not individually whitelisted

---

### User Story 2 - Create Owned Experiment (Priority: P1)

An authenticated user wants to create a new experiment. They navigate to the experiments page, click "Create Experiment", fill in the required details, and submit. The experiment is created and automatically assigned to them as the owner.

**Why this priority**: This is the first action users take after authentication and is essential for the platform's core value proposition. Without ownership, there's no basis for the sharing functionality.

**Independent Test**: Can be fully tested by logging in, creating an experiment, and verifying it appears in "My Experiments" list with the current user as owner. Delivers value by allowing users to start working with their own data.

**Acceptance Scenarios**:

1. **Given** an authenticated user is on the experiments page, **When** they create a new experiment, **Then** the experiment is automatically owned by that user
2. **Given** a user owns an experiment, **When** they view the experiment details, **Then** they can see they are listed as the owner
3. **Given** a user creates an experiment, **When** the experiment is created, **Then** any associated synth_group is automatically owned by the same user

---

### User Story 3 - Share Experiment with Another User (Priority: P2)

A user owns an experiment and wants to collaborate with a colleague. They navigate to the experiment's sharing settings, enter the colleague's email address, select the appropriate permission level, and click "Share". The colleague receives access to the experiment and its associated synth_group.

**Why this priority**: Sharing enables collaboration, which is important but not essential for initial MVP. Users can work independently before this feature is available.

**Independent Test**: Can be fully tested by creating an experiment as User A, sharing it with User B via email, then logging in as User B and verifying they can access the experiment. Delivers collaboration value.

**Acceptance Scenarios**:

1. **Given** a user owns an experiment, **When** they share it with another user's email, **Then** that user can access the experiment
2. **Given** a user shares an experiment, **When** the sharing is completed, **Then** the associated synth_group is automatically shared with the same permissions
3. **Given** a user has been granted access to an experiment, **When** they view the experiment, **Then** they can see their permission level (viewer, editor, etc.)
4. **Given** a user shares an experiment with someone not on the whitelist, **When** they attempt to add the collaborator, **Then** they see an error indicating the email must be on the whitelist

---

### User Story 4 - Share Synth Group Independently (Priority: P2)

A user owns a synth_group and wants to share it with another user without sharing a specific experiment. They navigate to the synth_group settings, enter the collaborator's email, and grant access. The collaborator can now use that synth_group in their own experiments.

**Why this priority**: This enables reusability of synth_groups across experiments and teams. Important for advanced collaboration but not essential for basic usage.

**Independent Test**: Can be fully tested by creating a synth_group as User A, sharing it with User B, then logging in as User B and verifying they can select that synth_group when creating a new experiment.

**Acceptance Scenarios**:

1. **Given** a user owns a synth_group, **When** they share it with another user, **Then** that user can access and use the synth_group
2. **Given** a user has access to a shared synth_group, **When** they create a new experiment, **Then** they can select the shared synth_group from the available options
3. **Given** a synth_group is shared independently, **When** a user views it, **Then** experiments associated with it are not automatically shared

---

### Edge Cases

- What happens when a user's Google account is deleted or access is revoked while they have an active session?
- What happens when a user tries to share with their own email address?
- How does the system handle concurrent access to the same experiment by multiple users?
- What happens when an experiment owner deletes their account but experiments are shared with others?
- How does the system handle whitelist checks when Google returns different email formats (capitalization, plus addressing)?
- What happens when a user has access to an experiment but the associated synth_group owner revokes their access to the synth_group?
- How does the system handle malformed whitelist entries in the environment variable?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST authenticate users exclusively via Google OAuth 2.0 SSO
- **FR-002**: System MUST create a user account automatically upon first successful Google authentication
- **FR-003**: System MUST check if the authenticated user's email or domain is on the whitelist before granting access
- **FR-004**: System MUST deny access to users whose email and domain are not on the whitelist, displaying a clear error message
- **FR-005**: System MUST support both individual email addresses and domain wildcards (e.g., "@company.com") in the whitelist, configured via WHITELIST environment variable (comma-separated values)
- **FR-006**: System MUST assign ownership of all created experiments to the creating user
- **FR-007**: System MUST assign ownership of all created synth_groups to the creating user
- **FR-008**: System MUST allow experiment owners to share their experiments with other whitelisted users
- **FR-009**: System MUST automatically share the associated synth_group when an experiment is shared
- **FR-010**: System MUST allow synth_group owners to share their synth_groups independently of experiments
- **FR-011**: System MUST prevent sharing with users who are not on the whitelist
- **FR-012**: System MUST maintain a clear distinction between owner and shared-with permissions
- **FR-013**: System MUST persist user identity across sessions using secure session management
- **FR-014**: System MUST log all authentication attempts (successful and failed) for security auditing
- **FR-015**: System MUST handle Google OAuth errors gracefully with user-friendly error messages
- **FR-016**: Users MUST be able to view all experiments they own or have been granted access to
- **FR-017**: Users MUST be able to view all synth_groups they own or have been granted access to
- **FR-018**: System MUST display ownership and sharing information for experiments and synth_groups
- **FR-019**: System MUST allow owners to revoke shared access to their experiments. When experiment access is revoked, synth_group access remains unchanged (synth_group access must be revoked separately if desired)
- **FR-020**: System MUST prevent users from accessing experiments or synth_groups they do not own and have not been granted access to
- **FR-021**: System MUST allow owners to revoke shared access to their synth_groups independently of experiment access

### Key Entities *(include if feature involves data)*

- **User**: Represents an authenticated person using the application. Key attributes include Google user ID, email address, display name, profile picture URL, and authentication timestamps. Each user is uniquely identified by their Google user ID.

- **Experiment**: Represents a scientific experiment created by a user. Key attributes include title, description, creation timestamp, and owner. Each experiment belongs to exactly one owner (User) but can be shared with multiple users.

- **SynthGroup**: Represents a synthetic data group used in experiments. Key attributes include name, configuration, and owner. Each synth_group belongs to exactly one owner (User) but can be shared with multiple users.

- **ExperimentShare**: Represents a sharing relationship between an experiment and a user. Key attributes include the experiment, the user being granted access, permission level (viewer, editor), and the timestamp when access was granted.

- **SynthGroupShare**: Represents a sharing relationship between a synth_group and a user. Key attributes include the synth_group, the user being granted access, permission level, and grant timestamp.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can complete the Google sign-in flow and access the application in under 30 seconds
- **SC-002**: 95% of authentication attempts for whitelisted users succeed on the first try
- **SC-003**: Users can share an experiment with a collaborator in under 1 minute
- **SC-004**: Unauthorized access attempts (non-whitelisted users) are blocked 100% of the time
- **SC-005**: Users can view all their owned and shared experiments in a single list
- **SC-006**: Shared collaborators can access an experiment within 5 seconds of being granted access
- **SC-007**: Zero data leakage - users cannot access experiments or synth_groups they don't own or haven't been granted access to

## Assumptions

- Users have existing Google accounts they want to use for authentication
- The application has been registered with Google Cloud Console and has valid OAuth 2.0 credentials
- Whitelist is managed via WHITELIST environment variable (comma-separated emails and domains)
- Whitelist changes require application restart to take effect
- Session duration follows industry standards (e.g., 30-day remember-me, 1-day default session)
- Permission levels for sharing include at minimum "view" and "edit" capabilities
- Google OAuth returns consistent email addresses for the same user across sessions
- Local development uses .env files, production uses Railway secrets for environment variables

## Dependencies

- Google OAuth 2.0 API availability and uptime
- Valid Google Cloud Platform project with OAuth consent screen configured
- Ability to store and verify OAuth tokens securely
- Database schema supports user ownership and many-to-many sharing relationships

## Out of Scope

- Integration with other OAuth providers (Facebook, GitHub, etc.) - only Google SSO
- Role-based access control beyond owner/shared distinction (e.g., admin, moderator roles)
- User profile management and settings (beyond basic Google profile info)
- Email notifications when experiments are shared
- Activity logs showing who accessed what and when (audit trails)
- Two-factor authentication in addition to Google SSO
- Password-based authentication as a fallback option
- User registration/invitation workflow - access is controlled solely by whitelist
- Admin interface for whitelist management - whitelist is managed via environment variables only
