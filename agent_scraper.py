"""
Competitor Ads Library Agent - Scraper Version
Scrapes Meta Ads Library public site. No API token required.
"""

import asyncio
import json
from datetime import datetime
from urllib.parse import quote
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from config import BRANDS

console = Console()
BASE_URL = "https://www.facebook.com/ads/library/"


async def dismiss_popups(page):
    for selector in [
        'button[title="Allow all cookies"]',
        'button:has-text("Allow all cookies")',
        'button:has-text("Accept all")',
        'button:has-text("Only allow essential cookies")',
        '[data-cookiebanner="accept_button"]',
    ]:
        try:
            await page.click(selector, timeout=2000)
            await asyncio.sleep(1)
            return
        except Exception:
            pass


def parse_ads_from_text(text: str, brand_name: str) -> list[dict]:
    """Parse ad data from page text using pattern matching."""
    import re
    ads = []

    # Split by Library ID which marks each new ad
    blocks = re.split(r'Library ID:\s*(\d+)', text)

    i = 1
    while i < len(blocks) - 1:
        library_id = blocks[i].strip()
        content = blocks[i + 1]

        # Status
        status = "Active" if "Active" in content[:100] else "Inactive"

        # Start date
        start_match = re.search(r'Started running on\s+([\w]+ \d+, \d+)', content)
        start_date = start_match.group(1) if start_match else ""

        # Date range for inactive
        range_match = re.search(r'(\w+ \d+, \d+)\s*-\s*(\w+ \d+, \d+)', content)
        end_date = range_match.group(2) if range_match and not start_date else ""
        if range_match and not start_date:
            start_date = range_match.group(1)

        # Advertiser name - look for brand after "Sponsored"
        adv_match = re.search(r'([\w\s\'.&-]+)\nSponsored', content)
        advertiser = adv_match.group(1).strip() if adv_match else brand_name

        # Ad body - text after "Sponsored" before next section
        body_match = re.search(r'Sponsored\n(.+?)(?=\n0:|\nSHOP\.|$)', content, re.DOTALL)
        body = ""
        if body_match:
            body = body_match.group(1).strip()[:500]

        # Platforms
        platforms = []
        if 'facebook' in content.lower(): platforms.append('Facebook')
        if 'instagram' in content.lower(): platforms.append('Instagram')
        if 'messenger' in content.lower(): platforms.append('Messenger')

        # Ads using this creative
        count_match = re.search(r'(\d+) ads use this creative', content)
        creative_count = int(count_match.group(1)) if count_match else 1

        ads.append({
            "library_id": library_id,
            "status": status,
            "advertiser": advertiser,
            "start_date": start_date,
            "end_date": end_date,
            "body": body,
            "platforms": platforms,
            "creative_variations": creative_count,
        })
        i += 2

    return ads


async def scrape_brand_ads(page, brand_name: str, max_scrolls: int = 3) -> list[dict]:
    url = (
        f"{BASE_URL}?active_status=all&ad_type=all"
        f"&country=US&q={quote(brand_name)}"
        f"&search_type=keyword_unordered&media_type=all"
    )

    console.print(f"  [dim]Loading ads library...[/dim]")
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(2)
    except PlaywrightTimeout:
        console.print(f"  [red]Page load timed out[/red]")
        return []

    await dismiss_popups(page)

    # Scroll to load more ads
    for i in range(max_scrolls):
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(1)

    # Get full page text
    text = await page.evaluate("document.body.innerText")

    ads = parse_ads_from_text(text, brand_name)
    return ads


async def run_agent(brands=None):
    brands = brands or BRANDS
    report = {
        "generated_at": datetime.utcnow().isoformat(),
        "brands": {}
    }

    console.print(Panel(
        f"[bold cyan]Meta Ads Library Agent (Scraper)[/bold cyan]\n"
        f"Tracking {len(brands)} brand(s): {', '.join(brands)}",
        expand=False
    ))

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"]
        )
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 900},
            locale="en-US",
        )
        page = await context.new_page()

        for brand in brands:
            console.print(f"\n[bold yellow]→ {brand}[/bold yellow]")
            ads = []
            for attempt in range(3):
                try:
                    ads = await scrape_brand_ads(page, brand)
                    break
                except Exception as e:
                    console.print(f"  [yellow]Attempt {attempt+1} failed: {e}. Retrying...[/yellow]")
                    await asyncio.sleep(5)
            report["brands"][brand] = {
                "total_ads": len(ads),
                "ads": ads
            }
            console.print(f"  [green]✓ Found {len(ads)} ads[/green]")
            await asyncio.sleep(1)

        await browser.close()

    # Summary table
    table = Table(title="\nAds Report Summary", show_lines=True)
    table.add_column("Brand", style="cyan")
    table.add_column("Total Ads", justify="right", style="green")
    table.add_column("Sample Ad", style="dim")

    for brand, data in report["brands"].items():
        sample = ""
        if data["ads"]:
            sample = data["ads"][0].get("body", "")[:60]
        table.add_row(brand, str(data["total_ads"]), sample or "—")

    console.print(table)

    with open("report.json", "w") as f:
        json.dump(report, f, indent=2, default=str)
    console.print(f"\n[bold green]Report saved to report.json[/bold green]")

    return report


if __name__ == "__main__":
    asyncio.run(run_agent())
