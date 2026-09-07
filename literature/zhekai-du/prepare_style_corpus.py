"""Extract local PDFs reproducibly; keep copyrighted derived text under texts/."""

import hashlib
import json
import re
import subprocess
import unicodedata
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent


def normalize(text):
    text = unicodedata.normalize("NFKC", text).replace("\x00", "")
    return re.sub(r"(?<=[a-z])-\n(?=[a-z])", "", text)


def main():
    destination = ROOT / "texts" / "normalized"
    destination.mkdir(parents=True, exist_ok=True)
    manifest = []
    for path in sorted((ROOT / "pdfs").glob("*.pdf")):
        paper_id = path.name[:4] if path.name.startswith("P0") else "P047"
        reader = PdfReader(path)
        pages = []
        for index in range(len(reader.pages)):
            result = subprocess.run(
                ["pdftotext", "-f", str(index + 1), "-l", str(index + 1),
                 "-enc", "UTF-8", str(path), "-"],
                check=True, capture_output=True, text=True,
            )
            pages.append(normalize(result.stdout).replace("\f", ""))
        (destination / f"{paper_id}.txt").write_text(
            "\n".join(f"[PDF PAGE {i + 1}]\n{p}" for i, p in enumerate(pages)),
            encoding="utf-8",
        )
        manifest.append({
            "id": paper_id, "file": str(path.relative_to(ROOT)),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "pages": len(pages),
            "extracted_full_pdf_word_count_approx": len(re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?", "\n".join(pages))),
            "first_page_author_check": "Zhekai Du" in pages[0],
        })
    (ROOT / "corpus_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
