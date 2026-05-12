"""One-shot driver: generate ad copy for the 6 Evergreen April concepts."""
import io
import sys
import tempfile
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
from ad_copy_agent import generate_ad_copy

MAX_RAW_BYTES = 3_500_000  # leaves headroom for base64 expansion under 5 MB API limit


def shrink_if_needed(src: Path) -> Path:
    if src.stat().st_size <= MAX_RAW_BYTES:
        return src
    img = Image.open(src)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    longest = max(img.size)
    if longest > 1600:
        ratio = 1600 / longest
        img = img.resize((int(img.size[0] * ratio), int(img.size[1] * ratio)), Image.LANCZOS)
    tmp = Path(tempfile.gettempdir()) / f"shrunk_{src.stem}.jpg"
    quality = 88
    while True:
        img.save(tmp, "JPEG", quality=quality, optimize=True)
        if tmp.stat().st_size <= MAX_RAW_BYTES or quality <= 60:
            break
        quality -= 8
    print(f"   (resized {src.name}: {src.stat().st_size//1024}KB -> {tmp.stat().st_size//1024}KB)")
    return tmp

BASE = Path("/Users/magi/Downloads/Evergreen creatives April ")

CONCEPTS = [
    ("Fasting and gaining",   "21 EDIT.png"),
    ("Looking for",           "hf_20260504_103831_b33fc6fc-1eaa-45b1-bc54-f063930744a3.png"),
    ("The biggest mistake",   "33.png"),
    ("The healthy food ",     "38 EDIT.png"),
    ("Thruth about cardio",   "29 EDIT.png"),
    ("eat and lose weight",   "15.png"),
]

BRAND_CONTEXT = (
    "Brand: Dr.Fit — Bulgarian digital fitness/metabolism transformation program. "
    "Audience: 30–55, overweight, struggling with metabolism, want a structured plan. "
    "WRITE THE AD COPY IN BULGARIAN. Address the reader as 'ти' (informal), never 'Вие'. "
    "Tone: direct, motivating, urgency-driven, results-oriented with concrete numbers. "
    "Core offer: 90-day transformation plan, 49 EUR, fully refundable after video testimonial + before/after photos = 0 EUR effective cost. "
    "Tagline reference: 'Промени се за 90 дни и плащаш 0 EUR'. "
    "Avoid medical claims. Emojis OK in headlines/CTA, not body. "
    "Each concept should feel unique to its visual hook."
)

out_path = BASE / "ad_copy_outputs.md"
buf = ["# Evergreen April — Ad Copy\n"]

for folder, filename in CONCEPTS:
    img = BASE / folder / filename
    print(f"\n>>> {folder} / {filename}", flush=True)
    img_for_api = shrink_if_needed(img)
    text = generate_ad_copy(
        image_path=str(img_for_api),
        copy_length="Medium",
        platform="Instagram/Facebook",
        extra_context=BRAND_CONTEXT,
    )
    buf.append(f"\n---\n\n## {folder.strip()}\n\n*Creative:* `{filename}`\n\n{text}\n")
    print(text, flush=True)

out_path.write_text("\n".join(buf), encoding="utf-8")
print(f"\n\nSaved: {out_path}")
