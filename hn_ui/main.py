import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from rich.console import Console
from rich.progress import track
from rich.table import Table
from rich.text import Text

from .constants import (
    DEFAULT_MAX_WORKERS,
    DEFAULT_MODE,
    DEFAULT_NUM_STORIES,
    DEFAULT_RATE_LIMIT,
    DEFAULT_START,
    FETCH_ITEM_TEMPLATE,
    FETCH_STORIES_TEMPLATE,
    MODE_LIMITS,
)
from .helpers import throttle


def get_stories(
    mode=DEFAULT_MODE,
    n=DEFAULT_NUM_STORIES,
    max_workers=DEFAULT_MAX_WORKERS,
    start=DEFAULT_START,
    rate_limit=DEFAULT_RATE_LIMIT,
):
    @throttle(rate_limit)
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

    # Fetch IDs of top N posts, starting at start index
    fetch_ids_url = FETCH_STORIES_TEMPLATE.format(mode)
    ids = requests.get(fetch_ids_url, timeout=10).json()[
        (start - 1) : (start - 1 + n)
    ]

    total_posts = len(ids)
    id_to_index = {id: i for i, id in enumerate(ids, start)}
    id_to_post = {}

    with ThreadPoolExecutor(max_workers=max_workers) as exe:
        future_to_id = {exe.submit(get_story_by_id, id): id for id in ids}
        for future in track(
            as_completed(future_to_id),
            description="Fetching...",
            total=total_posts,
        ):
            id = future_to_id[future]
            index = id_to_index[id]
            try:
                story = future.result()
            except Exception:
                # TODO: resubmit tasks, most likely it is rate limit
                id_to_post[id] = (str(index), "<RATE LIMITED>", "😭", "❌")
            else:
                title = story.get("title") or "<no title>"
                url = (
                    story.get("url")
                    or f"https://news.ycombinator.com/item?id={id}"
                )
                score = str(story.get("score") or "🙈")

                styled_title = Text(title)
                styled_title.stylize("bold yellow")

                styled_url = Text(url)
                styled_url.stylize("blue underline")

                styled_score = Text(score)
                styled_score.stylize("bold green")

                id_to_post[id] = (
                    str(index),
                    styled_title,
                    styled_url,
                    styled_score,
                )

    for id in ids:
        table.add_row(*id_to_post[id])

    console = Console()
    console.print(table)


def main():
    parser = argparse.ArgumentParser(
        prog="hnd",
        description="Display top Hacker News stories in the terminal.",
    )
    parser.add_argument(
        "-m",
        "--mode",
        type=str,
        default=DEFAULT_MODE,
        choices=list(MODE_LIMITS.keys()),
        help=f"Story mode to display (default: {DEFAULT_MODE}, must be one of: {', '.join(MODE_LIMITS.keys())})",  # noqa: E501
    )
    parser.add_argument(
        "-s",
        "--start",
        type=int,
        default=DEFAULT_START,
        help=f"Start from this rank article (1-based index, default: {DEFAULT_START})",  # noqa: E501
    )
    parser.add_argument(
        "-n",
        "--num",
        type=int,
        default=DEFAULT_NUM_STORIES,
        help=f"Number of articles to display (default: {DEFAULT_NUM_STORIES})",
    )
    parser.add_argument(
        "-t",
        "--threads",
        type=int,
        default=DEFAULT_MAX_WORKERS,
        help=f"Number of worker threads for fetching stories (default: {DEFAULT_MAX_WORKERS})",  # noqa: E501
    )
    args = parser.parse_args()

    if args.start < 1:
        parser.error("--start/-s must be at least 1.")
    if args.num < 1:
        parser.error("--num/-n must be at least 1.")

    num_posts = args.start + args.num - 1
    if num_posts > MODE_LIMITS[args.mode]:
        parser.error(
            f"The sum of start and num minus 1 (index of furthest post) must not exceed {MODE_LIMITS[args.mode]}, the Hacker News API limit."  # noqa: E501
        )

    get_stories(
        mode=args.mode, n=args.num, start=args.start, max_workers=args.threads
    )


if __name__ == "__main__":
    main()
