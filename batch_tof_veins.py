"""
TOF (Top of Funnel) ad copy generator for veins creatives.
- Reads images in ~/Downloads/Vein new ads 17.05/
- Generates UNIQUE short/medium copy + headlines per image
- Problem-aware, solution-unaware audience
- NO prices, NO brand/product name
- No em-dashes anywhere
"""
import base64
import io
import json
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from PIL import Image
from dotenv import load_dotenv
import anthropic

load_dotenv()

IMAGES_DIR = Path("/Users/magi/Downloads/Vein new ads 17.05")
OUTPUT_JSON = IMAGES_DIR / "ad_copy_TOF_EN.json"
OUTPUT_MD = IMAGES_DIR / "ad_copy_TOF_EN.md"

MAX_BYTES = 4_900_000
MAX_DIM = 1568

SUPPORTED = {".png", ".jpg", ".jpeg", ".webp", ".gif"}

SYSTEM_PROMPT = """You are a senior direct-response copywriter writing TOP-OF-FUNNEL Meta ad copy for a cold, problem-aware but solution-unaware audience.

Audience profile:
- Women 35+ who have heavy, achy legs at the end of the day, visible bulging or twisted veins on calves, swelling, the feeling that legs "carry too much."
- They KNOW the symptom (heaviness, pain, visible veins, embarrassment in summer clothes).
- They DON'T know there is a botanical/natural cream solution. You are NOT selling a specific product here; you are hooking on the pain/scene to earn the click into the advertorial.

Hard constraints (NEVER violate):
1. NEVER mention prices, currency, percentages of discount, money amounts. No "€", "$", "9.99", "for X", "only Y".
2. NEVER mention a brand or product name. No "Ina Essentials", no "Soothing Cream", no "Horse Chestnut Cream", no product label. You may reference natural ingredients in general terms ("a botanical remedy", "a natural extract") but only if it amplifies the curiosity hook, never as a product pitch.
3. NEVER use em-dashes (—) or en-dashes (–). Use commas, periods, colons, semicolons. Hyphens inside compound words are fine.
4. Keep it MEDIUM or SHORT length: primary text is 1 to 3 sentences (max ~50 words). Headlines under 9 words.

Each output must be UNIQUE per image. Look at the image's specific visual angle (close-up of swollen calves, before-after, woman hiding legs, anatomy diagram, kitchen scene, post-it diary, etc.) and write copy that FEELS like a direct reaction to THAT scene. The same pain, but framed by what the viewer is looking at.

Output format (exactly this JSON, no markdown fences):
{
  "ad_angle": "one sentence naming the angle and why it fits this visual",
  "headlines": ["headline 1", "headline 2", "headline 3"],
  "primary_text": "1 to 3 sentences. Pain-aware, no brand, no price.",
  "cta_suggestion": "LEARN_MORE | READ_MORE | SEE_MORE | SHOP_NOW (we will set the final CTA enum at upload time, just suggest the spirit)"
}

Style tone: warm, knowing, conversational, slightly intriguing. No alarmist or shame language. Speak to her like a friend who notices."""


def load_and_compress(path: Path) -> tuple[str, str]:
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


def strip_dashes(s: str) -> str:
    return s.replace("—", ", ").replace("–", ", ")


def generate(client: anthropic.Anthropic, path: Path) -> dict:
    image_data, media_type = load_and_compress(path)
    user_content = [
        {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": image_data}},
        {"type": "text", "text": "Generate the TOF ad copy JSON for this image. Remember: no prices, no product name, no em-dashes, medium/short length, unique to this image's angle."},
    ]
    for attempt in range(5):
        try:
            resp = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=1200,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_content}],
            )
            raw = resp.content[0].text.strip()
            if raw.startswith("```"):
                raw = raw.strip("`")
                if raw.lower().startswith("json"):
                    raw = raw[4:].lstrip()
            start = raw.find("{")
            end = raw.rfind("}")
            obj = json.loads(raw[start:end + 1])
            for k in ("ad_angle", "primary_text", "cta_suggestion"):
                if k in obj:
                    obj[k] = strip_dashes(obj[k])
            if "headlines" in obj:
                obj["headlines"] = [strip_dashes(h) for h in obj["headlines"]]
            return obj
        except (anthropic.APIStatusError, json.JSONDecodeError, ValueError) as e:
            if attempt < 4:
                wait = min(2 ** attempt + random.uniform(0, 1), 30)
                print(f"  retry in {wait:.1f}s: {type(e).__name__}", flush=True)
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

    for i, img in enumerate(images, 1):
        if img.name in done:
            continue
        print(f"[{i:02d}/{len(images)}] {img.name}", flush=True)
        try:
            copy = generate(client, img)
            results.append({
                "filename": img.name,
                "ad_angle": copy.get("ad_angle", ""),
                "headlines": copy.get("headlines", []),
                "primary_text": copy.get("primary_text", ""),
                "cta_suggestion": copy.get("cta_suggestion", ""),
            })
        except Exception as e:
            print(f"  FAILED: {e}", flush=True)
            results.append({"filename": img.name, "error": str(e)})
        OUTPUT_JSON.write_text(json.dumps(results, indent=2, ensure_ascii=False))

    lines = [
        "# Vein new ads 17.05, TOF Ad Copy (English source)",
        "",
        f"36 creatives, problem-aware audience, no prices, no product name.",
        "",
        "---",
        "",
    ]
    for r in results:
        lines.append(f"## `{r['filename']}`")
        lines.append("")
        if r.get("ad_angle"):
            lines.append(f"**Angle:** {r['ad_angle']}")
            lines.append("")
        lines.append("**Headlines:**")
        for j, h in enumerate(r.get("headlines", []), 1):
            lines.append(f"{j}. {h}")
        lines.append("")
        lines.append(f"**Primary Text:** {r.get('primary_text', '')}")
        lines.append("")
        lines.append(f"**CTA suggestion:** {r.get('cta_suggestion', '')}")
        lines.append("")
        lines.append("---")
        lines.append("")
    OUTPUT_MD.write_text("\n".join(lines))
    print(f"\nWrote {OUTPUT_JSON}")
    print(f"Wrote {OUTPUT_MD}")


if __name__ == "__main__":
    main()
