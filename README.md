# Movie-Recommender
Summary: Let's User's input their mood and finds a movie they might enjoy watching

# 🎬 Mood-Based Movie Recommender

This project recommends movies based on your mood. You just type in how you’re feeling, and the app uses AI + movie data from TMDB to give you a short list of movies you might like. It generates a movie poster, a description of the movie and a link to watch a trailer.

The app is built  in Python using **Streamlit**, the **TMDB API** for movie info, and **OpenAI’s API** to make the recommendations.

---

## What it Does
- You tell it your mood (happy, sad, bored, motivated, etc.).
- It gives you 3 movie suggestions that fit your vibe.
- Shows a poster, description, and release year for each movie
- Links you straight to the trailer so you can start watching faster.

---

## Why I Made It
I wanted to mix AI with a public API to make something useful but also fun to use  
Also, sometimes picking a movie is harder than actually watching one — so I thought I’d make that decision easier.

---

## How to Run It

1. **Clone this repo**  
   ```bash
   git clone https://github.com/yourusername/mood-based-movie-recommender.git
   cd mood-based-movie-recommender
   ```

2. **Install the requirements**  
   ```bash
   pip install -r requirements.txt
   ```

3. **Add your API keys**  
   Make a file at `.streamlit/secrets.toml` and put this inside:
   ```toml
   OPENAI_API_KEY = "your_openai_api_key"
   TMDB_API_KEY = "your_tmdb_api_key"
   ```

4. **Run it!**  
   ```bash
   streamlit run app.py
   ```
   Then open `http://localhost:8501` in your browser.

---

## Tools I Used
- **Python** (because it’s the easiest for this kind of project)
- **Streamlit** – to build the website
- **TMDB API** – for all the movie info and posters
- **OpenAI API** – to get mood-based suggestions

---

## Project Layout
```
mood-based-movie-recommender/
│
├── app.py               # The main app file
├── requirements.txt     # Stuff you need to install
└── .streamlit/
    └── secrets.toml     # Your API keys (don’t share this!)
```

---

## How to Deploy 
If you want to put it online, Streamlit Cloud makes it super easy:
1. Put your code on GitHub.
2. Go to [share.streamlit.io](https://share.streamlit.io/).
3. Connect your GitHub repo.
4. Add your API keys in the settings.
