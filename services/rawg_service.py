from config import RAWG_API_KEY, REQUEST_TIMEOUT, build_http_session, logger

http_session = build_http_session()


def fetch_game_metadata(game_name: str):
    """
    Uses the RAWG API to fetch metadata for a given videogame title,
    including the cover image.
    """
    url = "https://api.rawg.io/api/games"
    params = {
        "search": game_name,
        "key": RAWG_API_KEY,
        "page_size": 1,
    }
    try:
        response = http_session.get(url, params=params, timeout=REQUEST_TIMEOUT)
        data = response.json()
        if data.get("results"):
            game = data["results"][0]
            game_slug = game.get("slug")
            game_url = f"https://rawg.io/games/{game_slug}" if game_slug else "N/A"
            return {
                "name": game.get("name"),
                "released": game.get("released") or "Unknown",
                "rating": game.get("rating") or "N/A",
                "website": game_url,
                "cover": game.get("background_image"),
            }
    except Exception:
        logger.exception("Error calling RAWG API for '%s'", game_name)
    # Fallback if no data is found.
    return {"name": game_name, "released": "N/A", "rating": "N/A", "website": "N/A", "cover": None}
