"""Typed contracts between the LLM, the RAWG API and the web layer."""
import re
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

MAX_CANDIDATES = 8
MAX_TITLE_LENGTH = 120
LIST_MARKER = re.compile(r"^(?:\d{1,2}[.)]|[-*•])\s+")


# --- LLM output -------------------------------------------------------------
# These models double as the JSON schema sent to OpenAI (strict mode), so keep
# validation that OpenAI's strict schema can't express in validators, not Field().

class GameCandidate(BaseModel):
    title: str = Field(description="Exact official title of a real, released videogame.")
    release_year: Optional[int] = Field(description="Year of original release, or null if unsure.")

    @field_validator("title")
    @classmethod
    def clean_title(cls, v: str) -> str:
        # Strip list markers / quotes the model sometimes adds: "1. Hades", "- \"Celeste\""
        # (but keep titles like "7 Days to Die" or "2064: Read Only Memories" intact)
        v = LIST_MARKER.sub("", v.strip()).strip().strip("\"'").strip()
        if not v or len(v) > MAX_TITLE_LENGTH:
            raise ValueError("title must be 1-%d characters" % MAX_TITLE_LENGTH)
        return v

    @field_validator("release_year")
    @classmethod
    def plausible_year(cls, v: Optional[int]) -> Optional[int]:
        return v if v is not None and 1970 <= v <= 2100 else None


class RecommendationResponse(BaseModel):
    status: Literal["ok", "no_match"] = Field(
        description="'no_match' if the request is not a meaningful game description."
    )
    games: List[GameCandidate] = Field(description="Ranked best match first.")

    @field_validator("games", mode="before")
    @classmethod
    def drop_invalid_and_cap(cls, games):
        """Keep valid, unique candidates (case-insensitive), capped at MAX_CANDIDATES.

        Invalid items are dropped instead of failing the whole response.
        """
        kept, seen = [], set()
        for raw in games or []:
            try:
                game = GameCandidate.model_validate(raw)
            except ValueError:
                continue
            key = game.title.casefold()
            if key not in seen:
                seen.add(key)
                kept.append(game)
            if len(kept) == MAX_CANDIDATES:
                break
        return kept


# --- RAWG -------------------------------------------------------------------

class RawgGame(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int
    name: str
    slug: Optional[str] = None
    released: Optional[str] = None
    rating: Optional[float] = None
    background_image: Optional[str] = None

    @property
    def release_year(self) -> Optional[int]:
        try:
            return int(self.released[:4]) if self.released else None
        except ValueError:
            return None


class RawgSearchResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    results: List[RawgGame] = []


# --- What the template renders ------------------------------------------------

class GameResult(BaseModel):
    name: str
    released: str
    rating: str
    website: str
    cover: Optional[str] = None

    @classmethod
    def from_rawg(cls, game: RawgGame) -> "GameResult":
        cover = game.background_image
        return cls(
            name=game.name,
            released=game.released or "Unknown",
            rating=str(game.rating) if game.rating else "N/A",
            website=f"https://rawg.io/games/{game.slug}" if game.slug else "N/A",
            cover=cover if cover and cover.startswith("https://") else None,
        )
