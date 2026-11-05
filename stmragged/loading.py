"""Load RM0090 into one LangChain Document per content page.

Run:  uv run python -m stmragged.loading        # load everything, print summary + checks
      uv run python -m stmragged.loading 287    # print the extracted text of page 287
"""

import re
import sys

import pymupdf
from langchain_core.documents import Document

from stmragged.corpus import load_manifest

# Page numbers are 1-based and match the printed footer ("n/1741").
# Dropped: 1-56 (cover, contents, lists of tables/figures),
#          1703 (important security notice), 1704-1735 (revision history), 1736-1741 (index).
FIRST_CONTENT_PAGE = 57
LAST_CONTENT_PAGE = 1702

# Vertical band (in PDF points, y grows downward) between the header and footer.
# A4 is 595 x 842 pt. Header text + rule end around y=72; footer rule + text start around y=741.
HEADER_BOTTOM = 75
FOOTER_TOP = 738

# Text that should never survive cropping: footer "n/1741", "RM0090 Rev 22", header "RM0090".
LEAK_PATTERN = re.compile(r"^\d+/1741$|^RM0090 Rev 22$|^RM0090$", re.MULTILINE)


def load_pages() -> list[Document]:
    (doc,) = load_manifest()  # the manifest holds exactly one document: RM0090
    pages = []
    with pymupdf.open(doc.path) as pdf:
        if pdf.page_count != doc.pages:
            raise ValueError(f"{doc.path} has {pdf.page_count} pages, manifest says {doc.pages}")

        for page_num in range(FIRST_CONTENT_PAGE, LAST_CONTENT_PAGE + 1):
            page = pdf[page_num - 1]  # PyMuPDF indexes pages from 0
            body = pymupdf.Rect(0, HEADER_BOTTOM, page.rect.width, FOOTER_TOP)
            text = page.get_text(clip=body).strip()
            if not text:
                continue  # nothing to retrieve on this page
            pages.append(
                Document(
                    page_content=text,
                    metadata={"doc_id": doc.doc_id, "revision": doc.revision, "page": page_num},
                )
            )
    return pages


def main() -> int:
    pages = load_pages()

    if len(sys.argv) > 1:  # show one page
        wanted = int(sys.argv[1])
        match = [p for p in pages if p.metadata["page"] == wanted]
        if not match:
            print(f"Page {wanted} not loaded (outside {FIRST_CONTENT_PAGE}-{LAST_CONTENT_PAGE}, or empty)")
            return 1
        print(match[0].metadata)
        print("-" * 80)
        print(match[0].page_content)
        return 0

    expected = LAST_CONTENT_PAGE - FIRST_CONTENT_PAGE + 1
    loaded = {p.metadata["page"] for p in pages}
    empty = [n for n in range(FIRST_CONTENT_PAGE, LAST_CONTENT_PAGE + 1) if n not in loaded]
    leaks = [p.metadata["page"] for p in pages if LEAK_PATTERN.search(p.page_content)]
    total_chars = sum(len(p.page_content) for p in pages)

    print(f"Loaded {len(pages)} of {expected} content pages, {total_chars:,} characters")
    print(f"Empty pages skipped: {empty or 'none'}")
    print(f"Pages where header/footer text survived: {leaks or 'none'}")
    return 1 if leaks else 0


if __name__ == "__main__":
    sys.exit(main())
