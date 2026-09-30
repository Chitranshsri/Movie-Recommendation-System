# 🎬 CineVerse — Intelligent Movie Recommender System

A modern, cinematic movie recommendation web application built with **Python**, **Streamlit**, and **Scikit-Learn**, powered by content-based filtering and the **TMDB (The Movie Database) API**.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.64.0-red?logo=streamlit)
![Pandas](https://img.shields.io/badge/Pandas-DataFrames-yellow?logo=pandas)
![NumPy](https://img.shields.io/badge/NumPy-Vectors-blue?logo=numpy)

---

## 🌟 Key Features

- **Content-Based Filtering**: Recommends movies using cosine similarity on precomputed vector embeddings (genres, keywords, cast, crew, and overview).
- **Cinematic Dark UI**: Modern streaming-platform visual aesthetic with responsive movie cards, hover elevations, and clean typography.
- **Dynamic Poster Fetching**: High-resolution movie posters retrieved dynamically via the TMDB API.
- **Fault-Tolerant & Resilient**: Graceful error handling and fallback placeholders for missing posters, network timeouts, or invalid entries.
- **Streamlit Caching**: Optimized in-memory caching for instant model loading and fast user interactions.

---

## 🚀 Quick Start (Local Setup)

### 1. Clone the Repository

```bash
git clone https://github.com/Chitranshsri/movie-recommendr-system.git
cd movie-recommendr-system
```

### 2. Create and Activate a Virtual Environment

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure TMDB API Key

Create a `.streamlit/secrets.toml` file in the project root:

```toml
TMDB_API_KEY = "your_tmdb_api_key_here"
```

*(You can obtain a free API key from [The Movie Database](https://www.themoviedb.org/settings/api)).*

### 5. Launch the Application

```bash
streamlit run app.py
```

The application will automatically open at `http://localhost:8501`.

---

## ☁️ Deployment (Streamlit Community Cloud)

1. Fork or push this repository to your GitHub account.
2. Ensure `movies.pkl` and `similarity.pkl` are tracked with **Git LFS** (`git lfs install && git lfs track "*.pkl"`).
3. Log in to [Streamlit Community Cloud](https://share.streamlit.io/) and create a **New App**.
4. Select your repository, branch (`main`), and set the main file path to `app.py`.
5. Under **App Settings -> Secrets**, add:
   ```toml
   TMDB_API_KEY = "your_tmdb_api_key_here"
   ```
6. Click **Deploy**!

---

## 🛠️ Project Structure

```text
movie-recommendr-system/
├── .streamlit/
│   └── secrets.toml          # Local secrets (ignored by Git)
├── app.py                    # Main Streamlit application
├── movies.pkl                # Processed movie metadata (DataFrame)
├── similarity.pkl            # Precomputed cosine similarity matrix
├── requirements.txt          # Python dependencies
├── .gitignore                # Git ignore configuration
├── .gitattributes            # Git LFS tracking rules
└── README.md                 # Project documentation
```

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).
