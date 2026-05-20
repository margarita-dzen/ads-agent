"""
Generic spec builder for text-overlaid designs (BG, SK, etc.).
Maps each design file (hf_YYYYMMDD_HHMMSS_<uuid>_XX.png) to copy via the
HHMMSS timestamp -> original sorted/ filename mapping.
"""
import argparse
import json
import os
import re
from collections import OrderedDict
from pathlib import Path

ORIG_BG_JSON = Path("/Users/magi/Downloads/vitalaiz 3/Veins New ads/translations/BG.json")
TRANS_DIR = Path("/Users/magi/Downloads/vitalaiz 3/Veins New ads/translations")
MAX_PER_ADSET = 5

CATEGORY_ORDER = [
    "anatomy", "article", "before-after", "chart", "copy",
    "diary", "product", "review-list", "social-fb", "stat-hook",
    "testimonial-quote", "visual",
]


def category_of(filename: str) -> str:
    return filename.split("_")[0]


def extract_ts_from_design(filename: str) -> "str | None":
    m = re.match(r"hf_\d{8}_(\d{6})_", filename)
    return m.group(1) if m else None


def extract_ts_from_original(filename: str) -> "str | None":
    m = re.search(r"_(\d{6})(?:_|\.)", filename)
    return m.group(1) if m else None


def chunked(items, size):
    for i in range(0, len(items), size):
        yield items[i:i + size]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--lang", required=True, help="Language code, e.g. BG, SK")
    p.add_argument("--designs", required=True, help="Folder with hf_*_LANG.png design files")
    p.add_argument("--preset", required=True, help="Ads Uploader preset ID")
    p.add_argument("--upload", required=True, help="Upload batch ID")
    p.add_argument("--out", required=True, help="Output spec.json path")
    args = p.parse_args()

    # Load language translations
    lang_json = TRANS_DIR / f"{args.lang.upper()}.json"
    lang_data = json.loads(lang_json.read_text())

    # Map timestamp -> (original filename, language copy)
    orig_bg = json.loads(ORIG_BG_JSON.read_text())
    ts_to_origfn = {}
    for r in orig_bg:
        ts = extract_ts_from_original(r["filename"])
        if ts:
            ts_to_origfn[ts] = r["filename"]
    fn_to_lang_copy = {r["filename"]: r for r in lang_data}

    # List design files
    design_dir = Path(args.designs)
    design_files = sorted(
        f.name for f in design_dir.iterdir()
        if f.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp", ".gif")
    )

    # Map each design file to original filename via timestamp
    matched, unmapped = [], []
    for df in design_files:
        ts = extract_ts_from_design(df)
        orig_fn = ts_to_origfn.get(ts)
        if orig_fn and orig_fn in fn_to_lang_copy:
            matched.append((df, fn_to_lang_copy[orig_fn]))
        else:
            unmapped.append(df)

    print(f"Designs: {len(design_files)}")
    print(f"Matched to copy: {len(matched)}")
    print(f"Unmapped (no copy): {len(unmapped)}")
    if unmapped:
        for f in unmapped:
            print(f"  skip: {f}")

    # Build per-ad text + grouping by category, max 5 per group
    by_cat: dict[str, list[tuple[str, dict]]] = OrderedDict()
    for cat in CATEGORY_ORDER:
        by_cat[cat] = []
    for df, copy in matched:
        cat = category_of(copy["filename"])
        by_cat.setdefault(cat, []).append((df, copy))

    groups, per_ad = [], {}
    for cat in CATEGORY_ORDER:
        items = sorted(by_cat.get(cat, []), key=lambda x: x[1]["filename"])
        if not items:
            continue
        chunks = list(chunked(items, MAX_PER_ADSET))
        for i, chunk in enumerate(chunks, 1):
            suffix = f" {i}/{len(chunks)}" if len(chunks) > 1 else ""
            groups.append({
                "name": f"Veins | {cat}{suffix}",
                "media": [df for df, _ in chunk],
            })
            for df, copy in chunk:
                per_ad[df] = {
                    "headlines": copy["headlines"],
                    "bodies": [copy["primary_text"]],
                }

    spec = {
        "adPresetId": args.preset,
        "uploadId": args.upload,
        "adSet": {"groups": groups},
        "texts": {"perAd": per_ad, "strategy": "flexible"},
        "options": {"status": "PAUSED", "pauseAt": "ad"},
    }
    Path(args.out).write_text(json.dumps(spec, indent=2, ensure_ascii=False))
    print(f"\nWrote {args.out}")
    print(f"  Ad sets: {len(groups)}  |  Ads: {sum(len(g['media']) for g in groups)}")
    for g in groups:
        print(f"    {g['name']:35s}  {len(g['media'])} ads")


if __name__ == "__main__":
    main()
