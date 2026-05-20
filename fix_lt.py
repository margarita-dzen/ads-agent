"""Translate the 4 missing LT entries and merge into LT.json."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from translate_tof_veins import translate_chunk, SYSTEM_PROMPT
from dotenv import load_dotenv
import anthropic

load_dotenv()

FOLDER = Path("/Users/magi/Downloads/Vein new ads 17.05")
en = json.loads((FOLDER / "ad_copy_TOF_EN.json").read_text())
lt = json.loads((FOLDER / "ad_copy_TOF_LT.json").read_text())
done = {r["filename"] for r in lt}
missing = [r for r in en if r["filename"] not in done]
print(f"Missing: {len(missing)} entries")

client = anthropic.Anthropic()
translated = translate_chunk(client, "Lithuanian", "LT", missing)
print(f"Translated: {len(translated)}")
lt.extend(translated)
# Preserve original EN order
en_order = {r["filename"]: i for i, r in enumerate(en)}
lt.sort(key=lambda r: en_order.get(r["filename"], 9999))
(FOLDER / "ad_copy_TOF_LT.json").write_text(json.dumps(lt, indent=2, ensure_ascii=False))
print(f"LT now has {len(lt)} ads")
