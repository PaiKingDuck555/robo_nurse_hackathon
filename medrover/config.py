import os

SMALLEST_API_KEY    = os.environ.get("SMALLEST_API_KEY", "your_smallest_key")
CLAUDE_API_KEY      = os.environ.get("CLAUDE_API_KEY", "your_claude_key")
SCRAPEGRAPH_API_KEY = os.environ.get("SCRAPEGRAPH_API_KEY", "your_scrapegraph_key")
MONGODB_URI         = os.environ.get("MONGODB_URI", "mongodb://localhost:27017/medrover")
