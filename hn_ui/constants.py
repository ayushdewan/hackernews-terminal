# Default values for function arguments and CLI arguments
DEFAULT_MODE = "top"
DEFAULT_NUM_STORIES = 50
DEFAULT_MAX_WORKERS = 30
DEFAULT_START = 1
DEFAULT_RATE_LIMIT = 50  # req/s

# API URLs
BASE_API_URL = "https://hacker-news.firebaseio.com/v0"
FETCH_STORIES_TEMPLATE = f"{BASE_API_URL}/{{}}stories.json"
FETCH_ITEM_TEMPLATE = f"{BASE_API_URL}/item/{{}}.json"

# Mode limits for different story types
MODE_LIMITS = {
    "top": 500,
    "new": 500,
    "best": 500,
    "ask": 200,
    "show": 200,
    "job": 200,
}
