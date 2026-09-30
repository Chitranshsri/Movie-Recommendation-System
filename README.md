# CineVerse

CineVerse is a content-based movie recommendation web application built with Python and Streamlit. It leverages vectorized textual metadata and cosine similarity to recommend films based on user selection, integrating with The Movie Database (TMDB) API to render dynamic poster art and verified metadata.

## Features

- Content-Based Filtering: Computes pairwise cosine similarity over preprocessed tags comprising genres, keywords, overview, top cast members, and director.
- Cinematic User Interface: Modern dark layout featuring responsive cards, match rankings, and interactive overview modals.
- Authentic Metadata: Integrates TMDB API and dataset attributes for verified release dates, vote averages, and synopses without fabricated data.
- Resilient API Architecture: Features request timeouts, connection session pooling, and graceful fallback handling for missing posters or network interruptions.
- In-Memory Caching: Utilizes Streamlit resource and data caching for efficient model loading and minimal API overhead.

## How It Works

1. Feature Engineering: The TMDB 5,000 Movies and Credits datasets are merged on title. Selected features (overview, genres, keywords, cast, and crew) are normalized, tokenized, and stemmed into unified tag strings.
2. Vectorization: A CountVectorizer constructs a 5,000-dimensional bag-of-words representation for each film.
3. Similarity Matrix: Pairwise cosine similarity is computed across all 4,806 titles, generating a 4,806 x 4,806 similarity matrix.
4. Recommendation Retrieval: When a movie is selected, the application retrieves its similarity vector, sorts top distance scores in descending order, and extracts the top five matches.
5. Poster & Metadata Resolution: The application retrieves official posters via TMDB API endpoints and pulls synopses from verified dataset records.

## Tech Stack

- Application Framework: Streamlit
- Machine Learning & Vectorization: Scikit-Learn, NumPy
- Data Manipulation: Pandas
- API Communication: Requests
- Serialization: Pickle

## Project Structure

```text
CineVerse/
├── .streamlit/
│   └── secrets.toml              # Local secrets configuration (git-ignored)
├── app.py                        # Streamlit web application
├── Movie-Recommender-System.ipynb# Preprocessing and vectorization notebook
├── movies.pkl                    # Serialized DataFrame containing processed titles and tags
├── similarity.pkl                # Serialized cosine similarity matrix (float64)
├── tmdb_5000_movies.csv          # Metadata dataset for verified movie details
├── requirements.txt              # Production dependencies
├── .gitignore                    # Version control ignore rules
├── .gitattributes                # Git LFS tracking rules
└── README.md                     # Technical documentation
```

## Dataset / Model

- Primary Datasets: TMDB 5,000 Movies Dataset and TMDB 5,000 Credits Dataset.
- Total Titles: 4,806 unique films.
- Matrix Dimensions: 4,806 x 4,806 cosine similarity matrix stored in similarity.pkl.
- Precision: Standard float64 precision preserved to guarantee mathematical accuracy.

## Installation

### 1. Clone Repository

```bash
git clone https://github.com/Chitranshsri/CineVerse.git
cd CineVerse
```

### 2. Configure Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

## Running Locally

1. Create a `.streamlit/secrets.toml` file in the root directory:

```toml
TMDB_API_KEY = "your_tmdb_api_key_here"
```

2. Run the application:

```bash
streamlit run app.py
```

The application will launch at `http://localhost:8501`.

## Deployment

For deployment on Streamlit Community Cloud:

1. Push the repository to GitHub. Ensure `similarity.pkl` and `movies.pkl` are tracked with Git LFS (`git lfs install && git lfs track "*.pkl"`).
2. Connect your GitHub repository to Streamlit Community Cloud (`share.streamlit.io`).
3. Set the main file path to `app.py`.
4. Under App Settings -> Secrets, provide your TMDB credentials:

```toml
TMDB_API_KEY = "your_tmdb_api_key_here"
```

5. Deploy.

## Notebook

The Jupyter notebook `Movie-Recommender-System.ipynb` is included in the root directory. It contains the end-to-end data ingestion, merging, natural language preprocessing, stemming, vectorization, and model serialization steps.

## Author

Chitranshsri
