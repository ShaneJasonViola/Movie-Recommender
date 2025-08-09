# app.py
import streamlit as st
from openai import OpenAI
import requests
import json
import re

# --- Secrets / API keys ---
# Put these in .streamlit/secrets.toml (or Streamlit Cloud → Settings → Secrets):
# OPENAI_API_KEY="sk-..."
# TMDB_API_KEY="..."
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
TMDB_API_KEY = st.secrets["TMDB_API_KEY"]

# --- Streamlit UI ---
st.set_page_config(page_title="Mood-Based Movie Recommender", layout="wide")
st.title("Mood-Based Movie Recommender")
st.markdown("Tell us your mood and get 3 movie picks with posters, a reason to watch, and a trailer.")



st.set_page_config(page_title="Mood-Based Movie Recommender", layout="wide")

# Custom CSS: background + black bold text with white background
st.markdown("""
    <style>
        /* Background image */
        .stApp {
            background-image: url('https://wallpapercave.com/wp/wp1896112.jpg');
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }

        /* Global text style */
        html, body, [class*="st-"], p, span, div {
            color: black !important;
            font-weight: bold !important;
            font-size: 1.05rem !important;
            background-color: white;
        }

        /* Movie theater marquee style */
        .movie-header {
            font-family: 'Arial Black', Gadget, sans-serif;
            color: black !important;
            background-color: gold;
            border: 5px solid gold;
            padding: 20px;
            text-align: center;
            font-size: 2rem !important;
            letter-spacing: 2px;
            box-shadow: 0 0 20px gold;
            border-radius: 10px;
            margin-bottom: 20px;
        }
    </style>
""", unsafe_allow_html=True)

# Movie theater marquee header
st.markdown('<div class="movie-header">Mood-Based Movie Recommender App</div>', unsafe_allow_html=True)

# App description
st.markdown("Tell us your mood and get 3 movie picks with posters, a reason to watch, and a trailer.")





# App description styled in black
st.markdown('<div class="description-text">Tell us your mood and get 3 movie picks with posters, a reason to watch, and a trailer.</div>', unsafe_allow_html=True)





mood = st.text_input("How are you feeling right now?", placeholder="e.g. adventurous, sad, romantic")

# ---------- Helpers ----------
def safe_json_extract(text: str):
    """Extract and parse JSON from a model response that should be JSON."""
    if not text:
        raise ValueError("Empty response from model.")

    # Look for JSON fenced code block
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.DOTALL | re.IGNORECASE)
    if fence:
        text = fence.group(1).strip()

    # If there's extra text, slice from first '{' to last '}'
    if not text.strip().startswith("{"):
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            text = text[start : end + 1]

    return json.loads(text)

def tmdb_search_movie(title: str):
    params = {
        "api_key": TMDB_API_KEY,
        "query": title,
        "include_adult": "false",
        "language": "en-US"
    }
    try:
        r = requests.get("https://api.themoviedb.org/3/search/movie", params=params, timeout=20)
        r.raise_for_status()
        results = r.json().get("results", [])
        if not results:
            return None
        exact = [m for m in results if (m.get("title") or "").lower() == title.lower()]
        return (exact[0] if exact else results[0])
    except Exception:
        return None

def tmdb_movie_trailer_url(movie_id: int):
    params = {"api_key": TMDB_API_KEY, "language": "en-US"}
    try:
        r = requests.get(f"https://api.themoviedb.org/3/movie/{movie_id}/videos", params=params, timeout=20)
        r.raise_for_status()
        vids = r.json().get("results", [])
        if not vids:
            return None
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
    prompt = (
        f"Recommend exactly 3 movies that match the mood '{mood_text}'. "
        "Prefer the last 25 years unless the mood strongly suggests a classic. "
        "Avoid spoilers.\n\n"
        "Return ONLY valid JSON in this exact structure:\n"
        "{\n"
        '  "movies": [\n'
        '    {"title": "Movie 1", "why": "One-sentence reason"},\n'
        '    {"title": "Movie 2", "why": "One-sentence reason"},\n'
        '    {"title": "Movie 3", "why": "One-sentence reason"}\n'
        "  ]\n"
        "}\n"
        "Do not include any extra commentary or text outside the JSON."
    )

    resp = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt,
        temperature=0.7,
        max_output_tokens=500,
    )

    raw = getattr(resp, "output_text", None)
    if not raw:
        raw = "".join(
            [chunk.get("content", "") if isinstance(chunk, dict) else str(chunk)
             for chunk in getattr(resp, "output", [])]
        )
    data = safe_json_extract(raw)
    if "movies" not in data or not isinstance(data["movies"], list) or len(data["movies"]) < 3:
        raise ValueError("Model did not return the expected 'movies' array.")
    return data["movies"][:3]

# ---------- Main ----------
if st.button("Get Movie Recommendations") and mood:
    with st.spinner("Generating your recommendations..."):
        try:
            movies = openai_movies_json(mood)

            st.markdown("### Your picks")
            cols = st.columns(3)

            for i, m in enumerate(movies):
                title = m.get("title", "").strip()
                why = m.get("why", "").strip() or "Good fit for your mood."

                tmdb_movie = tmdb_search_movie(title) if title else None
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
                    st.markdown(f"**{title or 'Unknown Title'}** {f'({year})' if year else ''}")
                    st.caption(why)
                    if trailer_url:
                        st.link_button("Watch Trailer", trailer_url, use_container_width=True)
                    else:
                        st.write("No trailer found.")

        except json.JSONDecodeError as e:
            st.error("The AI response wasn’t valid JSON. Try again.")
            st.code(str(e))
        except Exception as e:
            st.error(f"Something went wrong: {e}")
            st.exception(e)

