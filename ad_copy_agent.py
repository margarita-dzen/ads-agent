"""
Ad Copy Agent
Reads an ad image and generates matching headlines and ad copy using Claude.
"""

import argparse
import base64
import os
import sys
from pathlib import Path

import anthropic
import questionary
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule

load_dotenv()
console = Console()

SUPPORTED_FORMATS = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".webp": "image/webp",
}

COPY_LENGTH_INSTRUCTIONS = {
    "Short": (
        "Primary Text length: 1–2 sentences only. "
        "Ultra-concise — every word must earn its place. "
        "Hook immediately, no build-up."
    ),
    "Medium": (
        "Primary Text length: 3–4 sentences. "
        "Hook + context + payoff. "
        "Balanced for standard feed placements."
    ),
    "Long": (
        "Primary Text length: 6–10 sentences. "
        "Tell a story: open with a strong hook, build tension or desire, "
        "introduce the product/offer as the solution, and close with urgency or social proof. "
        "Write for cold audiences who need more convincing."
    ),
}

SYSTEM_PROMPT = """You are an expert direct-response advertising copywriter with 15+ years of experience across Meta, Google, TikTok, and display advertising.

When given an ad image, you:
1. Analyze the visual: product, mood, colors, people, setting, and overall aesthetic
2. Identify the ad angle (e.g. problem/solution, transformation, lifestyle, curiosity hook, social proof, urgency, aspiration)
3. Write copy that amplifies what the image communicates — the words and visual should feel like one unified message

Your output format:
- **Ad Angle**: One sentence naming the angle and why it fits this visual
- **Headlines** (3 options, each under 10 words): Bold, punchy, benefit-driven. Vary the angle slightly across the 3.
- **Primary Text**: Follow the length instruction provided in the user message exactly.
- **CTA**: The single best call-to-action button text for this ad

Rules:
- No generic copy ("Discover the difference", "Transform your life"). Every line must feel specific to THIS image.
- Headlines should be strong enough to stop a scroll.
- If a product, brand, or offer is visible, incorporate it directly.
- Match tone to the visual: if the image is playful, be playful. If it's premium/aspirational, be sharp and confident."""


def ask_copy_length() -> str:
    """Prompt the user to choose ad copy length via an interactive menu."""
    choice = questionary.select(
        "How long should the ad copy be?",
        choices=[
            questionary.Choice("Short  — 1–2 sentences, ultra-concise", value="Short"),
            questionary.Choice("Medium — 3–4 sentences, balanced", value="Medium"),
            questionary.Choice("Long   — 6–10 sentences, full storytelling", value="Long"),
        ],
    ).ask()

    if choice is None:
        console.print("[yellow]Cancelled.[/yellow]")
        sys.exit(0)

    return choice


def load_image(path: str) -> tuple[str, str]:
    """Load an image from disk and return (base64_data, media_type)."""
    p = Path(path)
    if not p.exists():
        console.print(f"[red]Error: File not found — {path}[/red]")
        sys.exit(1)

    ext = p.suffix.lower()
    if ext not in SUPPORTED_FORMATS:
        console.print(
            f"[red]Unsupported format '{ext}'. Supported: {', '.join(SUPPORTED_FORMATS)}[/red]"
        )
        sys.exit(1)

    media_type = SUPPORTED_FORMATS[ext]
    with open(p, "rb") as f:
        data = base64.standard_b64encode(f.read()).decode("utf-8")

    return data, media_type


def generate_ad_copy(
    image_path: str,
    copy_length: str,
    platform: str = "Instagram/Facebook",
    extra_context: str = "",
) -> str:
    """Send the image to Claude and return the generated ad copy."""
    client = anthropic.Anthropic()

    image_data, media_type = load_image(image_path)
    length_instruction = COPY_LENGTH_INSTRUCTIONS[copy_length]

    user_content = [
        {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": media_type,
                "data": image_data,
            },
        },
        {
            "type": "text",
            "text": (
                f"Write ad copy for this image.\n"
                f"Target platform: {platform}.\n"
                f"Copy length instruction: {length_instruction}"
                + (f"\n\nAdditional context: {extra_context}" if extra_context else "")
            ),
        },
    ]

    import time, random
    max_retries = 5
    for attempt in range(max_retries):
        try:
            with console.status("[bold cyan]Analyzing image and generating ad copy...[/bold cyan]"):
                response = client.messages.create(
                    model="claude-sonnet-4-6",
                    max_tokens=2048,
                    system=SYSTEM_PROMPT,
                    messages=[{"role": "user", "content": user_content}],
                )
            return response.content[0].text
        except anthropic.APIStatusError as e:
            if e.status_code in (529, 500) and attempt < max_retries - 1:
                wait = min(2 ** attempt + random.uniform(0, 1), 30)
                console.print(f"[yellow]API overloaded — retrying in {wait:.1f}s (attempt {attempt + 1}/{max_retries})...[/yellow]")
                time.sleep(wait)
            else:
                raise


def display_output(image_path: str, platform: str, copy_length: str, copy_text: str):
    """Print the results with rich formatting."""
    console.print()
    console.print(Rule("[bold cyan]Ad Copy Agent[/bold cyan]"))
    console.print(
        Panel(
            f"[dim]Image:[/dim]    {image_path}\n"
            f"[dim]Platform:[/dim] {platform}\n"
            f"[dim]Length:[/dim]   {copy_length}",
            expand=False,
        )
    )
    console.print()
    console.print(Panel(copy_text, title="[bold green]Generated Ad Copy[/bold green]", padding=(1, 2)))
    console.print()


def main():
    parser = argparse.ArgumentParser(
        description="Generate ad headlines and copy from an image using Claude."
    )
    parser.add_argument("image", help="Path to the ad image file")
    parser.add_argument(
        "--platform",
        default="Instagram/Facebook",
        help="Target ad platform (default: Instagram/Facebook)",
    )
    parser.add_argument(
        "--context",
        default="",
        help="Optional extra context (e.g. product name, offer, target audience)",
    )
    args = parser.parse_args()

    if not os.getenv("ANTHROPIC_API_KEY"):
        console.print("[red]Error: ANTHROPIC_API_KEY not set in environment or .env file[/red]")
        sys.exit(1)

    copy_length = ask_copy_length()

    copy_text = generate_ad_copy(
        image_path=args.image,
        copy_length=copy_length,
        platform=args.platform,
        extra_context=args.context,
    )
    display_output(args.image, args.platform, copy_length, copy_text)


if __name__ == "__main__":
    main()
