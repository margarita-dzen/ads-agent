"""
Translate the GUMS TOF EN copy into the 15 languages present in the GUMS folder.
Oral-care TOF tone preserved.
"""
import json
import random
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
import anthropic

load_dotenv()

FOLDER = Path("/Users/magi/Downloads/GUMS 19.06.2026")
COPY_DIR = FOLDER / "Ad copy Sumac 19.05. "
if not COPY_DIR.exists():
    COPY_DIR = FOLDER
EN_JSON = COPY_DIR / "ad_copy_TOF_GUMS_EN.json"

LANGUAGES = [
    ("BG", "Bulgarian",             "BG", "inaessentials.bg"),
    ("FR", "French",                "FR", "inaessentials.fr"),
    ("RO", "Romanian",              "RO", "inaessentials.ro"),
    ("CZ", "Czech",                 "CZ", "www.inaessentials.cz"),
    ("DE", "German",                "DE", "inaessentials.de"),
    ("IT", "Italian",               "IT", "inaessentials.it"),
    ("ES", "Spanish",               "ES", "inaessentials.es"),
    ("NL", "Dutch",                 "NL", "inaessentials.nl"),
    ("PT", "Portuguese (European)", "PT", "inaessentials.pt"),
    ("PL", "Polish",                "PL", "inaessentials.pl"),
    ("HU", "Hungarian",             "HU", "inaessentials.hu"),
    ("HR", "Croatian",              "HR", "inaessentials.hr"),
    ("RS", "Serbian (Latin)",       "RS", "inaessentials.rs"),
    ("DK", "Danish",                "DK", "inaessentials.dk"),
    ("SE", "Swedish",               "SE", "inaessentials.se"),
    ("SK", "Slovak",                "SK", "www.inaessentials.sk"),
    ("SI", "Slovenian",             "SI", "inaessentials.si"),
    ("LT", "Lithuanian",            "LT", "inaessentials.lt"),
    ("LV", "Latvian",               "LV", "inaessentials.lv"),
]

SYSTEM_PROMPT = """You are a senior native-level transcreator translating TOF (top-of-funnel) Meta ad copy about ORAL CARE into the target language.

Audience profile:
- Adults dealing with bad breath, bleeding gums, gum recession, sensitivity, plaque.
- Problem-aware. Solution-unaware. Hook on the pain or scene, do NOT pitch a product.

Hard constraints (NEVER violate):
1. NEVER add prices, currency, money amounts.
2. NEVER mention a brand or product name. No 'Ina Essentials', no 'Hydrolina', no 'Smoke Tree'.
3. NEVER use em-dashes (—) or en-dashes (–). Use commas, periods, colons, semicolons.
4. Keep length: 1 to 3 sentences in primary text (max ~50 words). Headlines under 9 words.

Transcreate, do not literally translate. Preserve hook, emotional beat, unique angle. Use native idioms, sentence structure, oral-health terminology the way native speakers actually say it.

Output: a JSON array. Each element MUST be:
{"filename": "...", "headlines": ["...", "...", "..."], "primary_text": "...", "cta_suggestion": "LEARN_MORE|READ_MORE|SEE_MORE|SHOP_NOW"}

Return ONLY the JSON array, no markdown fences, no commentary."""


def strip_dashes(s: str) -> str:
    return s.replace("—", ", ").replace("–", ", ")


def chunked(items, size):
    for i in range(0, len(items), size):
        yield items[i:i + size]


def translate_chunk(client, lang_name, market, chunk):
    src = json.dumps(
        [{"filename": r["filename"], "headlines": r["headlines"],
          "primary_text": r["primary_text"], "cta_suggestion": r["cta_suggestion"]} for r in chunk],
        ensure_ascii=False, indent=2,
    )
    user = (
        f"Transcreate the following TOF Meta ad copy into {lang_name} for the {market} market. "
        f"Preserve hook and tone, adapt to native idiom, never add prices or product names, "
        f"strip all em-dashes. Return JSON array only.\n\nSource:\n{src}"
    )
    for attempt in range(5):
        try:
            resp = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=16000,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user}],
                timeout=180.0,
            )
            raw = resp.content[0].text.strip()
            if raw.startswith("```"):
                raw = raw.strip("`")
                if raw.lower().startswith("json"):
                    raw = raw[4:].lstrip()
            start = raw.find("[")
            end = raw.rfind("]")
            try:
                data = json.loads(raw[start:end + 1])
            except json.JSONDecodeError:
                import re as _re
                txt = raw[start:end + 1]
                obj_matches = _re.findall(r"\{[^{}]*(?:\"[^\"]*\"[^{}]*)*\}", txt, _re.S)
                data = []
                for om in obj_matches:
                    try:
                        data.append(json.loads(om))
                    except json.JSONDecodeError:
                        pass
                if not data:
                    raise
            for d in data:
                d["primary_text"] = strip_dashes(d.get("primary_text", ""))
                d["headlines"] = [strip_dashes(h) for h in d.get("headlines", [])]
            return data
        except (anthropic.APIStatusError, json.JSONDecodeError, ValueError) as e:
            if attempt < 4:
                wait = min(2 ** attempt + random.uniform(0, 1), 30)
                print(f"  retry in {wait:.1f}s: {type(e).__name__}: {str(e)[:100]}", flush=True)
                time.sleep(wait)
            else:
                raise


def main():
    source = json.loads(EN_JSON.read_text())
    print(f"Source: {len(source)} ads", flush=True)
    client = anthropic.Anthropic()

    for code, name, market, dom in LANGUAGES:
        out = COPY_DIR / f"ad_copy_TOF_GUMS_{code}.json"
        if out.exists():
            print(f"[{code}] exists, skipping", flush=True)
            continue
        print(f"[{code}] translating to {name}", flush=True)
        all_translated = []
        for i, chunk in enumerate(chunked(source, 12), 1):
            print(f"  chunk {i}: {len(chunk)} ads", flush=True)
            t = translate_chunk(client, name, market, chunk)
            all_translated.extend(t)
        out.write_text(json.dumps(all_translated, indent=2, ensure_ascii=False))
        print(f"  wrote {out.name} ({len(all_translated)} ads)", flush=True)


if __name__ == "__main__":
    main()
