"""Corpus manifest: which documents we use, and a check that the files on disk match.

Run:  uv run python -m stmragged.corpus
"""

import hashlib
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = PROJECT_ROOT / "corpus" / "manifest.toml"


@dataclass(frozen=True)
class Document:
    doc_id: str
    title: str
    revision: str
    date: str
    pages: int
    path: Path
    sha256: str
    url: str


def load_manifest() -> list[Document]:
    with open(MANIFEST_PATH, "rb") as f:
        raw = tomllib.load(f)
    docs = []
    for d in raw["documents"]:
        d["path"] = PROJECT_ROOT / d["path"]  # manifest paths are relative to the repo root
        docs.append(Document(**d))
    return docs


def verify(docs: list[Document]) -> list[str]:
    """Return a list of problems. An empty list means the files match the manifest."""
    problems = []
    for doc in docs:
        if not doc.path.exists():
            problems.append(f"{doc.doc_id}: file not found at {doc.path}. Download it from {doc.url}")
            continue
        actual = hashlib.sha256(doc.path.read_bytes()).hexdigest()
        if actual != doc.sha256:
            problems.append(
                f"{doc.doc_id}: hash mismatch, probably not {doc.revision}\n"
                f"  expected {doc.sha256}\n"
                f"  actual   {actual}"
            )
    return problems


def main() -> int:
    docs = load_manifest()
    problems = verify(docs)
    if problems:
        print("Corpus check FAILED")
        print("\n".join(problems))
        return 1
    for doc in docs:
        print(f"OK  {doc.doc_id} {doc.revision}, {doc.pages} pages")
    return 0


if __name__ == "__main__":
    sys.exit(main())
