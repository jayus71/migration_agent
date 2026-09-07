"""Prepare audited prose selections and supplement the skill's PDF-blind metrics."""

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WORD = re.compile(r"[A-Za-z]+(?:'[A-Za-z]+)?")
NUMERIC_CITE = re.compile(r"\[(\d+(?:\s*[,\u2013\u2014-]\s*\d+)*)\]")
NAMED_CITE = re.compile(r"\([^()]*\b(?:19|20)\d{2}[a-z]?\b[^()]*\)")


def clean_citations(text):
    return NAMED_CITE.sub("", NUMERIC_CITE.sub("", text))


def main():
    selections = json.loads((ROOT / "prose_selection.json").read_text())
    manifest = {p["id"]: p for p in json.loads((ROOT / "corpus_manifest.json").read_text())}
    output_dir = ROOT / "texts" / "prose"
    output_dir.mkdir(exist_ok=True)
    records = []
    for paper_id, sections in selections.items():
        # Selection line numbers follow newline-only tools such as nl, not Unicode separators.
        lines = (ROOT / "texts" / "normalized" / f"{paper_id}.txt").read_text().split("\n")
        parts = []
        section_counts = {}
        citation_groups = 0
        citation_items = 0
        for name, spans in sections.items():
            text = "\n".join("\n".join(lines[a - 1:b]) for a, b in spans)
            text = re.sub(r"(?<=[a-z])-\s*\n\s*(?=[a-z])", "", text)
            text = re.sub(r"\s+", " ", text).strip()
            text = text.removeprefix("Abstract\u2014")
            if paper_id == "P047" and name == "introduction":
                text = re.sub(r"^HE rapid", "THE rapid", text)
            numeric = NUMERIC_CITE.findall(text)
            named = NAMED_CITE.findall(text)
            citation_groups += len(numeric) + len(named)
            for group in numeric:
                for item in group.split(","):
                    ends = re.split(r"\s*[\u2013\u2014-]\s*", item.strip())
                    citation_items += int(ends[-1]) - int(ends[0]) + 1 if len(ends) == 2 else 1
            citation_items += sum(len(re.findall(r"\b(?:19|20)\d{2}[a-z]?\b", group)) for group in named)
            prose = clean_citations(text)
            prose = re.sub(r"\s+([,.;:])", r"\1", prose)
            prose = re.sub(r"\s+", " ", prose).strip()
            assert prose.endswith((".", "?", "!")), (paper_id, name, "incomplete section")
            section_counts[name] = len(WORD.findall(prose))
            parts.append(prose)
        joined = "\n\n".join(parts)
        (output_dir / f"{paper_id}.txt").write_text(joined + "\n", encoding="utf-8")
        words = len(WORD.findall(joined))
        records.append({
            "id": paper_id,
            "normalized_text_sha256": hashlib.sha256(
                (ROOT / "texts" / "normalized" / f"{paper_id}.txt").read_bytes()
            ).hexdigest(),
            "pdf_sha256": manifest[paper_id]["sha256"],
            "section_word_counts": section_counts,
            "prose_words": words,
            "citation_groups": citation_groups,
            "citation_items": citation_items,
            "citation_groups_per_1000_prose_words": round(citation_groups * 1000 / words, 2),
            "citation_items_per_1000_prose_words": round(citation_items * 1000 / words, 2),
        })
    (ROOT / "prose_metrics.json").write_text(json.dumps(records, indent=2) + "\n")
    metadata = json.loads((ROOT / "layout_selection.json").read_text())
    for paper_id, record in metadata.items():
        lines = (ROOT / "texts" / "normalized" / f"{paper_id}.txt").read_text().split("\n")
        a, b = record["figure_1_caption_lines"]
        caption = " ".join(lines[a - 1:b])
        assert re.match(r"^(Fig\.|Figure)\s+1[.:]", caption), (paper_id, "caption boundary")
        caption = re.sub(r"^(Fig\.|Figure)\s+1[.:]\s*", "", caption)
        record["figure_1_caption_words_approx"] = len(WORD.findall(clean_citations(caption)))
    (ROOT / "layout_metrics.json").write_text(json.dumps(metadata, indent=2) + "\n")


if __name__ == "__main__":
    main()
