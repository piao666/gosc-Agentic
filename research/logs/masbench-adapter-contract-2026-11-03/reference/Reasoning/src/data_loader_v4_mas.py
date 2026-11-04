from __future__ import annotations

import json
import os
import random
from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Optional, Tuple

Mode = Literal["support", "context"]


@dataclass
class Sample:
    """Single QA item with asymmetric views for two agents."""

    question: str
    answer: str
    context_first: str
    context_second: str
    item_id: int | str
    level: str
    raw: Dict[str, Any]


class V4MasDataLoader:
    """
    Lightweight loader for the released asymmetric reasoning dataset.

    It exposes a HotpotQA-style interface:

        question, answer, context_first, context_second = dataloader.sample_once()

    The `mode` flag controls what each agent sees:
    - "support": only agent-specific supporting facts, no extra distractors.
    - "context": full agent-specific context blocks (may include distractors).
    """

    def __init__(self, data_path: str, mode: Mode = "context", seed: Optional[int] = None):
        if mode not in ("support", "context"):
            raise ValueError(f"mode must be 'support' or 'context', got {mode!r}")

        if not os.path.exists(data_path):
            raise FileNotFoundError(f"Dataset not found: {data_path}")

        self.data_path = data_path
        self.mode: Mode = mode
        self.rng = random.Random(seed)

        with open(data_path, "r", encoding="utf-8") as f:
            self._items: List[Dict[str, Any]] = json.load(f)

        if not isinstance(self._items, list):
            raise ValueError(f"Expected list at root of {data_path}, got {type(self._items).__name__}")

    def __len__(self) -> int:
        return len(self._items)

    # ---- public API -------------------------------------------------

    def sample_once(self, index: Optional[int] = None) -> Tuple[str, str, str, str]:
        """
        Return (question, answer, context_first, context_second).

        If `index` is None, a random item is sampled with the loader RNG.
        """
        sample = self.sample(index)
        return sample.question, sample.answer, sample.context_first, sample.context_second

    def sample(self, index: Optional[int] = None) -> Sample:
        """Return a structured Sample for easier inspection."""
        if len(self._items) == 0:
            raise RuntimeError(f"No items loaded from {self.data_path}")

        if index is None:
            index = self.rng.randrange(len(self._items))
        if not 0 <= index < len(self._items):
            raise IndexError(f"Index {index} out of range for dataset of size {len(self._items)}")

        item = self._items[index]

        question = item.get("question", "")
        answer = item.get("answer", "")
        level = item.get("level", "")
        item_id = item.get("id", index)

        if self.mode == "support":
            ctx_first = self._build_support_for_agent(item, "agent_a")
            ctx_second = self._build_support_for_agent(item, "agent_b")
        else:  # "context"
            ctx_first = self._build_context_for_agent(item, "agent_a")
            ctx_second = self._build_context_for_agent(item, "agent_b")

        return Sample(
            question=question,
            answer=answer,
            context_first=ctx_first,
            context_second=ctx_second,
            item_id=item_id,
            level=level,
            raw=item,
        )

    # ---- internal helpers -------------------------------------------

    @staticmethod
    def _build_support_for_agent(item: Dict[str, Any], agent_key: str) -> str:
        """
        Turn supporting_facts[agent_key] into a compact textual context.

        Format (per fact):
            Article: <title>
            Sentence <idx>: <sentence>
        """
        supporting_facts = item.get("supporting_facts", {})
        facts = supporting_facts.get(agent_key, []) or []

        lines: List[str] = []
        for fact in facts:
            if not isinstance(fact, list) or len(fact) < 3:
                continue
            title, sent_idx, sentence = fact[0], fact[1], fact[2]
            lines.append(f"Article: {title}")
            lines.append(f"Sentence {sent_idx}: {sentence}")
            lines.append("")  # blank line between facts

        return "\n".join(lines).strip()

    @staticmethod
    def _build_context_for_agent(item: Dict[str, Any], agent_key: str) -> str:
        """
        Turn context[agent_key] into a textual context with all sentences.

        Mirrors the formatting used in verify.py's extract_context_agent_* helpers.
        """
        context = item.get("context", {})
        agent_ctx = context.get(agent_key, []) or []

        lines: List[str] = []
        for article in agent_ctx:
            if not isinstance(article, list) or len(article) < 2:
                continue
            title, passages = article[0], article[1]
            lines.append(f"Article: {title}")
            for passage in passages:
                passage = (passage or "").strip()
                if passage:
                    lines.append(f"Sentence: {passage}")
            lines.append("")  # blank line between articles

        return "\n".join(lines).strip()
