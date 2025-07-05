# HN UI

A terminal-based Hacker News reader that displays stories in a beautiful table format.

![Screenshot](screenshot.png)

## Features

- View top, new, best, ask, show, and job stories from Hacker News
- Customizable number of stories to display
- Start from any rank in the story list
- Rich terminal interface with colored output
- Rate-limited API calls to respect Hacker News API limits
- Concurrent fetching for improved performance

## Installation

```bash
pip install hn-ui
```

## Usage

```bash
# Show top 50 stories (default)
hnd

# Show top 10 stories
hnd -n 10

# Show new stories
hnd -m new

# Show stories starting from rank 20
hnd -s 20

# Show 5 ask stories starting from rank 10
hnd -m ask -s 10 -n 5
```

### Command Line Options

- `-m, --mode`: Story mode to display (choices: top, new, best, ask, show, job)
- `-s, --start`: Start from this rank article (1-based index, default: 1)
- `-n, --num`: Number of articles to display (default: 50)

## Story Modes

- **top**: Top stories (up to 500)
- **new**: New stories (up to 500)
- **best**: Best stories (up to 500)
- **ask**: Ask HN stories (up to 200)
- **show**: Show HN stories (up to 200)
- **job**: Job stories (up to 200)

## Requirements

- Python 3.12+
- requests
- rich

## Development

This project uses uv for dependency management. To set up for development:

```bash
uv sync
```
