import logging
import os
from pathlib import Path

from requests import Session
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from openai import OpenAI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_env_from_file(path: str = ".env"):
    """Lightweight .env loader to avoid extra dependencies."""
    env_path = Path(path)
    if not env_path.is_file():
        return
    for line in env_path.read_text().splitlines():
        if not line or line.strip().startswith("#") or "=" not in line:
            continue
        key, val = line.split("=", 1)
        key = key.strip()
        val = val.strip()
        if key and key not in os.environ:
            os.environ[key] = val


load_env_from_file()

# Timing and model defaults
REQUEST_TIMEOUT = float(os.getenv("REQUEST_TIMEOUT", 10))
PRIMARY_MODEL = "gpt-4o-mini"
FALLBACK_MODEL = "gpt-3.5-turbo"

# RAWG API key: env wins; fallback to the original value if missing.
RAWG_API_KEY = os.getenv("RAWG_API_KEY", "7c11c6b61443433ba941a9c037147be8")


def build_http_session() -> Session:
    """HTTP session with retries/backoff for outbound calls."""
    retry_strategy = Retry(
        total=3,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET",),
        backoff_factor=0.5,
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session = Session()
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def build_openai_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")
    return OpenAI(api_key=api_key)
