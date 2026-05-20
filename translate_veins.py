"""
Translate the English ad copy for the Ina Essentials Veins campaign into 15 languages
and assemble one consolidated Markdown document organized by language.
"""
import json
import random
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
import anthropic

load_dotenv()

INPUT_JSON = Path("/Users/magi/Downloads/Veins New ads/ad_copy_EN.json")
TRANS_DIR = Path("/Users/magi/Downloads/Veins New ads/translations")
OUTPUT_MD = Path("/Users/magi/Downloads/Veins New ads/ad_copy_ALL_LANGUAGES.md")
TRANS_DIR.mkdir(exist_ok=True)

LANGUAGES = [
    ("EN", "English",     "UK, US, AU, IE", "inaessentials.co.uk, inaessentials.us, inaessentials.au, inaessentials.ie"),
    ("BG", "Bulgarian",   "BG",              "inaessentials.bg"),
    ("FR", "French",      "FR",              "inaessentials.fr"),
    ("RO", "Romanian",    "RO",              "inaessentials.ro"),
    ("SK", "Slovak",      "SK",              "www.inaessentials.sk"),
    ("CZ", "Czech",       "CZ",              "www.inaessentials.cz"),
    ("DE", "German",      "DE",              "inaessentials.de"),
    ("IT", "Italian",     "IT",              "inaessentials.it"),
    ("ES", "Spanish",     "ES",              "inaessentials.es"),
    ("NL", "Dutch",       "NL",              "inaessentials.nl"),
    ("PT", "Portuguese (European)", "PT",   "inaessentials.pt"),
    ("PL", "Polish",      "PL",              "inaessentials.pl"),
    ("HU", "Hungarian",   "HU",              "inaessentials.hu"),
    ("HR", "Croatian",    "HR",              "inaessentials.hr"),
    ("SI", "Slovenian",   "SI",              "inaessentials.si"),
    ("RS", "Serbian (Latin script)", "RS",   "inaessentials.rs"),
]

SYSTEM_PROMPT = """You are a senior direct-response copywriter and native-level translator working on Meta (Instagram/Facebook) ad copy for a premium European skincare brand (Ina Essentials).

Your job: TRANSCREATE — not literal translation. Preserve the punch, the hook, the emotional beat, and the CTA energy of the English original, while making the target-language version sound like it was written by a native pro copywriter for that market. Idioms, expressions, and word play should be adapted, not translated word-for-word.

Hard rules:
1. NEVER use em-dashes (—) or en-dashes (–) ANYWHERE in your output. Use commas, periods, colons, or semicolons. Hyphens inside compound words are fine.
2. Keep brand names and the product name "Soothing Cream with Horse Chestnut and Smoke Tree" recognizable: translate naturally to the target language if there is an established translation, otherwise keep close to the source (e.g. German: "Beruhigende Creme mit Rosskastanie und Perückenstrauch"). For "Ina Essentials" always keep as is.
3. Keep the same structure as the source: Ad Angle / Headlines (same number of options) / Primary Text / CTA.
4. Keep numbers, prices (€9.99), and percentages exactly as in the source.
5. Headlines must remain punchy and short in the target language. Adapt for sentence structure, do not pad.
6. Primary text length should stay in the same Medium range (3-4 sentences).
7. Match the trustworthy, warm, evidence-led, natural brand voice. Never alarmist.

Output format: a single JSON array. Each element MUST be: {"filename": "...", "ad_angle": "...", "headlines": ["...", "...", "..."], "primary_text": "...", "cta": "..."} — fields in this exact order. Return ONLY the JSON array, no markdown fences, no commentary."""


def parse_english_copy(copy_text: str) -> dict:
    """Best-effort parse of the English copy text into fields.

    Handles both **Label**: and **Label:** formatting variants.
    """
    import re
    fields = {"ad_angle": "", "headlines": [], "primary_text": "", "cta": ""}

    def label(name):
        # Matches all variants:
        #   **Label**:       (colon after closing **)
        #   **Label**        (no colon)
        #   **Label:**       (colon before closing **)
        #   **Label (3 options):**   (modifier in label, colon before closing **)
        return rf"\*\*{name}(?:\s*\([^)\n]*\))?(?:\s*:\s*\*\*|\s*\*\*\s*:?)"

    angle_m = re.search(
        rf"(?:{label('Ad Angle')})\s*(.+?)(?=\n\s*---|\n\s*\*\*Headlines|\n\s*$)",
        copy_text, re.S,
    )
    if angle_m:
        fields["ad_angle"] = angle_m.group(1).strip()

    head_section_m = re.search(
        rf"(?:{label('Headlines')})\s*(.+?)(?=\n\s*\*\*Primary Text|\n\s*---\s*\n\s*\*\*Primary)",
        copy_text, re.S,
    )
    if head_section_m:
        lines = head_section_m.group(1).strip().splitlines()
        for line in lines:
            line = line.strip()
            if not line or line == "---":
                continue
            m = re.match(r"^\d+[.\)]\s*(.+)$", line)
            if m:
                fields["headlines"].append(m.group(1).strip().strip("*").strip())

    pt_m = re.search(
        rf"(?:{label('Primary Text')})\s*(.+?)(?=\n\s*\*\*CTA|\n\s*---\s*\n\s*\*\*CTA)",
        copy_text, re.S,
    )
    if pt_m:
        body = pt_m.group(1)
        body = re.sub(r"^\s*---\s*$", "", body, flags=re.M).strip()
        fields["primary_text"] = body

    cta_m = re.search(rf"(?:{label('CTA')})\s*([^\n]+)", copy_text)
    if cta_m:
        fields["cta"] = cta_m.group(1).strip()

    return fields


def build_source_payload(english_data: list) -> list:
    out = []
    for r in english_data:
        parsed = parse_english_copy(r["copy"])
        out.append({
            "filename": r["filename"],
            "category": r["category"],
            "ad_angle": parsed["ad_angle"],
            "headlines": parsed["headlines"],
            "primary_text": parsed["primary_text"],
            "cta": parsed["cta"],
        })
    return out


def strip_dashes(text: str) -> str:
    return text.replace("—", ", ").replace("–", ", ")


def chunked(items, size):
    for i in range(0, len(items), size):
        yield items[i:i + size]


def translate_chunk(client, lang_name, market_label, chunk):
    src = json.dumps(
        [{"filename": r["filename"], "ad_angle": r["ad_angle"], "headlines": r["headlines"],
          "primary_text": r["primary_text"], "cta": r["cta"]} for r in chunk],
        ensure_ascii=False, indent=2,
    )
    user_msg = (
        f"Transcreate the following Meta ad copy into {lang_name} for the {market_label} market. "
        f"Preserve hook, energy, and CTA. Strip ALL em-dashes and en-dashes. "
        f"Return JSON array only.\n\n"
        f"Source (English):\n{src}"
    )
    for attempt in range(5):
        try:
            resp = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=16000,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_msg}],
            )
            raw = resp.content[0].text.strip()
            if raw.startswith("```"):
                raw = raw.strip("`")
                if raw.lower().startswith("json"):
                    raw = raw[4:].lstrip()
            start = raw.find("[")
            end = raw.rfind("]")
            if start == -1 or end == -1:
                raise ValueError(f"No JSON array found in response: {raw[:200]}")
            data = json.loads(raw[start:end + 1])
            for d in data:
                d["ad_angle"] = strip_dashes(d.get("ad_angle", ""))
                d["primary_text"] = strip_dashes(d.get("primary_text", ""))
                d["cta"] = strip_dashes(d.get("cta", ""))
                d["headlines"] = [strip_dashes(h) for h in d.get("headlines", [])]
            return data
        except (anthropic.APIStatusError, json.JSONDecodeError, ValueError) as e:
            if attempt < 4:
                wait = min(2 ** attempt + random.uniform(0, 1), 30)
                print(f"  retry in {wait:.1f}s: {type(e).__name__}: {str(e)[:120]}", flush=True)
                time.sleep(wait)
            else:
                raise


def translate_language(client, source, code, lang_name, country_codes, domains):
    cache = TRANS_DIR / f"{code}.json"
    if cache.exists():
        print(f"[{code}] cached, skipping", flush=True)
        return json.loads(cache.read_text())
    print(f"[{code}] translating to {lang_name} ({country_codes})", flush=True)
    all_translated = []
    for i, chunk in enumerate(chunked(source, 15), 1):
        print(f"  chunk {i}: {len(chunk)} ads", flush=True)
        translated = translate_chunk(client, lang_name, country_codes, chunk)
        all_translated.extend(translated)
    cache.write_text(json.dumps(all_translated, indent=2, ensure_ascii=False))
    return all_translated


def render_md(source_with_cat, all_langs):
    lines = [
        "# Ina Essentials, Soothing Cream with Horse Chestnut and Smoke Tree",
        "## Multi-language Ad Copy Master Document",
        "",
        f"61 ads, 16 language versions, 19 European markets. Generated by Anchor Media.",
        "",
        "**Source images:** `/Users/magi/Downloads/Veins New ads/sorted/`",
        "**English master:** `ad_copy_EN.md`",
        "",
        "---",
        "",
        "## Table of Contents",
        "",
    ]
    for code, name, ccs, dom in LANGUAGES:
        anchor = name.lower().replace(" ", "-").replace("(", "").replace(")", "").replace(",", "")
        lines.append(f"- [{name} ({ccs})](#{anchor}-{ccs.lower().replace(', ', '-')})")
    lines.append("")
    lines.append("---")
    lines.append("")

    cat_lookup = {r["filename"]: r["category"] for r in source_with_cat}

    for code, name, ccs, dom in LANGUAGES:
        anchor = name.lower().replace(" ", "-").replace("(", "").replace(")", "").replace(",", "")
        lines.append(f"# {name} ({ccs}) <a name=\"{anchor}-{ccs.lower().replace(', ', '-')}\"></a>")
        lines.append("")
        lines.append(f"**Markets:** {ccs}")
        lines.append(f"**Shopify domains:** {dom}")
        lines.append("")
        data = all_langs[code]
        by_cat = {}
        for r in data:
            cat = cat_lookup.get(r["filename"], "misc")
            by_cat.setdefault(cat, []).append(r)
        for cat in sorted(by_cat):
            lines.append(f"## {name}, Category: {cat}  ({len(by_cat[cat])})")
            lines.append("")
            for r in by_cat[cat]:
                lines.append(f"### `{r['filename']}`")
                lines.append("")
                lines.append("**Headlines:**")
                for i, h in enumerate(r.get("headlines", []), 1):
                    lines.append(f"{i}. {h}")
                lines.append("")
                lines.append("**Primary Text:**")
                lines.append("")
                lines.append(r.get("primary_text", ""))
                lines.append("")
                lines.append(f"**CTA:** {r.get('cta', '')}")
                lines.append("")
                lines.append("---")
                lines.append("")
        lines.append("")
    OUTPUT_MD.write_text("\n".join(lines))
    print(f"\nWrote {OUTPUT_MD}")


def main():
    english_raw = json.loads(INPUT_JSON.read_text())
    source = build_source_payload(english_raw)

    sample = source[0]
    print("Sample parse of first ad:")
    print(json.dumps(sample, indent=2, ensure_ascii=False)[:600])
    print("---")

    client = anthropic.Anthropic()

    all_langs = {}
    en_payload = [{
        "filename": r["filename"],
        "ad_angle": r["ad_angle"],
        "headlines": r["headlines"],
        "primary_text": r["primary_text"],
        "cta": r["cta"],
    } for r in source]
    (TRANS_DIR / "EN.json").write_text(json.dumps(en_payload, indent=2, ensure_ascii=False))
    all_langs["EN"] = en_payload

    for code, name, ccs, dom in LANGUAGES:
        if code == "EN":
            continue
        try:
            all_langs[code] = translate_language(client, source, code, name, ccs, dom)
        except Exception as e:
            print(f"[{code}] FAILED: {e}", flush=True)
            all_langs[code] = [{"filename": r["filename"], "ad_angle": f"ERROR: {e}",
                                "headlines": [], "primary_text": "", "cta": ""} for r in source]

    render_md(source, all_langs)


if __name__ == "__main__":
    main()
