# CI/CD Pipeline Documentation

## Overview

This project uses a "Build Once, Deploy Anywhere" CI/CD strategy. Docker images are built once and promoted through environments, ensuring identical deployments across staging and production.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              LOCAL (pre-commit)                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Git pre-commit hook        → Smoke, contract, schema tests (~30s)          │
│                                                                             │
│  Runs automatically on every commit. Blocks commit if tests fail.           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ Push to remote + Open PR
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              PULL REQUEST                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. tests-pr.yml            → Unit & integration tests (excl. smoke/etc)    │
│  2. tests-e2e.yml           → Build images → Push to GHCR → E2E tests       │
│                                                                             │
│  Images tagged: ghcr.io/<owner>/synth-lab-api:pr-<number>                  │
│                 ghcr.io/<owner>/synth-lab-frontend:pr-<number>             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ Merge to main
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              STAGING DEPLOY                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  deploy-staging.yml:                                                        │
│  1. Build images → Push to GHCR (tagged: <sha>, staging)                   │
│  2. Reset staging database                                                  │
│  3. Run migrations                                                          │
│  4. Seed database                                                           │
│  5. Deploy images to Railway staging                                        │
│  6. Run smoke tests                                                         │
│  7. Tag images as :staging-verified                                         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ Manual trigger
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            PRODUCTION DEPLOY                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  deploy.yml (manual):                                                       │
│  1. Verify :staging-verified images exist                                   │
│  2. Run migrations on production DB                                         │
│  3. Deploy SAME images to Railway production                                │
│  4. Run smoke tests                                                         │
│  5. Tag images as :production, :latest                                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Image Tags

| Tag | Description | When Created |
|-----|-------------|--------------|
| `pr-<number>` | PR-specific image for E2E testing | On PR |
| `<sha>` | Commit SHA, immutable reference | On merge to main |
| `staging` | Latest staging deployment | On merge to main |
| `staging-verified` | Passed staging smoke tests | After staging deploy |
| `production` | Current production deployment | After production deploy |
| `latest` | Alias for production | After production deploy |

## Workflows

### Pre-commit Hook (Local)
- **Trigger**: Every commit (local git hook)
- **Duration**: ~30 seconds
- **Tests**: smoke, contract, schema
- **Purpose**: Fast feedback before code leaves your machine
- **Bypass**: `git commit --no-verify` (not recommended)

### tests-pr.yml
- **Trigger**: Pull requests to main
- **Duration**: ~5 minutes
- **Tests**: Unit and integration tests (excluding smoke/contract/schema)
- **Purpose**: Validate business logic and integrations

### tests-e2e.yml
- **Trigger**: Pull requests to main
- **Duration**: ~15 minutes
- **Process**:
  1. Build backend and frontend images
  2. Push to GHCR with `pr-<number>` tag
  3. Start docker-compose with pre-built images
  4. Run Playwright E2E tests
- **Purpose**: Validate full stack integration

### deploy-staging.yml
- **Trigger**: Push to main (automatic)
- **Duration**: ~10-15 minutes
- **Process**:
  1. Build and push images to GHCR
  2. Reset, migrate, and seed staging database
  3. Deploy images to Railway via API
  4. Run smoke tests
  5. Tag as `staging-verified`
- **Purpose**: Deploy and validate on staging

### deploy.yml
- **Trigger**: Manual (workflow_dispatch)
- **Duration**: ~5-10 minutes
- **Process**:
  1. Verify `staging-verified` images exist
  2. Run production migrations
  3. Deploy same images to production
  4. Run smoke tests
  5. Tag as `production` and `latest`
- **Purpose**: Promote to production

## Railway Setup

### Initial Configuration (One-time)

Railway services must be configured to accept Docker images from GHCR:

1. **Go to Railway Dashboard** → Project → Service (synth-lab-api or synth-lab-frontend)

2. **Change Source to Docker Image**:
   - Click on "Settings" tab
   - Under "Source", select "Docker Image"
   - Enter initial image URL:
     ```
     ghcr.io/<owner>/synth-lab-api:staging
     ```
   - For frontend:
     ```
     ghcr.io/<owner>/synth-lab-frontend:staging
     ```

3. **Configure Registry Credentials** (if repo is private):
   - In "Docker Image" settings, add credentials:
     - Registry: `ghcr.io`
     - Username: Your GitHub username
     - Password: GitHub Personal Access Token (PAT) with `read:packages` scope

4. **Repeat for both environments** (staging and production)

### Required Secrets

Add these secrets to GitHub repository settings:

| Secret | Description |
|--------|-------------|
| `RAILWAY_API_TOKEN` | Railway API token with deploy permissions |
| `RAILWAY_PROJECT_ID` | Railway project ID |
| `DATABASE_STAGING_URL` | PostgreSQL connection string for staging |
| `DATABASE_PRODUCTION_URL` | PostgreSQL connection string for production |
| `OPENAI_API_KEY` | OpenAI API key for LLM features |

### Required Variables

Add these variables to GitHub repository settings:

| Variable | Description | Example |
|----------|-------------|---------|
| `STAGING_FRONTEND_URL` | Staging frontend URL | `https://synth-lab-frontend-staging.up.railway.app` |
| `STAGING_BACKEND_URL` | Staging backend URL | `https://synth-lab-api-staging.up.railway.app` |

## Local Development

### Running E2E Tests Locally

```bash
# Option 1: Build and test locally
make test-e2e

# Option 2: Use pre-built images from GHCR
BACKEND_IMAGE=ghcr.io/<owner>/synth-lab-api:staging \
FRONTEND_IMAGE=ghcr.io/<owner>/synth-lab-frontend:staging \
docker compose -f docker-compose.e2e.yml up -d

cd frontend && TEST_ENV=docker npm run test:e2e
```

### Running Smoke Tests Against Deployed Environments

```bash
# Against staging
make test-smoke-staging

# Against production
make test-smoke-production
```

## Troubleshooting

### Images not pulling from GHCR

1. Verify the image exists:
   ```bash
   docker pull ghcr.io/<owner>/synth-lab-api:staging
   ```

2. Check GitHub Packages visibility:
   - Go to GitHub → Packages → synth-lab-api
   - Ensure visibility matches your needs (public/private)

3. If private, ensure Railway has valid credentials

### Railway deploy fails

1. Check Railway API token has correct permissions
2. Verify service names match exactly:
   - `synth-lab-api`
   - `synth-lab-frontend`
3. Check environment names match: `staging`, `production`

### E2E tests fail in CI

1. Check docker-compose logs:
   - Download artifacts → docker-compose-logs
2. Verify frontend can reach backend:
   - Frontend at `http://localhost:8091`
   - Backend at `http://localhost:8001`
3. Check OPENAI_API_KEY is set in secrets

## Benefits of This Architecture

1. **Reproducibility**: Same image in all environments
2. **Speed**: No rebuild for production deploy
3. **Confidence**: What you test is what you deploy
4. **Rollback**: Easy to deploy previous image tags
5. **Auditability**: Image digests provide immutable references
