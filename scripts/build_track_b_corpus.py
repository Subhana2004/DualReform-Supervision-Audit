"""Acquire a small, attributed Wikipedia lead snapshot; never uses benchmark gold fields."""
import argparse
import hashlib
import json
from pathlib import Path
import time
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from dualreform_audit.io import write_jsonl


def acquire(titles, output):
    if not titles or len(set(titles)) != len(titles):
        raise ValueError("Titles must be distinct and nonempty")
    docs = []
    for start in range(0, len(titles), 10):
        batch = titles[start:start + 10]
        url = "https://en.wikipedia.org/w/api.php?" + urlencode({
            "action": "query", "titles": "|".join(batch), "prop": "extracts|revisions",
            "exintro": "1", "explaintext": "1", "exlimit": "20", "rvprop": "ids", "redirects": "1",
            "format": "json", "formatversion": "2"})
        request = Request(url, headers={"User-Agent":
                          "DualReformTrackB/1.0 (independent reproducibility audit)"})
        for attempt in range(4):
            try:
                with urlopen(request, timeout=30) as response:
                    payload = json.load(response)
                break
            except HTTPError as exc:
                if exc.code != 429 or attempt == 3:
                    raise
                time.sleep(5 * (attempt + 1))
        pages = payload["query"]["pages"]
        if len(pages) != len(batch):
            raise ValueError(f"Missing or redirected-duplicate Wikipedia pages: {batch}")
        for page in pages:
            if "missing" in page or not page.get("extract") or not page.get("revisions"):
                raise ValueError(f"Missing Wikipedia lead: {page.get('title')}")
            revision = page["revisions"][0]["revid"]
            text = page["extract"].strip()
            docs.append({"doc_id": f"enwiki:{page['pageid']}", "title": page["title"],
                         "revision_id": revision,
                         "revision_url": f"https://en.wikipedia.org/w/index.php?oldid={revision}",
                         "text": text, "text_sha256": hashlib.sha256(text.encode()).hexdigest()})
        time.sleep(1.5)
    if len({d["doc_id"] for d in docs}) != len(docs):
        raise ValueError("Redirected duplicate Wikipedia page")
    write_jsonl(Path(output), docs)
    return docs


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/track_b.yaml")
    parser.add_argument("--refresh", action="store_true",
                        help="Explicitly replace the committed snapshot with current revisions")
    args = parser.parse_args()
    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    if Path(config["corpus_path"]).exists() and not args.refresh:
        raise SystemExit("Corpus snapshot exists; use --refresh only to create a new version")
    print(json.dumps({"documents": len(acquire(config["titles"], config["corpus_path"]))}))
