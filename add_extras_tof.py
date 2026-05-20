"""
Add the 7 'extra' creatives to the TOF workflow.
- Appends EN entries to ad_copy_TOF_EN.json
- For each existing language JSON, translates only the new entries via API and appends
- Then build_tof_docx.py is run to regenerate the docs
"""
import json
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from translate_tof_veins import translate_chunk, LANGUAGES
from dotenv import load_dotenv
import anthropic

load_dotenv()

FOLDER = Path("/Users/magi/Downloads/Vein new ads 17.05")
EN_JSON = FOLDER / "ad_copy_TOF_EN.json"

EXTRAS_EN = [
    {
        "filename": "extra 1.png",
        "ad_angle": "Film-strip timeline of one calf from Day 1 to Day 28; gradual progression.",
        "headlines": [
            "Day 1 to Day 28, same calf.",
            "What four weeks can do to a leg.",
            "The slow change you can actually see."
        ],
        "primary_text": "Most evenings nothing seems different. Then you place two photos next to each other a month apart and the calf looks like a stranger. See what shifts week by week.",
        "cta_suggestion": "LEARN_MORE"
    },
    {
        "filename": "extra 2.png",
        "ad_angle": "Cute cartoon 'final boss defeated' metaphor with stick figure and varicose-veins monster.",
        "headlines": [
            "Final boss. Day 14. Defeated.",
            "What varicose veins look like when they lose.",
            "Two weeks. One small ritual."
        ],
        "primary_text": "She had been losing the fight against her own calves for years. Then she found the boss-killer most women never hear about. Read what happened by day fourteen.",
        "cta_suggestion": "LEARN_MORE"
    },
    {
        "filename": "extra 3.png",
        "ad_angle": "Bold 'Zero prescriptions' claim with 100,000 women endorsement.",
        "headlines": [
            "Zero prescriptions.",
            "100,000 women, no doctor's note.",
            "What changed without a single pill."
        ],
        "primary_text": "No prescription, no clinic, no waiting room. Over a hundred thousand women improved the look and feel of their varicose veins without any of it. Read how.",
        "cta_suggestion": "LEARN_MORE"
    },
    {
        "filename": "extra 4.png",
        "ad_angle": "Vintage dictionary page treating varicose veins as past tense after Day 14.",
        "headlines": [
            "Varicose veins, past tense.",
            "When your veins become a memory.",
            "Fourteen days, one word change."
        ],
        "primary_text": "There is a day when 'I have varicose veins' becomes 'I had them.' For many women, it happens two weeks into a quiet evening routine they almost never talk about. Read what that routine is.",
        "cta_suggestion": "LEARN_MORE"
    },
    {
        "filename": "extra 5.png",
        "ad_angle": "Whiteboard sketch with BEFORE and AFTER Day 14, 80,000+ adults endorsement.",
        "headlines": [
            "Before. Day 14. Same legs.",
            "What 80,000 adults figured out.",
            "Two weeks on the whiteboard."
        ],
        "primary_text": "Before, calves she did not want to show. Day 14, smooth enough to roll up the jeans again. The change does not need a clinic, just a couple of weeks of one small evening habit.",
        "cta_suggestion": "LEARN_MORE"
    },
    {
        "filename": "extra 6.png",
        "ad_angle": "Whiteboard single-leg before/after, 100,000+ women endorsement.",
        "headlines": [
            "Before and after, on a whiteboard.",
            "100,000 women drew this conclusion.",
            "What changes after two quiet weeks."
        ],
        "primary_text": "Drawn simply because the change is. Before, visible bulging lines. After fourteen days, the same calf looks unrecognizable. Read what shifted in those two weeks.",
        "cta_suggestion": "LEARN_MORE"
    },
    {
        "filename": "extra 7.png",
        "ad_angle": "Aged chalkboard variant of before/after, Day 10 transformation.",
        "headlines": [
            "Ten days on the chalkboard.",
            "Day 10, and the calves looked different.",
            "Two weeks is usual. Ten works too."
        ],
        "primary_text": "Some women see the shift sooner. By day ten, calves that used to map blue and purple lines look quieter. Read what those ten days actually look like.",
        "cta_suggestion": "LEARN_MORE"
    },
]


def main():
    # 1) Append to EN.json
    en = json.loads(EN_JSON.read_text())
    en_files = {r["filename"] for r in en}
    new_entries = [e for e in EXTRAS_EN if e["filename"] not in en_files]
    print(f"Appending {len(new_entries)} new EN entries (had {len(en)})")
    en.extend(new_entries)
    EN_JSON.write_text(json.dumps(en, indent=2, ensure_ascii=False))
    print(f"EN now {len(en)} ads")

    # 2) For each language file, translate missing entries and append
    client = anthropic.Anthropic()
    src_for_trans = [{k: v for k, v in e.items() if k != "ad_angle"} for e in EXTRAS_EN]
    # Add BG to the iteration since BG was done manually before
    languages_with_bg = [("BG", "Bulgarian", "BG", "inaessentials.bg")] + list(LANGUAGES)
    for code, name, market, dom in languages_with_bg:
        out = FOLDER / f"ad_copy_TOF_{code}.json"
        if not out.exists():
            print(f"[{code}] missing translation file, skipping")
            continue
        data = json.loads(out.read_text())
        have = {r["filename"] for r in data}
        missing_src = [e for e in src_for_trans if e["filename"] not in have]
        if not missing_src:
            print(f"[{code}] up to date")
            continue
        print(f"[{code}] translating {len(missing_src)} extras to {name}")
        try:
            translated = translate_chunk(client, name, market, missing_src)
            data.extend(translated)
            out.write_text(json.dumps(data, indent=2, ensure_ascii=False))
            print(f"  [{code}] now {len(data)} ads")
        except Exception as e:
            print(f"  [{code}] FAILED: {e}")


if __name__ == "__main__":
    main()
