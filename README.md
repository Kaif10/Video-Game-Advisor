# Video Game Advisor 🎮

Video Game Advisor is a small Flask web app that helps you discover videogames based on a natural‑language description of what you feel like playing.  
You type a short prompt (e.g. *“cozy farming sim with light combat and great characters”*), and the app:

- Uses the OpenAI API to generate a list of matching game titles.
- Looks up each title in the RAWG videogame database.
- Shows you a clean grid of games with cover art, release date, rating, and a link to a game detail page.

The UI is a single-page, retro‑styled experience backed by two service layers: one for OpenAI and one for RAWG.

---

## Tech Stack

- **Backend:** Python, Flask
- **AI:** OpenAI Chat Completions with Structured Outputs (`gpt-4o-mini`)
- **Validation:** Pydantic
- **Game data:** RAWG API
- **Server:** Gunicorn (via `Dockerfile` and `Procfile` for deployment)

---

## Project Structure

- `app.py` – Flask app, routes, session handling, security headers.
- `services/openai_service.py` – Calls OpenAI to turn your prompt into specific game titles.
- `services/rawg_service.py` – Verifies each candidate on RAWG (capped at 15 calls/request) and fetches cover art, rating, release date and canonical game URLs.
- `services/schemas.py` – Pydantic models validating LLM output and RAWG responses.
- `services/recommender.py` – Orchestrates the pipeline: query → candidates → verified results.
- `tests/` – Pipeline tests with OpenAI and RAWG mocked.
- `config.py` – Environment loading, HTTP session, OpenAI client, global config.
- `templates/index.html` – Main HTML template and UI.
- `static/` – Logos and other static assets.
- `requirements.txt` – Python dependencies.
- `Dockerfile` / `Procfile` – Container and process configuration for deployment.

---

## Prerequisites

- Python **3.10+** (3.12 is used in the `Dockerfile`)
- A valid **OpenAI API key**
- A **RAWG API key** (free tier available at RAWG)
- `git`

Optional:

- Docker, if you prefer to run the app in a container.

---

## Getting Started (Local)

### 1. Clone the repository

```bash
git clone https://github.com/Kaif10/Video-Game-Advisor.git
cd Video-Game-Advisor
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv
# Windows (PowerShell)
.venv\Scripts\Activate.ps1
# macOS / Linux
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Create your `.env` file

In the project root (same folder as `app.py`), create a file named `.env`.

You can start by copying `env.example` to `.env`, then fill in your keys.

```env
OPENAI_API_KEY=your-openai-api-key-here
RAWG_API_KEY=your-rawg-api-key-here
FLASK_SECRET_KEY=some-long-random-string
PORT=8080
```

Notes:

- `config.py` automatically loads `.env` at startup.
- The `OPENAI_API_KEY` **must** be set; the app will raise an error if it is missing.
- `RAWG_API_KEY` is optional; if you omit it, the app will still run but it will skip RAWG lookups (you’ll see `"N/A"` metadata).
- `.env` is listed in `.gitignore` and should **never** be committed.

### 5. Run the app

With the virtual environment active and `.env` configured:

```bash
python app.py
```

By default the app listens on `http://0.0.0.0:8080` (or the port from your `PORT` env var).  
Open your browser at:

```text
http://localhost:8080
```

---

## How It Works

```
query ─► OpenAI (strict JSON schema) ─► Pydantic validation ─► RAWG lookups (parallel, capped) ─► cards
```

1. **User input**  
   On `/`, you describe the kind of game you want. The query is whitespace-normalised and capped at 300 characters.

2. **AI game selection** – `services/openai_service.py`  
   `get_game_candidates()` calls `gpt-4o-mini` with Structured Outputs (`chat.completions.parse`), so the reply is
   guaranteed to match `RecommendationResponse`: a `status` (`ok` / `no_match`) and a ranked list of
   `{title, release_year}`. The user's text is delimited and treated as data, not instructions.
   Refusals and nonsense input return `no_match`; API errors become a friendly message instead of a 500.

3. **Validation layer** – `services/schemas.py`  
   Pydantic models clean titles (list markers, quotes), drop empty/overlong ones, de-duplicate,
   and cap the list at 8 candidates. RAWG responses are validated by models too.

4. **Game lookup** – `services/rawg_service.py`  
   Candidates are searched on RAWG in parallel. Each search looks at the top 5 hits and keeps the best one
   only if title and release year match confidently, so wrong or hallucinated games are dropped.
   A per-request budget caps RAWG at **15 HTTP calls** (retries included); 429/5xx/timeouts are retried once.

5. **Rendering** – `services/recommender.py`, `app.py`  
   The first 5 verified games (in the LLM's order) are stored in the session, and `/` renders them as cards.

6. **Health check & security headers**  
   - `/healthz` returns a simple JSON `{"status": "ok"}` for uptime checks.  
   - `app.after_request` sets CSP, HSTS, and other standard security headers.

---

## Tests

```bash
pip install -r requirements.txt -r requirements-dev.txt
pytest -q
```

OpenAI and RAWG are mocked, so tests need no API keys or network.

---

## Environment Variables (Summary)

- `OPENAI_API_KEY` – **Required.** Your OpenAI API key.
- `RAWG_API_KEY` – **Required.** Your RAWG API key.
- `FLASK_SECRET_KEY` – Secret used for Flask sessions. Set to a long random value in production.
- `PORT` – Port to bind to. Defaults to `8080`.

All of these can go into `.env` for local development.

---

## Running with Docker

If you prefer containers:

```bash
docker build -t video-game-advisor .
docker run -p 8080:8080 --env-file .env video-game-advisor
```

Then visit `http://localhost:8080`.

The `Dockerfile`:

- Uses `python:3.12-slim`
- Installs dependencies from `requirements.txt`
- Copies the app code
- Runs Gunicorn: `gunicorn -b 0.0.0.0:8080 -k gthread --threads 4 --workers 2 app:app`

---

## Deployment Notes

- The `Procfile` (`web: gunicorn app:app`) is suitable for platforms like Heroku or Render that support Procfiles.
- You should always configure `OPENAI_API_KEY`, `RAWG_API_KEY`, `FLASK_SECRET_KEY`, and `PORT` using the platform’s environment variable settings.
- Do **not** check secrets into Git. Keep `.env` local and private.

---

## Troubleshooting

- **`RuntimeError: OPENAI_API_KEY is not set`**  
  Check that `OPENAI_API_KEY` is defined in your shell or `.env`, and that `.env` is in the project root.

- **RAWG data missing or incomplete**  
  If RAWG doesn’t return a result or errors, the app falls back to showing the raw title with `"N/A"` for missing fields.

- **Blank or odd recommendations**  
  Try rephrasing your description or using a bit more detail. The app tells OpenAI to return exactly a comma‑separated list of real game titles, but quality still depends on the prompt.

---

## License

This project is intended as a personal/learning tool for videogame discovery.  
Before reusing any part of it in production, make sure you understand and comply with the terms of the OpenAI and RAWG APIs, as well as any license associated with this repository.

