from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from functools import wraps
import requests
import argparse
import time

from rich.console import Console
from rich.table import Table
from rich.progress import track
from rich.text import Text

from .constants import (
    DEFAULT_MODE,
    DEFAULT_NUM_STORIES,
    DEFAULT_MAX_WORKERS,
    DEFAULT_START,
    FETCH_ITEM_TEMPLATE,
    FETCH_STORIES_TEMPLATE,
    MODE_LIMITS,
)


def rate_limit(calls_per_sec):
    """A decorator to limit function calls to a specified rate per second."""
    interval = 1.0 / calls_per_sec

    def decorator(func):
        lock = Lock()
        last_time = 0.0

        @wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal last_time
            with lock:
                now = time.monotonic()
                elapsed = now - last_time
                wait = interval - elapsed
                if wait > 0:
                    time.sleep(wait)
                last_time = time.monotonic()
            result = func(*args, **kwargs)
            return result

        return wrapper

    return decorator


def get_stories(
    mode=DEFAULT_MODE,
    n=DEFAULT_NUM_STORIES,
    max_workers=DEFAULT_MAX_WORKERS,
    start=DEFAULT_START,
):
    @rate_limit(15)
    def get_story_by_id(id):
        fetch_story_url = FETCH_ITEM_TEMPLATE.format(id)
        return requests.get(fetch_story_url, timeout=10).json()

    # TODO: add a way to show/summarize comments
    table = Table(
        show_header=True,
        header_style="bold magenta",
        show_lines=True,
        collapse_padding=True,
    )
    table.add_column("No.", justify="right")
    table.add_column("Title", justify="left")
    table.add_column("URL", justify="left")
    table.add_column("Score", justify="left")

    fetch_ids_url = FETCH_STORIES_TEMPLATE.format(mode)
    ids = requests.get(fetch_ids_url, timeout=10).json()[(start - 1) : (start - 1 + n)]

    total_posts = len(ids)
    id_to_index = {id: i for i, id in enumerate(ids, start)}
    max_workers = max(max_workers, n)
    id_to_post = {}

    with ThreadPoolExecutor(max_workers=max_workers) as exe:
        future_to_id = {exe.submit(get_story_by_id, id): id for id in ids}
        for future in track(
            as_completed(future_to_id), description="Fetching...", total=total_posts
        ):
            id = future_to_id[future]
            index = id_to_index[id]
            try:
                story = future.result()
            except Exception:
                # TODO: case on the exception type/message, most likely it is rate limit
                id_to_post[id] = (str(index), "<RATE LIMITED>", "😭", "❌")
            else:
                title = story.get("title") or "<no title>"
                url = story.get("url") or f"https://news.ycombinator.com/item?id={id}"
                score = str(story.get("score")) or "🙈"

                styled_title = Text(title)
                styled_title.stylize("bold yellow")

                styled_url = Text(url)
                styled_url.stylize("blue underline")

                styled_score = Text(score)
                styled_score.stylize("bold green")

                id_to_post[id] = (str(index), styled_title, styled_url, styled_score)

    for id in ids:
        table.add_row(*id_to_post[id])

    console = Console()
    console.print(table)


def main():
    parser = argparse.ArgumentParser(
        prog="hnd", description="Display top Hacker News stories in the terminal."
    )
    parser.add_argument(
        "-m",
        "--mode",
        type=str,
        default=DEFAULT_MODE,
        choices=list(MODE_LIMITS.keys()),
        help=f"Story mode to display (default: {DEFAULT_MODE}, must be one of: {', '.join(MODE_LIMITS.keys())})",
    )
    parser.add_argument(
        "-s",
        "--start",
        type=int,
        default=DEFAULT_START,
        help=f"Start from this rank article (1-based index, default: {DEFAULT_START})",
    )
    parser.add_argument(
        "-n",
        "--num",
        type=int,
        default=DEFAULT_NUM_STORIES,
        help=f"Number of articles to display (default: {DEFAULT_NUM_STORIES})",
    )
    args = parser.parse_args()

    if args.start < 1:
        parser.error("--start/-s must be at least 1.")
    if args.num < 1:
        parser.error("--num/-n must be at least 1.")

    num_posts = args.start + args.num - 1
    if num_posts > MODE_LIMITS[args.mode]:
        parser.error(
            f"The sum of start and num minus 1 (index of furthest post) must not exceed {MODE_LIMITS[args.mode]}, the Hacker News API limit."
        )

    max_workers = max(num_posts, 10)
    get_stories(mode=args.mode, n=args.num, start=args.start, max_workers=max_workers)


if __name__ == "__main__":
    main()
