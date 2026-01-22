# Phase 0: Research & Technology Decisions

**Feature**: User Login with Google SSO and Access Control
**Date**: 2026-01-22
**Status**: Complete

## OAuth Library Selection (Backend)

### Decision
Use **Authlib** for Google OAuth 2.0 implementation

### Rationale
- Mature, actively maintained OAuth client library for Python
- Supports OAuth 2.0 and OpenID Connect protocols
- Integrates well with FastAPI via Starlette integration
- Provides both async and sync interfaces (we'll use async for FastAPI)
- Handles token validation, refresh tokens, and PKCE flow automatically
- Documentation: https://docs.authlib.org/en/latest/

### Alternatives Considered
1. **python-social-auth**: More heavyweight, designed for Django primarily
2. **httpx-oauth**: Lighter weight but less feature-complete, would require more manual implementation
3. **google-auth + google-auth-oauthlib**: Google's official library but more low-level, requires more boilerplate

### Implementation Notes
```python
# Example usage in FastAPI
from authlib.integrations.starlette_client import OAuth

oauth = OAuth()
oauth.register(
    name='google',
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)
```

## Session Management Strategy

### Decision
Use **JWT (JSON Web Tokens)** with HTTP-only cookies for session management

### Rationale
- Stateless authentication suitable for modern web applications
- No server-side session storage required (reduces infrastructure complexity)
- Works well with FastAPI middleware
- Secure when using HTTP-only cookies (prevents XSS attacks)
- Can include user claims (id, email, is_admin) in token payload
- python-jose library provides JOSE implementation for Python

### Alternatives Considered
1. **Server-side sessions with Redis**: More traditional but requires Redis infrastructure, adds operational complexity
2. **Database sessions**: Simple but requires DB query on every request, slower
3. **Starlette SessionMiddleware**: Uses cookie-based sessions but not as standardized as JWT

### Implementation Notes
```python
# JWT token creation
from jose import jwt
from datetime import datetime, timedelta

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=30))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")
```

### Security Considerations
- Store SECRET_KEY in environment variables
- Set cookie flags: httpOnly=True, secure=True (HTTPS only), sameSite='lax'
- Token expiration: 30 minutes for access token, 30 days for refresh token
- Implement token refresh mechanism

## Frontend OAuth Library

### Decision
Use **@react-oauth/google** for Google Sign-In button and OAuth flow

### Rationale
- Official React library from Google (maintained by Google)
- Simple integration with Google Identity Services
- Handles OAuth flow with minimal boilerplate
- TypeScript support built-in
- Provides both popup and redirect flows
- Documentation: https://www.npmjs.com/package/@react-oauth/google

### Alternatives Considered
1. **react-google-login**: Deprecated, uses older Google Sign-In platform
2. **Custom implementation with Google Identity Services**: More control but more code to maintain
3. **gapi-script**: Lower-level Google API client, more complex integration

### Implementation Notes
```tsx
import { GoogleOAuthProvider, GoogleLogin } from '@react-oauth/google';

<GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>
  <GoogleLogin
    onSuccess={(response) => handleLoginSuccess(response)}
    onError={() => handleLoginError()}
  />
</GoogleOAuthProvider>
```

## Database Schema Design

### Decision
Add new tables: `users`, `experiment_shares`, `synth_group_shares`

### Rationale
- Normalized design to avoid data duplication
- Separate sharing tables for flexibility (experiment and synth_group can be shared independently)
- Whitelist is NOT stored in database - managed via environment variable for simplicity
- Follows existing synth-lab database patterns

### Tables Overview

1. **users**
   - Primary key: `id` (UUID)
   - Unique: `google_user_id`, `email`
   - Indexes: `email`, `google_user_id`
   - Stores: email, display_name, profile_picture_url, created_at, updated_at

2. **experiment_shares**
   - Primary key: `id` (UUID)
   - Foreign keys: `experiment_id`, `user_id`
   - Composite unique: (`experiment_id`, `user_id`)
   - Includes `permission_level` (ENUM: 'viewer', 'editor')

3. **synth_group_shares**
   - Similar structure to experiment_shares
   - Foreign keys: `synth_group_id`, `user_id`

### Migration Strategy
- Single Alembic migration to create tables: users, experiment_shares, synth_group_shares
- Add `owner_id` foreign key to existing `experiments` and `synth_groups` tables
- Default existing experiments/synth_groups owner_id to NULL initially (requires manual assignment)

## Permission Check Strategy

### Decision
Implement **permission_service.py** with cached permission checks

### Rationale
- Centralized permission logic (DRY principle)
- Can be easily unit tested
- Performance: Cache user permissions in request context to avoid repeated DB queries
- Extensible for future role-based access control (RBAC)

### Implementation Pattern
```python
class PermissionService:
    async def can_access_experiment(self, user_id: UUID, experiment_id: UUID) -> bool:
        # Check if user is owner
        if experiment.owner_id == user_id:
            return True
        # Check if experiment is shared with user
        share = await share_repository.get_experiment_share(experiment_id, user_id)
        return share is not None

    async def can_edit_experiment(self, user_id: UUID, experiment_id: UUID) -> bool:
        # Similar but checks for 'editor' permission level
        ...
```

## Whitelist Management

### Decision
Store whitelist in environment variable `WHITELIST` (comma-separated list of emails and domains)

### Rationale
- Simple to configure via .env file (local) or Railway secrets (production)
- Secure: requires infrastructure access to modify
- No admin UI or database table needed - reduces complexity
- Changes require application restart (acceptable tradeoff for simplicity)
- Format: supports both exact emails (user@example.com) and domains (@example.com)

### Implementation
```python
# In config.py or infrastructure/auth/whitelist.py
WHITELIST = os.getenv("WHITELIST", "").split(",")

# Parse into emails and domains
whitelist_emails = [entry.strip() for entry in WHITELIST if not entry.startswith("@")]
whitelist_domains = [entry.strip() for entry in WHITELIST if entry.startswith("@")]

def is_whitelisted(email: str) -> bool:
    # Check exact email match
    if email in whitelist_emails:
        return True
    # Check domain match
    domain = "@" + email.split("@")[1]
    return domain in whitelist_domains
```

### Example Configuration
```bash
# .env.local
WHITELIST=user@example.com,admin@company.com,@company.com,@partner.org

# This allows:
# - user@example.com (exact match)
# - admin@company.com (exact match)
# - anyone@company.com (domain match)
# - anyone@partner.org (domain match)
```

## Whitelist Check Implementation

### Decision
Use **in-memory validation** with parsed whitelist from environment variable

### Rationale
- Fast validation - no database query needed
- Whitelist parsed once at application startup
- Simple string matching for exact emails, domain suffix matching for domains
- No additional database load on every authentication

### Implementation Details
- Whitelist loaded from WHITELIST env var at application startup
- Split into two lists: exact emails and domain patterns
- Validation is O(1) for email lookups (using set), O(n) for domain checks where n is number of domains
- For better performance, could use set for both and construct all possible patterns at startup

## CORS Configuration

### Decision
Configure CORS in FastAPI to allow frontend origin with credentials

### Rationale
- Frontend and backend run on different ports in development
- OAuth callback requires credentials (cookies) to be sent cross-origin
- Production will use same domain but CORS still needed for cookie handling

### Implementation
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Error Handling Strategy

### Decision
Custom exception classes with user-friendly messages

### Rationale
- Separate authentication errors from authorization errors
- Return appropriate HTTP status codes (401 vs 403)
- Provide clear error messages without exposing security details

### Exception Types
- `AuthenticationError` (401): Invalid or missing credentials
- `AuthorizationError` (403): Valid user but insufficient permissions
- `WhitelistError` (403): User not on whitelist
- `OAuthError` (500): Google OAuth failure

## Testing Strategy

### Decision
Three-tier testing: unit, integration, e2e

### Fast Tests (< 5s, run on every commit)
- Unit tests for permission logic (mocked repositories)
- Unit tests for whitelist validation (in-memory)
- Unit tests for JWT token creation/validation
- Unit tests for email/domain matching logic

### Slow Tests (run before PR)
- Integration tests with test database
- OAuth flow with mocked Google responses
- Full sharing workflows
- Whitelist validation with various email formats

### E2E Tests (run in CI)
- Browser-based login flow (Playwright/Selenium)
- End-to-end sharing workflow

## Security Best Practices

### Decisions Made
1. **HTTPS Only**: OAuth requires HTTPS, enforce in production
2. **CSRF Protection**: FastAPI CSRF middleware + sameSite cookie flag
3. **Rate Limiting**: Add rate limiting to /auth/login endpoint (prevent brute force)
4. **Input Validation**: Pydantic models for all API inputs
5. **SQL Injection Prevention**: SQLAlchemy ORM with parameterized queries
6. **XSS Prevention**: HTTP-only cookies, React's built-in XSS protection
7. **Secrets Management**: All secrets in environment variables, never committed

### Implementation Notes
```python
# Rate limiting example (using slowapi)
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/auth/callback")
@limiter.limit("5/minute")  # 5 attempts per minute
async def oauth_callback(...):
    ...
```

## Development Environment Setup

### Decision
Add Google OAuth credentials to .env.example with placeholder values

### Required Environment Variables
```bash
# Google OAuth
GOOGLE_CLIENT_ID=your_client_id_here.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_client_secret_here

# JWT
JWT_SECRET_KEY=generate_with_openssl_rand_hex_32
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=30

# Whitelist (comma-separated emails and domains)
WHITELIST=user@example.com,admin@company.com,@company.com,@partner.org

# CORS
FRONTEND_URL=http://localhost:5173
```

### Setup Documentation
- Add quickstart.md with Google Cloud Console setup instructions
- Document OAuth consent screen configuration
- Document redirect URI setup (http://localhost:8000/auth/callback)

## Dependency Additions

### Backend (pyproject.toml)
```toml
[project.dependencies]
authlib = "^1.3.0"
python-jose = "^3.3.0"
passlib = "^1.7.4"  # For future password hashing if needed
slowapi = "^0.1.9"  # Rate limiting
```

### Frontend (package.json)
```json
{
  "dependencies": {
    "@react-oauth/google": "^0.12.1"
  }
}
```

## Summary

All technology decisions have been made with the following priorities:
1. **Security**: OAuth best practices, JWT with HTTP-only cookies, CSRF protection
2. **Simplicity**: Leverage well-maintained libraries, avoid over-engineering
3. **Performance**: Stateless JWT, cached permission checks, indexed database queries
4. **Maintainability**: Follow existing synth-lab patterns, comprehensive testing strategy

No unresolved questions remain. Ready to proceed to Phase 1 (Design & Contracts).
