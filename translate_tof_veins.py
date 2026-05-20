"""
Translate the TOF EN copy into the 15 remaining languages.
Same em-dash ban, same TOF / problem-aware tone, no brand/price leakage.
"""
import json
import random
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
import anthropic

load_dotenv()

FOLDER = Path("/Users/magi/Downloads/Vein new ads 17.05")
EN_JSON = FOLDER / "ad_copy_TOF_EN.json"

# BG already done manually
LANGUAGES = [
    ("FR", "French",                "FR",   "inaessentials.fr"),
    ("RO", "Romanian",              "RO",   "inaessentials.ro"),
    ("SK", "Slovak",                "SK",   "www.inaessentials.sk"),
    ("CZ", "Czech",                 "CZ",   "www.inaessentials.cz"),
    ("DE", "German",                "DE",   "inaessentials.de"),
    ("IT", "Italian",               "IT",   "inaessentials.it"),
    ("ES", "Spanish",               "ES",   "inaessentials.es"),
    ("NL", "Dutch",                 "NL",   "inaessentials.nl"),
    ("PT", "Portuguese (European)", "PT",   "inaessentials.pt"),
    ("PL", "Polish",                "PL",   "inaessentials.pl"),
    ("HU", "Hungarian",             "HU",   "inaessentials.hu"),
    ("HR", "Croatian",              "HR",   "inaessentials.hr"),
    ("SI", "Slovenian",             "SI",   "inaessentials.si"),
    ("RS", "Serbian (Latin)",       "RS",   "inaessentials.rs"),
    ("EL", "Greek",                 "GR",   "inaessentials.gr"),
    ("DK", "Danish",                "DK",   "inaessentials.dk"),
    ("LT", "Lithuanian",            "LT",   "inaessentials.lt"),
    ("LV", "Latvian",               "LV",   "inaessentials.lv"),
    ("SE", "Swedish",               "SE",   "inaessentials.se"),
]

SYSTEM_PROMPT = """You are a senior native-level transcreator translating TOF (top-of-funnel) Meta ad copy into the target language.

Audience profile:
- Women 35+ with heavy, achy legs at end of day, visible veins on calves, swelling.
- Problem-aware. Solution-unaware. Hook on the pain/visual scene to earn the click, do NOT pitch a product.

Hard constraints (NEVER violate):
1. NEVER add prices, currency, money amounts. The English text has none — keep it that way.
2. NEVER mention a brand or product name. No 'Ina Essentials', no 'Soothing Cream', no 'REMORRHOIDS'. The English does not name a product — neither should you.
3. NEVER use em-dashes (—) or en-dashes (–). Use commas, periods, colons, semicolons. Hyphens inside compound words are fine.
4. Keep length: 1 to 3 sentences in primary text (~50 words). Headlines under 9 words.

Transcreate, do not literally translate. Preserve the hook, the emotional beat, the unique angle per image. Use native idioms and sentence structure for the target language. Refer to body parts and concepts the way native speakers actually do.

Output format: a JSON array. Each element MUST be:
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
        f"Preserve the hook and tone, adapt to native idiom, never add prices or product names, "
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
                # Fallback: parse each object individually to skip broken ones
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
        out = FOLDER / f"ad_copy_TOF_{code}.json"
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
