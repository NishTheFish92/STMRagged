"""Check that every chunk fits in the embedding model's 512-token window.

bge-base-en-v1.5 silently truncates anything past 512 tokens, so an oversized chunk would be
embedded from its first part only. The splitter counts characters, and dense tables (hex values,
register names) tokenize into far more tokens per character than prose, so they are the risk.

Run:  uv run python -m stmragged.token_check
"""

import sys

from transformers import AutoTokenizer

from stmragged.chunking import EMBEDDING_MODEL as MODEL_NAME
from stmragged.chunking import chunk_pages
from stmragged.loading import load_pages

MAX_TOKENS = 512  # the model's limit, including the [CLS] and [SEP] tokens
MARGIN = 450  # a safety threshold below the limit
SHOW_WORST = 10


def main() -> int:
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    chunks = chunk_pages(load_pages())

    texts = [c.page_content for c in chunks]
    # add_special_tokens=True counts [CLS] and [SEP], which the model's 512 limit includes
    counts = [len(ids) for ids in tokenizer(texts, add_special_tokens=True)["input_ids"]]

    over_limit = sum(n > MAX_TOKENS for n in counts)
    over_margin = sum(n > MARGIN for n in counts)
    chars_per_token = sum(len(t) for t in texts) / sum(counts)

    print(f"{len(chunks)} chunks, tokenized with {MODEL_NAME}")
    print(f"Tokens per chunk: min {min(counts)}, mean {sum(counts) // len(counts)}, max {max(counts)}")
    print(f"Average characters per token: {chars_per_token:.2f}")
    print(f"Chunks over {MARGIN} tokens: {over_margin}")
    print(f"Chunks over {MAX_TOKENS} tokens (would be truncated): {over_limit}")

    print(f"\nWorst {SHOW_WORST} chunks:")
    worst = sorted(zip(counts, chunks), key=lambda pair: pair[0], reverse=True)[:SHOW_WORST]
    for n, c in worst:
        print(f"  {n:4d} tokens  {len(c.page_content):4d} chars  {c.metadata['chunk_id']}")

    return 1 if over_limit else 0


if __name__ == "__main__":
    sys.exit(main())
