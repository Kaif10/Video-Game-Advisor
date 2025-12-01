from typing import List, Tuple

from config import PRIMARY_MODEL, FALLBACK_MODEL, build_openai_client, logger

client = build_openai_client()


def get_game_recommendations(query: str) -> Tuple[List[str], str | None]:
    """Generate game recommendations using OpenAI with primary + fallback models."""
    prompt = (
        f"Recommend 5 videogame names that match the following description in terms of gameplay and genre, and make sure to recommend those specific games. "
        f"If the input appears to be a videogame title, recommend that game along with related games: '{query}'. "
        "Return only the game names separated by commas."
    )

    errors = []

    def _generate(model_name: str):
        return client.chat.completions.create(
            model=model_name,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a precise videogame recommender. Return only real, existing game titles "
                        "that best match the described story, genre, and tone. "
                        "Output exactly a comma-separated list of titles and nothing else."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,  # a bit more variety while staying grounded
            max_tokens=256,  # more room for robust results
            timeout=15,
        )

    for model in (PRIMARY_MODEL, FALLBACK_MODEL):
        try:
            response = _generate(model)
            answer = response.choices[0].message.content.strip()
            game_names = [name.strip() for name in answer.split(",") if name.strip()]
            if game_names:
                return game_names, None
            errors.append(f"{model}: empty response")
        except Exception as exc:
            errors.append(f"{model}: {exc}")
            logger.exception("Error calling OpenAI API with model '%s' for query '%s'", model, query)

    logger.error("All OpenAI attempts failed: %s", "; ".join(errors))
    return [], "We hit a snag generating recommendations. Please try again in a moment."
