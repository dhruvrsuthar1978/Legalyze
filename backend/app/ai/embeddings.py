# app/ai/embeddings.py

from sentence_transformers import SentenceTransformer
from typing import List, Union, Optional
import numpy as np
import torch
import logging

logger = logging.getLogger("legalyze.embeddings")

# ── Global Model Cache ────────────────────────────────────────────
_embedding_model: Optional[SentenceTransformer] = None


# ══════════════════════════════════════════════════════════════════
# LOAD EMBEDDING MODEL
# ══════════════════════════════════════════════════════════════════

def load_embedding_model(
    model_name: str = "all-MiniLM-L6-v2"
) -> SentenceTransformer:
    """
    Loads a sentence transformer model for embeddings.
    
    Recommended models:
    - all-MiniLM-L6-v2: Fast, 384 dim (default) ✅
    - all-mpnet-base-v2: Accurate, 768 dim
    - multi-qa-mpnet-base-dot-v1: QA optimized, 768 dim
    - paraphrase-multilingual-mpnet-base-v2: Multilingual, 768 dim
    
    Returns:
        SentenceTransformer model
    """
    global _embedding_model
    
    if _embedding_model is not None:
        logger.info(f"Embedding model already loaded: {model_name}")
        return _embedding_model
    
    logger.info(f"Loading embedding model: {model_name}")
    
    try:
        # Detect device
        device = "cuda" if torch.cuda.is_available() else "cpu"
        
        model = SentenceTransformer(model_name, device=device)
        
        logger.info(
            f"✅ Embedding model loaded | "
            f"model={model_name}, "
            f"dimensions={model.get_sentence_embedding_dimension()}, "
            f"device={device}"
        )
        
        _embedding_model = model
        return _embedding_model
    
    except Exception as e:
        logger.error(f"Failed to load embedding model: {e}")
        raise


def get_embedding_model() -> SentenceTransformer:
    """
    Returns the loaded embedding model.
    Lazy-loads if not already loaded.
    """
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = load_embedding_model()
    return _embedding_model


# ══════════════════════════════════════════════════════════════════
# GENERATE EMBEDDINGS
# ══════════════════════════════════════════════════════════════════

def encode_text(
    text: Union[str, List[str]],
    normalize: bool = True,
    batch_size: int = 32,
    show_progress_bar: bool = False
) -> np.ndarray:
    """
    Converts text to vector embeddings.
    
    Args:
        text: Single text string or list of strings
        normalize: Whether to normalize vectors to unit length
        batch_size: Batch size for encoding
        show_progress_bar: Show encoding progress
    
    Returns:
        numpy array of embeddings
        - Single text: shape (embedding_dim,)
        - List of texts: shape (num_texts, embedding_dim)
    """
    model = get_embedding_model()
    
    logger.debug(
        f"Encoding text | "
        f"inputs={1 if isinstance(text, str) else len(text)}"
    )
    
    try:
        embeddings = model.encode(
            text,
            normalize_embeddings=normalize,
            batch_size=batch_size,
            show_progress_bar=show_progress_bar,
            convert_to_numpy=True
        )
        
        logger.debug(
            f"Embeddings generated | "
            f"shape={embeddings.shape}"
        )
        
        return embeddings
    
    except Exception as e:
        logger.error(f"Encoding failed: {e}")
        raise


# ══════════════════════════════════════════════════════════════════
# SIMILARITY COMPUTATION
# ══════════════════════════════════════════════════════════════════

def compute_similarity(
    text1: Union[str, np.ndarray],
    text2: Union[str, np.ndarray],
    metric: str = "cosine"
) -> float:
    """
    Computes similarity between two texts or embeddings.
    
    Args:
        text1: First text or embedding
        text2: Second text or embedding
        metric: "cosine" or "dot"
    
    Returns:
        Similarity score (0.0 to 1.0 for cosine, unbounded for dot)
    """
    # Encode texts if needed
    if isinstance(text1, str):
        emb1 = encode_text(text1, normalize=(metric == "cosine"))
    else:
        emb1 = text1
    
    if isinstance(text2, str):
        emb2 = encode_text(text2, normalize=(metric == "cosine"))
    else:
        emb2 = text2
    
    # Compute similarity
    if metric == "cosine":
        # Cosine similarity (assumes normalized vectors)
        similarity = float(np.dot(emb1, emb2))
    else:  # dot product
        similarity = float(np.dot(emb1, emb2))
    
    return similarity


def compute_similarity_matrix(
    texts: List[str],
    metric: str = "cosine"
) -> np.ndarray:
    """
    Computes pairwise similarity matrix for a list of texts.
    
    Args:
        texts: List of texts
        metric: "cosine" or "dot"
    
    Returns:
        Square matrix of shape (n, n) where entry [i,j] is similarity(texts[i], texts[j])
    """
    embeddings = encode_text(texts, normalize=(metric == "cosine"))
    
    # Compute similarity matrix
    similarity_matrix = np.dot(embeddings, embeddings.T)
    
    return similarity_matrix


# ══════════════════════════════════════════════════════════════════
# SEMANTIC SEARCH
# ══════════════════════════════════════════════════════════════════

def semantic_search(
    query: str,
    corpus: List[str],
    top_k: int = 5
) -> List[dict]:
    """
    Performs semantic search to find most similar texts in corpus.
    
    Args:
        query: Query text
        corpus: List of texts to search
        top_k: Number of top results to return
    
    Returns:
        List of dicts with 'corpus_id', 'score', 'text'
    """
    model = get_embedding_model()
    
    logger.debug(
        f"Semantic search | "
        f"query_length={len(query)}, "
        f"corpus_size={len(corpus)}, "
        f"top_k={top_k}"
    )
    
    try:
        # Encode query
        query_emb = encode_text(query, normalize=True)
        
        # Encode corpus
        corpus_embs = encode_text(corpus, normalize=True, batch_size=64)
        
        # Compute similarities
        similarities = np.dot(corpus_embs, query_emb)
        
        # Get top-k indices
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        # Build results
        results = [
            {
                "corpus_id": int(idx),
                "score": float(similarities[idx]),
                "text": corpus[idx]
            }
            for idx in top_indices
        ]
        
        logger.debug(
            f"Search complete | "
            f"top_score={results[0]['score']:.3f}"
        )
        
        return results
    
    except Exception as e:
        logger.error(f"Semantic search failed: {e}")
        raise


# ══════════════════════════════════════════════════════════════════
# CLUSTERING
# ══════════════════════════════════════════════════════════════════

def cluster_texts(
    texts: List[str],
    num_clusters: int = 5,
    min_community_size: int = 2
) -> List[List[int]]:
    """
    Clusters texts using community detection on similarity graph.
    
    Args:
        texts: List of texts to cluster
        num_clusters: Approximate number of clusters (ignored if using community detection)
        min_community_size: Minimum size of a cluster
    
    Returns:
        List of clusters, where each cluster is a list of text indices
    """
    from sklearn.cluster import AgglomerativeClustering
    
    # Encode texts
    embeddings = encode_text(texts, normalize=True)
    
    # Perform clustering
    clustering_model = AgglomerativeClustering(
        n_clusters=num_clusters,
        metric="cosine",
        linkage="average"
    )
    
    cluster_labels = clustering_model.fit_predict(embeddings)
    
    # Group by cluster
    clusters = {}
    for idx, label in enumerate(cluster_labels):
        if label not in clusters:
            clusters[label] = []
        clusters[label].append(idx)
    
    # Filter by minimum size
    filtered_clusters = [
        cluster for cluster in clusters.values()
        if len(cluster) >= min_community_size
    ]
    
    logger.info(
        f"Clustering complete | "
        f"texts={len(texts)}, "
        f"clusters={len(filtered_clusters)}"
    )
    
    return filtered_clusters


# ══════════════════════════════════════════════════════════════════
# UTILITIES
# ══════════════════════════════════════════════════════════════════

def get_embedding_dimension() -> int:
    """
    Returns the dimensionality of the embedding model.
    """
    model = get_embedding_model()
    return model.get_sentence_embedding_dimension()


def clear_embedding_cache():
    """
    Clears the cached embedding model to free memory.
    """
    global _embedding_model
    
    logger.info("Clearing embedding model cache...")
    
    _embedding_model = None
    
    # Force garbage collection
    import gc
    gc.collect()
    
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    
    logger.info("✅ Embedding cache cleared")