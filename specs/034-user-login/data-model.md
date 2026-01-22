# Data Model: User Login with Google SSO and Access Control

**Feature**: 034-user-login
**Date**: 2026-01-22
**Status**: Complete

## Overview

This document defines the data entities, relationships, and validation rules for user authentication and access control. The model supports Google OAuth authentication, user ownership of experiments and synth_groups, and flexible sharing with permission levels.

## Entities

### User

Represents an authenticated user who has successfully logged in via Google OAuth.

**Attributes**:
- `id` (UUID, PK): Unique identifier
- `google_user_id` (String, Unique, Not Null): Google's unique user identifier (sub claim from JWT)
- `email` (String, Unique, Not Null): User's email from Google account
- `display_name` (String, Nullable): User's full name from Google profile
- `profile_picture_url` (String, Nullable): URL to user's Google profile picture
- `created_at` (DateTime, Not Null): When user first logged in
- `updated_at` (DateTime, Not Null): Last profile update from Google

**Validation Rules**:
- `google_user_id` must be unique across all users
- `email` must be unique and valid email format
- `email` must match whitelist (checked at login, not stored in DB)
- `created_at` and `updated_at` automatically managed

**Indexes**:
- Primary key on `id`
- Unique index on `google_user_id`
- Unique index on `email`

**Relationships**:
- One-to-Many with Experiment (as owner)
- One-to-Many with SynthGroup (as owner)
- One-to-Many with ExperimentShare (as shared user)
- One-to-Many with SynthGroupShare (as shared user)

**State Transitions**:
- Created: When user first authenticates via Google OAuth
- Updated: When user logs in again and profile info has changed in Google

---

### ExperimentShare

Represents a sharing relationship where an experiment owner grants access to another user.

**Attributes**:
- `id` (UUID, PK): Unique identifier
- `experiment_id` (UUID, FK to experiments.id, Not Null): The experiment being shared
- `user_id` (UUID, FK to users.id, Not Null): The user receiving access
- `permission_level` (ENUM, Not Null): Level of access granted ('viewer', 'editor')
- `granted_at` (DateTime, Not Null): When access was granted
- `granted_by_id` (UUID, FK to users.id, Not Null): User who granted access (typically the owner)

**Validation Rules**:
- (`experiment_id`, `user_id`) must be unique (user can only have one permission level per experiment)
- `user_id` cannot be the same as experiment's `owner_id` (owners have implicit full access)
- `permission_level` must be one of: 'viewer', 'editor'
- `user_id` must reference an existing user
- `experiment_id` must reference an existing experiment
- User being shared with must be whitelisted (checked at share time)

**Indexes**:
- Primary key on `id`
- Unique composite index on (`experiment_id`, `user_id`)
- Index on `user_id` for efficient "my shared experiments" queries

**Relationships**:
- Many-to-One with Experiment (experiment_id)
- Many-to-One with User (user_id)
- Many-to-One with User (granted_by_id)

**State Transitions**:
- Created: When owner shares experiment with another user
- Deleted: When owner revokes access

---

### SynthGroupShare

Represents a sharing relationship where a synth_group owner grants access to another user.

**Attributes**:
- `id` (UUID, PK): Unique identifier
- `synth_group_id` (UUID, FK to synth_groups.id, Not Null): The synth_group being shared
- `user_id` (UUID, FK to users.id, Not Null): The user receiving access
- `permission_level` (ENUM, Not Null): Level of access granted ('viewer', 'editor')
- `granted_at` (DateTime, Not Null): When access was granted
- `granted_by_id` (UUID, FK to users.id, Not Null): User who granted access (typically the owner)

**Validation Rules**:
- (`synth_group_id`, `user_id`) must be unique
- `user_id` cannot be the same as synth_group's `owner_id`
- `permission_level` must be one of: 'viewer', 'editor'
- `user_id` must reference an existing user
- `synth_group_id` must reference an existing synth_group
- User being shared with must be whitelisted (checked at share time)

**Indexes**:
- Primary key on `id`
- Unique composite index on (`synth_group_id`, `user_id`)
- Index on `user_id` for efficient "my shared synth_groups" queries

**Relationships**:
- Many-to-One with SynthGroup (synth_group_id)
- Many-to-One with User (user_id)
- Many-to-One with User (granted_by_id)

**State Transitions**:
- Created: When owner shares synth_group with another user (explicitly or via experiment share)
- Deleted: When owner revokes access

---

## Modified Existing Entities

### Experiment (Modification)

**New Attributes**:
- `owner_id` (UUID, FK to users.id, Nullable): User who owns this experiment

**Migration Notes**:
- Add `owner_id` column as nullable
- Existing experiments will have `owner_id = NULL` initially
- Create manual data migration script to assign owners (if needed)
- Consider adding `NOT NULL` constraint after data migration

**New Relationships**:
- Many-to-One with User (as owner)
- One-to-Many with ExperimentShare

---

### SynthGroup (Modification)

**New Attributes**:
- `owner_id` (UUID, FK to users.id, Nullable): User who owns this synth_group

**Migration Notes**:
- Same migration strategy as Experiment
- Add `owner_id` column as nullable
- Assign owners via manual script if needed

**New Relationships**:
- Many-to-One with User (as owner)
- One-to-Many with SynthGroupShare

---

## Enumerations

### PermissionLevel

Defines the level of access a user has to a shared resource.

**Values**:
- `viewer`: Read-only access (can view but not modify)
- `editor`: Read-write access (can view and modify)

**Usage**:
- Used in `ExperimentShare.permission_level`
- Used in `SynthGroupShare.permission_level`

**Future Extensibility**:
- Could add 'admin' level for delegation of sharing permissions
- Could add 'commenter' level for intermediate permission

---

## Relationships Diagram

```
User
├─ owns ────────> Experiment (1:N)
├─ owns ────────> SynthGroup (1:N)
├─ shared with ─> ExperimentShare (1:N via user_id)
├─ shared with ─> SynthGroupShare (1:N via user_id)
├─ granted ─────> ExperimentShare (1:N via granted_by_id)
└─ granted ─────> SynthGroupShare (1:N via granted_by_id)

Experiment
├─ owned by ───> User (N:1 via owner_id)
└─ shares ─────> ExperimentShare (1:N)

SynthGroup
├─ owned by ───> User (N:1 via owner_id)
└─ shares ─────> SynthGroupShare (1:N)

ExperimentShare
├─ references ─> Experiment (N:1)
├─ granted to ─> User (N:1 via user_id)
└─ granted by ─> User (N:1 via granted_by_id)

SynthGroupShare
├─ references ─> SynthGroup (N:1)
├─ granted to ─> User (N:1 via user_id)
└─ granted by ─> User (N:1 via granted_by_id)
```

---

## Business Rules

### Authentication
1. User must authenticate via Google OAuth 2.0
2. User's email must match WHITELIST environment variable (exact match or domain match)
3. User account is created automatically on first successful login
4. User profile is updated from Google on each login

### Ownership
1. Every new experiment must have an owner (the creating user)
2. Every new synth_group must have an owner (the creating user)
3. Owner has implicit full access (no need for ExperimentShare/SynthGroupShare record)
4. Ownership cannot be transferred (future feature)

### Sharing
1. Only owners can share their experiments/synth_groups
2. Sharing an experiment automatically shares its associated synth_group
3. Revoking experiment access does NOT revoke synth_group access
4. Cannot share with yourself (owner already has access)
5. Can only share with whitelisted users
6. Same user cannot have multiple permission levels for the same resource
7. Permission levels: viewer (read-only), editor (read-write)

### Access Control
1. User can access experiment if:
   - They own it (owner_id matches)
   - OR they have an ExperimentShare record
2. User can access synth_group if:
   - They own it (owner_id matches)
   - OR they have a SynthGroupShare record
3. Access checks must verify both ownership and sharing tables

---

## Query Patterns

### Get User's Experiments (Owned + Shared)
```sql
-- Owned experiments
SELECT * FROM experiments WHERE owner_id = :user_id
UNION
-- Shared experiments
SELECT e.* FROM experiments e
INNER JOIN experiment_shares es ON e.id = es.experiment_id
WHERE es.user_id = :user_id
```

### Check Experiment Access
```python
# Pseudocode
async def can_access_experiment(user_id, experiment_id):
    experiment = await get_experiment(experiment_id)
    if experiment.owner_id == user_id:
        return True
    share = await get_experiment_share(experiment_id, user_id)
    return share is not None
```

### Check Edit Permission
```python
async def can_edit_experiment(user_id, experiment_id):
    experiment = await get_experiment(experiment_id)
    if experiment.owner_id == user_id:
        return True  # Owner can always edit
    share = await get_experiment_share(experiment_id, user_id)
    return share and share.permission_level == 'editor'
```

### Share Experiment (with automatic synth_group sharing)
```python
async def share_experiment(experiment_id, with_user_id, permission_level, by_user_id):
    # Validate user is whitelisted
    user = await get_user(with_user_id)
    if not is_whitelisted(user.email):
        raise ValidationError("User not whitelisted")

    # Create experiment share
    exp_share = ExperimentShare(
        experiment_id=experiment_id,
        user_id=with_user_id,
        permission_level=permission_level,
        granted_by_id=by_user_id
    )
    await save(exp_share)

    # Automatically share associated synth_group
    experiment = await get_experiment(experiment_id)
    if experiment.synth_group_id:
        sg_share = SynthGroupShare(
            synth_group_id=experiment.synth_group_id,
            user_id=with_user_id,
            permission_level=permission_level,
            granted_by_id=by_user_id
        )
        await save(sg_share)
```

---

## Migration Checklist

- [ ] Create `users` table with indexes
- [ ] Create `experiment_shares` table with indexes
- [ ] Create `synth_group_shares` table with indexes
- [ ] Create `PermissionLevel` enum type
- [ ] Add `owner_id` to `experiments` table (nullable)
- [ ] Add `owner_id` to `synth_groups` table (nullable)
- [ ] Create foreign key constraints
- [ ] Test rollback capability

---

## Data Integrity Constraints

### Database Constraints
- NOT NULL on required fields
- UNIQUE constraints on email, google_user_id, composite keys
- FOREIGN KEY constraints with CASCADE on delete for shares
- CHECK constraints on ENUM values

### Application-Level Validation
- Email format validation (Pydantic)
- Whitelist validation (not in DB, checked at runtime)
- Permission level validation
- Owner cannot share with themselves
- User must exist before sharing

---

## Performance Considerations

1. **Indexes**: All foreign keys and frequently queried columns indexed
2. **Composite Queries**: Use JOINs for "my experiments" queries
3. **Caching**: Consider caching user permissions in request context
4. **Query Optimization**: Use SELECT only needed columns, not `SELECT *`
5. **Pagination**: Implement pagination for list queries (experiments, shares)

---

## Security Considerations

1. **Data at Rest**: Standard PostgreSQL encryption
2. **Access Control**: All queries must include user_id check
3. **Audit Trail**: `granted_at` and `granted_by_id` provide basic audit
4. **Cascade Delete**: Deleting user cascades to their shares (configurable)
5. **Input Validation**: All user inputs validated via Pydantic models

---

## Future Enhancements

- Add `deleted_at` for soft deletes
- Add `last_accessed_at` for access tracking
- Add audit log table for all permission changes
- Support ownership transfer
- Support group-based permissions (teams/organizations)
- Add `permission_level = 'admin'` for delegated sharing rights
- Add notification records for share events
