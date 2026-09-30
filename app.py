import streamlit as st
import pickle
import pandas as pd
import numpy as np
import requests
import os
import sys
import socket

# CHANGE: Configured modern page metadata, wide layout, and collapsed sidebar.
# PURPOSE: Create an immersive, cinematic widescreen canvas for movie cards.
st.set_page_config(
    page_title="CineVerse | Modern Movie Recommender",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CHANGE: Added lightweight DNS fallback ONLY for local Windows environments.
# PURPOSE: Certain Indian ISPs (such as Reliance Jio) sinkhole TMDB's API domain
#          to an unreachable IP. On Linux/Streamlit Cloud, standard AWS DNS is used.
def setup_tmdb_dns_fallback():
    if sys.platform != "win32":
        return  # Linux / Cloud deployment environments have clean DNS

    host = "api.themoviedb.org"
    try:
        ip = socket.gethostbyname(host)
        s = socket.socket()
        s.settimeout(1.0)
        s.connect((ip, 443))
        s.close()
        return  # Default DNS works fine
    except Exception:
        pass

    try:
        r = requests.get(f"https://dns.google/resolve?name={host}&type=A", timeout=2)
        if r.status_code == 200:
            for ans in r.json().get("Answer", []):
                ip = ans.get("data")
                if ip:
                    try:
                        s = socket.socket()
                        s.settimeout(1.0)
                        s.connect((ip, 443))
                        s.close()
                        orig_gai = socket.getaddrinfo
                        def custom_gai(h, p, *args, **kwargs):
                            if h == host:
                                return orig_gai(ip, p, *args, **kwargs)
                            return orig_gai(h, p, *args, **kwargs)
                        socket.getaddrinfo = custom_gai
                        return
                    except Exception:
                        continue
    except Exception:
        pass

setup_tmdb_dns_fallback()

# CHANGE: Replaced hardcoded API key with flexible, case-insensitive secrets lookup.
# PURPOSE: Seamlessly read TMDB_API_KEY from Streamlit Cloud Secrets or local secrets.toml.
def get_tmdb_api_key():
    key = ""
    if hasattr(st, "secrets"):
        for k in ["TMDB_API_KEY", "tmdb_api_key", "api_key", "API_KEY", "TMDB_KEY"]:
            if k in st.secrets:
                key = str(st.secrets[k])
                break
    if not key:
        key = os.environ.get("TMDB_API_KEY", os.environ.get("API_KEY", ""))
    return key.strip().strip('"').strip("'")

FALLBACK_POSTER_URL = "https://placehold.co/500x750.png?text=No+Poster"
session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0"})

# CHANGE: Added dual support for standard v3 API keys and v4 Bearer tokens with diagnostics.
# PURPOSE: Support both TMDB v3 API keys and v4 Read Access Tokens without configuration errors.
@st.cache_data(show_spinner=False)
def fetch_poster(movie_id):
    api_key = get_tmdb_api_key()
    if not api_key:
        print("[TMDB ERROR] No API key detected in st.secrets or os.environ.")
        return FALLBACK_POSTER_URL

    headers = {"User-Agent": "Mozilla/5.0"}
    if len(api_key) > 50 or api_key.startswith("eyJ"):
        # TMDB v4 Read Access Token (JWT Bearer Auth)
        headers["Authorization"] = f"Bearer {api_key}"
        headers["accept"] = "application/json"
        url = f"https://api.themoviedb.org/3/movie/{movie_id}?language=en-US"
    else:
        # Standard TMDB v3 API Key (32 hex characters)
        url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}&language=en-US"

    try:
        response = session.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            poster_path = data.get("poster_path")
            if poster_path:
                return "https://image.tmdb.org/t/p/w500" + poster_path
        else:
            print(f"[TMDB ERROR] Movie ID {movie_id}: Status {response.status_code}, Response: {response.text[:200]}")
    except Exception as e:
        print(f"[TMDB EXCEPTION] Movie ID {movie_id}: {type(e).__name__}: {e}")

    return FALLBACK_POSTER_URL

# CHANGE: Added @st.cache_resource to load heavy pickle models into memory once at startup.
# PURPOSE: Eliminate multi-second unpickling delays on every user interaction without changing model logic.
@st.cache_resource
def load_data():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    movies_data = pickle.load(open(os.path.join(base_dir, 'movies.pkl'), 'rb'))
    similarity_data = pickle.load(open(os.path.join(base_dir, 'similarity.pkl'), 'rb'))
    return movies_data, similarity_data

movies, similarity = load_data()

def recommend(movie):
    # Search in the loaded DataFrame 'movies'
    movie_index = movies[movies['title'] == movie].index[0]
    distances = similarity[movie_index]
    movies_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:6]

    recommended_movies = []
    recommended_movie_posters = []

    for i in movies_list:
        movie_id = movies.iloc[i[0]].movie_id
        recommended_movies.append(movies.iloc[i[0]].title)
        # to fetch movie poster by id and API
        recommended_movie_posters.append(fetch_poster(movie_id))

    return recommended_movies, recommended_movie_posters

# CHANGE: Injected professional custom CSS for dark cinematic UI, glassmorphism, and responsive movie cards.
# PURPOSE: Elevate application visual design to commercial streaming portfolio standards without external frameworks.
st.markdown("""
<style>
    /* Dark cinematic background */
    .stApp {
        background: radial-gradient(circle at 50% 0%, #111827 0%, #07090e 65%, #030407 100%);
        color: #f3f4f6;
    }

    /* Container constraints */
    .main .block-container {
        max-width: 1200px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    /* Hero Header Branding */
    .hero-header {
        text-align: center;
        margin-bottom: 2.2rem;
        padding: 0 1rem;
    }

    .hero-badge {
        display: inline-block;
        font-size: 0.72rem;
        letter-spacing: 2px;
        font-weight: 700;
        text-transform: uppercase;
        padding: 0.3rem 0.9rem;
        border-radius: 9999px;
        background: rgba(229, 9, 20, 0.12);
        color: #ff4b4b;
        border: 1px solid rgba(255, 75, 75, 0.28);
        margin-bottom: 0.8rem;
    }

    .hero-title {
        font-size: 2.8rem;
        font-weight: 800;
        letter-spacing: -0.5px;
        margin-bottom: 0.4rem;
        color: #ffffff;
        text-shadow: 0 2px 10px rgba(0,0,0,0.5);
    }

    .hero-title span {
        background: linear-gradient(135deg, #ff4b4b 0%, #ff8585 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .hero-tagline {
        font-size: 1.05rem;
        color: #9ca3af;
        max-width: 580px;
        margin: 0 auto;
        line-height: 1.5;
    }

    /* Search & Action Card */
    .search-card {
        background: rgba(17, 24, 39, 0.65);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 1.8rem 2rem;
        max-width: 680px;
        margin: 0 auto 2.5rem auto;
        box-shadow: 0 20px 40px -15px rgba(0, 0, 0, 0.6);
        backdrop-filter: blur(14px);
    }

    /* Streamlit Selectbox custom styling */
    div[data-baseweb="select"] {
        border-radius: 10px !important;
    }
    div[data-baseweb="select"] > div {
        background-color: #0d121c !important;
        border-color: rgba(255, 255, 255, 0.12) !important;
        color: #ffffff !important;
        border-radius: 10px !important;
        min-height: 48px !important;
    }
    div[data-baseweb="select"] * {
        color: #ffffff !important;
    }

    /* Streamlit Button custom styling */
    div.stButton > button {
        width: 100%;
        background: linear-gradient(135deg, #e50914 0%, #b81d24 100%) !important;
        color: #ffffff !important;
        border: none !important;
        padding: 0.75rem 1.5rem !important;
        font-size: 1.02rem !important;
        font-weight: 600 !important;
        letter-spacing: 0.5px !important;
        border-radius: 10px !important;
        box-shadow: 0 4px 18px rgba(229, 9, 20, 0.38) !important;
        transition: all 0.25s ease-in-out !important;
        cursor: pointer !important;
        margin-top: 0.6rem !important;
    }

    div.stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 24px rgba(229, 9, 20, 0.55) !important;
        background: linear-gradient(135deg, #f40b17 0%, #c42028 100%) !important;
    }

    div.stButton > button:active {
        transform: translateY(0) !important;
    }

    /* Results Header */
    .results-heading {
        margin: 2.2rem 0 1.5rem 0;
        padding-bottom: 0.6rem;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        display: flex;
        align-items: center;
        justify-content: space-between;
    }

    .results-title {
        font-size: 1.35rem;
        font-weight: 700;
        color: #ffffff;
        letter-spacing: -0.2px;
    }

    .results-badge {
        font-size: 0.75rem;
        color: #9ca3af;
        background: rgba(255, 255, 255, 0.06);
        padding: 0.25rem 0.7rem;
        border-radius: 6px;
        font-weight: 500;
    }

    /* Movie Poster Card Visuals */
    div[data-testid="column"] {
        background: rgba(17, 24, 39, 0.45);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 14px;
        padding: 0.75rem;
        transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.3s ease, border-color 0.3s ease;
    }

    div[data-testid="column"]:hover {
        transform: translateY(-6px);
        box-shadow: 0 14px 28px rgba(0, 0, 0, 0.5);
        border-color: rgba(255, 75, 75, 0.3);
    }

    div[data-testid="stImage"] img {
        border-radius: 10px;
        width: 100%;
        aspect-ratio: 2 / 3;
        object-fit: cover;
        box-shadow: 0 6px 14px rgba(0, 0, 0, 0.4);
    }

    /* Movie Title Styling */
    .movie-card-title {
        font-size: 0.92rem;
        font-weight: 600;
        color: #f3f4f6;
        text-align: center;
        margin-top: 0.65rem;
        margin-bottom: 0.25rem;
        line-height: 1.35;
        min-height: 2.7rem;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }

    .movie-card-rank {
        font-size: 0.7rem;
        font-weight: 700;
        color: #ff4b4b;
        text-align: center;
        letter-spacing: 1px;
        text-transform: uppercase;
        margin-bottom: 0.2rem;
    }
</style>
""", unsafe_allow_html=True)

# Hero Header Brand Section
st.markdown("""
<div class="hero-header">
    <div class="hero-badge">AI-Powered Discovery</div>
    <div class="hero-title">CINE<span>VERSE</span></div>
    <p class="hero-tagline">Select any movie you love to instantly discover similar cinematic titles curated through cosine similarity analysis.</p>
</div>
""", unsafe_allow_html=True)

# Search Card Container
movies_titles = movies['title'].values

st.markdown('<div class="search-card">', unsafe_allow_html=True)
selected_movie_name = st.selectbox(
    "Search or select a movie from the database",
    movies_titles,
    help="Type to search among 4,800+ movies"
)
recommend_button = st.button("Show Recommendations")
st.markdown('</div>', unsafe_allow_html=True)

if recommend_button:
    with st.spinner("Analyzing similarity vectors and curating recommendations..."):
        names, posters = recommend(selected_movie_name)

    st.markdown(f"""
    <div class="results-heading">
        <div class="results-title">Recommended For You <span style="color: #9ca3af; font-size: 0.95rem; font-weight: 400;">based on <em>{selected_movie_name}</em></span></div>
        <div class="results-badge">TOP 5 MATCHES</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3, col4, col5 = st.columns(5)
    cols = [col1, col2, col3, col4, col5]

    for idx, col in enumerate(cols):
        with col:
            st.markdown(f'<div class="movie-card-rank">MATCH #{idx+1}</div>', unsafe_allow_html=True)
            try:
                st.image(posters[idx], width="stretch")
            except TypeError:
                st.image(posters[idx], use_container_width=True)
            st.markdown(f'<div class="movie-card-title" title="{names[idx]}">{names[idx]}</div>', unsafe_allow_html=True)
