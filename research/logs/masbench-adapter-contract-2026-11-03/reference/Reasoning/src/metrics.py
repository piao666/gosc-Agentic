# from __future__ import annotations

# from collections import Counter
# import re
# from typing import Callable, Iterable, List, Optional


# def _default_tokenize(text: str) -> List[str]:
#     """
#     Fallback tokenizer for F1 scoring.

#     The original HotpotQA code uses `tokenizer.tokenize` from a LLaMA
#     tokenizer. Here we approximate it with a simple word tokenizer:
#     - lowercase
#     - strip leading/trailing whitespace
#     - split on non-alphanumeric boundaries
#     """
#     text = text.lower().strip()
#     # Replace non-alphanumeric characters with spaces, then split.
#     text = re.sub(r"[^0-9a-z]+", " ", text)
#     tokens = text.split()
#     return tokens


# def count_text_tokens(
#     text: str,
#     tokenizer: Optional[Callable[[str], Iterable[str]]] = None,
# ) -> int:
#     """
#     Count tokens in `text` using the same default tokenizer as F1,
#     unless a custom tokenizer is provided.
#     """
#     if tokenizer is None:
#         tokens = _default_tokenize(text)
#     else:
#         tokens = list(tokenizer(text))
#     return len(tokens)


# def cal_f1_score(
#     ref: str,
#     tar: str,
#     tokenizer: Optional[Callable[[str], Iterable[str]]] = None,
# ) -> float:
#     """
#     Compute token-level F1 between reference answer `ref` and target `tar`.

#     This mirrors the structure of the original Hotpot implementation:
#     - lowercase
#     - strip spaces and trivial 'm=' / 'm = ' prefixes
#     - tokenize
#     - compute precision/recall/F1 via multiset overlap

#     If `tokenizer` is None, a simple regex-based tokenizer is used.
#     """
#     if tokenizer is None:
#         tok = _default_tokenize
#     else:
#         tok = lambda x: list(tokenizer(x))  # ensure iterable → list

#     def _preprocess(s: str) -> str:
#         s = s.lower().strip()
#         # Remove 'm=' or 'm = ' prefix if present (use lstrip with regex, not strip)
#         if s.startswith("m="):
#             s = s[2:].lstrip()
#         elif s.startswith("m = "):
#             s = s[4:].lstrip()
#         return s

#     ref_norm = _preprocess(ref)
#     tar_norm = _preprocess(tar)

#     ref_tokens = list(tok(ref_norm))
#     tar_tokens = list(tok(tar_norm))

#     counter_ref = Counter(ref_tokens)
#     counter_tar = Counter(tar_tokens)

#     tp = sum((counter_ref & counter_tar).values())
#     fp = sum((counter_tar - counter_ref).values())
#     fn = sum((counter_ref - counter_tar).values())

#     precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
#     recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0

#     if precision + recall == 0:
#         return 0.0

#     return 2 * (precision * recall) / (precision + recall)

from __future__ import annotations

from collections import Counter
import re
import string
from typing import Callable, Iterable, List, Optional


def normalize_answer(s: str) -> str:
    """
    Standard normalization for QA evaluation (SQuAD style).
    1. Lowercase
    2. Remove punctuation
    3. Remove articles (a, an, the)
    4. Fix whitespace
    """
    def remove_articles(text):
        return re.sub(r'\b(a|an|the)\b', ' ', text)

    def white_space_fix(text):
        return ' '.join(text.split())

    def remove_punc(text):
        exclude = set(string.punctuation)
        return ''.join(ch for ch in text if ch not in exclude)

    def lower(text):
        return text.lower()

    return white_space_fix(remove_articles(remove_punc(lower(s))))


def _default_tokenize(text: str) -> List[str]:
    """
    Tokenizes text by splitting on whitespace after normalization.
    """
    text = normalize_answer(text)
    return text.split()


def count_text_tokens(
    text: str,
    tokenizer: Optional[Callable[[str], Iterable[str]]] = None,
) -> int:
    if tokenizer is None:
        tokens = _default_tokenize(text)
    else:
        tokens = list(tokenizer(text))
    return len(tokens)


def cal_f1_score(
    ref: str,
    tar: str,
    tokenizer: Optional[Callable[[str], Iterable[str]]] = None,
) -> float:
    """
    Compute F1 score with SQuAD-style normalization.
    """
    if tokenizer is not None:
        ref_tokens = list(tokenizer(ref))
        tar_tokens = list(tokenizer(tar))
    else:
        ref_tokens = _default_tokenize(ref)
        tar_tokens = _default_tokenize(tar)

    if len(ref_tokens) == 0 or len(tar_tokens) == 0:
        return 1.0 if ref_tokens == tar_tokens else 0.0

    counter_ref = Counter(ref_tokens)
    counter_tar = Counter(tar_tokens)

    common = counter_ref & counter_tar
    num_same = sum(common.values())

    if num_same == 0:
        return 0.0

    precision = 1.0 * num_same / len(tar_tokens)
    recall = 1.0 * num_same / len(ref_tokens)
    
    f1 = (2 * precision * recall) / (precision + recall)
    
    return f1
