"""
Fill in the missing ads in CZ (1) and EL (7) by uploading just those files
and creating them ACTIVE in the same campaigns under fresh "catch-up" ad sets.
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

FOLDER = Path("/Users/magi/Downloads/Vein new ads 17.05")
COPY_DIR = FOLDER / "Ad copy 17.05."
DESIGNS = FOLDER / "_designs_only"
SPECS_DIR = FOLDER / "_specs"
TMP_BASE = FOLDER / "_catchup"

GAPS = [
    ("act_293575628641389", "CZ", "Czech",     "6a05a988bbfc49049c01e38f", ["GPT veins 1.png"]),
    ("act_1152767151915470","EL", "Greek (GR)","6a05a996bbfc49049c01e42b", [
        "GPT veins 2.png", "GPT veins 3.png", "GPT veins 4.png",
        "GPT veins 5.png", "GPT veins 6.png",
        "GPT veins 16.png", "GPT veins 17.png",
    ]),
]


def run(cmd):
    print(f"$ {' '.join(cmd)}", flush=True)
    return subprocess.run(cmd, capture_output=True, text=True)


for account, code, lname, preset, files in GAPS:
    print(f"\n===== {code} catch-up ({len(files)} ads ACTIVE) =====", flush=True)
    tmp = TMP_BASE / code
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir(parents=True)
    for f in files:
        shutil.copy(DESIGNS / f, tmp / f)

    r = run(["ads", "account", account])
    print(r.stdout, flush=True)

    r = run(["ads", "upload", str(tmp)])
    print((r.stdout or "")[-400:], flush=True)
    batch_id = None
    for line in (r.stdout or "").splitlines():
        line = line.strip()
        if line.startswith("Batch:"):
            batch_id = line.split(":", 1)[1].strip()
    if not batch_id:
        print(f"  [{code}] no batch id, abort"); continue
    print(f"  batch: {batch_id}", flush=True)

    lang_data = json.loads((COPY_DIR / f"ad_copy_TOF_{code}.json").read_text())
    by_file = {r["filename"]: r for r in lang_data}
    per_ad = {}
    for f in files:
        r = by_file.get(f)
        if not r:
            print(f"  [{code}] no copy for {f}, skip"); continue
        per_ad[f] = {"headlines": r["headlines"], "bodies": [r["primary_text"]]}

    spec = {
        "adPresetId": preset,
        "uploadId": batch_id,
        "adSet": {"groups": [{"name": "Veins TOF | catch-up", "media": files}]},
        "texts": {"perAd": per_ad, "strategy": "flexible"},
        "options": {"status": "ACTIVE", "pauseAt": "ad"},
    }
    spec_path = SPECS_DIR / f"spec_TOF_{code}_catchup.json"
    spec_path.write_text(json.dumps(spec, indent=2, ensure_ascii=False))

    r = run(["ads", "create", str(spec_path), "--status", "ACTIVE"])
    tail = (r.stdout + r.stderr).splitlines()[-4:]
    for l in tail:
        print(f"  {l}", flush=True)
