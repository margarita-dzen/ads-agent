"""
Competitor Ads Library Agent
Fetches ads from Meta Ads Library for tracked brands.
"""

import os
import json
import requests
from datetime import datetime
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from config import BRANDS, FILTERS, FIELDS, META_API_BASE, PAGE_LIMIT

load_dotenv()
console = Console()


class MetaAdsAgent:
    def __init__(self):
        self.token = os.getenv("META_ACCESS_TOKEN")
        if not self.token:
            raise ValueError(
                "META_ACCESS_TOKEN not set.\n"
                "1. Go to https://developers.facebook.com/tools/explorer/\n"
                "2. Select your app (or create one)\n"
                "3. Add permission: ads_read\n"
                "4. Generate token and paste it into your .env file"
            )

    def fetch_ads_for_brand(self, brand_name: str, limit: int = PAGE_LIMIT) -> list[dict]:
        """Fetch all ads for a single brand from Meta Ads Library."""
        params = {
            "search_terms": brand_name,
            "fields": ",".join(FIELDS),
            "limit": limit,
            "access_token": self.token,
            **{k: v if not isinstance(v, list) else ",".join(v)
               for k, v in FILTERS.items()},
        }

        ads = []
        url = META_API_BASE
        page = 1

        while url:
            console.print(f"  [dim]Fetching page {page} for '{brand_name}'...[/dim]")
            response = requests.get(url, params=params if page == 1 else None)
            data = response.json()

            if "error" in data:
                console.print(f"[red]API Error: {data['error']['message']}[/red]")
                break

            batch = data.get("data", [])
            ads.extend(batch)

            # Follow pagination
            paging = data.get("paging", {})
            url = paging.get("next")
            params = None  # next URL already has params embedded
            page += 1

            # Safety: stop after 5 pages (250 ads) per brand by default
            if page > 5:
                break

        return ads

    def run(self, brands: list[str] = None) -> dict:
        """Run the agent for all tracked brands. Returns structured report data."""
        brands = brands or BRANDS
        report = {
            "generated_at": datetime.utcnow().isoformat(),
            "brands": {}
        }

        console.print(Panel(
            f"[bold cyan]Meta Ads Library Agent[/bold cyan]\n"
            f"Tracking {len(brands)} brand(s): {', '.join(brands)}",
            expand=False
        ))

        for brand in brands:
            console.print(f"\n[bold yellow]→ {brand}[/bold yellow]")
            ads = self.fetch_ads_for_brand(brand)
            report["brands"][brand] = {
                "total_ads": len(ads),
                "ads": ads
            }
            console.print(f"  [green]✓ Found {len(ads)} ads[/green]")

        self._print_summary(report)
        return report

    def _print_summary(self, report: dict):
        """Print a summary table to the console."""
        table = Table(title="\nAds Report Summary", show_lines=True)
        table.add_column("Brand", style="cyan")
        table.add_column("Total Ads", justify="right", style="green")
        table.add_column("Platforms", style="dim")

        for brand, data in report["brands"].items():
            platforms = set()
            for ad in data["ads"]:
                for p in ad.get("publisher_platforms", []):
                    platforms.add(p)
            table.add_row(
                brand,
                str(data["total_ads"]),
                ", ".join(sorted(platforms)) or "—"
            )

        console.print(table)

    def save_report(self, report: dict, path: str = "report.json"):
        """Save report as JSON file."""
        with open(path, "w") as f:
            json.dump(report, f, indent=2, default=str)
        console.print(f"\n[bold green]Report saved to {path}[/bold green]")


if __name__ == "__main__":
    agent = MetaAdsAgent()
    report = agent.run()
    agent.save_report(report)
