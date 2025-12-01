import logging
import os

from flask import Flask, request, render_template, redirect, url_for, session

from services.openai_service import get_game_recommendations
from services.rawg_service import fetch_game_metadata

app = Flask(__name__)

app.secret_key = os.getenv("FLASK_SECRET_KEY", "yfootballm")

@app.route("/", methods=["GET", "POST"])
def index():
    default_quote = "Uncover the game that fuels your passion."
    if request.method == "POST":
        query = request.form.get("query")
        recommendations = []
        error_msg = None
        if query:
            game_names, gen_error = get_game_recommendations(query)
            if gen_error:
                error_msg = gen_error
            elif not game_names:
                error_msg = "No games matched that description. Try adjusting keywords or genre."
            else:
                game_names = list(dict.fromkeys(game_names))
                for game in game_names:
                    details = fetch_game_metadata(game)
                    recommendations.append(details)
        # Save query, quote, recommendations, and error message in session
        session["query"] = query
        session["quote"] = default_quote
        session["recommendations"] = recommendations
        session["error_msg"] = error_msg
        return redirect(url_for("index"))
    else:
        # Retrieve from session for GET
        query = session.pop("query", "")
        quote = session.pop("quote", default_quote)
        recommendations = session.pop("recommendations", [])
        error_msg = session.pop("error_msg", None)
        return render_template("index.html", query=query, quote=quote, recommendations=recommendations, error_msg=error_msg)

@app.route("/healthz", methods=["GET"])
def healthcheck():
    return {"status": "ok"}, 200

@app.after_request
def apply_security_headers(response):
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "img-src 'self' data: https://media.rawg.io https://*.rawg.io; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdnjs.cloudflare.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; "
        "connect-src 'self'; "
        "frame-ancestors 'none';"
    )
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
    return response

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080)), debug=os.getenv("FLASK_DEBUG", "").lower() == "true")
