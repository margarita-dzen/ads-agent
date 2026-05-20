"""
Build TOF spec for Greek (_GR suffix) veins creatives.
- Strip _GR to map to EN theme_map + EL ad copy (Greek text).
- UUID-prefixed files (no EN match) go into a "Storytelling / Real Stories" bucket
  and use the preset's default ad copy (no per-ad override).
- Theme-based grouping, max 5 per ad set, balanced chunking.
"""
import json
import math
from pathlib import Path

BASE = Path("/Users/magi/Downloads/Vein new ads 17.05")
GR_DIR = BASE / "GR_designs" / "GR"
EL_COPY_JSON = BASE / "Ad copy 17.05." / "ad_copy_TOF_EL.json"
THEME_MAP_JSON = BASE / "Ad copy 17.05." / "theme_map.json"
SPEC_OUT = BASE / "_specs" / "spec_TOF_GR_localized.json"

PRESET_ID = "6a05a996bbfc49049c01e42b"  # Advertorial Veins General | GR
ACCOUNT_ID = "act_1152767151915470"     # InaEssentials NEW
MAX_PER_ADSET = 5

UUID_BUCKET = "Storytelling / Real Stories"


def strip_gr(fn: str) -> str:
    base = fn.replace("_GR.png", ".png").replace("_GR.jpg", ".jpg")
    return base


def balanced_chunks(items, max_size):
    n = len(items)
    if n <= max_size:
        return [items]
    n_chunks = math.ceil(n / max_size)
    base = n // n_chunks
    rem = n % n_chunks
    sizes = [base + 1 if i < rem else base for i in range(n_chunks)]
    out, idx = [], 0
    for s in sizes:
        out.append(items[idx:idx + s])
        idx += s
    return out


def main():
    el_copy_list = json.loads(EL_COPY_JSON.read_text())
    en_to_copy = {r["filename"]: r for r in el_copy_list}

    theme_map = json.loads(THEME_MAP_JSON.read_text())
    themes_order = list(theme_map["themes"]) + [UUID_BUCKET]
    en_to_theme = theme_map["assignments"]

    gr_files = sorted([p.name for p in GR_DIR.iterdir() if p.suffix.lower() == ".png"])
    print(f"Found {len(gr_files)} GR files")

    by_theme: dict[str, list[str]] = {t: [] for t in themes_order}
    per_ad_text: dict[str, dict] = {}
    uuid_count = 0
    matched = 0

    for gr_fn in gr_files:
        en_fn = strip_gr(gr_fn)
        theme = en_to_theme.get(en_fn)
        copy = en_to_copy.get(en_fn)

        if theme and copy:
            by_theme[theme].append(gr_fn)
            per_ad_text[gr_fn] = {
                "headlines": copy.get("headlines", []),
                "bodies": [copy.get("primary_text", "")],
            }
            matched += 1
        else:
            by_theme[UUID_BUCKET].append(gr_fn)
            uuid_count += 1

    print(f"Matched to EN themes: {matched}")
    print(f"UUID/unmatched -> '{UUID_BUCKET}': {uuid_count}")

    groups = []
    for theme in themes_order:
        media = by_theme[theme]
        if not media:
            continue
        chunks = balanced_chunks(media, MAX_PER_ADSET)
        for i, chunk in enumerate(chunks, 1):
            suffix = f" {i}/{len(chunks)}" if len(chunks) > 1 else ""
            groups.append({
                "name": f"Veins TOF | {theme}{suffix}",
                "media": chunk,
            })
            print(f"  {theme}{suffix}: {len(chunk)} ads")

    spec = {
        "adPresetId": PRESET_ID,
        "uploadId": "batch_cf994ed55416f6c3d9b88679",
        "adSet": {"groups": groups},
        "texts": {
            "perAd": per_ad_text,
            "strategy": "flexible",
        },
        "options": {
            "status": "PAUSED",
            "pauseAt": "ad",
        },
    }

    SPEC_OUT.parent.mkdir(exist_ok=True)
    SPEC_OUT.write_text(json.dumps(spec, indent=2, ensure_ascii=False))
    print(f"\nWrote spec: {SPEC_OUT}")
    print(f"Total ad sets: {len(groups)}")
    print(f"Total ads: {sum(len(g['media']) for g in groups)}")


if __name__ == "__main__":
    main()
