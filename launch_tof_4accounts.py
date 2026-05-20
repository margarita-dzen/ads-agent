"""
Launch the TOF Veins 17.05 campaign in 5 ad accounts, PAUSED.
- PL: Polish copy + PL translated designs
- RO: Romanian copy + RO translated designs
- FR: French copy + FR translated designs
- CZ: Czech copy + CZ translated designs
- SK: Slovak copy + SK translated designs
(EL skipped - handled in another terminal)
Each market reads its own _designs_{code}/, ad_copy_TOF_{code}_v2.json, and theme_map_{code}.json.
Ad sets grouped by theme, max 5 ads per set, balanced chunking, PAUSED.
"""
import json
import os
import subprocess
import sys
from collections import OrderedDict
from pathlib import Path

FOLDER = Path("/Users/magi/Downloads/Vein new ads 17.05")
COPY_DIR = FOLDER / "Ad copy 17.05."
SPECS_DIR = FOLDER / "_specs"
SPECS_DIR.mkdir(exist_ok=True)

MAX_PER_ADSET = 5

# (account_id, lang_code, lang_name, preset_id)
TARGETS = [
    ("act_290320662280613",  "PL", "Polish",   "6a0c3d00ca66cf22b50594f6"),
    ("act_1721457611349826", "RO", "Romanian", "6a0c3d25ca66cf22b5059583"),
    ("act_3243709282434657", "FR", "French",   "6a0c3d67ca66cf22b50596cf"),
    # CZ + SK pending user deletion of old EN-image adsets; uncomment when ready:
    # ("act_293575628641389",  "CZ", "Czech",    "6a05a988bbfc49049c01e38f"),
    # ("act_247195616530370",  "SK", "Slovak",   "6a05a974bbfc49049c01e2f2"),
]


def load_theme_map(code: str):
    p = COPY_DIR / f"theme_map_{code}.json"
    tm = json.loads(p.read_text())
    return tm["themes"], tm["assignments"]


def balanced_chunks(items, max_size):
    n = len(items)
    if n <= max_size:
        return [items]
    n_chunks = (n + max_size - 1) // max_size
    base, rem = divmod(n, n_chunks)
    chunks, i = [], 0
    for c in range(n_chunks):
        size = base + (1 if c < rem else 0)
        chunks.append(items[i:i + size])
        i += size
    return chunks


def run(cmd, capture=True):
    print(f"$ {' '.join(cmd)}", flush=True)
    res = subprocess.run(cmd, capture_output=capture, text=True)
    if capture:
        print(res.stdout, flush=True)
        if res.stderr:
            print(res.stderr, flush=True)
    return res


def build_spec(lang_code: str, preset_id: str, batch_id: str, lang_data: list,
               themes_order: list, file_to_theme: dict) -> Path:
    by_theme = OrderedDict()
    for t in themes_order:
        by_theme[t] = []
    for r in lang_data:
        t = file_to_theme.get(r["filename"], "Misc")
        by_theme.setdefault(t, []).append(r)

    groups, per_ad = [], {}
    for theme, items in by_theme.items():
        if not items:
            continue
        items_sorted = sorted(items, key=lambda r: r["filename"])
        chunks = balanced_chunks(items_sorted, MAX_PER_ADSET)
        for i, chunk in enumerate(chunks, 1):
            suffix = f" {i}/{len(chunks)}" if len(chunks) > 1 else ""
            groups.append({
                "name": f"Veins TOF | {theme}{suffix}",
                "media": [r["filename"] for r in chunk],
            })
            for r in chunk:
                per_ad[r["filename"]] = {
                    "headlines": r["headlines"],
                    "bodies": [r["primary_text"]],
                }

    spec = {
        "adPresetId": preset_id,
        "uploadId": batch_id,
        "adSet": {"groups": groups},
        "texts": {"perAd": per_ad, "strategy": "flexible"},
        "options": {"status": "PAUSED", "pauseAt": "ad"},
    }
    p = SPECS_DIR / f"spec_TOF_{lang_code}.json"
    p.write_text(json.dumps(spec, indent=2, ensure_ascii=False))
    return p


def main():
    for account, code, lname, preset_id in TARGETS:
        print(f"\n===== {code} ({account}) =====", flush=True)
        run(["ads", "account", account])
        designs_dir = FOLDER / f"_designs_{code}"
        # Load per-market language copy + theme map
        lang_data = json.loads((COPY_DIR / f"ad_copy_TOF_{code}_v2.json").read_text())
        themes_order, file_to_theme = load_theme_map(code)
        # Filter to files that actually exist in market designs folder
        existing = {f.name for f in designs_dir.iterdir() if f.suffix.lower() in (".png", ".jpg", ".jpeg")}
        lang_data = [r for r in lang_data if r["filename"] in existing]
        print(f"  {len(lang_data)} ads mapped to designs ({designs_dir.name})", flush=True)
        # Upload
        upload_log = SPECS_DIR / f"upload_{code}.log"
        with upload_log.open("w") as f:
            res = subprocess.run(
                ["ads", "upload", str(designs_dir), "--account", account],
                capture_output=True, text=True,
            )
            f.write(res.stdout + "\n" + res.stderr)
        # Extract batch ID
        batch_id = None
        for line in (res.stdout + res.stderr).splitlines():
            line = line.strip()
            if line.startswith("Batch:"):
                batch_id = line.split(":", 1)[1].strip()
                break
        if not batch_id:
            print(f"  [{code}] could not parse batch ID, last 20 lines:", flush=True)
            print("\n".join(res.stdout.splitlines()[-20:]))
            continue
        print(f"  batch: {batch_id}", flush=True)
        # Build spec
        spec_path = build_spec(code, preset_id, batch_id, lang_data, themes_order, file_to_theme)
        print(f"  spec: {spec_path}", flush=True)
        # Preview
        prev = subprocess.run(
            ["ads", "create:preview", str(spec_path), "--account", account],
            capture_output=True, text=True,
        )
        head = prev.stdout.splitlines()[:3]
        print(f"  preview: {head}", flush=True)
        # Create
        print(f"  creating in {code} PAUSED...", flush=True)
        res = subprocess.run(
            ["ads", "create", str(spec_path), "--status", "PAUSED", "--account", account],
            capture_output=True, text=True,
        )
        tail = (res.stdout + res.stderr).splitlines()[-3:]
        for l in tail:
            print(f"    {l}", flush=True)


if __name__ == "__main__":
    main()
