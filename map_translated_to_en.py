"""
Vision-match translated TOF veins creatives (PL/RO/FR) to the closest EN ad_angle.
Reads translated PNGs from both drive-download folders, sends each (in batches of 4)
to Claude vision with the 43 EN candidates, and produces a mapping per market.
Output: angle_match_{lang}.json with {translated_filename: en_filename}.
"""
import base64
import io
import json
import os
import random
import sys
import time
from pathlib import Path

from PIL import Image
from dotenv import load_dotenv
import anthropic

load_dotenv()

BASE = Path("/Users/magi/Downloads/Vein new ads 17.05")
COPY_DIR = BASE / "Ad copy 17.05."
EN_JSON = COPY_DIR / "ad_copy_TOF_EN.json"
DRIVE_DIRS = [
    BASE / "drive-download-20260519T135937Z-3-001",
    BASE / "drive-download-20260519T135937Z-3-002",
]
OUT_DIR = COPY_DIR

# (folder_code, asset_code) — folder under drive-download / suffix on asset files
MARKETS = [
    ("PL", "PL"),
    ("RO", "RO"),
    ("FR", "FR"),
    ("CZ", "CZ"),
    ("GR", "EL"),
    ("SK", "SK"),
]
BATCH_SIZE = 4
MAX_DIM = 1024
MAX_BYTES = 4_500_000


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
        for quality in (78, 65, 55, 45):
            buf = io.BytesIO()
            im.save(buf, format="JPEG", quality=quality, optimize=True)
            data = buf.getvalue()
            if len(data) <= MAX_BYTES:
                return base64.standard_b64encode(data).decode("utf-8"), "image/jpeg"
        return base64.standard_b64encode(data).decode("utf-8"), "image/jpeg"


def collect_for_market(folder_code: str) -> list[Path]:
    files = []
    seen = set()
    for d in DRIVE_DIRS:
        sub = d / folder_code
        if not sub.exists():
            continue
        for p in sorted(sub.iterdir()):
            if p.suffix.lower() in (".png", ".jpg", ".jpeg") and p.name not in seen:
                files.append(p)
                seen.add(p.name)
    return files


def build_candidate_block(en_data: list) -> str:
    lines = []
    for r in en_data:
        lines.append(f"- {r['filename']} :: {r.get('ad_angle','').strip()}")
    return "\n".join(lines)


def match_batch(client: anthropic.Anthropic, batch_paths: list[Path], en_candidates_block: str) -> dict[str, str]:
    content = []
    name_index = []
    for p in batch_paths:
        data, mt = load_and_compress(p)
        content.append({"type": "image", "source": {"type": "base64", "media_type": mt, "data": data}})
        name_index.append(p.name)

    text = (
        "You are matching each of the attached creatives to the closest item in the EN candidate list below. "
        "Each EN candidate is `filename :: angle description`. For each attached image (in order), pick the "
        "single EN filename whose described angle/visual best matches that creative. Multiple attached images "
        "may map to the same EN filename if they share an angle. Return ONLY JSON in this exact shape, no markdown:\n\n"
        "{\n  \"matches\": [\n    {\"image_index\": 0, \"en_filename\": \"...\"},\n    ...\n  ]\n}\n\n"
        f"Attached images in order: {name_index}\n\n"
        f"EN candidates ({len(en_candidates_block.splitlines())} options):\n{en_candidates_block}"
    )
    content.append({"type": "text", "text": text})

    for attempt in range(4):
        try:
            resp = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=1200,
                messages=[{"role": "user", "content": content}],
                timeout=180.0,
            )
            raw = resp.content[0].text.strip()
            if raw.startswith("```"):
                raw = raw.strip("`")
                if raw.lower().startswith("json"):
                    raw = raw[4:].lstrip()
            start = raw.find("{")
            end = raw.rfind("}")
            obj = json.loads(raw[start:end + 1])
            result = {}
            for m in obj.get("matches", []):
                idx = int(m["image_index"])
                en_fn = m["en_filename"].strip()
                if 0 <= idx < len(name_index):
                    result[name_index[idx]] = en_fn
            return result
        except (anthropic.APIStatusError, json.JSONDecodeError, ValueError, KeyError) as e:
            if attempt < 3:
                wait = min(2 ** attempt + random.uniform(0, 1), 30)
                print(f"  retry in {wait:.1f}s: {type(e).__name__}: {str(e)[:120]}", flush=True)
                time.sleep(wait)
            else:
                raise


def main():
    en_data = json.loads(EN_JSON.read_text())
    en_filenames = {r["filename"] for r in en_data}
    candidates_block = build_candidate_block(en_data)
    client = anthropic.Anthropic()

    for folder_code, asset_code in MARKETS:
        out_path = OUT_DIR / f"angle_match_{asset_code}.json"
        existing = {}
        if out_path.exists():
            existing = json.loads(out_path.read_text())
            print(f"[{asset_code}] resume: {len(existing)} already mapped", flush=True)
        files = collect_for_market(folder_code)
        todo = [p for p in files if p.name not in existing]
        print(f"[{asset_code}] {len(files)} total, {len(todo)} to map (folder={folder_code})", flush=True)

        mapping = dict(existing)
        for i in range(0, len(todo), BATCH_SIZE):
            batch = todo[i:i + BATCH_SIZE]
            print(f"[{asset_code}] batch {i//BATCH_SIZE + 1}: {len(batch)} images", flush=True)
            try:
                res = match_batch(client, batch, candidates_block)
            except Exception as e:
                print(f"  FAILED batch: {e}", flush=True)
                continue
            bad = [(fn, en) for fn, en in res.items() if en not in en_filenames]
            if bad:
                print(f"  WARN unknown EN filename(s): {bad}", flush=True)
            mapping.update(res)
            out_path.write_text(json.dumps(mapping, indent=2, ensure_ascii=False))
        unmatched = [p.name for p in files if p.name not in mapping]
        print(f"[{asset_code}] DONE: {len(mapping)} mapped, {len(unmatched)} unmatched", flush=True)
        if unmatched:
            print(f"  unmatched sample: {unmatched[:3]}", flush=True)


if __name__ == "__main__":
    main()
