import streamlit as st
import pickle
import pandas as pd
import numpy as np
import requests
import os
import sys
import socket

# UI CHANGE: Configured modern page metadata and wide layout for CineVerse.
# PURPOSE: Establish a professional, cinematic widescreen canvas for movie cards.
st.set_page_config(
    page_title="CineVerse | Modern Movie Recommender",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# FEATURE: Added lightweight DNS fallback ONLY for local Windows environments.
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

# FEATURE: Replaced hardcoded API key with flexible, case-insensitive secrets lookup.
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

# FEATURE: Added dual support for standard v3 API keys and v4 Bearer tokens with diagnostics.
# PURPOSE: Support both TMDB v3 API keys and v4 Read Access Tokens without configuration errors.
@st.cache_data(show_spinner=False)
def fetch_poster(movie_id):
    api_key = get_tmdb_api_key()
    if not api_key:
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
    except Exception:
        pass

    return FALLBACK_POSTER_URL

# FEATURE: Added @st.cache_resource to load heavy pickle models into memory once at startup.
# PURPOSE: Eliminate multi-second unpickling delays on every user interaction without changing model logic.
@st.cache_resource
def load_data():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    movies_data = pickle.load(open(os.path.join(base_dir, 'movies.pkl'), 'rb'))
    similarity_data = pickle.load(open(os.path.join(base_dir, 'similarity.pkl'), 'rb'))
    return movies_data, similarity_data

movies, similarity = load_data()

# FEATURE: Cached lookup for rich metadata including director, cast, genres, and synopsis.
# PURPOSE: Provide rich authentic details inside the overview modal without external latency.
@st.cache_resource
def load_metadata():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(base_dir, "movie_metadata.csv")
    if os.path.exists(csv_path):
        try:
            df = pd.read_csv(csv_path)
            return df.set_index("id").to_dict("index")
        except Exception:
            return {}
    return {}

movie_metadata = load_metadata()

# FEATURE: Optional genre filtering built cleanly on top of cosine similarity distance ranking.
# PURPOSE: Enable users to explore specific genres while preserving exact baseline when 'All Genres' is chosen.
def recommend(movie, genre_filter="All Genres"):
    movie_index = movies[movies['title'] == movie].index[0]
    distances = similarity[movie_index]
    sorted_indices = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:]

    recommended_movies = []
    recommended_movie_posters = []

    for i in sorted_indices:
        if len(recommended_movies) >= 5:
            break
        cand_id = movies.iloc[i[0]].movie_id
        cand_title = movies.iloc[i[0]].title

        # If genre filter active, verify candidate matches selected genre
        if genre_filter and genre_filter != "All Genres":
            m_info = movie_metadata.get(cand_id, {})
            genres = [g.strip() for g in str(m_info.get("genre_names", "")).split(",") if g.strip()]
            if genre_filter not in genres:
                continue

        recommended_movies.append(cand_title)
        recommended_movie_posters.append(fetch_poster(cand_id))

    return recommended_movies, recommended_movie_posters

# FEATURE: Rich movie overview modal with synopsis, director, top cast, and genre pills.
# PURPOSE: Offer comprehensive cinematic metadata directly inside the interactive modal.
@st.dialog("Movie Overview")
def show_movie_details(movie_id, title, poster_url):
    info = movie_metadata.get(movie_id, {})
    rel_date = str(info.get("release_date", ""))
    year = rel_date[:4] if len(rel_date) >= 4 else "N/A"
    rating = info.get("vote_average", None)
    overview = info.get("overview", "No synopsis available for this title.")
    director = info.get("director", "")
    top_cast = info.get("top_cast", "")
    genre_names = str(info.get("genre_names", ""))

    col_img, col_info = st.columns([1, 1.8], gap="medium")
    with col_img:
        try:
            st.image(poster_url, width="stretch")
        except TypeError:
            st.image(poster_url, use_container_width=True)
    with col_info:
        st.markdown(f"<h3 style='margin-top:0; color:#ffffff; font-weight:800;'>{title}</h3>", unsafe_allow_html=True)

        meta_items = []
        if year != "N/A":
            meta_items.append(f"<span style='color:#9ca3af;'>Year:</span> <strong style='color:#f3f4f6;'>{year}</strong>")
        if rating is not None and not pd.isna(rating):
            meta_items.append(f"<span style='color:#9ca3af;'>Rating:</span> <strong style='color:#f59e0b;'>★ {rating:.1f}/10</strong>")
        if meta_items:
            st.markdown(f"<div style='margin-bottom:0.8rem; font-size:0.92rem;'>{' &nbsp;|&nbsp; '.join(meta_items)}</div>", unsafe_allow_html=True)

        if genre_names and genre_names != "nan":
            genre_pills = " ".join([f"<span class='genre-pill'>{g.strip()}</span>" for g in genre_names.split(",") if g.strip()])
            st.markdown(f"<div style='margin-bottom:0.9rem;'>{genre_pills}</div>", unsafe_allow_html=True)

        if director and str(director) != "nan" and director != "N/A":
            st.markdown(f"<p style='margin:0.2rem 0; font-size:0.88rem;'><span style='color:#9ca3af;'>Director:</span> <strong style='color:#e5e7eb;'>{director}</strong></p>", unsafe_allow_html=True)

        if top_cast and str(top_cast) != "nan":
            st.markdown(f"<p style='margin:0.2rem 0; font-size:0.88rem;'><span style='color:#9ca3af;'>Starring:</span> <strong style='color:#e5e7eb;'>{top_cast}</strong></p>", unsafe_allow_html=True)

        st.markdown("<hr style='border-color: rgba(255,255,255,0.1); margin: 0.8rem 0;'>", unsafe_allow_html=True)
        st.markdown(f"<p style='color:#d1d5db; line-height:1.6; font-size:0.9rem;'>{overview}</p>", unsafe_allow_html=True)

# UI CHANGE: Professional CineVerse CSS styling with dark theme, responsive grid, and badge styling.
st.markdown("""
<style>
    /* Dark cinematic background */
    .stApp {
        background: radial-gradient(circle at 50% 0%, #111827 0%, #07090e 65%, #030407 100%);
        color: #f3f4f6;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }

    /* Container constraints */
    .main .block-container {
        max-width: 1200px;
        padding-top: 2rem;
        padding-bottom: 3.5rem;
    }

    /* Hero Header Branding */
    .hero-header {
        text-align: center;
        margin-bottom: 2rem;
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
        font-size: 3rem;
        font-weight: 900;
        letter-spacing: -0.5px;
        margin-bottom: 0.3rem;
        color: #ffffff;
        text-shadow: 0 2px 14px rgba(0,0,0,0.6);
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

    /* Streamlit Selectbox custom styling */
    div[data-baseweb="select"] {
        border-radius: 10px !important;
    }
    div[data-baseweb="select"] > div {
        background-color: #0d121c !important;
        border-color: rgba(255, 255, 255, 0.15) !important;
        color: #ffffff !important;
        border-radius: 10px !important;
        min-height: 48px !important;
    }
    div[data-baseweb="select"] * {
        color: #ffffff !important;
    }

    /* Primary Action Button */
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
    }

    div.stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 24px rgba(229, 9, 20, 0.55) !important;
        background: linear-gradient(135deg, #f40b17 0%, #c42028 100%) !important;
    }

    /* Card Details secondary buttons */
    .card-col div.stButton > button {
        background: rgba(255, 255, 255, 0.08) !important;
        color: #d1d5db !important;
        font-size: 0.82rem !important;
        font-weight: 500 !important;
        padding: 0.4rem 0.8rem !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        box-shadow: none !important;
        margin-top: 0.4rem !important;
        border-radius: 8px !important;
    }

    .card-col div.stButton > button:hover {
        background: rgba(229, 9, 20, 0.2) !important;
        color: #ffffff !important;
        border-color: rgba(255, 75, 75, 0.4) !important;
        transform: none !important;
        box-shadow: none !important;
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
        font-weight: 600;
        letter-spacing: 0.5px;
    }

    /* Movie Card Grid */
    div[data-testid="column"] {
        background: rgba(17, 24, 39, 0.65);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 14px;
        padding: 0.75rem;
        transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.3s ease, border-color 0.3s ease;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }

    div[data-testid="column"]:hover {
        transform: translateY(-6px);
        box-shadow: 0 16px 32px rgba(0, 0, 0, 0.65);
        border-color: rgba(255, 75, 75, 0.35);
    }

    div[data-testid="stImage"] img {
        border-radius: 10px;
        width: 100%;
        aspect-ratio: 2 / 3;
        object-fit: cover;
        box-shadow: 0 6px 14px rgba(0, 0, 0, 0.4);
    }

    /* Card Badge Top Row */
    .card-top-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.45rem;
        font-size: 0.72rem;
    }

    .card-rank {
        font-weight: 700;
        color: #ff4b4b;
        letter-spacing: 0.8px;
        text-transform: uppercase;
    }

    .card-score {
        font-weight: 600;
        color: #f59e0b;
        background: rgba(245, 158, 11, 0.12);
        padding: 0.15rem 0.45rem;
        border-radius: 4px;
    }

    /* Movie Title Styling */
    .movie-card-title {
        font-size: 0.92rem;
        font-weight: 600;
        color: #f3f4f6;
        text-align: center;
        margin-top: 0.65rem;
        margin-bottom: 0.15rem;
        line-height: 1.35;
        min-height: 2.7rem;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }

    .card-meta-year {
        text-align: center;
        font-size: 0.75rem;
        color: #9ca3af;
        margin-bottom: 0.4rem;
    }

    /* Genre Pill Badge */
    .genre-pill {
        display: inline-block;
        font-size: 0.72rem;
        padding: 0.2rem 0.6rem;
        border-radius: 6px;
        background: rgba(255, 75, 75, 0.12);
        color: #ff7575;
        border: 1px solid rgba(255, 75, 75, 0.25);
        font-weight: 500;
        margin-right: 0.35rem;
        margin-bottom: 0.35rem;
    }
</style>
""", unsafe_allow_html=True)

# CineVerse Header Branding
st.markdown("""
<div class="hero-header">
    <div class="hero-badge">Curated Recommendations</div>
    <div class="hero-title">CINE<span>VERSE</span></div>
    <p class="hero-tagline">Discover your next cinematic experience through content-based similarity analysis.</p>
</div>
""", unsafe_allow_html=True)

# Unified Hero Discovery Section
movies_titles = movies['title'].values

# Collect unique genres for the optional filter dropdown
available_genres = [
    "All Genres", "Action", "Adventure", "Animation", "Comedy", "Crime",
    "Drama", "Family", "Fantasy", "History", "Horror", "Music",
    "Mystery", "Romance", "Science Fiction", "Thriller", "War", "Western"
]

_, center_col, _ = st.columns([1, 4, 1])
with center_col:
    with st.container(border=True):
        st.markdown("<div style='font-size:0.95rem; font-weight:600; margin-bottom:0.4rem; color:#e5e7eb;'>Search or select a movie</div>", unsafe_allow_html=True)
        col_sel, col_gen = st.columns([3, 1.4])
        with col_sel:
            selected_movie_name = st.selectbox(
                "Movie Title",
                movies_titles,
                index=0,
                label_visibility="collapsed",
                help="Type to search among 4,800+ movies"
            )
        with col_gen:
            selected_genre = st.selectbox(
                "Genre Filter",
                available_genres,
                index=0,
                label_visibility="collapsed",
                help="Filter recommendations by genre"
            )
        st.markdown("<div style='height: 0.4rem;'></div>", unsafe_allow_html=True)
        recommend_button = st.button("DISCOVER SIMILAR MOVIES")

# Session state management to keep recommendations persistent during card interactions
if recommend_button:
    with st.spinner("Analyzing similarity vectors and curating recommendations..."):
        rec_names, rec_posters = recommend(selected_movie_name, selected_genre)
        rec_ids = [movies[movies['title'] == n].iloc[0].movie_id for n in rec_names]
        st.session_state["cineverse_results"] = {
            "selected_movie": selected_movie_name,
            "selected_genre": selected_genre,
            "names": rec_names,
            "posters": rec_posters,
            "ids": rec_ids
        }

if "cineverse_results" in st.session_state:
    res = st.session_state["cineverse_results"]
    selected_name = res["selected_movie"]
    active_genre = res.get("selected_genre", "All Genres")
    names = res["names"]
    posters = res["posters"]
    ids = res["ids"]

    genre_note = f" &bull; <em>{active_genre}</em>" if active_genre != "All Genres" else ""
    st.markdown(f"""
    <div class="results-heading">
        <div class="results-title">Recommended For You <span style="color: #9ca3af; font-size: 0.95rem; font-weight: 400;">based on <em>{selected_name}</em>{genre_note}</span></div>
        <div class="results-badge">TOP 5 MATCHES</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3, col4, col5 = st.columns(5)
    cols = [col1, col2, col3, col4, col5]

    for idx, col in enumerate(cols):
        m_id = ids[idx]
        m_title = names[idx]
        m_poster = posters[idx]
        m_meta = movie_metadata.get(m_id, {})
        rel_date = str(m_meta.get("release_date", ""))
        year_str = rel_date[:4] if len(rel_date) >= 4 else ""
        vote_avg = m_meta.get("vote_average", None)

        with col:
            st.markdown('<div class="card-col">', unsafe_allow_html=True)
            rating_html = f"<span class='card-score'>★ {vote_avg:.1f}</span>" if (vote_avg is not None and not pd.isna(vote_avg)) else ""
            st.markdown(f"""
            <div class="card-top-row">
                <span class="card-rank">MATCH #{idx+1}</span>
                {rating_html}
            </div>
            """, unsafe_allow_html=True)

            try:
                st.image(m_poster, width="stretch")
            except TypeError:
                st.image(m_poster, use_container_width=True)

            st.markdown(f'<div class="movie-card-title" title="{m_title}">{m_title}</div>', unsafe_allow_html=True)
            if year_str:
                st.markdown(f'<div class="card-meta-year">{year_str}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="card-meta-year">&nbsp;</div>', unsafe_allow_html=True)

            if st.button("Overview", key=f"details_btn_{idx}"):
                show_movie_details(m_id, m_title, m_poster)

            st.markdown('</div>', unsafe_allow_html=True)
