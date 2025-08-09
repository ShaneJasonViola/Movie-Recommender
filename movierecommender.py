# app.py
import streamlit as st
from openai import OpenAI
import requests
import json
import re

# --- Secrets / API keys ---
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
TMDB_API_KEY = st.secrets["TMDB_API_KEY"]

st.set_page_config(page_title="Mood-Based Movie Recommender", layout="wide")

# 🎨 Custom CSS
st.markdown("""
    <style>
        /* Popcorn background for entire app */
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
        }

        /* White background style for title, input, and primary button */
        .page-title, .description-text, input, .stButton>button {
            background-color: white !important;
            color: black !important;
            padding: 6px 12px;
            border-radius: 5px;
            border: none !important;
        }

        /* Center the title */
        .page-title {
            font-size: 1.8rem !important;
            text-align: center;
            margin-bottom: 20px;
            width: fit-content;
            display: block;
            margin-left: auto;
            margin-right: auto;
        }

        /* "Why" white box */
        .movie-why {
            background-color: white !important;
            color: black !important;
            padding: 8px 12px;
            border-radius: 6px;
            margin-top: 8px;
            font-weight: bold !important;
            text-align: center;
            display: inline-block;
        }

        /* Our custom WATCH TRAILER button (always white) */
        .trailer-btn {
            display: inline-block;
            background-color: #ffffff !important;
            color: #000000 !important;
            border: 2px solid #ffffff !important;
            border-radius: 6px !important;
            padding: 8px 14px !important;
            text-decoration: none !important;
            font-weight: bold !important;
            text-align: center;
            margin-top: 8px;
        }
        .trailer-btn:hover {
            background-color: #f5f5f5 !important;
            color: #000000 !important;
            border-color: #f5f5f5 !important;
        }
    </style>
""", unsafe_allow_html=True)

# Page title & description
st.markdown('<div class="page-title">Mood-Based Movie Recommender</div>', unsafe_allow_html=True)
st.markdown('<div class="description-text">Tell us your mood and get 3 movie picks with posters, a reason to watch, and a trailer.</div>', unsafe_allow_html=True)

# Mood input
mood = st.text_input("How are you feeling right now?", placeholder="e.g. adventurous, sad, romantic")

# ---------- Helpers ----------
def safe_json_extract(text: str):
    if not text:
        raise ValueError("Empty response from model.")
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.DOTALL | re.IGNORECASE)
    if fence:
        text = fence.group(1).strip()
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
        vids_sorted = sorted(vids, key=score, reverse=True)
        for v in vids_sorted:
            if v.get("site") == "YouTube" and v.get("key"):
                return f"https://www.youtube.com/watch?v={v['key']}"
        return None
    except Exception:
        return None

def openai_movies_json(mood_text: str):
    # Ask for 6 so we can filter down to 3 that have both poster & trailer
    prompt = (
        f"Recommend exactly 6 movies that match the mood '{mood_text}'. "
        "Prefer the last 25 years unless the mood strongly suggests a classic. "
        "Avoid spoilers.\n\n"
        "Return ONLY valid JSON in this exact structure:\n"
        "{\n"
        '  "movies": [\n'
        '    {"title": "Movie 1", "why": "One-sentence reason"},\n'
        '    {"title": "Movie 2", "why": "One-sentence reason"},\n'
        '    {"title": "Movie 3", "why": "One-sentence reason"},\n'
        '    {"title": "Movie 4", "why": "One-sentence reason"},\n'
        '    {"title": "Movie 5", "why": "One-sentence reason"},\n'
        '    {"title": "Movie 6", "why": "One-sentence reason"}\n'
        "  ]\n"
        "}\n"
        "Do not include any extra commentary or text outside the JSON."
    )
    resp = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt,
        temperature=0.7,
        max_output_tokens=600,
    )
    raw = getattr(resp, "output_text", None)
    if not raw:
        raw = "".join([chunk.get("content", "") if isinstance(chunk, dict) else str(chunk)
                       for chunk in getattr(resp, "output", [])])
    data = safe_json_extract(raw)
    if "movies" not in data or not isinstance(data["movies"], list) or len(data["movies"]) < 1:
        raise ValueError("Model did not return the expected 'movies' array.")
    return data["movies"]

# ---------- Main ----------
if st.button("Get Movie Recommendations") and mood:
    with st.spinner("Generating your recommendations..."):
        try:
            candidates = openai_movies_json(mood)  # 6 candidates
            st.markdown("### Your picks")
            cols = st.columns(3)

            shown = 0
            for m in candidates:
                if shown >= 3:
                    break

                title = (m.get("title") or "").strip()
                why = (m.get("why") or "").strip() or "Good fit for your mood."
                if not title:
                    continue

                tmdb_movie = tmdb_search_movie(title)
                if not tmdb_movie:
                    continue

                poster_path = tmdb_movie.get("poster_path")
                if not poster_path:
                    continue  # require poster

                movie_id = tmdb_movie.get("id")
                trailer_url = tmdb_movie_trailer_url(movie_id) if movie_id else None
                if not trailer_url:
                    continue  # require trailer

                poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}"
                year = (tmdb_movie.get("release_date") or "")[:4]

                with cols[shown]:
                    if poster_url:
                        st.image(poster_url, width=260)
                    st.markdown(f"**{title}** {f'({year})' if year else ''}")
                    st.markdown(f'<div class="movie-why">{why}</div>', unsafe_allow_html=True)
                    # Our custom always-white trailer button:
                    st.markdown(f'<a class="trailer-btn" href="{trailer_url}" target="_blank">Watch Trailer</a>', unsafe_allow_html=True)

                shown += 1

            if shown == 0:
                st.warning("No matches with both a trailer and a poster. Try a different mood.")
            elif shown < 3:
                st.info(f"Found {shown} with both trailer and poster. Try again for more options.")

        except json.JSONDecodeError as e:
            st.error("The AI response wasn’t valid JSON. Try again.")
            st.code(str(e))
        except Exception as e:
            st.error(f"Something went wrong: {e}")
            st.exception(e)



