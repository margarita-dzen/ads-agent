"""
Launch GUMS TOF campaign in the Bulgarian Ina Essentials account, PAUSED.
- Uses Bulgarian/ folder (18 localized designs with BG text overlay)
- Theme-based balanced grouping per memory protocol
- BG oral preset: 6a06dcf9bbfc49049c069ed2 (newer Sumac pack)
"""
import json
import math
import subprocess
import sys
from collections import OrderedDict, defaultdict
from pathlib import Path

FOLDER = Path("/Users/magi/Downloads/GUMS 19.06.2026")
COPY_DIR = FOLDER / "Ad copy Sumac 19.05. "
BG_DESIGNS = FOLDER / "Bulgarian"
SPECS_DIR = FOLDER / "_specs"
SPECS_DIR.mkdir(exist_ok=True)

ACCOUNT = "act_573285966372221"
PRESET = "6a06dcf9bbfc49049c069ed2"
MAX_PER_ADSET = 5

LANG_SUFFIXES = ('_BG','_CZ','_DE','_DK','_ES','_FR','_HR','_HU','_IT','_LT','_LV',
                 '_NL','_PL','_PT','_RO','_RS','_SE','_SI','_SK','_EN','_EL','_GR')


def base_id(filename: str) -> str:
    stem, _, _ = filename.rpartition(".")
    if not stem:
        stem = filename
    for suf in LANG_SUFFIXES:
        if stem.endswith(suf):
            return stem[:-len(suf)]
    return stem


def balanced_chunks(items, max_size):
    n = len(items)
    if n <= max_size:
        return [items]
    n_chunks = math.ceil(n / max_size)
    base = n // n_chunks
    rem = n % n_chunks
    chunks, idx = [], 0
    for i in range(n_chunks):
        size = base + (1 if i < rem else 0)
        chunks.append(items[idx:idx + size])
        idx += size
    return chunks


def run(cmd):
    print(f"$ {' '.join(cmd)}", flush=True)
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.stdout:
        print(r.stdout, flush=True)
    if r.stderr:
        print(r.stderr, flush=True)
    return r


def main():
    # Load translations + theme map
    bg_copy = json.loads((COPY_DIR / "ad_copy_TOF_GUMS_BG.json").read_text())
    theme_map = json.loads((FOLDER / "theme_map.json").read_text())

    # EN-base-id -> theme
    en_base_to_theme = {base_id(en_fn): theme for en_fn, theme in theme_map["assignments"].items()}
    # EN-base-id -> BG copy entry
    bg_by_base = {base_id(r["filename"]): r for r in bg_copy}

    # List BG image files
    bg_images = sorted(
        [f for f in BG_DESIGNS.iterdir() if f.suffix.lower() in ('.png','.jpg','.jpeg')],
        key=lambda p: p.name,
    )
    print(f"BG images available: {len(bg_images)}")

    # Group BG image filenames by theme, with their copy
    theme_to_files = defaultdict(list)
    per_ad_text = {}
    matched, unmapped = 0, []
    for img in bg_images:
        bid = base_id(img.name)
        theme = en_base_to_theme.get(bid)
        copy = bg_by_base.get(bid)
        if not theme or not copy:
            unmapped.append(img.name)
            continue
        theme_to_files[theme].append(img.name)
        per_ad_text[img.name] = {
            "headlines": copy["headlines"],
            "bodies": [copy["primary_text"]],
        }
        matched += 1
    print(f"Matched to theme+copy: {matched}, unmapped: {len(unmapped)}")
    if unmapped:
        for u in unmapped[:5]:
            print(f"  unmapped: {u}")

    # Build ad-set groups with balanced chunks per theme
    groups = []
    for theme in theme_map["themes"]:
        files = theme_to_files.get(theme, [])
        if not files:
            continue
        chunks = balanced_chunks(sorted(files), MAX_PER_ADSET)
        for i, chunk in enumerate(chunks, 1):
            name = f"Sumac TOF | {theme}"
            if len(chunks) > 1:
                name = f"{name} {i}/{len(chunks)}"
            groups.append({"name": name, "media": chunk})

    print(f"\nAd set plan ({len(groups)} sets):")
    for g in groups:
        print(f"  {g['name']}: {len(g['media'])} ads")

    spec = {
        "adPresetId": PRESET,
        "adSet": {"groups": groups},
        "texts": {"perAd": per_ad_text, "strategy": "flexible"},
        "options": {"status": "PAUSED", "pauseAt": "ad"},
    }

    # Upload
    print(f"\n--- Set account ---")
    run(["ads", "account", ACCOUNT])

    print(f"\n--- Upload BG designs ---")
    upload_log_path = SPECS_DIR / "upload_GUMS_BG.log"
    r = subprocess.run(["ads", "upload", str(BG_DESIGNS), "--account", ACCOUNT],
                       capture_output=True, text=True)
    upload_log_path.write_text((r.stdout or "") + "\n" + (r.stderr or ""))
    print((r.stdout or "")[-600:])

    batch_id = None
    for line in (r.stdout or "").splitlines():
        line = line.strip()
        if line.startswith("Batch:"):
            batch_id = line.split(":", 1)[1].strip()
            break
    if not batch_id:
        print("ERROR: no batch ID parsed")
        sys.exit(1)
    print(f"batch: {batch_id}")
    spec["uploadId"] = batch_id

    # Write spec
    spec_path = SPECS_DIR / "spec_GUMS_BG.json"
    spec_path.write_text(json.dumps(spec, indent=2, ensure_ascii=False))
    print(f"spec: {spec_path}")

    # Preview
    print(f"\n--- Preview ---")
    r = subprocess.run(["ads", "create:preview", str(spec_path), "--account", ACCOUNT],
                       capture_output=True, text=True)
    for line in r.stdout.splitlines()[:5]:
        print(line)
    if r.stderr:
        print(r.stderr)

    # Create PAUSED
    print(f"\n--- Create PAUSED ---")
    r = subprocess.run(["ads", "create", str(spec_path), "--account", ACCOUNT, "--status", "PAUSED"],
                       capture_output=True, text=True)
    tail = (r.stdout + r.stderr).splitlines()[-6:]
    for l in tail:
        print(l)


if __name__ == "__main__":
    main()
