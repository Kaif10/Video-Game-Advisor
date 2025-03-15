import os
import openai
import requests
from flask import Flask, request, render_template, redirect, url_for, session

app = Flask(__name__)

app.secret_key = "yfootballm"


#api keys for openai and RAWG (gaming metadat)
os.environ["OPENAI_API_KEY"] = "REDACTED_OPENAI_KEY"
openai.api_key = os.getenv("OPENAI_API_KEY")
os.environ["RAWG_API_KEY"] = "7c11c6b61443433ba941a9c037147be8"
RAWG_API_KEY = os.getenv("RAWG_API_KEY")

def get_game_recommendations(query):
    """
    Uses OpenAI's GPT-3.5-turbo model to return a list of recommended videogame titles 
    based on a natural language query 
    (If possible use a more advanced model like gpt o-series for more amazing and accurate results.)
    """


    prompt = (
    f"Recommend 5 videogame names that match the following description in terms of gameplay and genre. "
    f"If the input appears to be a videogame title, recommend that game along with related games: '{query}'. "
    "Return only the game names separated by commas."
)


    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful videogame recommender."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.6,
            max_tokens=20, #max tokens can be increased for more results like 7-8 games per description
        )

        answer = response.choices[0].message.content.strip()

        # Expect a comma-separated list of game titles.
        game_names = [name.strip() for name in answer.split(",")]
        return game_names
    except Exception as e:
        print("Error calling OpenAI API:", e)
        return []

def fetch_game_metadata(game_name):
    """
    Uses the RAWG API to fetch metadata for a given videogame title,
    including the cover image.
    """
    url = "https://api.rawg.io/api/games"
    params = {
        "search": game_name,
        "key": RAWG_API_KEY,
        "page_size": 1
    }
    try:
        response = requests.get(url, params=params)
        data = response.json()
        if data.get("results"):
            game = data["results"][0]

            ''' Construct a URL using the game's slug. This is so the user can click on the game and 
               view more details about it on the RAWG website '''
            game_slug = game.get("slug")
            game_url = f"https://rawg.io/games/{game_slug}" if game_slug else "N/A"
            return {
                "name": game.get("name"),
                "released": game.get("released") or "Unknown",
                "rating": game.get("rating") or "N/A",
                "website": game_url,
                "cover": game.get("background_image")  
            }

    except Exception as e:
        print("Error calling RAWG API for", game_name, ":", e)
    # Fallback if no data is found.
    return {"name": game_name, "released": "N/A", "rating": "N/A", "website": "N/A", "cover": None}



@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        quote = "Reveal the game your heart seeks—but you can't name it."
        recommendations = []
        error_msg = None
        query = request.form.get("query")
        if query:
            game_names = get_game_recommendations(query)
            if not game_names or all(name == "" for name in game_names):
                error_msg = "Oops, it looks like we're currently down. Please try again in sometime or contact the owner if the issue persists."
            else:
                # Filter duplicate games in the list
                game_names = list(dict.fromkeys(game_names))
                for game in game_names:
                    details = fetch_game_metadata(game)
                    recommendations.append(details)
        # Save the results in the session
        session["quote"] = quote
        session["recommendations"] = recommendations
        session["error_msg"] = error_msg
        # Redirect to the same page (GET request) after reloading
        return redirect(url_for("index"))
    else:
        # For GET, retrieve values from the session if available, then clear them
        quote = session.pop("quote", "Reveal the game your heart seeks—but you can't name it.")
        recommendations = session.pop("recommendations", [])
        error_msg = session.pop("error_msg", None)
        return render_template("index.html", quote=quote, recommendations=recommendations, error_msg=error_msg)


if __name__ == "__main__":
    app.run(debug=True)
