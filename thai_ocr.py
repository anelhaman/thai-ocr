"""thai-ocr: command-line wrapper around OpenThai2.0-OCR-Text (iApp, Apache-2.0).

Runs fully offline on the CPU. Reads PDFs (each page is rendered, then OCR'd) and images.
Always run through the venv python in isolated mode (see bin/thai-ocr).
"""
import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

HOME = Path(os.environ.get("THAI_OCR_HOME", Path(__file__).resolve().parent))
MODEL_DIR = HOME / "model"
IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}

# --- opt-in baht fix ---------------------------------------------------------
# The recogniser often reads the baht sign as "B" or "8" (e.g. "฿114.92" -> "8114.92").
AMOUNT = r"\d{1,3}(?:,\d{3})*\.\d{2}"
BARE = re.compile(rf"(?<![\w.,])({AMOUNT})(?!\d)")
PREFIXED = re.compile(rf"(?<![\w.,])([B8])({AMOUNT})(?!\d)")


def fix_baht(text: str):
    """B<amount> -> ฿<amount>. 8<amount> -> ฿<amount> only when <amount> also appears
    on its own elsewhere on the page (otherwise a real 8114.92 would be damaged)."""
    standalone = set(BARE.findall(text))
    changes = []

    def sub(m):
        lead, amount = m.group(1), m.group(2)
        if lead == "B" or amount in standalone:
            changes.append(f"{m.group(0)} -> ฿{amount}")
            return "฿" + amount
        return m.group(0)

    return PREFIXED.sub(sub, text), changes


def main():
    ap = argparse.ArgumentParser(
        prog="thai-ocr",
        description="OCR Thai/English printed text from PDFs and images (OpenThai2.0-OCR-Text, offline, CPU).",
    )
    ap.add_argument("files", nargs="+", metavar="FILE", help="PDF or image file(s)")
    ap.add_argument("-o", "--out", metavar="DIR", help="write <name>.txt (and .json) into DIR instead of printing")
    ap.add_argument("--json", action="store_true", help="also output lines with boxes and confidence (to .json in -o mode, to stdout otherwise)")
    ap.add_argument("--dpi", type=int, default=200, help="PDF render resolution (default 200)")
    ap.add_argument("--threads", type=int, default=min(4, os.cpu_count() or 1), help="CPU threads (default min(4, cores))")
    ap.add_argument("--pages", metavar="N-M", help="only these PDF pages, 1-based, e.g. 2 or 1-3")
    ap.add_argument("--headers", action="store_true", help="print '===== file / page N =====' headers in stdout mode")
    ap.add_argument("--fix-baht", action="store_true", help="heuristically repair ฿ misread as B/8 before an amount (changes are listed on stderr)")
    ap.add_argument("-q", "--quiet", action="store_true", help="no progress on stderr")
    a = ap.parse_args()

    def log(msg):
        if not a.quiet:
            print(msg, file=sys.stderr, flush=True)

    sys.path.insert(0, str(MODEL_DIR))  # explicit: python -I does not add any path itself
    import pymupdf

    from runtime.line_engine import LineOCR

    ocr = LineOCR(str(MODEL_DIR), threads=a.threads)
    out_dir = Path(a.out).expanduser() if a.out else None
    if out_dir:
        out_dir.mkdir(parents=True, exist_ok=True)

    lo = hi = None
    if a.pages:
        p = a.pages.split("-")
        lo, hi = int(p[0]), int(p[-1])

    rc, stdout_json = 0, []
    for f in a.files:
        src = Path(f).expanduser()
        if not src.is_file():
            log(f"thai-ocr: not a file: {src}")
            rc = 1
            continue
        items = []  # (page number, png/image bytes)
        if src.suffix.lower() == ".pdf":
            doc = pymupdf.open(src)
            for i, page in enumerate(doc, 1):
                if (lo and i < lo) or (hi and i > hi):
                    continue
                items.append((i, page.get_pixmap(dpi=a.dpi).tobytes("png")))
        elif src.suffix.lower() in IMAGE_EXT:
            items.append((1, src.read_bytes()))
        else:
            log(f"thai-ocr: unsupported file type: {src.name}")
            rc = 1
            continue

        texts, dump, t_all = [], [], 0.0
        for n, data in items:
            t0 = time.time()
            r = ocr.read(data)
            t_all += time.time() - t0
            text = r["text"]
            if a.fix_baht:
                text, changes = fix_baht(text)
                for c in changes:
                    log(f"fix-baht [{src.name} p{n}]: {c}")
            texts.append((n, text))
            dump.append({
                "file": src.name, "page": n, "rotation": r["rotation"], "text": text,
                "lines": [{"text": l["text"], "confidence": round(l["confidence"], 4),
                           "box": [[round(float(x), 1) for x in pt] for pt in l["box"]]} for l in r["lines"]],
            })
        log(f"{src.name}: {len(items)} page(s), {t_all:.2f}s ({t_all / max(len(items), 1):.2f}s/page)")

        if out_dir:
            body = "\n".join(f"===== page {n} =====\n{t}\n" for n, t in texts)
            (out_dir / f"{src.stem}.txt").write_text(body, encoding="utf-8")
            if a.json:
                (out_dir / f"{src.stem}.json").write_text(json.dumps(dump, ensure_ascii=False, indent=1), encoding="utf-8")
            log(f"-> {out_dir / (src.stem + '.txt')}")
        elif a.json:
            stdout_json.extend(dump)
        else:
            for n, t in texts:
                if a.headers:
                    print(f"===== {src.name} / page {n} =====")
                print(t)
                print()

    if stdout_json:
        print(json.dumps(stdout_json, ensure_ascii=False, indent=1))
    sys.exit(rc)


if __name__ == "__main__":
    main()
