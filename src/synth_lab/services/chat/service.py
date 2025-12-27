"""
Chat service for synth conversation after interview.

Generates contextual responses from synths using their persona
and interview history as context.

References:
    - LLM Client: src/synth_lab/infrastructure/llm_client.py
    - Research Repository: src/synth_lab/repositories/research_repository.py
    - Architecture: docs/arquitetura.md (LLM calls must use Phoenix tracing)
"""

from datetime import datetime

from loguru import logger

from synth_lab.infrastructure.llm_client import get_llm_client
from synth_lab.infrastructure.phoenix_tracing import get_tracer
from synth_lab.models.chat import ChatRequest, ChatResponse
from synth_lab.repositories.research_repository import ResearchRepository
from synth_lab.repositories.synth_repository import SynthRepository
from synth_lab.services.chat.instructions import format_chat_instructions

# Phoenix/OpenTelemetry tracer for observability
_tracer = get_tracer("chat-service")


class ChatService:
    """Service for generating synth chat responses."""

    def __init__(self):
        """Initialize chat service with dependencies."""
        self.llm_client = get_llm_client()
        self.research_repo = ResearchRepository()
        self.synths_repo = SynthRepository()
        self.logger = logger.bind(component="chat_service")

    def _build_messages(self, synth_id: str, request: ChatRequest) -> tuple[list[dict], str]:
        """
        Build LLM messages with synth context.

        Args:
            synth_id: ID of the synth to chat with.
            request: Chat request with message and history.

        Returns:
            Tuple of (messages list, synth first name).
        """
        # Load synth profile
        synth = self.synths_repo.get_by_id(synth_id)
        synth_first_name = synth.nome.split()[0] if synth.nome else "Synth"

        # Load interview transcript
        transcript = self.research_repo.get_transcript(request.exec_id, synth_id)

        # Format interview history for context
        interview_history = self._format_transcript(transcript)

        # Build system prompt
        system_prompt = format_chat_instructions(
            synth_name=synth.nome,
            synth_age=synth.demografia.idade if synth.demografia else None,
            synth_profile=self._format_synth_profile(synth),
            interview_history=interview_history,
        )

        # Build messages for LLM
        messages = [
            {"role": "system", "content": system_prompt},
        ]

        # Add chat history as alternating user/assistant messages
        for msg in request.chat_history:
            role = "user" if msg.role == "user" else "assistant"
            messages.append({"role": role, "content": msg.content})

        # Add current message
        messages.append({"role": "user", "content": request.message})

        return messages, synth_first_name

    def generate_response(self, synth_id: str, request: ChatRequest) -> ChatResponse:
        """
        Generate a response from the synth.

        Args:
            synth_id: ID of the synth to chat with.
            request: Chat request with message and history.

        Returns:
            ChatResponse with synth's message.
        """
        self.logger.info(
            f"Generating chat response for synth {synth_id}, exec {request.exec_id}"
        )

        messages, synth_name = self._build_messages(synth_id, request)

        # Generate response with Phoenix tracing
        with _tracer.start_as_current_span(
            "ChatService: generate_response",
            attributes={
                "synth_id": synth_id,
                "synth_name": synth_name,
                "exec_id": request.exec_id,
            },
        ):
            response_text = self.llm_client.complete(
                messages=messages,
                temperature=0.8,
                operation_name=f"ChatCompl with {synth_name}",
            )

        self.logger.info(f"Generated response: {len(response_text)} chars")

        return ChatResponse(
            message=response_text,
            timestamp=datetime.now(),
        )

    def generate_response_stream(self, synth_id: str, request: ChatRequest):
        """
        Generate a streaming response from the synth.

        Args:
            synth_id: ID of the synth to chat with.
            request: Chat request with message and history.

        Yields:
            str: Chunks of the response text.
        """
        self.logger.info(
            f"Generating streaming chat response for synth {synth_id}, exec {request.exec_id}"
        )

        messages, synth_name = self._build_messages(synth_id, request)

        # Generate streaming response with Phoenix tracing
        with _tracer.start_as_current_span(
            "ChatService: generate_response_stream",
            attributes={
                "synth_id": synth_id,
                "synth_name": synth_name,
                "exec_id": request.exec_id,
            },
        ):
            for chunk in self.llm_client.complete_stream(
                messages=messages,
                temperature=0.8,
                operation_name=f"ChatCompl with {synth_name}",
            ):
                yield chunk

    def _format_transcript(self, transcript) -> str:
        """Format transcript messages for context."""
        lines = []
        for msg in transcript.messages:
            speaker = "Entrevistador" if msg.speaker == "Interviewer" else "Você"
            lines.append(f"{speaker}: {msg.text}")
        return "\n".join(lines)

    def _format_chat_history(self, history: list) -> str:
        """Format chat history for context."""
        if not history:
            return ""
        lines = []
        for msg in history:
            speaker = "Usuário" if msg.role == "user" else "Você"
            lines.append(f"{speaker}: {msg.content}")
        return "\n".join(lines)

    def _format_synth_profile(self, synth) -> str:
        """Format synth profile for context."""
        parts = []

        parts.append(f"Nome: {synth.nome}")

        if synth.descricao:
            parts.append(f"Descrição: {synth.descricao}")

        if synth.demografia:
            demo = synth.demografia
            if demo.idade:
                parts.append(f"Idade: {demo.idade} anos")
            if demo.genero_biologico:
                parts.append(f"Gênero: {demo.genero_biologico}")
            if demo.ocupacao:
                parts.append(f"Ocupação: {demo.ocupacao}")
            if demo.escolaridade:
                parts.append(f"Escolaridade: {demo.escolaridade}")
            if demo.estado_civil:
                parts.append(f"Estado civil: {demo.estado_civil}")
            if demo.localizacao:
                loc = demo.localizacao
                if loc.cidade and loc.estado:
                    parts.append(f"Localização: {loc.cidade}, {loc.estado}")

        if synth.psicografia:
            psico = synth.psicografia
            if psico.interesses:
                parts.append(f"Interesses: {', '.join(psico.interesses[:5])}")
            if psico.personalidade_big_five:
                bf = psico.personalidade_big_five
                traits = []
                if bf.abertura and bf.abertura > 70:
                    traits.append("criativo e curioso")
                if bf.conscienciosidade and bf.conscienciosidade > 70:
                    traits.append("organizado e responsável")
                if bf.extroversao and bf.extroversao > 70:
                    traits.append("extrovertido e sociável")
                if bf.amabilidade and bf.amabilidade > 70:
                    traits.append("amável e cooperativo")
                if bf.neuroticismo and bf.neuroticismo > 70:
                    traits.append("sensível e emotivo")
                if traits:
                    parts.append(f"Personalidade: {', '.join(traits)}")

        return "\n".join(parts)
