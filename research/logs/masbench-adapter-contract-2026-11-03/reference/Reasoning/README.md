<div align="center">

# MASBench · Reasoning

**Two agents. Private evidence. One shared answer.**

[Main README](../README.md) · [Scheduling](../Scheduling/README.md) · [Game](../Game/README.md)

</div>

<p align="center">
  <img src="../docs/assets/reasoning.png" alt="Reasoning task: two agents exchange complementary private evidence to answer a shared question" width="320">
</p>

## Task and Data

Two agents, Alice and Bob, receive different evidence for the same question. They exchange clues and produce a final answer. This task compares **free-form dialogue** with a **structured communication protocol**.

`reasoning.json` contains **300 questions**: 200 `easy` and 100 `hard` instances, corresponding to the paper's simple and complex splits. Each record includes a question, reference answer, per-agent context, supporting facts, and metadata.

### Data Source and License

This dataset is adapted from [HotpotQA: A Dataset for Diverse, Explainable Multi-hop Question Answering](https://hotpotqa.github.io/) by Zhilin Yang, Peng Qi, Saizheng Zhang, Yoshua Bengio, William W. Cohen, Ruslan Salakhutdinov, and Christopher D. Manning (EMNLP 2018).

HotpotQA is released under [Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)](https://creativecommons.org/licenses/by-sa/4.0/). The adapted dataset in `reasoning.json` is distributed under the same license. We rewrite the original questions and context passages and distribute evidence across two agents for collaborative reasoning. This is a modified dataset, not an official HotpotQA release. When redistributing or adapting it, retain attribution, link to the license, indicate changes, and license adaptations under CC BY-SA 4.0 or a compatible license. This notice covers the dataset; it does not license the task's source code.

The task's original source code is licensed under [MIT](../LICENSE), copyright (c) 2026 Qizhi Chu.

## Setup

Activate the shared environment from the [main installation guide](../README.md#1-install). From the repository root:

```bash
cd Reasoning
cp .env.example .env
```

Edit `.env`:

```dotenv
OPENAI_API_KEY=your_api_key
OPENAI_BASE_URL=https://your-openai-compatible-endpoint/v1
QWEN_PLUS_MODEL=qwen-plus
```

Environment variables override `.env`. All commands below run inside `Reasoning/`.

## Run One Question

```bash
python -m src.run_asymmetric_agents \
  --model-key qwen_plus \
  --chat-style protocol \
  --mode context \
  --num-samples 1 \
  --max-rounds 6 \
  --max-tokens 1024 \
  --seed 42
```

The two agents use the same model. A completed run prints `Samples completed: 1` and writes:

```text
results/run_asymmetric_agents_results_qwen_plus_protocol.json
logs/run_asymmetric_agents_qwen_plus_protocol.log
```

The result contains `item_id`, `transcript`, `final_answer`, `f1_team`, and communication counts. Reaching the turn limit without a final answer still produces a record.

## Experiment Settings

| Option | Values / behavior |
| :--- | :--- |
| `--chat-style` | `base` for free-form dialogue; `protocol` for structured messages |
| `--mode` | `context` for full private context; `support` for supporting facts only |
| `--num-samples` | `1` for a smoke test; `-1` for all 300 records in order |
| `--max-rounds` | Maximum individual speaking turns, not Alice/Bob pairs |
| `--max-tokens` | Per-response output limit sent to the provider |
| `--seed` | Dataset sampling seed; positive sample counts sample with replacement |
| `--model-key` | A logical alias or raw provider model ID |

Common aliases are `qwen_plus`, `deepseek_v3_2_exp`, `gemini_2_5_flash_lite`, and `gpt_5_nano`. Override their provider IDs in `.env` or use a raw model ID. The provider must support the model and request parameters.

Run the full dataset by replacing `--num-samples 1` with `--num-samples -1` and selecting your intended turn/token budgets. To launch both dialogue styles in tmux:

```bash
bash run_model.sh qwen_plus --num-samples 10 --max-rounds 10
```

The launcher replaces an existing tmux session with the same model name.

## Analyze Results

```bash
python script/analyze_first_answer_protocol.py \
  --input results/run_asymmetric_agents_results_qwen_plus_protocol.json \
  --output results/first_answer_eval_protocol.json

python script/analyze_answer_tokens.py \
  --log logs/run_asymmetric_agents_qwen_plus_protocol.log \
  --output results/answer_token_stats.json
```

The first command analyzes first-answer stopping; the second estimates answer lengths. For dataset supporting-fact statistics:

```bash
python script/analyze_support_facts_tokens.py \
  --data reasoning.json \
  --output results/support_facts_token_stats.json
```

The shared requirements include `tiktoken` for tokenizer-based supporting-fact counts. On first use, it downloads and caches the tokenizer data.

## Practical Notes

- **Output reuse:** filenames include only the model alias and chat style. Archive results before changing mode, seed, or other settings.
- **Resume:** use only with matching configuration. Partial random-sample resumes do not restore RNG state; prefer an uninterrupted run for reproducible sampling.
- **Metrics:** F1 is 0–1; communication uses normalized word counts. The efficiency field uses mean F1 divided by total communication, and unanswered samples are excluded from mean F1.
- **API limits:** run smoke tests sequentially if your endpoint has low rate limits. Hosted models incur provider charges.
