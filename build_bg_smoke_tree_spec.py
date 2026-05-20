"""
Build the Ads Uploader spec.json for the Smoke Tree BG launch.

Inputs:
- preset:  6a06dcf9bbfc49049c069ed2  (Website advertorial | Sumac pack)
- upload:  batch_8bc3af399af89bf853681b42
- copy:    /Users/magi/Downloads/AI ADS MAY/{folder}/{label}_AdCopy_BG.json

Output:
- /Users/magi/ads-agent/storage/bg_smoke_tree_spec.json

Splits 24 creatives into 5 themed ad sets with per-ad Bulgarian text.
"""
import json
from pathlib import Path

PRESET_ID = "6a06dcf9bbfc49049c069ed2"
UPLOAD_ID = "batch_8bc3af399af89bf853681b42"
LANDING_URL = (
    "https://inaessentials.com/blogs/new/"
    "%D0%B1%D1%8A%D0%BB%D0%B3%D0%B0%D1%80%D1%81%D0%BA%D0%B0%D1%82%D0%B0-"
    "%D0%B1%D0%B8%D0%BB%D0%BA%D0%B0-%D1%81%D1%80%D0%B5%D1%89%D1%83-"
    "%D0%BA%D1%8A%D1%80%D0%B2%D1%8F%D1%89%D0%B8-%D0%B2%D0%B5%D0%BD%D1%86%D0%B8"
)
ROOT = Path("/Users/magi/Downloads/AI ADS MAY")
OUT = Path("/Users/magi/ads-agent/storage/bg_smoke_tree_spec.json")

CTA_MAP = {
    "Научи повече":      "LEARN_MORE",
    "Виж повече":        "LEARN_MORE",
    "Открий продукта":   "LEARN_MORE",
    "Купи сега":         "SHOP_NOW",
    "Поръчай сега":      "ORDER_NOW",
}

GROUPS = [
    {
        "name": "Smoke Tree | BG | Set 1 UGC Relatable",
        "media": [
            "08_ugc_mirror_teeth_check.png",
            "09_ugc_hand_covering_mouth.png",
            "10_ugc_toothbrush_moment.png",
        ],
    },
    {
        "name": "Smoke Tree | BG | Set 2 Stat & Educational",
        "media": [
            "04_whiteboard_why_bad_breath_returns.png",
            "05_anatomy_diagram_tongue_bacteria.png",
            "07_stat_surround_one_in_three.png",
            "13_leaf_macro_with_stat.png",
            "A05_tongue_coating.png",
        ],
    },
    {
        "name": "Smoke Tree | BG | Set 3 Heritage & Bold Statement",
        "media": [
            "01_breaking_news_gum_headline.png",
            "03_mystery_hook_article.png",
            "11_pink_smoke_tree_with_headline.png",
            "14_color_block_bold_statement.png",
        ],
    },
    {
        "name": "Smoke Tree | BG | Set 4 Diagnostic Close-ups",
        "media": [
            "A01_gum_recession_diagnostic.png",
            "A02_bleeding_gums_diagnostic.png",
            "A03_gingivitis_inflammation.png",
            "A04_tartar_at_gumline.png",
            "A06_exposed_tooth_root.png",
            "A07_periodontal_pocket.png",
            "A08_plaque_buildup.png",
        ],
    },
    {
        "name": "Smoke Tree | BG | Set 5 Smoke Tree Nature",
        "media": [
            "hf_20260514_142022_79e54613-3c54-4a3e-b21a-7362b8ec9547.png",
            "hf_20260514_142124_10609a2d-6875-4003-bc2b-749cd629f0d4.png",
            "hf_20260515_060236_d5319956-8e84-4edf-95c2-91c8162495a9.png",
            "hf_20260515_060324_c4173df7-fec4-45b6-a768-7192c042feb1.png",
            "hf_20260515_060350_10be5a72-7baa-46d4-b014-c82b652cb80d.png",
        ],
    },
]


def load_copy() -> dict[str, dict]:
    """Pull BG copy directly from the build_smoke_tree_docx module."""
    from build_smoke_tree_docx import GENERAL, GUM_RECESSION
    out = {}
    for item in GENERAL + GUM_RECESSION:
        out[item["filename"]] = {
            "filename": item["filename"],
            "headlines": item["headlines"],
            "primary": item["primary"],
            "cta": item["cta"],
        }
    return out


def main():
    copy = load_copy()
    per_ad = {}
    seen = set()
    for grp in GROUPS:
        for fname in grp["media"]:
            seen.add(fname)
            if fname not in copy:
                raise KeyError(f"No BG copy for {fname}")
            item = copy[fname]
            cta = CTA_MAP.get(item["cta"].strip(), "LEARN_MORE")
            per_ad[fname] = {
                "headlines": item["headlines"],
                "bodies":    [item["primary"]],
                "cta":       cta,
                "link":      LANDING_URL,
            }
    missing = set(copy.keys()) - seen
    if missing:
        raise RuntimeError(f"Copy entries not assigned to any ad set: {missing}")

    spec = {
        "adPresetId": PRESET_ID,
        "uploadId":   UPLOAD_ID,
        "adSet": {
            "groups":      [{"name": g["name"], "media": g["media"]} for g in GROUPS],
            "namePattern": "{group}",
        },
        "texts": {
            "perAd":    per_ad,
            "strategy": "flexible",
        },
        "adNamePattern": "Smoke Tree | BG | {filename}",
        "options": {
            "status":  "ACTIVE",
            "pauseAt": "ad",
        },
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {OUT}  ({OUT.stat().st_size} bytes)")
    print(f"  ad sets: {len(GROUPS)}")
    print(f"  ads:     {sum(len(g['media']) for g in GROUPS)}")
    print(f"  per-ad texts: {len(per_ad)}")


if __name__ == "__main__":
    main()
