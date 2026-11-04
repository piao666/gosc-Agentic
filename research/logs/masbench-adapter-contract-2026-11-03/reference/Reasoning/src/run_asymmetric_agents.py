from __future__ import annotations

import argparse
import json
import os
from typing import Literal, Optional

from .agents import OpenAIAgent
from .conversation import (
    run_conversation,
    run_conversation_protocol,
    parse_answer,
    extract_message_block,
    ANSWER_TAG_PATTERN,
    BOXED_PATTERN,
)
from .data_loader_v4_mas import V4MasDataLoader
from .metrics import cal_f1_score, count_text_tokens
from .prompts import QA_INFO_EXCHANGE_PROMPT, QA_INFO_EXCHANGE_PROMPT_PROTOCOL


Mode = Literal["support", "context"]
ConversationStyle = Literal["base", "protocol"]


def _strip_answer_spans(text: str) -> str:
    """
    Remove explicit answer spans (<A>...</A>, \\boxed{...}) before counting
    communication tokens so that answer text itself is treated as external
    output rather than agent-to-agent communication.
    """
    text = ANSWER_TAG_PATTERN.sub(" ", text)
    text = BOXED_PATTERN.sub(" ", text)
    return text


def compute_comm_tokens(transcript: list[str], conversation_style: str) -> int:
    """
    Approximate communication cost as the total number of tokens
    that are visible to the partner.

    - base: partner sees each full utterance.
    - protocol: partner only sees MESSAGE blocks (thinking happens internally).
    """
    total = 0

    if conversation_style == "protocol":
        for full in transcript:
            if full.startswith("Alice:"):
                speaker = "Alice"
            elif full.startswith("Bob:"):
                speaker = "Bob"
            else:
                # Unexpected format, conservatively count the whole thing
                clean = _strip_answer_spans(full)
                total += count_text_tokens(clean)
                continue

            message = extract_message_block(full, speaker)
            visible = message or ""
            clean = _strip_answer_spans(visible)
            total += count_text_tokens(clean)
    else:
        # base: partner sees the full utterance
        for content in transcript:
            clean = _strip_answer_spans(content)
            total += count_text_tokens(clean)

    return total


def resolve_dataset_path(dataset_path: Optional[str] = None) -> str:
    """Get the dataset path, defaulting to the released reasoning dataset."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if dataset_path:
        return dataset_path if os.path.isabs(dataset_path) else os.path.join(project_root, dataset_path)
    return os.path.join(project_root, "reasoning.json")


def build_agent(name: str, model_key: str, temperature: float, max_tokens: int) -> OpenAIAgent:
    """Factory for OpenAIAgent with basic defaults."""
    return OpenAIAgent(
        name=name,
        model_key=model_key,
        temperature=temperature,
        max_tokens=max_tokens,
    )


def main(
    mode: Mode = "context",
    num_samples: int = 1,
    seed: Optional[int] = None,
    model_key: str = "gemini_flash",
    temperature: float = 0.0,
    max_tokens: int = 4096,
    max_rounds: int = 8,
    conversation_style: ConversationStyle = "base",
    resume: bool = False,
    dataset_path: Optional[str] = None,
    ) -> None:
    # Normalize the seed: if not provided, fall back to a fixed default so that
    # repeated runs with the same arguments remain reproducible.
    DEFAULT_SEED = 0
    if num_samples == -1:
        # When running the full dataset sequentially by index, we do not rely on
        # RNG at all, so keep the original seed (often None) for clearer logging.
        effective_seed: Optional[int] = seed
    else:
        effective_seed = DEFAULT_SEED if seed is None else seed

    resolved_dataset_path = resolve_dataset_path(dataset_path)
    dataloader = V4MasDataLoader(data_path=resolved_dataset_path, mode=mode, seed=effective_seed)

    # Determine actual number of samples to run
    # -1 means run the entire dataset sequentially by index
    if num_samples == -1:
        actual_num_samples = len(dataloader)
        run_all_sequential = True
    else:
        actual_num_samples = num_samples
        run_all_sequential = False

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    results_dir = os.path.join(project_root, "results")
    logs_dir = os.path.join(project_root, "logs")
    os.makedirs(results_dir, exist_ok=True)
    os.makedirs(logs_dir, exist_ok=True)

    # File names include model_key, mode, and conversation style to avoid overwriting
    # when running multiple models simultaneously
    file_suffix = f"{model_key}_{conversation_style}"
    results_path = os.path.join(results_dir, f"run_asymmetric_agents_results_{file_suffix}.json")
    logs_path = os.path.join(logs_dir, f"run_asymmetric_agents_{file_suffix}.log")

    sample_records: list[dict] = []
    log_lines: list[str] = []

    processed_indices = set()
    if resume and os.path.exists(results_path):
        print(f"--> [RESUME MODE] Found existing results: {results_path}")
        try:
            with open(results_path, "r", encoding="utf-8") as f_old:
                old_data = json.load(f_old)
                if "samples" in old_data:
                    sample_records = old_data["samples"]
                    for rec in sample_records:
                        if "sample_index" in rec:
                            processed_indices.add(rec["sample_index"])
            print(f"--> Loaded {len(sample_records)} existing samples. These will be skipped.")
        except Exception as e:
            print(f"--> Warning: Failed to load existing results ({e}). Starting fresh.")
    elif resume and not os.path.exists(results_path):
        print(f"--> [RESUME MODE] No existing file found at {results_path}. Starting fresh.")
    else:
        print("--> [OVERWRITE MODE] Starting fresh (any existing file will be overwritten).")
   
    if resume and os.path.exists(logs_path):
        print(f"--> [RESUME MODE] Found existing logs: {logs_path}")
        try:
            with open(logs_path, "r", encoding="utf-8") as f_log_old:
                content = f_log_old.read().splitlines()
                log_lines = content

            log_lines.append("")
            log_lines.append("=" * 80)
            log_lines.append(f"   RESUMING RUN (Skipped {len(processed_indices)} samples)")
            log_lines.append("=" * 80)
            log_lines.append("")
            
            print(f"--> Loaded {len(log_lines)} lines of existing logs.")
        except Exception as e:
            print(f"--> Warning: Failed to load existing logs ({e}). Logs will start fresh.")

    if not resume:
        if os.path.exists(results_path) or os.path.exists(logs_path):
            print("--> [OVERWRITE MODE] Existing files will be overwritten.")
        else:
            print("--> [NEW RUN] Starting fresh.")

    run_summary = {
        "dataset_path": resolved_dataset_path,
        "mode": mode,
        "conversation_style": conversation_style,
        "seed": effective_seed,
        "num_samples_requested": num_samples,
        "num_samples_actual": actual_num_samples,
        "num_samples_completed": 0,
        "model_key": model_key,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "max_rounds": max_rounds,
        "average_f1": None,
        "samples": sample_records,
    }

    def append_log_line(line: str = "") -> None:
        log_lines.append(line)

    def write_outputs() -> None:
        run_summary["num_samples_completed"] = len(sample_records)
        with open(results_path, "w", encoding="utf-8") as f_out:
            json.dump(run_summary, f_out, ensure_ascii=False, indent=2)
        with open(logs_path, "w", encoding="utf-8") as f_log:
            f_log.write("\n".join(log_lines))

    append_log_line("=== MAS Asymmetric QA Demo ===")
    append_log_line(f"Dataset    : {resolved_dataset_path}")
    append_log_line(f"Dataset size: {len(dataloader)}")
    append_log_line(f"Mode       : {mode}")
    append_log_line(f"Chat style : {conversation_style}")
    append_log_line(f"Num samples: {actual_num_samples} {'(full dataset, sequential)' if run_all_sequential else '(random)'}")
    append_log_line(f"Model      : {model_key}")
    append_log_line(f"Temperature: {temperature}")
    append_log_line(f"Max tokens : {max_tokens}")
    append_log_line(f"Max rounds : {max_rounds}")
    append_log_line("Early stop : first <A>")
    if effective_seed is not None:
        if seed is None and num_samples != -1:
            append_log_line(f"Seed       : {effective_seed} (default)")
        else:
            append_log_line(f"Seed       : {effective_seed}")
    append_log_line("")
    if not resume: 
        write_outputs() 

    # Run for the specified number of samples
    for sample_idx in range(actual_num_samples):
        if resume and sample_idx in processed_indices:
            continue

        if actual_num_samples > 1:
            print(f"\n{'='*80}")
            print(f"Running sample {sample_idx + 1}/{actual_num_samples}")
            print(f"{'='*80}\n")

        # If running all sequential (-1), use index; otherwise random sample
        if run_all_sequential:
            sample = dataloader.sample(index=sample_idx)
        else:
            sample = dataloader.sample(index=None)  # Random sample

        alice = build_agent("Alice", model_key=model_key, temperature=temperature, max_tokens=max_tokens)
        bob = build_agent("Bob", model_key=model_key, temperature=temperature, max_tokens=max_tokens)

        # Select prompt template based on conversation style
        if conversation_style == "protocol":
            prompt_template = QA_INFO_EXCHANGE_PROMPT_PROTOCOL
        else:
            prompt_template = QA_INFO_EXCHANGE_PROMPT

        # Initialize per-agent system prompts with asymmetric information.
        alice.init_system_prompt(
            prompt_template,
            {
                "name": "Alice",
                "partner": "Bob",
                "question": sample.question,
                "information": sample.context_first or "(empty for Alice)",
            },
        )
        bob.init_system_prompt(
            prompt_template,
            {
                "name": "Bob",
                "partner": "Alice",
                "question": sample.question,
                "information": sample.context_second or "(empty for Bob)",
            },
        )

        print("=== MAS Asymmetric QA Demo ===")
        print(f"Difficulty : {sample.level}")
        print(f"Item ID    : {sample.item_id}")
        print(f"Mode       : {mode} (per-agent {'supporting facts only' if mode == 'support' else 'full context blocks'})")
        print(f"Chat style : {conversation_style}")
        print(f"Model      : {model_key}")
        print()
        print("Question:")
        print(sample.question)
        print()
        print(f"Ground-truth answer: {sample.answer}")
        print("-" * 80)
        print("Conversation:")
        print("-" * 80)

        # Run conversation with appropriate function based on style
        if conversation_style == "protocol":
            transcript, final_answer = run_conversation_protocol(
                [alice, bob],
                max_rounds=max_rounds,
            )
        else:
            transcript, final_answer = run_conversation(
                [alice, bob],
                max_rounds=max_rounds,
            )

        for turn, utterance in enumerate(transcript):
            print(f"[{turn:02d}] {utterance}")

        # Communication cost (tokens visible to partner)
        comm_tokens = compute_comm_tokens(transcript, conversation_style)
        comm_tokens_per_turn = comm_tokens / max(len(transcript), 1)

        print("-" * 80)
        print(f"Communication tokens (shared): {comm_tokens}")
        print(f"Tokens per turn (shared)     : {comm_tokens_per_turn:.1f}")
        print("-" * 80)
        print("Final extracted answer:", final_answer if final_answer is not None else "<none>")
        print("Ground-truth answer   :", sample.answer)

        # Team F1: based on the final answer from the conversation
        f1_team: Optional[float] = None
        if final_answer is not None:
            f1_team = cal_f1_score(sample.answer, final_answer)
            print(f"F1 team (final answer): {f1_team:.4f}")
        else:
            print("F1 team (final answer): <n/a>")

        sample_records.append(
            {
                "sample_index": sample_idx,
                "item_id": sample.item_id,
                "level": sample.level,
                "question": sample.question,
                "ground_truth_answer": sample.answer,
                "final_answer": final_answer,
                "f1_team": f1_team,
                "comm_tokens": comm_tokens,
                "comm_tokens_per_turn": comm_tokens_per_turn,
                "transcript": transcript,
                "conversation_style": conversation_style,
                "max_rounds": max_rounds,
                "model_key": model_key,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
        )

        append_log_line(f"--- Sample {sample_idx + 1}/{actual_num_samples} ---")
        append_log_line(f"Difficulty : {sample.level}")
        append_log_line(f"Item ID    : {sample.item_id}")
        append_log_line("Question:")
        append_log_line(sample.question)
        append_log_line("")
        append_log_line(f"Ground-truth answer: {sample.answer}")
        append_log_line("-" * 80)
        append_log_line("Conversation:")
        append_log_line("-" * 80)
        for turn, utterance in enumerate(transcript):
            append_log_line(f"[{turn:02d}] {utterance}")
        append_log_line("-" * 80)
        append_log_line("Final extracted answer: " + (final_answer if final_answer is not None else "<none>"))
        append_log_line("Ground-truth answer   : " + sample.answer)
        append_log_line(f"Communication tokens  : {comm_tokens}")
        append_log_line(f"Tokens per turn       : {comm_tokens_per_turn:.1f}")
        if f1_team is not None:
            append_log_line(f"F1 team (final answer): {f1_team:.4f}")
        append_log_line("")
        write_outputs()

    team_f1_values = [r["f1_team"] for r in sample_records if r["f1_team"] is not None]
    comm_values = [record["comm_tokens"] for record in sample_records if record["comm_tokens"] is not None]

    average_f1_team = sum(team_f1_values) / len(team_f1_values) if team_f1_values else None
    avg_comm_tokens = sum(comm_values) / len(comm_values) if comm_values else None

    # Efficiency metric: F1 per 1000 tokens (higher is better)
    f1_per_1k_tokens: Optional[float] = None
    if average_f1_team is not None and comm_values:
        total_comm = sum(comm_values)
        if total_comm > 0:
            f1_per_1k_tokens = average_f1_team / (total_comm / 1000.0)

    run_summary["average_f1_team"] = average_f1_team
    run_summary["average_comm_tokens"] = avg_comm_tokens
    run_summary["f1_per_1k_tokens"] = f1_per_1k_tokens

    print("\n=== Run Summary ===")
    print(f"Samples completed: {len(sample_records)}")
    if average_f1_team is not None:
        print(f"Average F1 (team best): {average_f1_team:.4f}")
    else:
        print("Average F1 (team best): <n/a>")
    if avg_comm_tokens is not None:
        print(f"Average comm tokens (shared): {avg_comm_tokens:.1f}")
    if f1_per_1k_tokens is not None:
        print(f"F1 per 1k shared tokens     : {f1_per_1k_tokens:.4f}")

    append_log_line("=== Run Summary ===")
    append_log_line(f"Samples completed: {len(sample_records)}")
    if average_f1_team is not None:
        append_log_line(f"Average F1 (team best): {average_f1_team:.4f}")
    else:
        append_log_line("Average F1 (team best): <n/a>")
    if avg_comm_tokens is not None:
        append_log_line(f"Average comm tokens (shared): {avg_comm_tokens:.1f}")
    if f1_per_1k_tokens is not None:
        append_log_line(f"F1 per 1k shared tokens     : {f1_per_1k_tokens:.4f}")
    write_outputs()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run an asymmetric Alice-Bob conversation on the released reasoning dataset.",
    )
    parser.add_argument(
        "--mode",
        "-m",
        choices=["support", "context"],
        default="context",
        help="Whether each agent sees only its supporting_facts ('support') or its full context block ('context').",
    )
    parser.add_argument(
        "--num-samples",
        "-n",
        type=int,
        default=-1,
        help="Number of samples to run. Use -1 to run the entire dataset sequentially by index (default: 1).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for sampling items. If omitted (default), uses 0 so results are reproducible.",
    )
    parser.add_argument(
        "--model-key",
        default="gemini_flash",
        help="Logical model key passed to api_key_loader.get_api/get_model_name (e.g. 'gemini_flash', 'gpt_4o_mini').",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.0,
        help="Sampling temperature for the underlying chat model.",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=4096,
        help="Maximum number of new tokens per agent turn.",
    )
    parser.add_argument(
        "--max-rounds",
        type=int,
        default=10,
        help="Maximum number of alternating turns between the two agents.",
    )
    parser.add_argument(
        "--chat-style",
        choices=["base", "protocol"],
        default="base",
        help="Conversation style between agents: 'base' for free-form, 'protocol' for INTERNAL+MESSAGE protocol.",
    )
    parser.add_argument(
        "--dataset-path",
        default=None,
        help="Path to the reasoning dataset. Defaults to reasoning.json in this directory.",
    )

    parser.add_argument(
        "--resume",
        action="store_true",
        help="If set, try to load existing results file and skip samples that have already been processed.",
    )

    args = parser.parse_args()
    main(
        mode=args.mode,  # type: ignore[arg-type]
        num_samples=args.num_samples,
        seed=args.seed,
        model_key=args.model_key,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
        max_rounds=args.max_rounds,
        conversation_style=args.chat_style,  # type: ignore[arg-type]
        resume=args.resume,
        dataset_path=args.dataset_path,
    )
