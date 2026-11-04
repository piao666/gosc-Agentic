from __future__ import annotations

from dataclasses import dataclass
from string import Template
from typing import Any, Dict, List, Optional

from api_key_loader import get_api, get_model_name


@dataclass
class LlmMessage:
    """Simple container for a chat message."""

    content: str


class BaseAgent:
    """
    Minimal agent abstraction with per-agent system prompt and local memory.

    The implementation here is intentionally lightweight compared to the
    original project: memory is a plain list of message strings, and the
    actual LLM call is delegated to subclasses.
    """

    def __init__(self, name: str):
        self.name = name
        self.system_prompt: str = ""
        self.memory: List[LlmMessage] = []

    # --- lifecycle ---------------------------------------------------

    def init_system_prompt(self, template: str | Template, args: Dict[str, Any]) -> None:
        """Render and store the system prompt for this agent."""
        if isinstance(template, Template):
            self.system_prompt = template.safe_substitute(args)
        else:
            self.system_prompt = Template(template).safe_substitute(args)

    def add_memory(self, new_memory: str | LlmMessage) -> None:
        """Append a new utterance to the local memory."""
        if isinstance(new_memory, LlmMessage):
            self.memory.append(new_memory)
        else:
            self.memory.append(LlmMessage(content=str(new_memory)))

    def reset(self) -> None:
        """Clear the conversation state but keep the system prompt."""
        self.memory = []

    # --- interaction -------------------------------------------------

    def step(self) -> str:
        """
        Produce the next utterance for this agent.

        Subclasses should implement `_generate` and typically call `add_memory`
        before returning the content.
        """
        raise NotImplementedError


# class OpenAIAgent(BaseAgent):
#     """
#     Agent backed by an OpenAI-compatible chat completion endpoint.

#     All historical utterances (from both Alice and Bob) are fed back to the
#     model as `user` messages, while the system prompt encodes the role and
#     private context. This avoids depending on any custom chat_template logic.
#     """

#     def __init__(
#         self,
#         name: str,
#         model_key: str = "gemini_flash",
#         temperature: float = 0.0,
#         max_tokens: int = 1024,
#     ) -> None:
#         super().__init__(name=name)
#         self.model_key = model_key
#         self.model_name = get_model_name(model_key)
#         self.client = get_api(model_key)
#         self.temperature = float(temperature)
#         self.max_tokens = int(max_tokens)

#     def _build_messages(self) -> List[Dict[str, str]]:
#         """Convert system prompt + memory into OpenAI chat messages."""
#         if not self.system_prompt:
#             raise RuntimeError(f"System prompt for agent {self.name} is empty; call init_system_prompt() first.")

#         messages: List[Dict[str, str]] = [
#             {"role": "system", "content": self.system_prompt},
#         ]

#         for msg in self.memory:
#             # Treat all past utterances as user messages; we encode speaker
#             # identity directly in the text (e.g. 'Alice: ...', 'Bob: ...').
#             messages.append({"role": "user", "content": msg.content})

#         return messages

#     def step(self) -> str:
#         messages = self._build_messages()

#         resp = self.client.chat.completions.create(
#             model=self.model_name,
#             messages=messages,
#             temperature=self.temperature,
#             max_tokens=self.max_tokens,
#         )

#         content = resp.choices[0].message.content or ""
#         content = content.strip()

#         # Enforce the "Name: ..." prefix even if the model forgets.
#         if not content.startswith(f"{self.name}:"):
#             content = f"{self.name}: {content}"

#         self.add_memory(content)
#         return content

# gpt
class OpenAIAgent(BaseAgent):
    """
    Agent backed by an OpenAI-compatible chat completion endpoint.
    """

    def __init__(
        self,
        name: str,
        model_key: str = "gemini_flash",
        temperature: float = 0.0,
        max_tokens: int = 1024,
    ) -> None:
        super().__init__(name=name)
        self.model_key = model_key
        self.model_name = get_model_name(model_key)
        self.client = get_api(model_key)
        self.temperature = float(temperature)
        self.max_tokens = int(max_tokens)

    def _build_messages(self) -> List[Dict[str, str]]:
        """
        Convert system prompt + memory into OpenAI chat messages.
        
        Distinguishes between 'user' (partner) and 'assistant' (self)
        based on the message prefix.
        """
        if not self.system_prompt:
            raise RuntimeError(f"System prompt for agent {self.name} is empty; call init_system_prompt() first.")

        messages: List[Dict[str, str]] = [
            {"role": "system", "content": self.system_prompt},
        ]

        my_prefix = f"{self.name}:"

        for msg in self.memory:
            content = msg.content
            if content.strip().startswith(my_prefix):
                role = "assistant"
            else:
                role = "user"

            messages.append({"role": role, "content": content})

        return messages

    def step(self) -> str:
        messages = self._build_messages()

        resp = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )

        content = resp.choices[0].message.content or ""
        content = content.strip()

        # Enforce the "Name: ..." prefix even if the model forgets.
        if not content.startswith(f"{self.name}:"):
            content = f"{self.name}: {content}"

        self.add_memory(content)
        return content
