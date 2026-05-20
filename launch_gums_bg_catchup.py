"""Re-upload the BG files that failed and create remaining ads."""
import json, math, shutil, subprocess, sys
from collections import defaultdict
from pathlib import Path

FOLDER = Path("/Users/magi/Downloads/GUMS 19.06.2026")
COPY_DIR = FOLDER / "Ad copy Sumac 19.05. "
BG_DESIGNS = FOLDER / "Bulgarian"
SPECS_DIR = FOLDER / "_specs"
CATCHUP_DIR = FOLDER / "_bg_catchup"

ACCOUNT = "act_573285966372221"
PRESET = "6a06dcf9bbfc49049c069ed2"
MAX_PER = 5

LANG_SUFFIXES = ('_BG','_CZ','_DE','_DK','_ES','_FR','_HR','_HU','_IT','_LT','_LV',
                 '_NL','_PL','_PT','_RO','_RS','_SE','_SI','_SK','_EN','_EL','_GR')


def base_id(fn):
    stem, _, _ = fn.rpartition(".")
    for suf in LANG_SUFFIXES:
        if stem.endswith(suf):
            return stem[:-len(suf)]
    return stem


def balanced_chunks(items, mx):
    n = len(items)
    if n <= mx:
        return [items]
    nc = math.ceil(n / mx)
    base, rem = n // nc, n % nc
    out, idx = [], 0
    for i in range(nc):
        sz = base + (1 if i < rem else 0)
        out.append(items[idx:idx + sz])
        idx += sz
    return out


def run(cmd):
    print(f"$ {' '.join(cmd)}", flush=True)
    r = subprocess.run(cmd, capture_output=True, text=True)
    print((r.stdout or "") + (r.stderr or ""), flush=True)
    return r


def main():
    # Find failed files from log
    log = (SPECS_DIR / "upload_GUMS_BG.log").read_text()
    failed_names = []
    for line in log.splitlines():
        line = line.strip()
        if line.startswith("✗"):
            after = line[1:].strip()
            name = after.split(":", 1)[0].strip()
            failed_names.append(name)
    print(f"Failed files to retry: {len(failed_names)}")

    # Stage them
    if CATCHUP_DIR.exists():
        shutil.rmtree(CATCHUP_DIR)
    CATCHUP_DIR.mkdir(parents=True)
    actual = []
    for name in failed_names:
        src = BG_DESIGNS / name
        if src.exists():
            shutil.copy(src, CATCHUP_DIR / name)
            actual.append(name)
        else:
            print(f"  warn: {name} not in folder")
    print(f"Staged: {len(actual)}")

    if not actual:
        print("Nothing to do")
        return

    # Load theme map and BG copy
    tm = json.loads((FOLDER / "theme_map.json").read_text())
    en_base_to_theme = {base_id(en): t for en, t in tm["assignments"].items()}
    bg_copy = json.loads((COPY_DIR / "ad_copy_TOF_GUMS_BG.json").read_text())
    bg_by_base = {base_id(r["filename"]): r for r in bg_copy}

    # Map to themes
    theme_files = defaultdict(list)
    per_ad = {}
    unmapped = []
    for fn in actual:
        bid = base_id(fn)
        theme = en_base_to_theme.get(bid)
        copy = bg_by_base.get(bid)
        if theme and copy:
            theme_files[theme].append(fn)
            per_ad[fn] = {"headlines": copy["headlines"], "bodies": [copy["primary_text"]]}
        else:
            unmapped.append(fn)
    print(f"Mapped: {sum(len(v) for v in theme_files.values())}, unmapped: {len(unmapped)}")

    # Build groups with balanced chunks; suffix with "catch-up" to keep separate from main
    groups = []
    for theme in tm["themes"]:
        files = sorted(theme_files.get(theme, []))
        if not files:
            continue
        chunks = balanced_chunks(files, MAX_PER)
        for i, chunk in enumerate(chunks, 1):
            name = f"Sumac TOF | {theme}, catch-up"
            if len(chunks) > 1:
                name = f"{name} {i}/{len(chunks)}"
            groups.append({"name": name, "media": chunk})

    print(f"\nCatch-up ad sets: {len(groups)}")
    for g in groups:
        print(f"  {g['name']}: {len(g['media'])} ads")

    # Set account
    run(["ads", "account", ACCOUNT])

    # Upload
    print("\n--- Upload catch-up ---")
    r = subprocess.run(["ads", "upload", str(CATCHUP_DIR), "--account", ACCOUNT],
                       capture_output=True, text=True)
    out = (r.stdout or "") + (r.stderr or "")
    (SPECS_DIR / "upload_GUMS_BG_catchup.log").write_text(out)
    print(out[-600:])

    batch_id = None
    for line in out.splitlines():
        line = line.strip()
        if line.startswith("Batch:"):
            batch_id = line.split(":", 1)[1].strip()
            break
    if not batch_id:
        print("No batch id")
        return
    print(f"batch: {batch_id}")

    spec = {
        "adPresetId": PRESET,
        "uploadId": batch_id,
        "adSet": {"groups": groups},
        "texts": {"perAd": per_ad, "strategy": "flexible"},
        "options": {"status": "PAUSED", "pauseAt": "ad"},
    }
    spec_path = SPECS_DIR / "spec_GUMS_BG_catchup.json"
    spec_path.write_text(json.dumps(spec, indent=2, ensure_ascii=False))

    print("\n--- Create PAUSED ---")
    r = subprocess.run(["ads", "create", str(spec_path), "--account", ACCOUNT, "--status", "PAUSED"],
                       capture_output=True, text=True)
    tail = ((r.stdout or "") + (r.stderr or "")).splitlines()[-6:]
    for l in tail:
        print(l)


if __name__ == "__main__":
    main()
