"""
AI Engine: Semantic search + content-based recommendation using TF-IDF + cosine similarity.
Falls back gracefully if sentence-transformers not available.
"""
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import normalize
import pickle, os, re

CACHE_DIR = ".cache"
os.makedirs(CACHE_DIR, exist_ok=True)

_vectorizer = None
_tfidf_matrix = None
_book_ids = None
_df_global = None

def _clean_text(text: str) -> str:
    text = str(text).lower()
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def build_search_index(df: pd.DataFrame):
    global _vectorizer, _tfidf_matrix, _book_ids, _df_global
    _df_global = df.copy()
    # Combine fields for richer embeddings
    df["search_text"] = (
        df["title"].fillna("") + " " +
        df["authors"].fillna("") + " " +
        df["categories"].fillna("") + " " +
        df["description"].fillna("").str[:300]
    ).apply(_clean_text)

    cache_v = os.path.join(CACHE_DIR, "vectorizer.pkl")
    cache_m = os.path.join(CACHE_DIR, "tfidf_matrix.npy")
    cache_i = os.path.join(CACHE_DIR, "book_ids.pkl")

    if os.path.exists(cache_v) and os.path.exists(cache_m):
        with open(cache_v, "rb") as f:
            _vectorizer = pickle.load(f)
        _tfidf_matrix = np.load(cache_m)
        with open(cache_i, "rb") as f:
            _book_ids = pickle.load(f)
    else:
        _vectorizer = TfidfVectorizer(
            max_features=8000,
            ngram_range=(1, 2),
            stop_words="english",
            min_df=1
        )
        _tfidf_matrix = _vectorizer.fit_transform(df["search_text"]).toarray()
        _tfidf_matrix = normalize(_tfidf_matrix)
        _book_ids = df["book_id"].tolist()
        with open(cache_v, "wb") as f:
            pickle.dump(_vectorizer, f)
        np.save(cache_m, _tfidf_matrix)
        with open(cache_i, "wb") as f:
            pickle.dump(_book_ids, f)

def semantic_search(query: str, top_k: int = 10, category_filter: str = None) -> list:
    global _vectorizer, _tfidf_matrix, _book_ids, _df_global
    if _vectorizer is None or _tfidf_matrix is None:
        return []
    q_clean = _clean_text(query)
    q_vec = _vectorizer.transform([q_clean]).toarray()
    q_vec = normalize(q_vec)
    scores = cosine_similarity(q_vec, _tfidf_matrix)[0]
    top_idx = np.argsort(scores)[::-1]

    results = []
    for idx in top_idx:
        if scores[idx] < 0.01:
            break
        if len(results) >= top_k:
            break
        row = _df_global.iloc[idx]
        if category_filter and category_filter.lower() not in str(row.get("categories","")).lower():
            continue
        results.append({
            "book_id": row["book_id"],
            "title": row["title"],
            "authors": row["authors"],
            "categories": row["categories"],
            "description": str(row.get("description",""))[:200],
            "average_rating": row.get("average_rating", 0),
            "thumbnail": row.get("thumbnail",""),
            "score": round(float(scores[idx]), 3),
        })
    return results

def get_recommendations(user_categories: list, exclude_ids: list = None, top_k: int = 8) -> list:
    """Content-based recommendation from user's reading history categories."""
    global _vectorizer, _tfidf_matrix, _book_ids, _df_global
    if _vectorizer is None or _df_global is None:
        return []
    if not user_categories:
        # Return popular books
        df = _df_global.copy()
        df = df[~df["book_id"].isin(exclude_ids or [])]
        df = df.sort_values("ratings_count", ascending=False).head(top_k)
        return df[["book_id","title","authors","categories","thumbnail","average_rating","description"]].to_dict("records")

    query = " ".join(user_categories[:10])
    results = semantic_search(query, top_k=top_k + len(exclude_ids or []))
    return [r for r in results if r["book_id"] not in (exclude_ids or [])][:top_k]

def get_similar_books(book_id: str, top_k: int = 6) -> list:
    """Find books similar to a given book."""
    global _vectorizer, _tfidf_matrix, _book_ids, _df_global
    if _vectorizer is None or _book_ids is None:
        return []
    try:
        idx = _book_ids.index(book_id)
    except ValueError:
        return []
    book_vec = _tfidf_matrix[idx:idx+1]
    scores = cosine_similarity(book_vec, _tfidf_matrix)[0]
    top_idx = np.argsort(scores)[::-1]
    results = []
    for i in top_idx:
        if i == idx:
            continue
        if len(results) >= top_k:
            break
        row = _df_global.iloc[i]
        results.append({
            "book_id": row["book_id"],
            "title": row["title"],
            "authors": row["authors"],
            "categories": row["categories"],
            "thumbnail": row.get("thumbnail",""),
            "average_rating": row.get("average_rating", 0),
            "score": round(float(scores[i]), 3),
        })
    return results

# ── Multilingual query translation (basic) ───────────────────────────────────
LANG_MAP = {
    # Amharic transliterations → English hints
    "መጽሐፍ": "book",
    "ፍለጋ": "search",
}

def preprocess_multilingual_query(query: str) -> str:
    """Basic multilingual support: pass through, AI chatbot handles translation."""
    return query
