
# Import Libraries
import streamlit as st
from openai import OpenAI
import requests
import re

# Set your API keys
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
TMDB_API_KEY = st.secrets["TMDB_API_KEY"]

# Streamlit App Header
st.set_page_config(page_title="🎬 Mood-Based Movie Recommender", layout="wide")
st.title("🎬 Mood-Based Movie Recommender")
st.markdown("Tell us your mood, and get 3 movie suggestions — with posters!")

# User Input
mood = st.text_input("How are you feeling right now?", placeholder="e.g. adventurous, sad, romantic")

if st.button("🎥 Get Movie Recommendations") and mood:
    with st.spinner("Generating recommendations..."):
        prompt = f"Recommend 3 movies that match the mood '{mood}'. For each movie, include the title in **bold** and a one-sentence description."

        try:
            # Step 1: Ask OpenAI
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=500
            )
            ai_reply = response.choices[0].message.content.strip()

            # Step 2: Extract titles from AI response
            movie_titles = re.findall(r"\*\*(.*?)\*\*", ai_reply)
            if not movie_titles:
                movie_titles = [line.split(".")[1].strip().split("(")[0] for line in ai_reply.split("\n") if "." in line][:3]

            # Step 3: Fetch posters from TMDB
            st.markdown("### 🎞 Posters")
            cols = st.columns(3)

            for i, title in enumerate(movie_titles):
                params = {"api_key": TMDB_API_KEY, "query": title}
                result = requests.get("https://api.themoviedb.org/3/search/movie", params=params).json()

                if result["results"]:
                    movie = result["results"][0]
                    poster_path = movie.get("poster_path")
                    image_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None
                    release_year = movie.get("release_date", "")[:4]

                    with cols[i]:
                        if image_url:
                            st.image(image_url, width=250)
                        st.markdown(f"**{title}** ({release_year})")
                else:
                    with cols[i]:
                        st.markdown(f"**{title}** – Poster not found.")

        except Exception as e:
            st.error(f"Something went wrong: {e}")
