import requests
import argparse
import time

from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

from rich.console import Console
from rich.table import Table
from rich.progress import track
from rich.text import Text

def rate_limit(calls_per_sec):
    """A decorator to limit function calls to a specified rate per second."""
    interval = 1.0 / calls_per_sec
    lock = Lock()
    last_time = [0.0]

    def decorator(func):
        def wrapper(*args, **kwargs):
            with lock:
                now = time.time()
                elapsed = now - last_time[0]
                wait = interval - elapsed
                if wait > 0:
                    time.sleep(wait)
                last_time[0] = time.time()
            result = func(*args, **kwargs)
            return result
        return wrapper
    return decorator

def get_stories(mode="top", n=50, max_workers=10, start=1):
    BASE = "https://hacker-news.firebaseio.com/v0"
    STORIES = f"{BASE}/{mode}stories.json"
    ITEM = f"{BASE}/item/{{}}.json"

    @rate_limit(10)
    def get_article_by_id(id):
        return requests.get(ITEM.format(id), timeout=10).json()

    table = Table(show_header=True, header_style="bold magenta", show_lines=True)
    table.add_column("No.", justify="right")
    table.add_column("Title", justify="left")
    table.add_column("URL", justify="left")

    ids = requests.get(STORIES, timeout=10).json()[(start - 1):(start - 1 + n)]
    
    total_posts = len(ids)
    id_to_index = { id : i for i, id in enumerate(ids, start) }
    max_workers = max(max_workers, n)
    id_to_post = {}

    with ThreadPoolExecutor(max_workers=max_workers) as exe:
        future_to_id = { exe.submit(get_article_by_id, id) : id for id in ids }
        for future in track(as_completed(future_to_id), description="Fetching...", total=total_posts):
            id = future_to_id[future]
            index = id_to_index[id]
            try:
                story = future.result()
            except Exception as exc:
                id_to_post[id] = (str(index), "<RATE LIMITED>", "😭")
            else:
                title = story.get("title") or "<no title>"
                url = story.get("url") or f"https://news.ycombinator.com/item?id={id}"

                styled_title = Text(title)
                styled_title.stylize("bold yellow")

                styled_url = Text(url)
                styled_url.stylize("blue underline")

                id_to_post[id] = (str(index), styled_title, styled_url)
    
    for id in ids:
        table.add_row(*id_to_post[id])

    console = Console()
    console.print(table)

def main():
    MODE_LIMITS = {
        "top": 500,
        "new": 500,
        "best": 500,
        "ask": 200,
        "show": 200,
        "job": 200,
    }
    
    parser = argparse.ArgumentParser(prog="hnd", description="Display top Hacker News stories in the terminal.")
    parser.add_argument(
        "-m", "--mode", type=str, default="top", choices=list(MODE_LIMITS.keys()),
        help=f"Story mode to display (default: top, must be one of: {', '.join(MODE_LIMITS.keys())})"
    )
    parser.add_argument(
        "-s", "--start", type=int, default=1,
        help="Start from this rank article (1-based index, default: 1)"
    )
    parser.add_argument(
        "-n", "--num", type=int, default=50,
        help="Number of articles to display (default: 50)"
    )
    args = parser.parse_args()

    if args.start < 1:
        parser.error("--start/-s must be at least 1.")
    if args.num < 1:
        parser.error("--num/-n must be at least 1.")
    if args.start + args.num - 1 > MODE_LIMITS[args.mode]:
        parser.error(f"The sum of start and num minus 1 (index of furthest post) must not exceed {MODE_LIMITS[args.mode]}, the Hacker News API limit.")

    get_stories(mode=args.mode, n=args.num, start=args.start)

if __name__ == "__main__":
    main()
