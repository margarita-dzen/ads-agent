"""
Build a spec.json for the Ads Uploader CLI from the BG translation JSON.
Maps filename -> headlines + bodies (primary text). Excludes any files
that failed to upload.
"""
import json
from pathlib import Path

BG_JSON = Path("/Users/magi/Downloads/vitalaiz 3/Veins New ads/translations/BG.json")
OUT_SPEC = Path("/Users/magi/Downloads/vitalaiz 3/Veins New ads/spec_BG.json")

PRESET_ID = "6a05933abbfc49049c014f4f"  # ASC | Advertorial | Veins general (correct product, correct URL)
UPLOAD_ID = "batch_252c19118356ba3875cc4a01"

# Preset's template ad already points to the correct veins advertorial.
# No link override needed.

# All 61 ads should be in spec — visual_10 was uploaded fine, JSON error was on response parsing only
EXCLUDED: set[str] = set()


def main():
    data = json.loads(BG_JSON.read_text())
    per_ad = {}
    excluded = []
    for r in data:
        fn = r["filename"]
        if fn in EXCLUDED:
            excluded.append(fn)
            continue
        per_ad[fn] = {
            "headlines": r["headlines"],
            "bodies": [r["primary_text"]],
        }

    spec = {
        "adPresetId": PRESET_ID,
        "uploadId": UPLOAD_ID,
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
    print(f"  Ads in spec: {len(per_ad)}")
    print(f"  Excluded: {excluded if excluded else 'none'}")


if __name__ == "__main__":
    main()
