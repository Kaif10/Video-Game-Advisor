import logging
import re
import threading
import unicodedata
from difflib import SequenceMatcher
from typing import Optional

import requests
from pydantic import ValidationError

from config import RAWG_API_KEY, REQUEST_TIMEOUT, http_session
from services.schemas import GameCandidate, GameResult, RawgGame, RawgSearchResponse

logger = logging.getLogger(__name__)

SEARCH_URL = "https://api.rawg.io/api/games"
MAX_RAWG_CALLS_PER_REQUEST = 15
ATTEMPTS_PER_SEARCH = 2
SEARCH_PAGE_SIZE = 5
MIN_MATCH_SCORE = 0.8
RETRYABLE_STATUS = {429, 500, 502, 503, 504}


class RawgBudget:
    """Thread-safe cap on RAWG HTTP calls (retries included) for one user request."""

    def __init__(self, limit: int = MAX_RAWG_CALLS_PER_REQUEST):
        self.limit = limit
        self.used = 0
        self._lock = threading.Lock()

    def take(self) -> bool:
        with self._lock:
            if self.used >= self.limit:
                return False
            self.used += 1
            return True


def _normalize(title: str) -> str:
    title = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode()
    title = re.sub(r"[^a-z0-9 ]+", " ", title.casefold().replace("&", " and "))
    return " ".join(title.split())


def _match_score(candidate: GameCandidate, game: RawgGame) -> float:
    """0..1 confidence that a RAWG result is the game the LLM meant."""
    wanted, found = _normalize(candidate.title), _normalize(game.name)
    if not wanted or not found:
        return 0.0
    if wanted == found:
        score = 1.0
    elif found.startswith(wanted + " ") or wanted.startswith(found + " "):
        # "The Witcher 3" vs "The Witcher 3: Wild Hunt"
        score = 0.9
    else:
        score = SequenceMatcher(None, wanted, found).ratio()

    if candidate.release_year and game.release_year:
        if abs(candidate.release_year - game.release_year) <= 1:
            score = min(1.0, score + 0.05)
        else:
            # Same name, different game (e.g. a reboot) or a fuzzy false positive.
            score -= 0.15
    return score


def _search(title: str, budget: RawgBudget) -> Optional[RawgSearchResponse]:
    params = {"search": title, "key": RAWG_API_KEY, "page_size": SEARCH_PAGE_SIZE}
    for attempt in range(1, ATTEMPTS_PER_SEARCH + 1):
        if not budget.take():
            logger.warning("RAWG call budget exhausted; skipping %r", title)
            return None
        try:
            response = http_session.get(SEARCH_URL, params=params, timeout=REQUEST_TIMEOUT)
        except requests.RequestException as exc:
            logger.warning("RAWG request failed for %r (attempt %d): %s", title, attempt, exc)
            continue
        if response.status_code in RETRYABLE_STATUS:
            logger.warning("RAWG returned %d for %r (attempt %d)", response.status_code, title, attempt)
            continue
        if response.status_code != 200:
            logger.error("RAWG returned %d for %r", response.status_code, title)
            return None
        try:
            return RawgSearchResponse.model_validate(response.json())
        except (ValueError, ValidationError) as exc:
            logger.warning("RAWG returned an unexpected payload for %r: %s", title, exc)
            return None
    return None


def find_game(candidate: GameCandidate, budget: RawgBudget) -> Optional[GameResult]:
    """Look up an LLM candidate on RAWG. Returns None unless a confident match is found."""
    data = _search(candidate.title, budget)
    if not data or not data.results:
        return None
    best = max(data.results, key=lambda game: _match_score(candidate, game))
    score = _match_score(candidate, best)
    if score < MIN_MATCH_SCORE:
        logger.info("No confident RAWG match for %r (best %r, score %.2f)", candidate.title, best.name, score)
        return None
    return GameResult.from_rawg(best)
