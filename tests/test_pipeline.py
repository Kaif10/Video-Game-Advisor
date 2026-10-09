"""Pipeline tests with OpenAI and RAWG mocked out. Run: pytest -q"""
import os
import sys
from types import SimpleNamespace
from unittest import mock

import openai
import pytest
import requests

os.environ.setdefault("OPENAI_API_KEY", "sk-test")
os.environ.setdefault("RAWG_API_KEY", "test")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import app as flask_app  # noqa: E402
from services import openai_service, rawg_service, recommender  # noqa: E402
from services.schemas import GameCandidate, MAX_CANDIDATES, RecommendationResponse  # noqa: E402


# --- helpers ------------------------------------------------------------------

def llm_returns(status="ok", games=(), refusal=None):
    parsed = None if refusal else RecommendationResponse.model_validate({"status": status, "games": list(games)})
    message = SimpleNamespace(parsed=parsed, refusal=refusal)
    return mock.patch.object(
        openai_service.openai_client.chat.completions, "parse",
        return_value=SimpleNamespace(choices=[SimpleNamespace(message=message)]),
    )


def llm_raises(exc_type):
    return mock.patch.object(
        openai_service.openai_client.chat.completions, "parse",
        side_effect=exc_type.__new__(exc_type),
    )


def rawg_response(status=200, payload=None, text=None):
    def json():
        if text is not None:
            raise ValueError("not json")
        return payload
    return SimpleNamespace(status_code=status, json=json)


def rawg_game(name, year=2020, id_=None):
    slug = name.lower().replace(" ", "-")
    return {"id": id_ or hash(name) % 10**6, "name": name, "slug": slug, "released": f"{year}-01-01",
            "rating": 4.5, "background_image": f"https://media.rawg.io/{slug}.jpg"}


def rawg_catalog(*games):
    """Fake RAWG search: returns catalog entries whose name contains the search term."""
    norm = rawg_service._normalize

    def get(url, params, timeout):
        term = norm(params["search"])
        return rawg_response(payload={"results": [g for g in games if term in norm(g["name"])]})
    return mock.patch.object(rawg_service.http_session, "get", side_effect=get)


def c(title, year=2020):
    return {"title": title, "release_year": year}


# --- LLM output validation ----------------------------------------------------

def test_schema_cleans_dedupes_and_caps():
    raw = [c("1. Hades"), c("- \"Celeste\""), c("hades"), c("   "), c("x" * 500),
           c("7 Days to Die"), c("2064: Read Only Memories")] + [c(f"Game {i}") for i in range(20)]
    games = RecommendationResponse.model_validate({"status": "ok", "games": raw}).games
    titles = [g.title for g in games]
    assert titles[:4] == ["Hades", "Celeste", "7 Days to Die", "2064: Read Only Memories"]
    assert len(games) == MAX_CANDIDATES


def test_implausible_year_becomes_none():
    assert GameCandidate(title="Hades", release_year=3).release_year is None


def test_title_with_comma_stays_whole():
    with llm_returns(games=[c("Warhammer 40,000: Space Marine 2", 2024)]), \
            rawg_catalog(rawg_game("Warhammer 40,000: Space Marine 2", 2024)):
        results, error = recommender.recommend("grimdark shooter")
    assert error is None and [r["name"] for r in results] == ["Warhammer 40,000: Space Marine 2"]


# --- LLM failures -------------------------------------------------------------

@pytest.mark.parametrize("ctx", [
    lambda: llm_returns(refusal="I'm sorry, I can't help with that."),
    lambda: llm_returns(status="no_match"),
    lambda: llm_returns(games=[]),
])
def test_no_match_paths(ctx):
    with ctx(), mock.patch.object(rawg_service.http_session, "get") as get:
        results, error = recommender.recommend("asdkjh qwe")
    assert results == [] and error == recommender.NO_MATCH_MSG
    get.assert_not_called()


@pytest.mark.parametrize("exc", [openai.RateLimitError, openai.APIConnectionError, openai.APITimeoutError,
                                 openai.LengthFinishReasonError, openai.InternalServerError])
def test_openai_errors_give_friendly_message(exc):
    with llm_raises(exc):
        results, error = recommender.recommend("roguelike")
    assert results == []
    assert any(hint in error for hint in ("snag", "rephras", "minute"))


def test_blank_query_skips_llm():
    with mock.patch.object(openai_service.openai_client.chat.completions, "parse") as parse:
        results, error = recommender.recommend("   ")
    assert results == [] and error
    parse.assert_not_called()


def test_long_query_truncated_before_llm():
    with llm_returns(status="no_match") as parse:
        recommender.recommend("a" * 5000)
    sent = parse.call_args.kwargs["messages"][1]["content"]
    assert len(sent) <= recommender.MAX_QUERY_LENGTH + len("<request></request>")


# --- RAWG layer ---------------------------------------------------------------

def test_rawg_budget_caps_calls_at_15():
    always_503 = mock.patch.object(rawg_service.http_session, "get", return_value=rawg_response(503))
    with llm_returns(games=[c(f"Game {i}") for i in range(MAX_CANDIDATES)]), always_503 as get:
        results, error = recommender.recommend("anything")
    assert get.call_count == rawg_service.MAX_RAWG_CALLS_PER_REQUEST
    assert results == [] and error == recommender.NO_MATCH_MSG


@pytest.mark.parametrize("failure", [
    rawg_response(502, text="<html>Bad Gateway</html>"),
    rawg_response(200, text="<html>oops</html>"),
    rawg_response(200, payload=["not", "an", "object"]),
    rawg_response(200, payload={"results": [{"no_id": True}]}),
    requests.Timeout("slow"),
    requests.ConnectionError("down"),
])
def test_rawg_failures_never_crash(failure):
    kwargs = {"side_effect": failure} if isinstance(failure, Exception) else {"return_value": failure}
    with llm_returns(games=[c("Hades")]), mock.patch.object(rawg_service.http_session, "get", **kwargs):
        results, error = recommender.recommend("roguelike")
    assert results == [] and error == recommender.NO_MATCH_MSG


def test_rawg_retries_transient_error_once():
    responses = [rawg_response(429), rawg_response(payload={"results": [rawg_game("Hades")]})]
    with llm_returns(games=[c("Hades")]), \
            mock.patch.object(rawg_service.http_session, "get", side_effect=responses) as get:
        results, _ = recommender.recommend("roguelike")
    assert get.call_count == 2 and results[0]["name"] == "Hades"


@pytest.mark.parametrize("candidate, rawg_hits", [
    (c("Hades", 2020), [rawg_game("Hades Star", 2016), rawg_game("Hades II", 2024)]),  # related, wrong game
    (c("Starfall Chronicles", 2019), [rawg_game("Star Wars Chronicles", 2001)]),       # hallucinated title
])
def test_wrong_rawg_match_is_rejected(candidate, rawg_hits):
    with mock.patch.object(rawg_service.http_session, "get",
                           return_value=rawg_response(payload={"results": rawg_hits})):
        assert rawg_service.find_game(GameCandidate(**candidate), rawg_service.RawgBudget()) is None


@pytest.mark.parametrize("candidate, hits, expected", [
    (c("Hades", 2020), [rawg_game("Hades Star", 2016), rawg_game("Hades", 2020), rawg_game("Hades II", 2024)],
     ("Hades", "2020")),
    # Same title, different games: the matching year wins...
    (c("Doom", 1993), [rawg_game("Doom", 2016, 1), rawg_game("Doom", 1993, 2)], ("Doom", "1993")),
    # ...but an LLM year slip alone doesn't throw away an exact title match.
    (c("Doom", 1993), [rawg_game("Doom", 2016)], ("Doom", "2016")),
])
def test_best_of_several_rawg_hits_is_picked(candidate, hits, expected):
    with mock.patch.object(rawg_service.http_session, "get",
                           return_value=rawg_response(payload={"results": hits})):
        match = rawg_service.find_game(GameCandidate(**candidate), rawg_service.RawgBudget())
    assert (match.name, match.released[:4]) == expected


def test_subtitle_and_case_differences_still_match():
    with llm_returns(games=[c("The Witcher 3", 2015), c("My Time at Portia", 2019)]), \
            rawg_catalog(rawg_game("The Witcher 3: Wild Hunt", 2015), rawg_game("My Time At Portia", 2019)):
        results, _ = recommender.recommend("rpg")
    assert [r["name"] for r in results] == ["The Witcher 3: Wild Hunt", "My Time At Portia"]


def test_results_capped_ordered_and_deduped():
    names = ["Hades", "Celeste", "Dead Cells", "Hollow Knight", "Transistor", "Bastion", "Ori"]
    games = [c(n) for n in names] + [c("Hades.")]  # punctuation variant of a duplicate
    with llm_returns(games=games), rawg_catalog(*[rawg_game(n) for n in names]):
        results, error = recommender.recommend("indie")
    assert error is None
    assert [r["name"] for r in results] == names[:recommender.MAX_RESULTS]


def test_non_https_cover_dropped():
    game = rawg_game("Hades") | {"background_image": "javascript:alert(1)"}
    with llm_returns(games=[c("Hades")]), rawg_catalog(game):
        results, _ = recommender.recommend("roguelike")
    assert results[0]["cover"] is None


# --- Flask end to end ---------------------------------------------------------

def test_flask_renders_results_and_errors():
    client = flask_app.app.test_client()
    with llm_returns(games=[c("Hades")]), rawg_catalog(rawg_game("Hades")):
        assert client.post("/", data={"query": "roguelike"}).status_code == 302
    assert "<h2>Hades</h2>" in client.get("/").get_data(as_text=True)

    with llm_raises(openai.APIConnectionError):
        assert client.post("/", data={"query": "roguelike"}).status_code == 302
    page = client.get("/")
    assert page.status_code == 200 and "snag" in page.get_data(as_text=True)
