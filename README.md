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
- **AI:** OpenAI Chat Completions (`gpt-4o-mini` with `gpt-3.5-turbo` fallback)
- **Game data:** RAWG API
- **Server:** Gunicorn (via `Dockerfile` and `Procfile` for deployment)

---

## Project Structure

- `app.py` – Flask app, routes, session handling, security headers.
- `services/openai_service.py` – Calls OpenAI to turn your prompt into specific game titles.
- `services/rawg_service.py` – Calls RAWG to fetch cover art, rating, release date and canonical game URLs.
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

In the project root (same folder as `app.py`), create a file named `.env`:

```env
OPENAI_API_KEY=your-openai-api-key-here
RAWG_API_KEY=your-rawg-api-key-here
FLASK_SECRET_KEY=some-long-random-string
PORT=8080
```

Notes:

- `config.py` automatically loads `.env` at startup.
- The `OPENAI_API_KEY` **must** be set; the app will raise an error if it is missing.
- `RAWG_API_KEY` has a hard‑coded fallback in `config.py`, but you should always use your own key.
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

1. **User input**  
   On `/`, you enter a description of the kind of game you want.

2. **AI game selection**  
   `services/openai_service.get_game_recommendations()` sends that description to OpenAI with:
   - A system prompt that enforces “real game titles only”.
   - A user prompt that asks for 5 matching games, returned as a comma‑separated list.
   It tries the primary model first (`gpt-4o-mini`), then a fallback (`gpt-3.5-turbo`) if necessary.

3. **Game metadata lookup**  
   For each returned title, `services/rawg_service.fetch_game_metadata()` queries RAWG and extracts:
   - Name
   - Release date
   - Rating
   - Cover image
   - A canonical URL on RAWG

4. **Rendering**  
   `app.py` stores query + results in the session and redirects back to `/`, where `templates/index.html` renders a grid of recommendation cards with:
   - Cover art
   - Name, release year, rating
   - Click‑through link to more details

5. **Health check & security headers**  
   - `/healthz` returns a simple JSON `{"status": "ok"}` for uptime checks.  
   - `app.after_request` sets CSP, HSTS, and other standard security headers.

---

## Environment Variables (Summary)

- `OPENAI_API_KEY` – **Required.** Your OpenAI API key.
- `RAWG_API_KEY` – Recommended. Your RAWG API key; if missing, `config.py` falls back to a baked‑in key (you should override this).
- `FLASK_SECRET_KEY` – Secret used for Flask sessions. Set to a long random value in production.
- `PORT` – Port to bind to. Defaults to `8080`.
- `REQUEST_TIMEOUT` – Optional, request timeout in seconds for RAWG calls (default `10`).

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

