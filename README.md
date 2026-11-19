# STMRagged

Question answering over the STM32F4 reference manual (RM0090), with page citations and refusals when the manual doesn't cover the question. The project is built around its evaluation: a hand-verified golden set, retrieval and answer metrics, and a failure analysis.

*Work in progress. Results and failure analysis will be added once the eval harness exists.*

## Setup

```
uv sync
```

1. Download RM0090 **Rev 22** from ST (URL in `corpus/manifest.toml`) and save it as `data/STM_0090_sourcedoc.pdf`. The PDF isn't in the repo because of ST's licensing.
2. Check it's the exact file the results were measured on:
   ```
   uv run python -m stmragged.corpus
   ```
3. Put the LLM credentials in `.env`. It is git-ignored.

## Pipeline

| Module | File | Status |
|---|---|---|
| Corpus manifest | `stmragged/corpus.py`, `corpus/manifest.toml` | Done |
| Loading | `stmragged/loading.py` | Done |
| Chunking | `stmragged/chunking.py` | Done |
| Embedding + vector store | | Next |
| Retrieval (dense baseline) | | |
| Generation (citations + refusals) | | |
| Golden set | | |
| Eval harness | | |
| Hybrid retrieval (BM25 + dense) | | |

Each module can be run on its own, e.g. `uv run python -m stmragged.loading 287` prints one page's text, and `uv run python -m stmragged.chunking 287` prints its chunks.

## Key decisions and why

**Corpus: RM0090 Rev 22 only, pinned by SHA-256 and page count.** The revision is what a person reads; the hash proves the file is byte-identical; the page count protects the page-number evidence labels. ST's URL always serves the latest revision, so a newer download fails the check on purpose.

**Indexed pages: 57–1702 (1,646 pages).** Dropped: 1–56 (cover, contents, lists of tables and figures), 1703 (important security notice), 1704–1735 (revision history) and 1736–1741 (index). The TOC and index mention nearly every register name, so keyword search would match them constantly, but they are never the right evidence for an answer.

**Page numbers are 1-based and match the printed footer ("n/1741").** They are the citation and the golden-set evidence label, so an off-by-one would silently break both. PyMuPDF's 0-based index is converted at the one place a page is fetched.

**Loading: PyMuPDF called directly, headers and footers removed by cropping.** Each page is cropped to the band between y=75 pt and y=738 pt (A4 is 842 pt tall). Cropping by position is more robust than text patterns, because the header holds the chapter title and changes with every chapter. LangChain's `PyMuPDFLoader` doesn't expose cropping, so pages are wrapped into LangChain `Document`s by hand. Verified: no header/footer text survives on any page, no page is empty, and the first and last lines of spot-checked pages match the PDF.

**Figures: text only for now.** Captions and the text labels inside diagrams are extracted, but the connections between blocks are lost (e.g. the system-architecture figure lists "CCM data RAM" and "D-bus" but not that one connects through the other). Golden-set questions that need a figure are tagged, so the eval shows what this costs. If it costs a lot, the planned fix is a vision-model description of each figure, stored as a text chunk with its page number.

**Tables: kept as extracted (one cell per line, row by row).** Two-column tables read fine. Wide tables and tables with merged cells lose the link between a value and its column. For example, in the boundary-address tables one merged Bus cell covers several rows, so most rows don't say which bus they're on. This is a known limitation of the baseline; PyMuPDF's `find_tables()` is the candidate fix if it shows up in the failures.

**Chunking: recursive splitting within each page, 280 tokens max, 40 overlap, counted with the bge tokenizer.** Chunks never cross a page boundary, so each chunk cites exactly one page and page-level recall is unambiguous. The recursive splitter breaks at the largest natural boundary that fits (paragraph, then line, then word), so it doesn't cut mid-sentence the way fixed-size splitting does. Result: TODO chunks, mean TODO characters, TODO chunks per page. Chunk IDs look like `RM0090-p287-c2`. The cost: a paragraph or table running onto the next page is cut at the page break.

*Why tokens, not characters.* The first version split at 1,000 characters (150 overlap). A token-count check (`uv run python -m stmragged.token_check`) found 12 of the 4,001 chunks over `bge-base-en-v1.5`'s 512-token limit, which the model silently truncates, and 40 over 450. The worst was 727 tokens in 999 characters (p317). Prose averages 3.56 characters per token, but dense register and bit-field tables drop to about 1.4, so no single character limit suits both. A limit low enough for the tables (about 650 characters) would have cut every prose chunk by a third. Counting tokens limits what the model actually sees. 280 tokens is about 1,000 characters of prose, so prose chunks keep their old size and only dense tables get shorter, making the fix a single change. After the switch the largest chunk is 282 tokens to the model (280 plus `[CLS]` and `[SEP]`), and none is truncated.

**Embedding model: `bge-base-en-v1.5` (local, on a 4 GB GTX 1650 Ti).** It fits easily and embeds the corpus in minutes, which matters because every chunking change means re-embedding. `bge-large` is only about a point better on general benchmarks and has the same 512-token limit. The hard questions here turn on identifiers like `RCC_AHB1ENR`, where dense models are weak at any size and hybrid BM25 is expected to help more.

## Planned experiments (each one measured against the baseline on dev)

- Hybrid retrieval: BM25 + dense
- Structure-aware chunks (one per section or register), with the section heading prefixed to each chunk, so bit-field chunks still name their register
- Whole-document chunking, allowing chunks to cross pages
- Chunk size: 280 vs about 450 tokens (more context per chunk vs more precise retrieval)
- `bge-large-en-v1.5` vs `bge-base-en-v1.5`
- Table extraction with `find_tables()`, and vision descriptions of figures, only if the failure analysis points there
