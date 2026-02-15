# app/ai/__init__.py

"""
AI Pipeline package for Legalyze.

Provides NLP, transformer models, embeddings, and RAG capabilities.
"""

from app.ai.nlp_pipeline import (
    load_spacy_model,
    get_nlp,
    segment_sentences,
    tokenize,
    extract_noun_phrases,
    compute_similarity,
    extract_keywords,
    compute_text_statistics
)

from app.ai.transformer_model import (
    load_model,
    generate_text,
    summarize_text,
    answer_question,
    classify_text,
    get_device,
    clear_model_cache
)

from app.ai.embeddings import (
    load_embedding_model,
    get_embedding_model,
    encode_text,
    compute_similarity as compute_embedding_similarity,
    semantic_search,
    cluster_texts,
    get_embedding_dimension,
    clear_embedding_cache
)

from app.ai.rag_pipeline import (
    build_vector_store,
    load_vector_store,
    save_vector_store,
    retrieve_context,
    is_vector_store_ready,
    add_documents_to_store,
    initialize_legal_knowledge_base
)

from app.ai.prompt_templates import (
    build_suggestion_prompt,
    build_regeneration_prompt,
    build_simplification_prompt,
    build_summary_prompt,
    build_risk_explanation_prompt
)

__all__ = [
    # NLP
    "load_spacy_model",
    "get_nlp",
    "segment_sentences",
    "tokenize",
    "extract_noun_phrases",
    "compute_similarity",
    "extract_keywords",
    "compute_text_statistics",
    
    # Transformers
    "load_model",
    "generate_text",
    "summarize_text",
    "answer_question",
    "classify_text",
    "get_device",
    "clear_model_cache",
    
    # Embeddings
    "load_embedding_model",
    "get_embedding_model",
    "encode_text",
    "compute_embedding_similarity",
    "semantic_search",
    "cluster_texts",
    "get_embedding_dimension",
    "clear_embedding_cache",
    
    # RAG
    "build_vector_store",
    "load_vector_store",
    "save_vector_store",
    "retrieve_context",
    "is_vector_store_ready",
    "add_documents_to_store",
    "initialize_legal_knowledge_base",
    
    # Prompts
    "build_suggestion_prompt",
    "build_regeneration_prompt",
    "build_simplification_prompt",
    "build_summary_prompt",
    "build_risk_explanation_prompt"
]