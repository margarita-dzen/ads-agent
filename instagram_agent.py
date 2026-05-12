"""
Instagram Reels Agent
Logs into Instagram, scrapes competitor reels, scores them by quality metrics,
and follows up to 20 relevant accounts.

Metrics scored (highest to lowest priority):
  1. Play-through rate (views / followers)
  2. Engagement rate ((likes + comments) / followers)
  3. Save proxy score (likes / views ratio)
  4. Comment rate (comments / followers)
  5. Follower count
"""

import os
import json
import time
import instaloader
from datetime import datetime
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

load_dotenv()
console = Console()

# -------------------------------------------------------------------
# Brand handles
# -------------------------------------------------------------------
BRAND_HANDLES = [
    "ryzesuperfoods",
    "im8health",
    "wildmintcosmetics",
    "svensisland",
    "norse.organics",
    "dremmycare",
    "froyaorganics",
    "bestdentaladvice",     # will skip gracefully if not found
    "cocoandeve",
    "lalueur.official",
    "feroldi_store",
    "shopmarkt",
]

MAX_FOLLOWS   = 20
MAX_REELS     = 30   # max reels to pull per account


# -------------------------------------------------------------------
# Scoring
# -------------------------------------------------------------------
def score_reel(reel: dict) -> float:
    followers   = max(reel.get("followers", 1), 1)
    views       = reel.get("views", 0)
    likes       = reel.get("likes", 0)
    comments    = reel.get("comments", 0)

    playthrough = views / followers                          # weight 0.40
    engagement  = (likes + comments) / followers            # weight 0.30
    save_proxy  = (likes / max(views, 1))                   # weight 0.20
    comment_rate= comments / followers                       # weight 0.10

    return (
        playthrough  * 0.40 +
        engagement   * 0.30 +
        save_proxy   * 0.20 +
        comment_rate * 0.10
    )


# -------------------------------------------------------------------
# Main agent
# -------------------------------------------------------------------
def run_agent():
    username = os.getenv("INSTAGRAM_USERNAME")
    password = os.getenv("INSTAGRAM_PASSWORD")

    if not username or not password:
        console.print("[red]INSTAGRAM_USERNAME / INSTAGRAM_PASSWORD not set in .env[/red]")
        return

    L = instaloader.Instaloader(
        download_videos=False,
        download_video_thumbnails=False,
        download_geotags=False,
        download_comments=False,
        save_metadata=False,
        quiet=True,
    )

    # --- Login ---
    console.print(Panel(
        f"[bold cyan]Instagram Reels Agent[/bold cyan]\n"
        f"Logging in as [yellow]{username}[/yellow]",
        expand=False
    ))
    try:
        L.login(username, password)
        console.print("[green]✓ Logged in successfully[/green]")
    except Exception as e:
        console.print(f"[red]Login failed: {e}[/red]")
        return

    report = {
        "generated_at": datetime.utcnow().isoformat(),
        "followed": [],
        "brands": {}
    }

    followed_count = 0

    for handle in BRAND_HANDLES:
        console.print(f"\n[bold yellow]→ @{handle}[/bold yellow]")

        # --- Load profile ---
        try:
            profile = instaloader.Profile.from_username(L.context, handle)
        except instaloader.exceptions.ProfileNotExistsException:
            console.print(f"  [red]Profile not found, skipping[/red]")
            continue
        except Exception as e:
            console.print(f"  [red]Error loading profile: {e}[/red]")
            continue

        followers = profile.followers
        console.print(f"  Followers: {followers:,}")

        # --- Follow (up to MAX_FOLLOWS) ---
        if followed_count < MAX_FOLLOWS and not profile.followed_by_viewer:
            try:
                profile.follow()
                followed_count += 1
                report["followed"].append(handle)
                console.print(f"  [green]✓ Followed ({followed_count}/{MAX_FOLLOWS})[/green]")
                time.sleep(3)  # avoid rate limiting
            except Exception as e:
                console.print(f"  [yellow]Could not follow: {e}[/yellow]")

        # --- Scrape Reels ---
        reels = []
        try:
            posts = profile.get_posts()
            count = 0
            for post in posts:
                if count >= MAX_REELS:
                    break
                # Only video posts (reels)
                if not post.is_video:
                    continue
                reels.append({
                    "shortcode":   post.shortcode,
                    "url":         f"https://www.instagram.com/reel/{post.shortcode}/",
                    "date":        post.date_utc.isoformat(),
                    "caption":     (post.caption or "")[:200],
                    "likes":       post.likes,
                    "comments":    post.comments,
                    "views":       post.video_view_count or 0,
                    "followers":   followers,
                    "hashtags":    list(post.caption_hashtags),
                })
                count += 1
                time.sleep(1)
        except Exception as e:
            console.print(f"  [yellow]Error fetching reels: {e}[/yellow]")

        # --- Score and rank ---
        for r in reels:
            r["score"] = round(score_reel(r), 4)

        ranked = sorted(reels, key=lambda x: x["score"], reverse=True)

        report["brands"][handle] = {
            "followers":  followers,
            "total_reels_scraped": len(ranked),
            "top_reels":  ranked[:10],   # top 10 by score
            "all_reels":  ranked,
        }

        console.print(f"  [green]✓ Scraped {len(ranked)} reels[/green]")
        if ranked:
            top = ranked[0]
            console.print(
                f"  [cyan]Top reel:[/cyan] {top['views']:,} views, "
                f"{top['likes']:,} likes, score={top['score']}"
            )

        time.sleep(2)

    # --- Summary table ---
    table = Table(title="\nReels Report Summary", show_lines=True)
    table.add_column("Account",         style="cyan")
    table.add_column("Followers",       justify="right")
    table.add_column("Reels Scraped",   justify="right", style="green")
    table.add_column("Top Views",       justify="right", style="yellow")
    table.add_column("Top Score",       justify="right", style="magenta")

    for handle, data in report["brands"].items():
        top_views = str(data["top_reels"][0]["views"]) if data["top_reels"] else "—"
        top_score = str(data["top_reels"][0]["score"]) if data["top_reels"] else "—"
        table.add_row(
            f"@{handle}",
            f"{data['followers']:,}",
            str(data["total_reels_scraped"]),
            top_views,
            top_score,
        )

    console.print(table)
    console.print(f"\n[dim]Followed {followed_count} accounts: {', '.join('@'+h for h in report['followed'])}[/dim]")

    with open("instagram_report.json", "w") as f:
        json.dump(report, f, indent=2, default=str)
    console.print("[bold green]Report saved to instagram_report.json[/bold green]")

    return report


if __name__ == "__main__":
    run_agent()
