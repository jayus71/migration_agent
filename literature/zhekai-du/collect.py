"""Collect public bibliographic records and openly accessible author papers."""

import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import shutil
import time
import unicodedata
import urllib.parse
import xml.etree.ElementTree as ET

from bs4 import BeautifulSoup
from pypdf import PdfReader
import requests

ROOT = Path(__file__).resolve().parent
AUTHOR_ID = "A5003786587"
SESSION = requests.Session()
SESSION.headers["User-Agent"] = "AcademicPaperCollection/1.0 (personal literature research)"


def save_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def normalize(title):
    return re.sub(r"[^a-z0-9]", "", unicodedata.normalize("NFKD", title).lower())


def get(url, **kwargs):
    response = SESSION.get(url, timeout=(15, 45), **kwargs)
    response.raise_for_status()
    return response


def discover():
    sources = ROOT / "sources"
    sources.mkdir(exist_ok=True)
    author = get(f"https://api.openalex.org/authors/{AUTHOR_ID}").json()
    save_json(sources / "openalex-author.json", author)
    works = get("https://api.openalex.org/works", params={
        "filter": f"author.id:{AUTHOR_ID}", "per-page": 200,
        "sort": "publication_date:desc",
    }).json()
    save_json(sources / "openalex-works.json", works)
    arxiv = get("https://export.arxiv.org/api/query", params={
        "search_query": 'au:"Zhekai Du"', "max_results": 100,
    }).text
    (sources / "arxiv.xml").write_text(arxiv)
    grouped = {}
    for work in works["results"]:
        if not any(a["author_position"] == "first"
                   and (a["author"]["id"] or "").endswith(AUTHOR_ID)
                   for a in work["authorships"]):
            continue
        # Audiovisual conference records are not additional papers.
        locations = work.get("locations", [])
        if any(loc.get("raw_type") == "Audiovisual" for loc in locations):
            continue
        key = normalize(work["title"])
        record = grouped.setdefault(key, {
            "title": work["title"], "year": work["publication_year"],
            "authors": [a["author"]["display_name"] for a in work["authorships"]],
            "author_position": next((a["author_position"] for a in work["authorships"]
                                     if (a["author"]["id"] or "").endswith(AUTHOR_ID)), None),
            "records": [], "pdf_candidates": [], "landing_pages": [],
        })
        record["records"].append({
            "openalex_id": work["id"], "doi": work.get("doi"),
            "year": work["publication_year"], "type": work["type"],
            "venue": (work.get("primary_location") or {}).get("raw_source_name"),
            "authorship": next((a for a in work["authorships"]
                                if (a["author"]["id"] or "").endswith(AUTHOR_ID)), None),
        })
        for loc in locations:
            if loc.get("pdf_url"):
                record["pdf_candidates"].append(loc["pdf_url"])
            if loc.get("landing_page_url"):
                record["landing_pages"].append(loc["landing_page_url"])
    ns = {"a": "http://www.w3.org/2005/Atom"}
    for entry in ET.fromstring(arxiv).findall("a:entry", ns):
        title = " ".join(entry.findtext("a:title", namespaces=ns).split())
        key = normalize(title)
        authors = [a.findtext("a:name", namespaces=ns) for a in entry.findall("a:author", ns)]
        if not authors or normalize(authors[0]) != "zhekaidu":
            continue
        record = grouped.setdefault(key, {
            "title": title, "year": int(entry.findtext("a:published", namespaces=ns)[:4]),
            "authors": authors, "author_position": "first" if authors[0] == "Zhekai Du" else "middle",
            "records": [], "pdf_candidates": [], "landing_pages": [],
        })
        record["arxiv_id"] = entry.findtext("a:id", namespaces=ns).rsplit("/", 1)[-1]
        record["pdf_candidates"].insert(0, "https://arxiv.org/pdf/" + record["arxiv_id"])
    records = sorted(grouped.values(), key=lambda r: (r["year"], r["title"]))
    for index, record in enumerate(records, 1):
        record["id"] = f"P{index:03}"
        record["pdf_candidates"] = list(dict.fromkeys(record["pdf_candidates"]))
        record["landing_pages"] = list(dict.fromkeys(record["landing_pages"]))
        record["status"] = "pending"
        record["attempts"] = []
    save_json(ROOT / "catalog.json", records)
    for record in records:
        print(record["id"], record["year"], record["author_position"], record["title"],
              "PDF candidates:", len(record["pdf_candidates"]))


def store_pdf(record, content, url):
    if not content.startswith(b"%PDF-") or len(content) < 10000:
        raise ValueError("response is not a full PDF")
    reader = PdfReader(io.BytesIO(content))
    if len(reader.pages) < 3:
        raise ValueError("fewer than three pages; needs manual review")
    pages = [page.extract_text() or "" for page in reader.pages]
    first_pages = normalize(" ".join(pages[:2]))
    if "zhekaidu" not in first_pages:
        raise ValueError("author not found on first two pages; needs manual review")
    if "abstract" not in first_pages or "introduction" not in normalize(" ".join(pages[:3])):
        raise ValueError("abstract/introduction missing; possible supplement or preview")
    filename = f"{record['id']}_{record['year']}_{re.sub(r'[^a-zA-Z0-9]+', '_', record['title']).strip('_')[:140]}.pdf"
    (ROOT / "pdfs" / filename).write_bytes(content)
    textfile = ROOT / "texts" / (Path(filename).stem + ".txt")
    textfile.write_text("\n\n".join(f"[PDF PAGE {i+1}]\n{p}" for i, p in enumerate(pages)))
    record.update({"status": "downloaded", "pdf": f"pdfs/{filename}",
                   "text": f"texts/{textfile.name}", "download_url": url,
                   "sha256": hashlib.sha256(content).hexdigest(),
                   "bytes": len(content), "pages": len(pages)})


def download(ids=None):
    records = json.loads((ROOT / "catalog.json").read_text())
    for name in ("pdfs", "texts"):
        (ROOT / name).mkdir(exist_ok=True)
    for record in records:
        if record["status"] == "downloaded" or (ids and record["id"] not in ids):
            continue
        candidates = list(record["pdf_candidates"])
        attempted = {a["url"] for a in record["attempts"]}
        for url in candidates + record["landing_pages"]:
            if url in attempted:
                continue
            attempted.add(url)
            try:
                response = get(url.replace("http://arxiv.org", "https://arxiv.org"))
                if response.content.startswith(b"%PDF-"):
                    store_pdf(record, response.content, response.url)
                else:
                    soup = BeautifulSoup(response.text, "html.parser")
                    meta = soup.find("meta", attrs={"name": "citation_pdf_url"})
                    links = []
                    if meta and meta.get("content"):
                        links.append(urllib.parse.urljoin(response.url, meta["content"]))
                    for a in soup.find_all("a", href=True):
                        href = a["href"]
                        if (href.lower().endswith(".pdf") or "/article/download/" in href
                                or (a.get_text(strip=True).lower() in {"pdf", "download pdf"})):
                            links.append(urllib.parse.urljoin(response.url, href))
                    if not links:
                        raise ValueError("landing page has no public PDF link")
                    for link in dict.fromkeys(links):
                        if link in attempted:
                            continue
                        attempted.add(link)
                        try:
                            pdf = get(link)
                            store_pdf(record, pdf.content, pdf.url)
                            break
                        except Exception as error:
                            record["attempts"].append({"url": link, "error": str(error)[:250]})
                if record["status"] == "downloaded":
                    print("DOWNLOADED", record["id"], record["pages"], record["title"], flush=True)
                    break
            except Exception as error:
                record["attempts"].append({"url": url, "error": str(error)[:250]})
            time.sleep(1)
        if record["status"] != "downloaded":
            record["status"] = "unavailable"
            print("UNAVAILABLE", record["id"], record["title"], flush=True)
        save_json(ROOT / "catalog.json", records)


def focus(excluded):
    records = json.loads((ROOT / "catalog.json").read_text())
    save_json(ROOT / "sources/all-author-catalog.json", records)
    first = []
    for record in records:
        if record["author_position"] == "first":
            first.append(record)
            continue
        for key in ("pdf", "text"):
            if record.get(key):
                source = ROOT / record[key]
                target = excluded / record[key]
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(source, target)
    save_json(excluded / "excluded-records.json", [r for r in records if r["author_position"] != "first"])
    # The longer arXiv title and the ACM title describe the same AED method,
    # by the same five authors. Keep one corpus sample with both records.
    published = next(r for r in first if r["title"] == "Adversarial Energy Disaggregation")
    preprint = next(r for r in first if r["title"].startswith("Adversarial Energy Disaggregation for"))
    preprint["alternate_title"] = published["title"]
    preprint["records"].extend(published["records"])
    preprint["attempts"].extend(published["attempts"])
    preprint["version_note"] = "Grouped by matching five authors, AED method, and title; downloaded copy is the arXiv manuscript."
    first.remove(published)
    save_json(ROOT / "catalog.json", first)
    print(f"First-author works: {len(first)}; downloaded: {sum(r['status'] == 'downloaded' for r in first)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["discover", "download", "focus"])
    parser.add_argument("--ids", nargs="*")
    parser.add_argument("--excluded-dir", type=Path)
    args = parser.parse_args()
    if args.action == "discover":
        discover()
    elif args.action == "download":
        download(args.ids)
    elif args.excluded_dir:
        focus(args.excluded_dir)
    else:
        parser.error("focus requires --excluded-dir")
