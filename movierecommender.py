# app.py
# --- Imports ---
import streamlit as st
from openai import OpenAI
import requests
import json

# --- Secrets / API keys ---
# Put these in .streamlit/secrets.toml or Streamlit Cloud Secrets
# OPENAI_API_KEY="sk-..."
# TMDB_API_KEY="..."
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
TMDB_API_KEY = st.secrets["TMDB_API_KEY"]

# --- Streamlit UI ---
st.set_page_config(page_title="🎬 Mood-Based Movie Recommender", layout="wide")
st.title("🎬 Mood-Based Movie Recommender")
st.markdown("Tell us your mood and get **3** movie picks with posters, a reason to watch, and a trailer.")

mood = st.text_input("How are you feeling right now?", placeholder="e.g. adventurous, sad, romantic")

def tmdb_search_movie(title: str):
    """Search TMDB and return the best matching movie dict or None."""
    params = {
        "api_key": TMDB_API_KEY,
        "query": title,
        "include_adult": "false",
        "language": "en-US"
    }
    try:
        r = requests.get("https://api.themoviedb.org/3/search/movie", params=params, timeout=20)
        r.raise_for_status()
        data = r.json()
        results = data.get("results", [])
        if not results:
            return None
        # Prefer exact title match if available (case-insensitive)
        exact = [m for m in results if m.get("title", "").lower() == title.lower()]
        return (exact[0] if exact else results[0])
    except Exception:
        return None

def tmdb_movie_trailer_url(movie_id: int):
    """Fetch the best trailer (YouTube) URL for a TMDB movie id."""
    params = {
        "api_key": TMDB_API_KEY,
        "language": "en-US"
    }
    try:
        r = requests.get(f"https://api.themoviedb.org/3/movie/{movie_id}/videos", params=params, timeout=20)
        r.raise_for_status()
        vids = r.json().get("results", [])
        if not vids:
            return None
        # Prefer official YouTube trailer first, then any YouTube trailer/teaser
        def score(v):
            s = 0
            if v.get("site") == "YouTube": s += 2
            if v.get("type") == "Trailer": s += 2
            if v.get("official"): s += 1
            return s
        best = sorted(vids, key=score, reverse=True)[0]
        if best.get("site") == "YouTube" and best.get("key"):
            return f"https://www.youtube.com/watch?v={best['key']}"
        return None
    except Exception:
        return None

def openai_movies_json(mood_text: str):
    """Ask OpenAI for exactly 3 movies in strict JSON (title, why)."""
    prompt = (
        f"Recommend exactly 3 movies that match the mood '{mood_text}'. "
        "Prefer the last 25 years unless the mood strongly suggests a classic. "
        "Avoid spoilers. Return only JSON that matches the schema."
    )

    resp = client.responses.create(
        model="gpt-4.1-mini",         # low-cost & fast
        input=prompt,
        temperature=0.7,
        max_output_tokens=500,
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "movie_recs",
                "schema": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "movies": {
                            "type": "array",
                            "minItems": 3,
                            "maxItems": 3,
                            "items": {
                                "type": "object",
                                "additionalProperties": False,
                                "properties": {
                                    "title": {"type": "string"},
                                    "why": {"type": "string"}
                                },
                                "required": ["title", "why"]
                            }
                        }
                    },
                    "required": ["movies"]
                },
                "strict": True
            }
        },
    )

    # Prefer output_text; fall back to stitching content if SDK version differs
    raw = getattr(resp, "output_text", None)
    if not raw:
        raw = "".join([chunk.get("content", "") if isinstance(chunk, dict) else str(chunk)
                       for chunk in getattr(resp, "output", [])])
    data = json.loads(raw)
    return data["movies"]  # list of {title, why}

if st.button("🎥 Get Movie Recommendations") and mood:
    with st.spinner("Cooking up picks..."):
        try:
            movies = openai_movies_json(mood)

            st.markdown("### 🎞 Your picks")
            cols = st.columns(3)

            for i, m in enumerate(movies):
                title = m["title"]
                why = m["why"]

                tmdb_movie = tmdb_search_movie(title)
                poster_url, year, trailer_url = None, "", None

                if tmdb_movie:
                    poster_path = tmdb_movie.get("poster_path")
                    if poster_path:
                        poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}"
                    year = (tmdb_movie.get("release_date") or "")[:4]
                    movie_id = tmdb_movie.get("id")
                    if movie_id:
                        trailer_url = tmdb_movie_trailer_url(movie_id)

                with cols[i]:
                    if poster_url:
                        st.image(poster_url, width=260)
                    st.markdown(f"**{title}** {f'({year})' if year else ''}")
                    st.caption(why)
                    if trailer_url:
                        st.link_button("▶️ Watch Trailer", trailer_url, use_container_width=True)
                    else:
                        st.write("No trailer found 😕")

        except Exception as e:
            st.error(f"Something went wrong: {e}")
            st.exception(e)
