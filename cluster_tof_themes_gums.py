"""
Cluster the 93 GUMS (oral care) TOF creatives into 5-8 themes.
Writes theme_map.json next to the EN copy.
"""
import json
from pathlib import Path

from dotenv import load_dotenv
import anthropic

load_dotenv()

FOLDER = Path("/Users/magi/Downloads/GUMS 19.06.2026")
EN = FOLDER / "ad_copy_TOF_GUMS_EN.json"
OUT = FOLDER / "theme_map.json"

SYSTEM = """You are a paid-social strategist. You are given a set of top-of-funnel Meta ad creatives for an oral-care herbal-spray advertorial (Smoke Tree Hydrolina, for bad breath / bleeding gums / sensitivity / gum recession). Each creative has a filename, an ad_angle description, three headline candidates, and primary text.

Your job: cluster the creatives into a SMALL number (5 to 8) of testable marketing themes. Themes must be coherent, mutually exclusive enough to test against each other in ad sets, and named in short English (1-3 words). Examples of theme names that COULD apply here:
- "Bleeding Gums Hook"
- "Bad Breath Hook"
- "Gum Recession"
- "Sensitivity"
- "Mouthwash Alternative"
- "Anatomy / Mechanism"
- "Lifestyle / Embarrassment"
- "Natural / Botanical Reveal"
- "Before / After Proof"
- "Authority / Pharmacist / Doctor"

Pick the themes that actually fit THIS set, do not just copy the examples. Every filename must be assigned to exactly one theme. Aim for 5-8 themes total, with each theme having 3-15 creatives (avoid singletons; merge small themes into the nearest neighbor).

Return ONLY valid JSON in this exact shape, no markdown:

{
  "themes": ["Theme 1", "Theme 2", ...],
  "assignments": {
    "filename1.png": "Theme 1",
    "filename2.png": "Theme 2",
    ...
  },
  "reasoning": "one short paragraph explaining the cluster choices"
}"""


def main():
    data = json.loads(EN.read_text())
    creatives = [
        {
            "filename": r["filename"],
            "ad_angle": r.get("ad_angle", ""),
            "headlines": r.get("headlines", []),
            "primary_text": r.get("primary_text", ""),
        }
        for r in data
    ]
    user_msg = (
        f"Cluster these {len(creatives)} TOF oral-care creatives into 5-8 themes. "
        f"Every filename must be assigned. Return the JSON spec.\n\n"
        f"Creatives:\n{json.dumps(creatives, indent=2, ensure_ascii=False)}"
    )
    client = anthropic.Anthropic()
    resp = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=12000,
        system=SYSTEM,
        messages=[{"role": "user", "content": user_msg}],
        timeout=240.0,
    )
    raw = resp.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.lower().startswith("json"):
            raw = raw[4:].lstrip()
    start = raw.find("{")
    end = raw.rfind("}")
    obj = json.loads(raw[start:end + 1])

    assigned = set(obj["assignments"].keys())
    expected = {r["filename"] for r in data}
    missing = expected - assigned
    extra = assigned - expected
    if missing or extra:
        print(f"WARNING: missing={len(missing)}, extra={len(extra)}")
        for m in list(missing)[:5]:
            print(f"  miss: {m}")

    OUT.write_text(json.dumps(obj, indent=2, ensure_ascii=False))
    print(f"Wrote {OUT}")
    print(f"\nThemes ({len(obj['themes'])}):")
    counts = {}
    for fn, theme in obj["assignments"].items():
        counts[theme] = counts.get(theme, 0) + 1
    for t in obj["themes"]:
        print(f"  {t}: {counts.get(t, 0)} creatives")
    print(f"\nReasoning: {obj.get('reasoning', '')[:500]}")


if __name__ == "__main__":
    main()
