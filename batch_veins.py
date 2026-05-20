"""
Batch wrapper around ad_copy_agent.generate_ad_copy for the Veins (Ina Essentials)
campaign — processes every image in sorted/ and writes one consolidated Markdown doc.
"""
import base64
import io
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from ad_copy_agent import SYSTEM_PROMPT, COPY_LENGTH_INSTRUCTIONS
from dotenv import load_dotenv
from PIL import Image
import anthropic

load_dotenv()

IMAGES_DIR = Path("/Users/magi/Downloads/Veins New ads/sorted")
OUTPUT_MD = Path("/Users/magi/Downloads/Veins New ads/ad_copy_EN.md")
OUTPUT_JSON = Path("/Users/magi/Downloads/Veins New ads/ad_copy_EN.json")

BRAND_CONTEXT = (
    "Brand: Ina Essentials (premium natural Bulgarian skincare, 200,000+ customers across 28 European markets, family-owned, founder Veselina). "
    "Product: Soothing Cream with Horse Chestnut and Smoke Tree (Cotinus coggygria / smradlika). "
    "What it does: improves leg circulation, reduces swelling and venous inflammation, soothes the heavy/tired-legs feeling, "
    "supports the appearance of visible varicose veins. Key actives: horse chestnut (aescin), smoke tree extract, sweet almond oil, hyaluronic acid. "
    "100% natural formula, no synthetic chemicals. Price ~€9.99. Suitable for daily use, 1-2x per day with light massage. External use only. "
    "Target buyer: women 35+ on their feet all day (nurses, teachers, retail, parents), travelers, anyone with heavy legs at end of day or visible veins. "
    "Tone: trustworthy, warm, evidence-led, natural, never alarmist. Lean into heritage + clinically tested + visible relief. "
    "Brand voice rule (HARD): no em-dashes (—) and no en-dashes (–) anywhere in the output. Use commas, periods, colons, or semicolons instead. Hyphens (-) inside compound words are fine."
)

PLATFORM = "Instagram/Facebook"
COPY_LENGTH = "Medium"

SUPPORTED = {".png", ".jpg", ".jpeg", ".webp", ".gif"}


def strip_dashes(text: str) -> str:
    return text.replace("—", ", ").replace("–", ", ")


MAX_BYTES = 4_900_000
MAX_DIM = 1568


def load_and_compress(path: Path) -> tuple[str, str]:
    """Return (base64, media_type), resizing+compressing to fit under 5MB API limit."""
    with Image.open(path) as im:
        im.load()
        if im.mode in ("RGBA", "P"):
            bg = Image.new("RGB", im.size, (255, 255, 255))
            if im.mode == "P":
                im = im.convert("RGBA")
            bg.paste(im, mask=im.split()[-1] if im.mode == "RGBA" else None)
            im = bg
        elif im.mode != "RGB":
            im = im.convert("RGB")

        w, h = im.size
        scale = min(1.0, MAX_DIM / max(w, h))
        if scale < 1.0:
            im = im.resize((int(w * scale), int(h * scale)), Image.LANCZOS)

        for quality in (88, 80, 72, 64, 55, 45):
            buf = io.BytesIO()
            im.save(buf, format="JPEG", quality=quality, optimize=True)
            data = buf.getvalue()
            if len(data) <= MAX_BYTES:
                return base64.standard_b64encode(data).decode("utf-8"), "image/jpeg"
        return base64.standard_b64encode(data).decode("utf-8"), "image/jpeg"


def generate_for_image(client: anthropic.Anthropic, path: Path) -> str:
    image_data, media_type = load_and_compress(path)
    length_instruction = COPY_LENGTH_INSTRUCTIONS[COPY_LENGTH]
    user_content = [
        {
            "type": "image",
            "source": {"type": "base64", "media_type": media_type, "data": image_data},
        },
        {
            "type": "text",
            "text": (
                f"Write ad copy for this image.\n"
                f"Target platform: {PLATFORM}.\n"
                f"Copy length instruction: {length_instruction}\n\n"
                f"Additional context: {BRAND_CONTEXT}\n\n"
                f"Reminder: do not use em-dashes or en-dashes anywhere in your output."
            ),
        },
    ]

    import random
    for attempt in range(5):
        try:
            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=2048,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_content}],
            )
            return strip_dashes(response.content[0].text)
        except anthropic.APIStatusError as e:
            if e.status_code in (529, 500, 503) and attempt < 4:
                wait = min(2 ** attempt + random.uniform(0, 1), 30)
                print(f"  retry in {wait:.1f}s (got {e.status_code})", flush=True)
                time.sleep(wait)
            else:
                raise


def main():
    images = sorted(p for p in IMAGES_DIR.iterdir() if p.suffix.lower() in SUPPORTED)
    print(f"Found {len(images)} images", flush=True)

    client = anthropic.Anthropic()
    results = []

    if OUTPUT_JSON.exists():
        results = json.loads(OUTPUT_JSON.read_text())
        done = {r["filename"] for r in results}
        print(f"Resuming: {len(done)} already done", flush=True)
    else:
        done = set()

    for i, img in enumerate(images, 1):
        if img.name in done:
            print(f"[{i:02d}/{len(images)}] SKIP {img.name}", flush=True)
            continue
        print(f"[{i:02d}/{len(images)}] {img.name}", flush=True)
        try:
            copy_text = generate_for_image(client, img)
            results.append({
                "filename": img.name,
                "category": img.stem.split("_")[0],
                "copy": copy_text,
            })
            OUTPUT_JSON.write_text(json.dumps(results, indent=2, ensure_ascii=False))
        except Exception as e:
            print(f"  FAILED: {e}", flush=True)
            results.append({
                "filename": img.name,
                "category": img.stem.split("_")[0],
                "copy": f"ERROR: {e}",
            })
            OUTPUT_JSON.write_text(json.dumps(results, indent=2, ensure_ascii=False))

    by_category = {}
    for r in results:
        by_category.setdefault(r["category"], []).append(r)

    lines = [
        "# Ina Essentials, Soothing Cream with Horse Chestnut and Smoke Tree",
        "## Ad copy + headlines, English (Medium length, Instagram/Facebook)",
        "",
        f"Total ads: {len(results)}  |  Generated from `/Veins New ads/sorted/`",
        "",
        "---",
        "",
    ]
    for cat in sorted(by_category):
        lines.append(f"## Category: {cat}  ({len(by_category[cat])} ads)")
        lines.append("")
        for r in by_category[cat]:
            lines.append(f"### `{r['filename']}`")
            lines.append("")
            lines.append(r["copy"])
            lines.append("")
            lines.append("---")
            lines.append("")
    OUTPUT_MD.write_text("\n".join(lines))
    print(f"\nWrote {OUTPUT_MD}")
    print(f"Wrote {OUTPUT_JSON}")


if __name__ == "__main__":
    main()
