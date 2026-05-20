"""
Build one Markdown document per language (with the image embedded inline above every
ad's copy) and place them all in /Users/magi/Downloads/Veins New ads/by_language/.
Each document is self-contained and ready to share with the team.
"""
import json
import shutil
from pathlib import Path

ROOT = Path("/Users/magi/Downloads/Veins New ads")
TRANS_DIR = ROOT / "translations"
OUT_DIR = ROOT / "by_language"
SORTED_DIR = ROOT / "sorted"

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
    ("RS", "Serbian (Latin)", "RS",          "inaessentials.rs"),
    ("EL", "Greek",       "GR",              "inaessentials.gr"),
]

CATEGORY_ORDER = [
    "anatomy", "article", "before-after", "chart", "copy",
    "diary", "product", "review-list", "social-fb", "stat-hook",
    "testimonial-quote", "visual",
]


def category_of(filename: str) -> str:
    return filename.split("_")[0]


def render_language(code: str, name: str, markets: str, domains: str, data: list) -> str:
    lines = [
        f"# Ina Essentials, Soothing Cream with Horse Chestnut and Smoke Tree",
        f"## Ad copy + headlines, {name}",
        "",
        f"**Markets:** {markets}",
        f"**Shopify domains:** {domains}",
        f"**Total ads:** {len(data)}",
        "**Format:** Headlines (3 options), Primary Text (medium length), CTA",
        "**Image source folder:** `../sorted/`",
        "",
        "---",
        "",
    ]
    by_cat = {}
    for r in data:
        by_cat.setdefault(category_of(r["filename"]), []).append(r)

    ordered_cats = [c for c in CATEGORY_ORDER if c in by_cat] + [c for c in by_cat if c not in CATEGORY_ORDER]

    lines.append("## Table of Contents")
    lines.append("")
    for cat in ordered_cats:
        anchor = cat.replace(" ", "-")
        lines.append(f"- [{cat}](#{anchor}) ({len(by_cat[cat])} ads)")
    lines.append("")
    lines.append("---")
    lines.append("")

    for cat in ordered_cats:
        anchor = cat.replace(" ", "-")
        lines.append(f"## {cat} <a name=\"{anchor}\"></a>")
        lines.append("")
        for r in by_cat[cat]:
            fn = r["filename"]
            lines.append(f"### `{fn}`")
            lines.append("")
            lines.append(f"![{fn}](../sorted/{fn})")
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
    return "\n".join(lines)


def render_readme(per_lang_counts: dict) -> str:
    lines = [
        "# Ina Essentials, Veins Campaign, Multi-language Ad Copy",
        "",
        "One Markdown document per language. Each ad has its **image embedded inline above the headlines/primary text/CTA**, so the team can match the visual to the copy when uploading to Meta Ads Manager.",
        "",
        "Open any .md file in a Markdown viewer (VS Code, Obsidian, Typora, GitHub, etc.) to see the images rendered. The images themselves live in `../sorted/` alongside this folder.",
        "",
        "## Files",
        "",
    ]
    for code, name, markets, domains in LANGUAGES:
        count = per_lang_counts.get(code, 0)
        filename = f"{code}_{name.replace(' ', '_').replace('(', '').replace(')', '')}.md"
        lines.append(f"- **`{filename}`** ,  {name} ,  {markets} ,  {count} ads ,  `{domains}`")
    lines.append("")
    lines.append("## How to use")
    lines.append("")
    lines.append("1. Open the .md file for the target market language.")
    lines.append("2. For each ad: look at the embedded image, copy the headline + primary text + CTA you want.")
    lines.append("3. Paste into Meta Ads Manager when creating the ad.")
    lines.append("")
    lines.append("All copy is medium length (3-4 sentences), Instagram/Facebook ready, brand-compliant (no em-dashes).")
    return "\n".join(lines)


def main():
    OUT_DIR.mkdir(exist_ok=True)
    per_lang_counts = {}
    for code, name, markets, domains in LANGUAGES:
        src = TRANS_DIR / f"{code}.json"
        if not src.exists():
            print(f"[{code}] MISSING {src}")
            continue
        data = json.loads(src.read_text())
        per_lang_counts[code] = len(data)
        slug = name.replace(" ", "_").replace("(", "").replace(")", "")
        out = OUT_DIR / f"{code}_{slug}.md"
        out.write_text(render_language(code, name, markets, domains, data))
        print(f"[{code}] wrote {out.name} ({len(data)} ads)")

    readme = OUT_DIR / "README.md"
    readme.write_text(render_readme(per_lang_counts))
    print(f"wrote {readme.name}")


if __name__ == "__main__":
    main()
