import logging
import os
from pathlib import Path
from requests import Session
from openai import OpenAI

# Load .env file (overrides environment variables)
env_file = Path(".env")
if env_file.exists():
    for line in env_file.read_text(encoding='utf-8-sig').splitlines():
        if line and not line.startswith("#") and "=" in line:
            key, val = line.split("=", 1)
            os.environ[key.strip()] = val.strip().strip('"').strip("'")

# Get API keys from environment
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
RAWG_API_KEY = os.getenv("RAWG_API_KEY")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

MODEL = "gpt-4o-mini"
# (connect, read) seconds per RAWG call. Worst case per user request stays under
# gunicorn's 30s default: OpenAI 2 x 10s + RAWG 2 attempts x (3 + 5)s in parallel.
REQUEST_TIMEOUT = (3, 5)
OPENAI_TIMEOUT = 10
OPENAI_MAX_RETRIES = 1  # SDK retries connection errors, 408/409/429 and 5xx with backoff

http_session = Session()
openai_client = OpenAI(api_key=OPENAI_API_KEY, timeout=OPENAI_TIMEOUT, max_retries=OPENAI_MAX_RETRIES)
