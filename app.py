"""Ad Copy Agent — single-page Streamlit app."""

import base64, os, sys, time, random, io, tempfile, json

from PIL import Image
import anthropic
import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(__file__))
from _styles import apply_styles, label

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

st.set_page_config(
    page_title="Ad Copy Agent — Anchor Media",
    page_icon="✦",
    layout="centered",
    initial_sidebar_state="collapsed",
)
apply_styles()

# ── Constants ────────────────────────────────────────────────────────────────

SUPPORTED_FORMATS = {
    "jpg": "image/jpeg", "jpeg": "image/jpeg",
    "png": "image/png", "gif": "image/gif", "webp": "image/webp",
}
SUPPORTED_VIDEO_FORMATS = ["mp4", "mov", "avi", "webm"]
PLATFORMS = ["Instagram / Facebook", "TikTok", "Google Display", "YouTube", "LinkedIn", "Pinterest", "Twitter / X"]
COPY_LENGTH_INSTRUCTIONS = {
    "Short":  "Primary Text: 1–2 sentences. Ultra-concise — hook immediately, every word earns its place.",
    "Medium": "Primary Text: 3–4 sentences. Hook + context + payoff. Balanced for standard feed placements.",
    "Long":   "Primary Text: 6–10 sentences. Story arc: strong hook, build desire, present product as solution, close with urgency or social proof.",
}
SYSTEM_PROMPT = """You are an expert direct-response advertising copywriter with 15+ years of experience across Meta, Google, TikTok, and display advertising.

Respond in this EXACT format:

AD ANGLE
[one sentence naming the angle and why it fits this visual]

HEADLINES
1. [headline]
2. [headline]
3. [headline]

PRIMARY TEXT
[the copy — follow the length instruction exactly]

CTA
[call-to-action button text only]

Rules:
- No generic copy. Every line must feel specific to THIS image.
- Headlines under 10 words each.
- If a product/brand/offer is visible, use it.
- Match tone to the visual energy."""


# ── Helper functions ─────────────────────────────────────────────────────────

def scrape_product_page(url: str) -> str:
    from playwright.sync_api import sync_playwright
    info_parts = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
            page = browser.new_page(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page.goto(url, wait_until="domcontentloaded", timeout=25000)
            page.wait_for_timeout(2000)
            title = page.title()
            if title:
                info_parts.append(f"Page title: {title}")
            for selector in ['meta[property="og:description"]', 'meta[name="description"]']:
                meta = page.get_attribute(selector, "content")
                if meta:
                    info_parts.append(f"Meta description: {meta.strip()}")
                    break
            h1_els = page.locator("h1")
            if h1_els.count() > 0:
                h1 = h1_els.first.text_content(timeout=2000)
                if h1 and h1.strip():
                    info_parts.append(f"Product name: {h1.strip()}")
            for sel in ['[class*="price"]', '[data-testid*="price"]', '[itemprop="price"]',
                        '.product-price', '#price', '.price']:
                try:
                    el = page.locator(sel).first
                    if el.count() > 0:
                        price_text = el.text_content(timeout=1000)
                        if price_text and any(c.isdigit() for c in price_text):
                            info_parts.append(f"Price: {price_text.strip()}")
                            break
                except Exception:
                    pass
            for sel in ['[class*="description"]', '[itemprop="description"]',
                        '.product-description', '#product-description', '.product__description',
                        '.product__body', '[class*="product-detail"]']:
                try:
                    el = page.locator(sel).first
                    if el.count() > 0:
                        desc = el.text_content(timeout=1000)
                        if desc and len(desc.strip()) > 30:
                            info_parts.append(f"Product description: {desc.strip()[:800]}")
                            break
                except Exception:
                    pass
            if not any("Product description" in part for part in info_parts):
                body = page.evaluate("""() => {
                    ['nav','header','footer','script','style'].forEach(
                        tag => document.querySelectorAll(tag).forEach(el => el.remove())
                    );
                    const main = document.querySelector('main,[role="main"]') || document.body;
                    return main.innerText;
                }""")
                if body:
                    lines = [l.strip() for l in body.splitlines() if l.strip() and len(l.strip()) > 15]
                    snippet = " ".join(lines[:30])[:1200]
                    if snippet:
                        info_parts.append(f"Page content: {snippet}")
            browser.close()
    except Exception as e:
        return f"Could not fetch product page: {e}"
    return "\n".join(info_parts) if info_parts else "No product information could be extracted from this page."


def compress_image(image_bytes: bytes, media_type: str, max_bytes: int = 4 * 1024 * 1024) -> tuple[bytes, str]:
    if len(image_bytes) <= max_bytes:
        return image_bytes, media_type
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    quality = 85
    scale = 1.0
    for _ in range(8):
        w, h = int(img.width * scale), int(img.height * scale)
        resized = img.resize((w, h), Image.LANCZOS) if scale < 1.0 else img
        buf = io.BytesIO()
        resized.save(buf, format="JPEG", quality=quality)
        if buf.tell() <= max_bytes:
            return buf.getvalue(), "image/jpeg"
        scale *= 0.85
        quality = max(quality - 5, 50)
    buf = io.BytesIO()
    img.resize((800, int(800 * img.height / img.width)), Image.LANCZOS).save(buf, format="JPEG", quality=60)
    return buf.getvalue(), "image/jpeg"


def generate_copy(image_bytes, media_type, platform, length, context, product_info=""):
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    image_bytes, media_type = compress_image(image_bytes, media_type)
    b64 = base64.standard_b64encode(image_bytes).decode("utf-8")
    prompt = (
        f"Write ad copy for this image.\nTarget platform: {platform}.\n"
        f"Length instruction: {COPY_LENGTH_INSTRUCTIONS[length]}"
    )
    if product_info.strip():
        prompt += f"\n\nProduct page information (use this to ground the copy in real product details):\n{product_info}"
    if context.strip():
        prompt += f"\n\nExtra context: {context}"
    user_content = [
        {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": b64}},
        {"type": "text", "text": prompt},
    ]
    for attempt in range(5):
        try:
            r = client.messages.create(model="claude-sonnet-4-6", max_tokens=2048, system=SYSTEM_PROMPT,
                                        messages=[{"role": "user", "content": user_content}])
            return r.content[0].text
        except anthropic.APIStatusError as e:
            if e.status_code in (529, 500) and attempt < 4:
                time.sleep(min(2 ** attempt + random.uniform(0, 1), 30))
            else:
                raise


def translate_copy(text: str, language: str) -> str:
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    for attempt in range(5):
        try:
            r = client.messages.create(
                model="claude-sonnet-4-6", max_tokens=2048,
                messages=[{"role": "user", "content": (
                    f"Translate the following ad copy to {language}. "
                    f"Keep the same structure, tone, and formatting. "
                    f"Do not add explanations — output only the translated text.\n\n{text}"
                )}],
            )
            return r.content[0].text
        except anthropic.APIStatusError as e:
            if e.status_code in (529, 500) and attempt < 4:
                time.sleep(min(2 ** attempt + random.uniform(0, 1), 30))
            else:
                raise


def parse_result(text):
    out = {"angle": "", "headlines": [], "primary": "", "cta": ""}
    current = None
    for line in text.strip().splitlines():
        s = line.strip()
        if s == "AD ANGLE":          current = "angle"
        elif s == "HEADLINES":       current = "headlines"
        elif s == "PRIMARY TEXT":    current = "primary"
        elif s == "CTA":             current = "cta"
        elif s and current:
            if current == "angle" and not out["angle"]:
                out["angle"] = s
            elif current == "headlines":
                clean = s.lstrip("123456789.-) ").strip()
                if clean:
                    out["headlines"].append(clean)
            elif current == "primary":
                out["primary"] += (" " if out["primary"] else "") + s
            elif current == "cta" and not out["cta"]:
                out["cta"] = s
    return out


# ── Video processing ─────────────────────────────────────────────────────────

def extract_video_frames(video_bytes: bytes, max_frames: int = 8) -> list[bytes]:
    try:
        import cv2
    except ImportError:
        raise ImportError("opencv-python is required for video support. Run: pip install opencv-python")
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
        tmp.write(video_bytes)
        tmp_path = tmp.name
    try:
        cap = cv2.VideoCapture(tmp_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_frames <= 0:
            raise ValueError("Could not read video frames.")
        indices = [int(i * total_frames / max_frames) for i in range(max_frames)]
        frames = []
        for idx in indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = cap.read()
            if ret:
                _, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                frames.append(buf.tobytes())
        cap.release()
        return frames
    finally:
        os.unlink(tmp_path)


def transcribe_audio(video_bytes: bytes) -> str:
    try:
        import whisper
        import numpy as np
        import imageio_ffmpeg
        import subprocess
    except ImportError as e:
        raise ImportError(f"Missing dependency: {e}. Run: pip install openai-whisper imageio-ffmpeg")
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
        tmp.write(video_bytes)
        tmp_path = tmp.name
    try:
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        proc = subprocess.run(
            [ffmpeg_exe, "-nostdin", "-i", tmp_path, "-ar", "16000", "-ac", "1", "-f", "f32le", "-"],
            capture_output=True, check=True,
        )
        audio = np.frombuffer(proc.stdout, dtype=np.float32)
        model = whisper.load_model("base")
        result = model.transcribe(audio)
        return result["text"].strip()
    finally:
        os.unlink(tmp_path)


def transcribe_video_script(video_bytes: bytes, frames: list[bytes]) -> str:
    audio_transcript = transcribe_audio(video_bytes)
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    content = []
    for frame_bytes in frames:
        b64 = base64.standard_b64encode(frame_bytes).decode("utf-8")
        content.append({"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": b64}})
    content.append({
        "type": "text",
        "text": (
            f"Here is the spoken audio transcript from this video advertisement:\n\n"
            f"\"{audio_transcript}\"\n\n"
            "These are frames from the same video. Please:\n"
            "1. Describe what is happening visually across the frames.\n"
            "2. Note any on-screen text, logos, brand names, or pricing.\n"
            "3. Comment on how the visuals relate to the spoken script.\n\n"
            "Format as:\n\nSPOKEN SCRIPT\n[transcript]\n\nVISUAL DESCRIPTION\n[description]\n\n"
            "BRANDING & PRODUCT\n[details]\n\nSCRIPT + VISUAL ALIGNMENT\n[analysis]"
        ),
    })
    for attempt in range(5):
        try:
            r = client.messages.create(model="claude-sonnet-4-6", max_tokens=2048,
                                        messages=[{"role": "user", "content": content}])
            return r.content[0].text
        except anthropic.APIStatusError as e:
            if e.status_code in (529, 500) and attempt < 4:
                time.sleep(min(2 ** attempt + random.uniform(0, 1), 30))
            else:
                raise


def understand_video_concept(transcript: str) -> str:
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    for attempt in range(5):
        try:
            r = client.messages.create(
                model="claude-sonnet-4-6", max_tokens=1024,
                messages=[{"role": "user", "content": (
                    f"Based on this video ad analysis:\n\n{transcript}\n\n"
                    "Identify the core advertising strategy. Format as:\n\n"
                    "ANGLE\n[one sentence]\n\nTARGET AUDIENCE\n[who]\n\n"
                    "PRODUCT / KEY BENEFIT\n[what + #1 benefit]\n\n"
                    "EMOTIONAL HOOK\n[desire/pain point]\n\nTONE & ENERGY\n[feel]"
                )}],
            )
            return r.content[0].text
        except anthropic.APIStatusError as e:
            if e.status_code in (529, 500) and attempt < 4:
                time.sleep(min(2 ** attempt + random.uniform(0, 1), 30))
            else:
                raise


def generate_copy_from_video(transcript, concept, platform, length, context, product_info=""):
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    prompt = (
        f"Write ad copy based on this video advertisement analysis.\n"
        f"Target platform: {platform}.\n"
        f"Length instruction: {COPY_LENGTH_INSTRUCTIONS[length]}\n\n"
        f"VIDEO TRANSCRIPT & VISUALS:\n{transcript}\n\n"
        f"CONCEPT UNDERSTANDING:\n{concept}"
    )
    if product_info.strip():
        prompt += f"\n\nProduct page information:\n{product_info}"
    if context.strip():
        prompt += f"\n\nExtra context: {context}"
    for attempt in range(5):
        try:
            r = client.messages.create(model="claude-sonnet-4-6", max_tokens=2048, system=SYSTEM_PROMPT,
                                        messages=[{"role": "user", "content": prompt}])
            return r.content[0].text
        except anthropic.APIStatusError as e:
            if e.status_code in (529, 500) and attempt < 4:
                time.sleep(min(2 ** attempt + random.uniform(0, 1), 30))
            else:
                raise


# ── Page guard ───────────────────────────────────────────────────────────────

if not os.getenv("ANTHROPIC_API_KEY"):
    st.error("ANTHROPIC_API_KEY not found in .env")
    st.stop()

# ── Hero ─────────────────────────────────────────────────────────────────────

st.markdown("""
<div style="margin-bottom:8px;">
    <span class="label">Anchor Media</span>
</div>
<div style="font-family:'Space Grotesk',sans-serif;font-size:48px;font-weight:700;color:rgba(255,255,255,0.95);line-height:1.1;letter-spacing:-0.02em;">
    Ad Copy<br>
    <span class="serif-italic gradient-text">Agent</span>
</div>
<p style="margin-top:16px;font-size:16px;color:rgba(255,255,255,0.55);max-width:600px;">
    Upload an ad image or video — get scroll-stopping headlines, primary text, and a CTA instantly.
</p>
""", unsafe_allow_html=True)

st.markdown("<div style='height:48px'></div>", unsafe_allow_html=True)

# ── Input Section ────────────────────────────────────────────────────────────

left_col, spacer, right_col = st.columns([5, 1, 6])

with left_col:
    # Mode selector
    st.markdown("<span class='label'>Input</span>", unsafe_allow_html=True)
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    mode = st.radio(
        "Input mode", ["Image", "Video"],
        horizontal=True, label_visibility="collapsed",
    )
    is_video = mode == "Video"
    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    # Upload
    if is_video:
        label("Ad Video")
        video_uploaded = st.file_uploader("Drop video", type=SUPPORTED_VIDEO_FORMATS, label_visibility="collapsed")
        if video_uploaded:
            st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
            st.video(video_uploaded)
        uploaded = None
    else:
        label("Ad Image")
        uploaded = st.file_uploader("Drop image", type=list(SUPPORTED_FORMATS.keys()), label_visibility="collapsed")
        if uploaded:
            st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
            st.image(uploaded, use_container_width=True)
        video_uploaded = None

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    # Product URL
    if not is_video:
        label("Product Page URL")
        if "product_info" not in st.session_state:
            st.session_state.product_info = ""
        if "product_url" not in st.session_state:
            st.session_state.product_url = ""

        def _on_url_change():
            url = st.session_state._product_url_input.strip()
            if url and url != st.session_state.product_url:
                st.session_state.product_info = scrape_product_page(url)
                st.session_state.product_url = url
            elif not url:
                st.session_state.product_info = ""
                st.session_state.product_url = ""

        st.text_input(
            "Product URL", key="_product_url_input",
            value=st.session_state.product_url,
            placeholder="https://store.com/product",
            label_visibility="collapsed",
            on_change=_on_url_change,
        )
        if st.session_state.product_info:
            with st.expander("Product info extracted", expanded=False):
                st.text(st.session_state.product_info[:1500])
            if st.button("Clear product info"):
                st.session_state.product_info = ""
                st.session_state.product_url = ""
                st.rerun()
        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    else:
        if "product_info" not in st.session_state:
            st.session_state.product_info = ""
        if "video_link_url" not in st.session_state:
            st.session_state.video_link_url = ""
        if "product_url" not in st.session_state:
            st.session_state.product_url = ""

        label("Link URL")
        video_link_url = st.text_input(
            "Link URL", key="_video_link_url_input",
            value=st.session_state.video_link_url,
            placeholder="https://yourstore.com/product",
            label_visibility="collapsed",
        )
        st.session_state.video_link_url = video_link_url.strip()
        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # Settings
    label("Platform")
    platform = st.selectbox("Platform", PLATFORMS, label_visibility="collapsed")
    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    label("Copy Length")
    length = st.radio("Length", ["Short", "Medium", "Long"], horizontal=True, label_visibility="collapsed")
    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    label("Extra Context")
    context = st.text_area("Context", placeholder="e.g. Luxury skincare, targeting women 35–55, 20% off launch", height=80, label_visibility="collapsed")
    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    label("Testimonial / Text to Include")
    testimonial = st.text_area("Testimonial", placeholder='e.g. "This changed my life" — Sarah M.', height=80, label_visibility="collapsed")
    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    label("Translate To")
    LANGUAGES = ["— None —", "Romanian"]
    translate_to = st.selectbox("Translate", LANGUAGES, label_visibility="collapsed")
    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

    has_input = (uploaded is not None) if not is_video else (video_uploaded is not None)
    generate_btn = st.button("Generate Copy  →", disabled=not has_input, use_container_width=True)


# ── Results Column ───────────────────────────────────────────────────────────

with right_col:
    for key, default in [
        ("copy_result", None), ("copy_error", None),
        ("copy_testimonial", ""), ("copy_product_url", ""),
        ("copy_language", ""), ("copy_translated", ""),
        ("result_mode", "image"),
        ("video_transcript", ""), ("video_concept", ""),
    ]:
        if key not in st.session_state:
            st.session_state[key] = default

    # Image generation
    if generate_btn and not is_video and uploaded:
        st.session_state.copy_result = None
        st.session_state.copy_error = None
        st.session_state.copy_testimonial = testimonial
        st.session_state.copy_product_url = st.session_state.product_url
        st.session_state.copy_language = "" if translate_to == "— None —" else translate_to
        st.session_state.copy_translated = ""
        st.session_state.result_mode = "image"
        st.session_state.video_transcript = ""
        st.session_state.video_concept = ""
        ext = uploaded.name.rsplit(".", 1)[-1].lower()
        media_type = SUPPORTED_FORMATS.get(ext, "image/jpeg")
        with st.spinner("Analyzing image…"):
            try:
                raw = generate_copy(uploaded.read(), media_type, platform, length, context,
                                    product_info=st.session_state.product_info)
                st.session_state.copy_result = parse_result(raw)
            except Exception as e:
                st.session_state.copy_error = str(e)

    # Video generation
    if generate_btn and is_video and video_uploaded:
        st.session_state.copy_result = None
        st.session_state.copy_error = None
        st.session_state.copy_testimonial = testimonial
        st.session_state.copy_product_url = st.session_state.get("video_link_url", "")
        st.session_state.copy_language = "" if translate_to == "— None —" else translate_to
        st.session_state.copy_translated = ""
        st.session_state.result_mode = "video"
        st.session_state.video_transcript = ""
        st.session_state.video_concept = ""
        try:
            video_bytes = video_uploaded.read()
            with st.status("Processing video…", expanded=True) as status:
                st.write("Extracting frames…")
                frames = extract_video_frames(video_bytes)
                st.write(f"Extracted {len(frames)} frames")
                st.write("Step 1 — Transcribing audio & analyzing visuals…")
                transcript = transcribe_video_script(video_bytes, frames)
                st.session_state.video_transcript = transcript
                st.write("Step 2 — Understanding the ad concept…")
                concept = understand_video_concept(transcript)
                st.session_state.video_concept = concept
                st.write("Step 3 — Writing ad copy…")
                raw = generate_copy_from_video(transcript, concept, platform, length, context,
                                                product_info=st.session_state.product_info)
                st.session_state.copy_result = parse_result(raw)
                status.update(label="Ad copy generated!", state="complete", expanded=False)
        except Exception as e:
            st.session_state.copy_error = str(e)

    # Display results
    if st.session_state.copy_error:
        st.error(f"Error: {st.session_state.copy_error}")

    elif st.session_state.copy_result:
        r = st.session_state.copy_result

        st.markdown("<span class='label'>Results</span>", unsafe_allow_html=True)
        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

        # Video intermediate steps
        if st.session_state.result_mode == "video":
            if st.session_state.video_transcript:
                with st.expander("Step 1 — Video Transcript & Visuals", expanded=False):
                    st.text(st.session_state.video_transcript)
            if st.session_state.video_concept:
                with st.expander("Step 2 — Concept Understanding", expanded=False):
                    st.text(st.session_state.video_concept)
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

        # Ad Angle
        if r["angle"]:
            st.markdown(f"""
            <div class='result-card fade-up delay-1'>
                <div class='accent-bar'></div>
                <div class='card-label'>Ad Angle</div>
                <div class='card-content'>{r['angle']}</div>
            </div>""", unsafe_allow_html=True)

        # Headlines
        if r["headlines"]:
            hl = "".join(
                f"<div class='headline-item'><span class='headline-num'>{i+1}</span>{h}</div>"
                for i, h in enumerate(r["headlines"])
            )
            st.markdown(f"""
            <div class='result-card fade-up delay-2'>
                <div class='accent-bar'></div>
                <div class='card-label'>Headlines</div>
                {hl}
            </div>""", unsafe_allow_html=True)

        # Primary Text
        if r["primary"]:
            st.markdown(f"""
            <div class='result-card fade-up delay-3'>
                <div class='accent-bar'></div>
                <div class='card-label'>Primary Text</div>
                <div class='card-content'>{r['primary']}</div>
            </div>""", unsafe_allow_html=True)

        # CTA
        if r["cta"]:
            st.markdown(f"""
            <div class='result-card fade-up delay-4'>
                <div class='accent-bar'></div>
                <div class='card-label'>CTA</div>
                <span class='cta-badge'>{r['cta']}</span>
            </div>""", unsafe_allow_html=True)

        # Final Full Ad Copy
        saved_testimonial = st.session_state.copy_testimonial
        saved_url = st.session_state.copy_product_url

        if saved_testimonial or saved_url:
            st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
            st.markdown("<div class='card-label'>FINAL AD COPY</div>", unsafe_allow_html=True)

            parts = []
            if r["primary"]:
                parts.append(r["primary"])
            if saved_testimonial:
                clean_testimonial = saved_testimonial.strip('"\'')
                parts.append(f'"{clean_testimonial}"')
            if r["cta"]:
                parts.append(f"👉 {r['cta']}")
            if saved_url:
                parts.append(saved_url)

            final_copy = "\n\n".join(parts)

            if "final_copy_edited" not in st.session_state:
                st.session_state.final_copy_edited = final_copy
            if st.session_state.get("final_copy_base") != final_copy:
                st.session_state.final_copy_base = final_copy
                st.session_state.final_copy_edited = final_copy

            lang = st.session_state.copy_language
            tabs = ["Edit", "Copy"]
            if lang:
                tabs.append(f"{lang}")
            tab_objs = st.tabs(tabs)

            with tab_objs[0]:
                st.session_state.final_copy_edited = st.text_area(
                    "Final Copy",
                    value=st.session_state.final_copy_edited,
                    height=260,
                    label_visibility="collapsed",
                    key="final_copy_area",
                )
                text_json = json.dumps(st.session_state.final_copy_edited)
                components.html(f"""
                <button onclick="navigator.clipboard.writeText({text_json}).then(()=>{{this.innerText='Copied';setTimeout(()=>this.innerText='Copy to Clipboard',2000)}}).catch(()=>{{this.innerText='Copy failed'}})">
                    Copy to Clipboard
                </button>
                <style>
                button {{
                    background:rgba(37,99,235,0.12);color:#3B82F6;border:1px solid rgba(37,99,235,0.2);
                    padding:8px 20px;border-radius:100px;cursor:pointer;
                    font-size:13px;font-family:'Space Grotesk','Inter',sans-serif;font-weight:600;
                    margin-top:4px;letter-spacing:0.04em;
                    transition:all 0.35s cubic-bezier(0.16,1,0.3,1);
                }}
                button:hover{{background:rgba(37,99,235,0.2);border-color:rgba(37,99,235,0.4);}}
                </style>
                """, height=52)

            with tab_objs[1]:
                st.code(st.session_state.final_copy_edited, language=None)

            if lang:
                with tab_objs[2]:
                    if not st.session_state.copy_translated:
                        with st.spinner(f"Translating to {lang}…"):
                            try:
                                st.session_state.copy_translated = translate_copy(
                                    st.session_state.final_copy_edited, lang
                                )
                            except Exception as e:
                                st.session_state.copy_translated = f"Translation error: {e}"
                    st.code(st.session_state.copy_translated, language=None)

    else:
        # Empty state
        st.markdown("""
        <div style='height:400px;display:flex;flex-direction:column;align-items:center;justify-content:center;'>
            <div style="width:64px;height:64px;border-radius:20px;background:rgba(37,99,235,0.12);border:1px solid rgba(37,99,235,0.2);display:flex;align-items:center;justify-content:center;font-size:1.6rem;margin-bottom:16px;">
                ✦
            </div>
            <div style="font-family:'Space Grotesk',sans-serif;font-size:16px;font-weight:600;color:rgba(255,255,255,0.25);">
                Results will appear here
            </div>
            <div style="font-size:13px;color:rgba(255,255,255,0.15);margin-top:6px;">
                Upload an image or video to get started
            </div>
        </div>""", unsafe_allow_html=True)

# ── Footer ───────────────────────────────────────────────────────────────────

st.markdown("<div style='height:64px'></div>", unsafe_allow_html=True)
st.markdown("""
<div style="text-align:center;padding:32px;background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.06);border-radius:20px;backdrop-filter:blur(20px);">
    <span class="label" style="color:rgba(59,130,246,0.7);">Anchor Media</span>
    <div style="font-family:'Space Grotesk',sans-serif;font-size:20px;font-weight:600;color:rgba(255,255,255,0.95);margin-top:8px;">
        Built for <span class="serif-italic gradient-text">performance</span>
    </div>
    <p style="font-size:13px;color:rgba(255,255,255,0.25);margin-top:12px;font-family:'Space Grotesk',sans-serif;">
        Ad Copy Agent — Powered by Claude
    </p>
</div>
""", unsafe_allow_html=True)
