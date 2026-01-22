# Data Model: Docker Containerization

**Feature**: 033-docker-containerization
**Date**: 2026-01-20

## Overview

Este feature não introduz mudanças no data model do banco de dados. A containerização é puramente infraestrutura de deployment que empacota o sistema existente.

## Entidades Afetadas

Nenhuma entidade de banco de dados é criada ou modificada.

## Migrations

Nenhuma migration necessária. O sistema de migrations existente (Alembic) continuará funcionando normalmente em todos os ambientes (dev, test, prod).

## Configuration Entities

Embora não sejam entidades de banco de dados, os seguintes "configuration artifacts" são introduzidos:

### Docker Compose Services

| Service | Profile | Purpose |
|---------|---------|---------|
| postgres | - (sempre inicia) | Banco PostgreSQL compartilhado |
| backend-dev | dev | Backend com hot reload |
| frontend-dev | dev | Frontend com HMR |
| backend-test | test | Backend com imagem de produção |
| frontend-test | test | Frontend com imagem de produção |
| postgres-test | test | PostgreSQL isolado para testes |

### Environment Configuration

| File | Purpose |
|------|---------|
| `.env.docker.dev` | Variáveis para ambiente de desenvolvimento |
| `.env.docker.test` | Variáveis para ambiente de testes |

## Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    Docker Network                               │
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │   Frontend   │───▶│   Backend    │───▶│  PostgreSQL  │      │
│  │   :8080      │    │   :8000      │    │   :5432      │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌──────────────┐
                    │    Host      │
                    │  localhost   │
                    └──────────────┘
```

## Notes

- O PostgreSQL usa volume persistente em desenvolvimento, volume efêmero em testes
- Todas as migrações Alembic executam no startup do container backend
- O seeding de dados de teste ocorre apenas no profile `test`
