# app/ai/rag_pipeline.py

import faiss
import numpy as np
import pickle
import os
from typing import List, Dict, Optional, Tuple
from app.ai.embeddings import encode_text, get_embedding_dimension
import logging

logger = logging.getLogger("legalyze.rag")

# ── Configuration ─────────────────────────────────────────────────
VECTOR_STORE_DIR = "vector_store"
INDEX_FILE = os.path.join(VECTOR_STORE_DIR, "faiss_index.bin")
DOCUMENTS_FILE = os.path.join(VECTOR_STORE_DIR, "documents.pkl")

# ── Global Index ──────────────────────────────────────────────────
_faiss_index: Optional[faiss.Index] = None
_documents: Optional[List[str]] = None


# ══════════════════════════════════════════════════════════════════
# BUILD VECTOR STORE
# ══════════════════════════════════════════════════════════════════

def build_vector_store(
    documents: List[str],
    save_path: Optional[str] = None
) -> Tuple[faiss.Index, List[str]]:
    """
    Builds a FAISS vector store from a list of documents.
    
    Args:
        documents: List of text documents
        save_path: Directory to save index (optional)
    
    Returns:
        Tuple of (faiss_index, documents)
    """
    logger.info(f"Building vector store | documents={len(documents)}")
    
    # Get embedding dimension
    embedding_dim = get_embedding_dimension()
    
    # Encode all documents
    logger.info("Encoding documents...")
    embeddings = encode_text(
        documents,
        normalize=True,
        batch_size=64,
        show_progress_bar=True
    )
    
    # Create FAISS index
    # Using IndexFlatIP for cosine similarity (requires normalized vectors)
    logger.info("Creating FAISS index...")
    index = faiss.IndexFlatIP(embedding_dim)
    
    # Add vectors to index
    index.add(embeddings.astype(np.float32))
    
    logger.info(
        f"✅ Vector store built | "
        f"documents={len(documents)}, "
        f"dimension={embedding_dim}, "
        f"total_vectors={index.ntotal}"
    )
    
    # Save index
    if save_path:
        save_vector_store(index, documents, save_path)
    
    return index, documents


# ══════════════════════════════════════════════════════════════════
# SAVE/LOAD VECTOR STORE
# ══════════════════════════════════════════════════════════════════

def save_vector_store(
    index: faiss.Index,
    documents: List[str],
    save_dir: str = VECTOR_STORE_DIR
):
    """
    Saves FAISS index and documents to disk.
    """
    os.makedirs(save_dir, exist_ok=True)
    
    index_path = os.path.join(save_dir, "faiss_index.bin")
    docs_path = os.path.join(save_dir, "documents.pkl")
    
    # Save FAISS index
    faiss.write_index(index, index_path)
    
    # Save documents
    with open(docs_path, "wb") as f:
        pickle.dump(documents, f)
    
    logger.info(
        f"✅ Vector store saved | "
        f"index={index_path}, "
        f"documents={docs_path}"
    )


def load_vector_store(
    load_dir: str = VECTOR_STORE_DIR
) -> Tuple[faiss.Index, List[str]]:
    """
    Loads FAISS index and documents from disk.
    
    Returns:
        Tuple of (faiss_index, documents)
    """
    global _faiss_index, _documents
    
    # Check cache
    if _faiss_index is not None and _documents is not None:
        logger.info("Vector store already loaded from cache")
        return _faiss_index, _documents
    
    index_path = os.path.join(load_dir, "faiss_index.bin")
    docs_path = os.path.join(load_dir, "documents.pkl")
    
    if not os.path.exists(index_path) or not os.path.exists(docs_path):
        raise FileNotFoundError(
            f"Vector store not found at {load_dir}. "
            f"Build it first using build_vector_store()."
        )
    
    logger.info(f"Loading vector store from {load_dir}")
    
    # Load FAISS index
    index = faiss.read_index(index_path)
    
    # Load documents
    with open(docs_path, "rb") as f:
        documents = pickle.load(f)
    
    logger.info(
        f"✅ Vector store loaded | "
        f"vectors={index.ntotal}, "
        f"documents={len(documents)}"
    )
    
    # Cache
    _faiss_index = index
    _documents = documents
    
    return index, documents


# ══════════════════════════════════════════════════════════════════
# RETRIEVE CONTEXT
# ══════════════════════════════════════════════════════════════════

def retrieve_context(
    query: str,
    top_k: int = 5,
    min_similarity: float = 0.3
) -> Dict[str, any]:
    """
    Retrieves relevant documents for a given query.
    
    Args:
        query: Query text
        top_k: Number of documents to retrieve
        min_similarity: Minimum similarity threshold (0.0 to 1.0)
    
    Returns:
        Dict with 'docs', 'scores'
    """
    try:
        index, documents = load_vector_store()
    except FileNotFoundError:
        logger.warning("Vector store not loaded — returning empty results")
        return {"docs": [], "scores": []}
    
    logger.debug(
        f"Retrieving context | "
        f"query_length={len(query)}, "
        f"top_k={top_k}"
    )
    
    try:
        # Encode query
        query_emb = encode_text(query, normalize=True)
        query_emb = query_emb.reshape(1, -1).astype(np.float32)
        
        # Search index
        scores, indices = index.search(query_emb, top_k)
        
        # Extract results
        scores = scores[0].tolist()
        indices = indices[0].tolist()
        
        # Filter by minimum similarity
        results = [
            (documents[idx], score)
            for idx, score in zip(indices, scores)
            if idx >= 0 and score >= min_similarity
        ]
        
        # Sort by score descending
        results.sort(key=lambda x: x[1], reverse=True)
        
        docs = [doc for doc, _ in results]
        scores = [score for _, score in results]
        
        logger.debug(
            f"Context retrieved | "
            f"results={len(docs)}, "
            f"top_score={scores[0] if scores else 0:.3f}"
        )
        
        return {
            "docs": docs,
            "scores": scores
        }
    
    except Exception as e:
        logger.error(f"Context retrieval failed: {e}")
        return {"docs": [], "scores": []}


# ══════════════════════════════════════════════════════════════════
# CHECK IF VECTOR STORE IS READY
# ══════════════════════════════════════════════════════════════════

def is_vector_store_ready() -> bool:
    """
    Checks if vector store is loaded and ready for retrieval.
    """
    return (
        os.path.exists(INDEX_FILE) and
        os.path.exists(DOCUMENTS_FILE)
    )


# ══════════════════════════════════════════════════════════════════
# ADD DOCUMENTS TO EXISTING INDEX
# ══════════════════════════════════════════════════════════════════

def add_documents_to_store(new_documents: List[str]):
    """
    Adds new documents to an existing vector store.
    
    Args:
        new_documents: List of new documents to add
    """
    index, documents = load_vector_store()
    
    logger.info(f"Adding {len(new_documents)} documents to vector store")
    
    # Encode new documents
    new_embeddings = encode_text(
        new_documents,
        normalize=True,
        batch_size=64
    )
    
    # Add to index
    index.add(new_embeddings.astype(np.float32))
    
    # Append to documents list
    documents.extend(new_documents)
    
    # Save updated store
    save_vector_store(index, documents)
    
    # Update cache
    global _faiss_index, _documents
    _faiss_index = index
    _documents = documents
    
    logger.info(
        f"✅ Documents added | "
        f"new={len(new_documents)}, "
        f"total={len(documents)}"
    )


# ══════════════════════════════════════════════════════════════════
# INITIALIZE WITH LEGAL KNOWLEDGE BASE
# ══════════════════════════════════════════════════════════════════

def initialize_legal_knowledge_base():
    """
    Initializes the vector store with a default legal knowledge base.
    
    This is a sample implementation. In production, you would:
    1. Scrape legal databases (CaseLaw, Cornell LII, etc.)
    2. Parse legal textbooks and treatises
    3. Collect contract templates
    4. Add domain-specific knowledge
    """
    logger.info("Initializing legal knowledge base...")
    
    # Sample legal knowledge (replace with actual legal corpus)
    legal_documents = [
        # Contract law principles
        "A contract is a legally binding agreement between two or more parties that creates mutual obligations enforceable by law.",
        "Consideration is something of value exchanged between parties to a contract, making the agreement legally enforceable.",
        "An offer and acceptance are required for a valid contract formation.",
        
        # Confidentiality
        "Confidentiality clauses protect sensitive information from unauthorized disclosure to third parties.",
        "Non-disclosure agreements (NDAs) should specify the duration of confidentiality obligations and permitted disclosures.",
        
        # Payment terms
        "Payment terms should clearly specify amounts, due dates, and acceptable payment methods.",
        "Late payment penalties must be reasonable and proportionate to avoid being deemed unenforceable penalty clauses.",
        
        # Termination
        "Termination clauses should specify grounds for termination, notice periods, and consequences of termination.",
        "Material breach typically allows for immediate termination, while minor breaches may require cure periods.",
        
        # Liability
        "Limitation of liability clauses cap damages but typically cannot exclude liability for fraud, gross negligence, or death/personal injury.",
        "Indemnification clauses require one party to compensate the other for specified losses or damages.",
        
        # IP Rights
        "Work-for-hire agreements transfer intellectual property ownership from creator to commissioning party.",
        "License agreements grant permission to use intellectual property while retaining ownership.",
        
        # Dispute Resolution
        "Arbitration clauses require disputes to be resolved through arbitration rather than litigation.",
        "Mediation is a non-binding dispute resolution process facilitated by a neutral third party.",
        
        # Force Majeure
        "Force majeure clauses excuse non-performance due to unforeseeable circumstances beyond parties' control.",
        "Force majeure events typically include natural disasters, war, pandemics, and government actions.",
        
        # General principles
        "Contracts should be interpreted according to their plain meaning and the parties' intent.",
        "Ambiguities in contracts are typically construed against the drafter.",
        "Severability clauses ensure that if one provision is unenforceable, the remainder of the contract remains valid."
    ]
    
    # Build vector store
    build_vector_store(legal_documents, save_path=VECTOR_STORE_DIR)
    
    logger.info("✅ Legal knowledge base initialized")