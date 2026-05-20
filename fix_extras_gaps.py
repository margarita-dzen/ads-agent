"""Fix missing translations and filename typos across language files."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from translate_tof_veins import translate_chunk
from dotenv import load_dotenv
import anthropic

load_dotenv()

FOLDER = Path("/Users/magi/Downloads/Vein new ads 17.05")
EN = json.loads((FOLDER / "ad_copy_TOF_EN.json").read_text())
EN_FILES = {r["filename"] for r in EN}
EN_BY_FILE = {r["filename"]: r for r in EN}

LANG_META = {
    "CZ": ("Czech", "CZ"),
    "LT": ("Lithuanian", "LT"),
    "PL": ("Polish", "PL"),
    "RO": ("Romanian", "RO"),
    "SK": ("Slovak", "SK"),
    "LV": ("Latvian", "LV"),
    "NL": ("Dutch", "NL"),
    "SI": ("Slovenian", "SI"),
}

client = anthropic.Anthropic()

for code, (lname, market) in LANG_META.items():
    p = FOLDER / f"ad_copy_TOF_{code}.json"
    data = json.loads(p.read_text())

    # Drop entries whose filenames aren't in EN (typos)
    bad = [r for r in data if r["filename"] not in EN_FILES]
    if bad:
        print(f"[{code}] dropping {len(bad)} typo entries: {[r['filename'] for r in bad]}")
        data = [r for r in data if r["filename"] in EN_FILES]

    have = {r["filename"] for r in data}
    missing_filenames = [f for f in EN_FILES if f not in have]
    if not missing_filenames:
        p.write_text(json.dumps(data, indent=2, ensure_ascii=False))
        print(f"[{code}] OK ({len(data)})")
        continue

    print(f"[{code}] translating {len(missing_filenames)} missing")
    src = [{k: v for k, v in EN_BY_FILE[fn].items() if k != "ad_angle"} for fn in missing_filenames]
    try:
        translated = translate_chunk(client, lname, market, src)
        # Drop any translated entries whose filenames don't match
        translated = [t for t in translated if t["filename"] in EN_FILES]
        data.extend(translated)
        # Restore order
        order = {r["filename"]: i for i, r in enumerate(EN)}
        data.sort(key=lambda r: order.get(r["filename"], 9999))
        p.write_text(json.dumps(data, indent=2, ensure_ascii=False))
        print(f"  [{code}] now {len(data)}")
    except Exception as e:
        print(f"  [{code}] FAILED: {e}")
