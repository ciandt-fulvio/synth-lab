"""
Infrastructure layer for synth-lab.

Contains cross-cutting concerns:
- config: Environment configuration
- database: SQLite connection management
- llm_client: Centralized OpenAI client with retry logic
"""
