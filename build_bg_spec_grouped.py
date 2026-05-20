"""
Build a spec.json for Ads Uploader CLI that splits the 61 BG vein ads into
ad sets by category, max 5 ads per ad set.
"""
import json
from collections import OrderedDict
from pathlib import Path

BG_JSON = Path("/Users/magi/Downloads/vitalaiz 3/Veins New ads/translations/BG.json")
OUT_SPEC = Path("/Users/magi/Downloads/vitalaiz 3/Veins New ads/spec_BG_grouped.json")

PRESET_ID = "6a05933abbfc49049c014f4f"
UPLOAD_ID = "batch_252c19118356ba3875cc4a01"
MAX_PER_ADSET = 5

CATEGORY_ORDER = [
    "anatomy", "article", "before-after", "chart", "copy",
    "diary", "product", "review-list", "social-fb", "stat-hook",
    "testimonial-quote", "visual",
]


def category_of(filename: str) -> str:
    return filename.split("_")[0]


def chunked(items, size):
    for i in range(0, len(items), size):
        yield items[i:i + size]


def main():
    data = json.loads(BG_JSON.read_text())
    by_cat: dict[str, list[dict]] = OrderedDict()
    for cat in CATEGORY_ORDER:
        by_cat[cat] = []
    for r in data:
        by_cat.setdefault(category_of(r["filename"]), []).append(r)

    groups = []
    per_ad = {}
    for cat in CATEGORY_ORDER:
        cat_files = sorted(by_cat.get(cat, []), key=lambda r: r["filename"])
        if not cat_files:
            continue
        chunks = list(chunked(cat_files, MAX_PER_ADSET))
        for i, chunk in enumerate(chunks, 1):
            suffix = f" {i}/{len(chunks)}" if len(chunks) > 1 else ""
            group_name = f"Veins | {cat}{suffix}"
            groups.append({
                "name": group_name,
                "media": [r["filename"] for r in chunk],
            })
            for r in chunk:
                per_ad[r["filename"]] = {
                    "headlines": r["headlines"],
                    "bodies": [r["primary_text"]],
                }

    spec = {
        "adPresetId": PRESET_ID,
        "uploadId": UPLOAD_ID,
        "adSet": {
            "groups": groups,
        },
        "texts": {
            "perAd": per_ad,
            "strategy": "flexible",
        },
        "options": {
            "status": "PAUSED",
            "pauseAt": "ad",
        },
    }

    OUT_SPEC.write_text(json.dumps(spec, indent=2, ensure_ascii=False))
    print(f"Wrote {OUT_SPEC}")
    print(f"  Ad sets: {len(groups)}")
    print(f"  Ads total: {sum(len(g['media']) for g in groups)}")
    print(f"  Layout:")
    for g in groups:
        print(f"    {g['name']:35s}  {len(g['media'])} ads")


if __name__ == "__main__":
    main()
