"""Pipeline: user query -> LLM candidates (validated) -> RAWG lookups (capped, verified) -> results."""
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional, Tuple

from services.openai_service import RecommendationError, get_game_candidates
from services.rawg_service import RawgBudget, find_game
from services.schemas import GameResult

logger = logging.getLogger(__name__)

MAX_RESULTS = 5
MAX_QUERY_LENGTH = 300
RAWG_CONCURRENCY = 5

NO_MATCH_MSG = "No games matched that description. Try adjusting keywords or genre."


def recommend(query: str) -> Tuple[List[dict], Optional[str]]:
    """Return (results as template-ready dicts, user-facing error message or None)."""
    query = " ".join(query.split())[:MAX_QUERY_LENGTH]
    if not query:
        return [], "Please describe the kind of game you're looking for."

    try:
        candidates = get_game_candidates(query)
    except RecommendationError as exc:
        return [], str(exc)
    if not candidates:
        return [], NO_MATCH_MSG

    # Look candidates up concurrently; budget caps total RAWG calls for this request.
    budget = RawgBudget()
    with ThreadPoolExecutor(max_workers=RAWG_CONCURRENCY) as pool:
        matches = list(pool.map(lambda c: find_game(c, budget), candidates))

    results: List[GameResult] = []
    seen = set()
    for match in matches:  # pool.map keeps the LLM's ranking order
        if match and match.website not in seen:
            seen.add(match.website)
            results.append(match)
        if len(results) == MAX_RESULTS:
            break

    logger.info(
        "query=%r candidates=%d verified=%d rawg_calls=%d",
        query, len(candidates), len(results), budget.used,
    )
    if not results:
        return [], NO_MATCH_MSG
    return [r.model_dump() for r in results], None
