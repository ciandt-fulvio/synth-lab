"""
Infrastructure layer for synth-lab.

Contains cross-cutting concerns:
- config: Environment configuration
- database_v2: PostgreSQL connection management via SQLAlchemy
- llm_client: Centralized OpenAI client with retry logic
- phoenix_tracing: Observability and tracing setup
"""
