"""
Post-mapping: build the per-market launch assets.
- Fix any hallucinated EN filenames in angle_match_{lang}.json (fuzzy nearest).
- Build ad_copy_TOF_{lang}_v2.json keyed by translated filename, pulling text from existing translated JSON via EN-filename lookup.
- Build theme_map_{lang}.json keyed by translated filename, pulling theme from EN theme_map.json.
- Build per-market combined designs folder by symlinking from drive-download-*/{lang} into _designs_{lang}/.
"""
import json
import os
import shutil
from pathlib import Path
from difflib import get_close_matches

BASE = Path("/Users/magi/Downloads/Vein new ads 17.05")
COPY_DIR = BASE / "Ad copy 17.05."
EN_JSON = COPY_DIR / "ad_copy_TOF_EN.json"
THEME_MAP_PATH = COPY_DIR / "theme_map.json"
DRIVE_DIRS = [
    BASE / "drive-download-20260519T135937Z-3-001",
    BASE / "drive-download-20260519T135937Z-3-002",
]

# (folder_code, asset_code)
MARKETS = [
    ("PL", "PL"),
    ("RO", "RO"),
    ("FR", "FR"),
    ("CZ", "CZ"),
    ("SK", "SK"),
]


def fuzzy_fix(en_name, en_filenames):
    if en_name in en_filenames:
        return en_name
    matches = get_close_matches(en_name, en_filenames, n=1, cutoff=0.6)
    return matches[0] if matches else None


def main():
    en_data = json.loads(EN_JSON.read_text())
    en_filenames = {r["filename"] for r in en_data}
    theme_map = json.loads(THEME_MAP_PATH.read_text())
    file_to_theme = theme_map["assignments"]

    for folder_code, code in MARKETS:
        print(f"\n=== {code} (folder={folder_code}) ===")
        am_path = COPY_DIR / f"angle_match_{code}.json"
        am = json.loads(am_path.read_text())
        # Fix typos
        fixed = {}
        bad = 0
        for trans_fn, en_fn in am.items():
            corrected = fuzzy_fix(en_fn, en_filenames)
            if corrected is None:
                print(f"  ERR unresolvable: {trans_fn} → {en_fn}")
                bad += 1
                continue
            if corrected != en_fn:
                print(f"  fuzzy fix: {en_fn[:50]}... → {corrected[:50]}...")
            fixed[trans_fn] = corrected
        am_path.write_text(json.dumps(fixed, indent=2, ensure_ascii=False))
        print(f"  mapping: {len(fixed)} valid, {bad} unresolved")

        # Load translated copy (keyed by EN filename)
        lang_json = COPY_DIR / f"ad_copy_TOF_{code}.json"
        lang_copy_list = json.loads(lang_json.read_text())
        en_to_copy = {r["filename"]: r for r in lang_copy_list}

        # Build per-market copy v2 (keyed by translated filename)
        out_copy = []
        out_theme = {}
        missing_copy = 0
        for trans_fn, en_fn in fixed.items():
            c = en_to_copy.get(en_fn)
            if not c:
                print(f"  ERR no copy for EN {en_fn}")
                missing_copy += 1
                continue
            out_copy.append({
                "filename": trans_fn,
                "headlines": c.get("headlines", []),
                "primary_text": c.get("primary_text", ""),
                "cta_suggestion": c.get("cta_suggestion", "LEARN_MORE"),
            })
            theme = file_to_theme.get(en_fn, "Misc")
            out_theme[trans_fn] = theme

        out_copy_path = COPY_DIR / f"ad_copy_TOF_{code}_v2.json"
        out_copy_path.write_text(json.dumps(out_copy, indent=2, ensure_ascii=False))
        print(f"  copy v2: {len(out_copy)} entries → {out_copy_path.name}")

        out_theme_obj = {"themes": theme_map["themes"], "assignments": out_theme}
        out_theme_path = COPY_DIR / f"theme_map_{code}.json"
        out_theme_path.write_text(json.dumps(out_theme_obj, indent=2, ensure_ascii=False))
        # Sanity: count per theme
        by_theme = {}
        for t in out_theme.values():
            by_theme[t] = by_theme.get(t, 0) + 1
        print(f"  theme_map: {len(out_theme)} entries → {out_theme_path.name}")
        for t in theme_map["themes"]:
            print(f"    {t}: {by_theme.get(t, 0)}")

        # Build combined designs folder via symlink
        designs_dir = BASE / f"_designs_{code}"
        if designs_dir.exists():
            shutil.rmtree(designs_dir)
        designs_dir.mkdir()
        for d in DRIVE_DIRS:
            src = d / folder_code
            if not src.exists():
                continue
            for p in src.iterdir():
                if p.suffix.lower() in (".png", ".jpg", ".jpeg"):
                    target = designs_dir / p.name
                    target.symlink_to(p)
        n = len(list(designs_dir.iterdir()))
        print(f"  designs dir: {n} files → {designs_dir.name}")


if __name__ == "__main__":
    main()
