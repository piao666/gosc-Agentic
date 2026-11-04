from __future__ import annotations

import re
from typing import List, Optional, Sequence, Tuple

from .agents import BaseAgent


# Hotpot-style answer markers: we follow the original parser
# behavior and always take the *last* match within a message.
ANSWER_TAG_PATTERN = re.compile(r"<A>(.*?)</A>", re.DOTALL)
BOXED_PATTERN = re.compile(r"\\boxed\{(.+?)\}")

# Extract facts written inside <R>...</R> tags.
RESPONSE_TAG_PATTERN = re.compile(r"<R>(.*?)</R>", re.DOTALL)

# def parse_answer(text: str) -> Optional[str]:
#     """
#     Extract a candidate answer from the agent's utterance.

#     - For `<A>answer</A>` we mimic `hotpot_qa_parser` and return the *last*
#       occurrence in the string, if any.
#     - For `\\boxed{answer}` we return the first match as a fallback format.
#     """
#     if not text:
#         return None

#     # Hotpot convention: last <A>...</A> wins inside a single message.
#     answers = ANSWER_TAG_PATTERN.findall(text)
#     if answers:
#         return answers[-1].strip()

#     m = BOXED_PATTERN.search(text)
#     if m:
#         return m.group(1).strip()

#     return None

def parse_answer(text: str) -> Optional[str]:
    """
    Extract a candidate answer from the agent's utterance.
    
    Improvements:
    - Filters out placeholder values like "answer" or "final answer".
    - Strips trailing punctuation from the extracted content.
    """
    if not text:
        return None

    INVALID_ANSWERS = {"answer", "final answer", "the answer", "answer:"}

    matches = ANSWER_TAG_PATTERN.findall(text)

    if matches:
        for candidate in reversed(matches):
            cleaned = candidate.strip()
            if cleaned.lower() in INVALID_ANSWERS:
                continue
            if cleaned.endswith("."):
                cleaned = cleaned[:-1]
                
            return cleaned

    m = BOXED_PATTERN.search(text)
    if m:
        return m.group(1).strip()

    return None

def extract_message_block(
    full_text: str,
    speaker_name: str,
) -> str:
    """
    Extract the MESSAGE block from thinking model output.

    For thinking models, the format is simply:
        {speaker_name}: MESSAGE
        - content here

    Returns the MESSAGE block content, or the full text as fallback.
    """
    # Build pattern for MESSAGE section
    message_pattern = re.compile(
        rf"^\s*{re.escape(speaker_name)}:\s*MESSAGE\b",
        re.MULTILINE | re.IGNORECASE
    )

    message_match = message_pattern.search(full_text)

    # If MESSAGE marker not found, fallback: entire text is message
    if message_match is None:
        return full_text

    # Extract message block (from MESSAGE marker to end)
    message_block = full_text[message_match.start():].strip()

    return message_block


def run_conversation(
    agents: Sequence[BaseAgent],
    max_rounds: int = 10,
) -> Tuple[List[str], Optional[str]]:
    """
    Baseline: free-form conversation between two agents.

    Args:
        agents: Sequence of exactly two agents.
        max_rounds: Maximum number of total turns.

    Returns:
        transcript: list of utterance strings in chronological order.
        final_answer: first answer extracted via `parse_answer`, or None.
    """
    if len(agents) != 2:
        raise ValueError("run_conversation currently supports exactly two agents (Alice/Bob).")

    transcript: List[str] = []
    final_answer: Optional[str] = None

    current_idx = 0  # 0 -> first agent, 1 -> second agent

    for _ in range(max_rounds):
        speaker = agents[current_idx]
        listener = agents[1 - current_idx]

        content = speaker.step()
        transcript.append(content)

        # Share this utterance with the other agent.
        listener.add_memory(content)

        # Try to parse an explicit answer. We stop at the first answer span.
        extracted = parse_answer(content)
        if extracted:
            final_answer = extracted
            break

        current_idx = 1 - current_idx

    return transcript, final_answer


def run_conversation_protocol(
    agents: Sequence[BaseAgent],
    max_rounds: int = 10,
) -> Tuple[List[str], Optional[str]]:
    """
    Protocol-based conversation for thinking models: only MESSAGE blocks are visible to the partner.

    Each agent produces output containing MESSAGE block. Only the MESSAGE block
    is shared with the partner and counts toward communication cost.
    The thinking process happens automatically in the model's internal reasoning.

    Args:
        agents: Sequence of exactly two agents.
        max_rounds: Maximum number of total turns.

    Returns:
        transcript: list of full utterance strings in chronological order.
        final_answer: last stable answer extracted from MESSAGE blocks via `parse_answer`, or None.
    """
    if len(agents) != 2:
        raise ValueError("run_conversation_protocol currently supports exactly two agents (Alice/Bob).")

    transcript: List[str] = []
    final_answer: Optional[str] = None

    shared_blackboard: List[str] = []

    current_idx = 0

    for _ in range(max_rounds):
        speaker = agents[current_idx]
        listener = agents[1 - current_idx]

        full = speaker.step()              # full output from thinking model
        transcript.append(full)

        # Extract MESSAGE block, fallback to full if parsing fails
        message = extract_message_block(full, speaker.name)
        visible = message or full

        new_facts = RESPONSE_TAG_PATTERN.findall(visible)
        if new_facts:
            for fact in new_facts:
                fact = fact.strip()
                if fact and fact not in shared_blackboard:
                    shared_blackboard.append(fact)

        if shared_blackboard:
            board_text = "\n".join([f"{i+1}. {f}" for i, f in enumerate(shared_blackboard)])
            enriched_message = (
                f"{visible}\n\n"
                f"--- SHARED KNOWLEDGE BOARD (Cumulative Facts) ---\n"
                f"{board_text}\n"
                f"-------------------------------------------------"
            )
            listener.add_memory(enriched_message)
        else:
            listener.add_memory(visible)

        # # Only send MESSAGE to the other agent
        # listener.add_memory(visible)

        # Extract answer only from MESSAGE. We stop at the first answer span.
        ans = parse_answer(visible)
        if ans:
            final_answer = ans
            break

        current_idx = 1 - current_idx

    return transcript, final_answer
