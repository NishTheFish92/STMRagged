"""Split each page into chunks. Chunks never cross a page boundary, so each one cites exactly one page.

Length is measured in tokens of the embedding model's tokenizer, not characters: dense tables pack
far more tokens per character than prose, and the model silently truncates past 512 tokens.

Run:  uv run python -m stmragged.chunking        # chunk everything, print stats
      uv run python -m stmragged.chunking 287    # print the chunks of page 287
"""

import sys
from collections import Counter

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from transformers import AutoTokenizer

from stmragged.loading import load_pages

EMBEDDING_MODEL = "BAAI/bge-base-en-v1.5"  # its tokenizer measures chunk length
# About 1,000 / 150 characters of prose (3.56 chars per token), so prose chunks keep their old size
# and only dense tables get cut shorter. Well under the model's 512-token limit.
CHUNK_SIZE = 280  # max tokens per chunk, excluding [CLS] and [SEP]
CHUNK_OVERLAP = 40  # tokens repeated from the end of one chunk at the start of the next


def chunk_pages(pages: list[Document]) -> list[Document]:
    tokenizer = AutoTokenizer.from_pretrained(EMBEDDING_MODEL)
    splitter = RecursiveCharacterTextSplitter.from_huggingface_tokenizer(
        tokenizer, chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP
    )
    chunks = []
    for page in pages:
        for i, text in enumerate(splitter.split_text(page.page_content)):
            meta = page.metadata  # doc_id, revision, page
            chunk_id = f"{meta['doc_id']}-p{meta['page']}-c{i}"
            chunks.append(Document(page_content=text, metadata={**meta, "chunk_id": chunk_id}))
    return chunks


def main() -> int:
    chunks = chunk_pages(load_pages())

    if len(sys.argv) > 1:  # show one page's chunks
        wanted = int(sys.argv[1])
        for c in chunks:
            if c.metadata["page"] == wanted:
                print(f"=== {c.metadata['chunk_id']} ({len(c.page_content)} chars) ===")
                print(c.page_content)
                print()
        return 0

    lengths = [len(c.page_content) for c in chunks]
    per_page = Counter(c.metadata["page"] for c in chunks)
    spread = Counter(per_page.values())  # how many pages produced 1 chunk, 2 chunks, ...

    print(f"{len(chunks)} chunks from {len(per_page)} pages")
    print(f"Chunk length in characters: min {min(lengths)}, mean {sum(lengths) // len(lengths)}, max {max(lengths)}")
    print("Chunks per page: " + ", ".join(f"{n} chunk(s): {spread[n]} pages" for n in sorted(spread)))
    print("(Token counts and the 512-limit check: uv run python -m stmragged.token_check)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
