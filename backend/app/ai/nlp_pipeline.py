# app/ai/nlp_pipeline.py

import spacy
from spacy.language import Language
from typing import List, Dict, Optional, Tuple
import logging

logger = logging.getLogger("legalyze.nlp")

# ── Global spaCy Model ────────────────────────────────────────────
_nlp: Optional[Language] = None


# ══════════════════════════════════════════════════════════════════
# LOAD SPACY MODEL
# ══════════════════════════════════════════════════════════════════

def load_spacy_model(model_name: str = "en_core_web_lg") -> Language:
    """
    Loads and configures the spaCy NLP model.
    
    Model options:
    - en_core_web_sm: Small, fast (11 MB)
    - en_core_web_md: Medium, balanced (40 MB)
    - en_core_web_lg: Large, accurate (560 MB) ← Recommended
    - en_core_web_trf: Transformer-based, most accurate (438 MB)
    
    Returns:
        Configured spaCy Language pipeline
    """
    global _nlp
    
    if _nlp is not None:
        logger.info(f"spaCy model already loaded: {model_name}")
        return _nlp
    
    try:
        logger.info(f"Loading spaCy model: {model_name}")
        nlp = spacy.load(model_name)
        
        # Configure pipeline
        # Disable components we don't need for performance
        nlp.disable_pipes(["ner", "lemmatizer"])  # We only need tokenization and sentence boundary detection
        
        # Increase max_length for long contracts
        nlp.max_length = 2_000_000  # 2 million characters
        
        logger.info(
            f"✅ spaCy model loaded successfully | "
            f"pipeline={nlp.pipe_names}, "
            f"max_length={nlp.max_length}"
        )
        
        _nlp = nlp
        return _nlp
    
    except OSError as e:
        logger.error(
            f"Failed to load spaCy model '{model_name}'. "
            f"Install with: python -m spacy download {model_name}"
        )
        raise RuntimeError(f"spaCy model not found: {model_name}") from e


def get_nlp() -> Language:
    """
    Returns the loaded spaCy model.
    Lazy-loads if not already loaded.
    """
    global _nlp
    if _nlp is None:
        _nlp = load_spacy_model()
    return _nlp


# ══════════════════════════════════════════════════════════════════
# SENTENCE SEGMENTATION
# ══════════════════════════════════════════════════════════════════

def segment_sentences(text: str) -> List[str]:
    """
    Splits text into sentences using spaCy's sentence boundary detection.
    
    Args:
        text: Input text to segment
    
    Returns:
        List of sentence strings
    
    spaCy's sentence segmentation is superior to simple regex splitting
    because it handles:
    - Abbreviations (Dr., Inc., etc.)
    - Decimal numbers (3.14)
    - Multiple periods (...)
    - Complex punctuation
    """
    nlp = get_nlp()
    
    # Process in chunks to handle very long documents
    sentences = []
    chunk_size = 500_000  # 500k chars per chunk
    
    for i in range(0, len(text), chunk_size):
        chunk = text[i:i + chunk_size]
        doc = nlp(chunk)
        
        for sent in doc.sents:
            sentence_text = sent.text.strip()
            if sentence_text:
                sentences.append(sentence_text)
    
    logger.debug(f"Segmented {len(text)} chars into {len(sentences)} sentences")
    
    return sentences


# ══════════════════════════════════════════════════════════════════
# TOKENIZATION
# ══════════════════════════════════════════════════════════════════

def tokenize(text: str) -> List[str]:
    """
    Tokenizes text into words/tokens.
    
    Returns:
        List of token strings
    """
    nlp = get_nlp()
    doc = nlp(text)
    
    tokens = [token.text for token in doc if not token.is_space]
    
    return tokens


def tokenize_with_pos(text: str) -> List[Dict[str, str]]:
    """
    Tokenizes text and includes part-of-speech tags.
    
    Returns:
        List of dicts with 'text', 'pos', 'tag', 'lemma'
    """
    nlp = get_nlp()
    
    # Re-enable lemmatizer temporarily
    if "lemmatizer" not in nlp.pipe_names:
        nlp.add_pipe("lemmatizer")
    
    doc = nlp(text)
    
    tokens = []
    for token in doc:
        if not token.is_space:
            tokens.append({
                "text": token.text,
                "pos": token.pos_,      # Universal POS tag
                "tag": token.tag_,      # Detailed POS tag
                "lemma": token.lemma_,  # Base form
                "is_stop": token.is_stop,
                "is_punct": token.is_punct
            })
    
    # Disable lemmatizer again
    nlp.disable_pipes(["lemmatizer"])
    
    return tokens


# ══════════════════════════════════════════════════════════════════
# NOUN PHRASE EXTRACTION
# ══════════════════════════════════════════════════════════════════

def extract_noun_phrases(text: str) -> List[str]:
    """
    Extracts noun phrases from text.
    
    Useful for:
    - Key term extraction
    - Contract party identification
    - Subject identification
    
    Returns:
        List of noun phrase strings
    """
    nlp = get_nlp()
    doc = nlp(text)
    
    noun_phrases = [chunk.text for chunk in doc.noun_chunks]
    
    logger.debug(f"Extracted {len(noun_phrases)} noun phrases")
    
    return noun_phrases


# ══════════════════════════════════════════════════════════════════
# DEPENDENCY PARSING
# ══════════════════════════════════════════════════════════════════

def extract_subject_verb_object(sentence: str) -> Dict[str, List[str]]:
    """
    Extracts subject-verb-object triples from a sentence.
    
    Example:
        "The company shall pay the contractor" 
        → {
            "subjects": ["company"],
            "verbs": ["pay"],
            "objects": ["contractor"]
        }
    
    Returns:
        Dict with subjects, verbs, objects lists
    """
    nlp = get_nlp()
    doc = nlp(sentence)
    
    subjects = []
    verbs = []
    objects = []
    
    for token in doc:
        # Subject
        if "subj" in token.dep_:
            subjects.append(token.text)
        
        # Verb
        if token.pos_ == "VERB":
            verbs.append(token.text)
        
        # Object
        if "obj" in token.dep_:
            objects.append(token.text)
    
    return {
        "subjects": subjects,
        "verbs": verbs,
        "objects": objects
    }


# ══════════════════════════════════════════════════════════════════
# TEXT STATISTICS
# ══════════════════════════════════════════════════════════════════

def compute_text_statistics(text: str) -> Dict[str, int]:
    """
    Computes various text statistics.
    
    Returns:
        Dict with character count, word count, sentence count,
        average sentence length, etc.
    """
    nlp = get_nlp()
    doc = nlp(text)
    
    sentences = list(doc.sents)
    tokens = [token for token in doc if not token.is_space]
    words = [token for token in tokens if token.is_alpha]
    
    stats = {
        "char_count": len(text),
        "token_count": len(tokens),
        "word_count": len(words),
        "sentence_count": len(sentences),
        "avg_sentence_length": len(words) / len(sentences) if sentences else 0,
        "avg_word_length": sum(len(w.text) for w in words) / len(words) if words else 0,
        "unique_words": len(set(w.text.lower() for w in words)),
        "stopword_ratio": sum(1 for w in words if w.is_stop) / len(words) if words else 0
    }
    
    return stats


# ══════════════════════════════════════════════════════════════════
# CLAUSE BOUNDARY DETECTION
# ══════════════════════════════════════════════════════════════════

def detect_clause_boundaries(sentence: str) -> List[Tuple[int, int]]:
    """
    Detects sub-clause boundaries within a sentence.
    
    Useful for splitting long, compound sentences.
    
    Returns:
        List of (start, end) character positions for each clause
    """
    nlp = get_nlp()
    doc = nlp(sentence)
    
    boundaries = []
    current_start = 0
    
    for i, token in enumerate(doc):
        # Look for clause separators: commas, semicolons, conjunctions
        if token.text in [",", ";"] or token.dep_ == "cc":
            if i > 0:
                boundaries.append((current_start, token.idx))
                current_start = token.idx + len(token.text)
    
    # Add final clause
    if current_start < len(sentence):
        boundaries.append((current_start, len(sentence)))
    
    return boundaries


# ══════════════════════════════════════════════════════════════════
# SIMILARITY COMPUTATION
# ══════════════════════════════════════════════════════════════════

def compute_similarity(text1: str, text2: str) -> float:
    """
    Computes semantic similarity between two texts using spaCy vectors.
    
    Args:
        text1: First text
        text2: Second text
    
    Returns:
        Similarity score (0.0 to 1.0)
    
    Note: Requires spaCy model with word vectors (md, lg, or trf)
    """
    nlp = get_nlp()
    
    doc1 = nlp(text1)
    doc2 = nlp(text2)
    
    # spaCy computes cosine similarity of averaged word vectors
    similarity = doc1.similarity(doc2)
    
    return float(similarity)


# ══════════════════════════════════════════════════════════════════
# KEYWORD EXTRACTION
# ══════════════════════════════════════════════════════════════════

def extract_keywords(
    text: str,
    top_n: int = 10,
    pos_filter: Optional[List[str]] = None
) -> List[Tuple[str, float]]:
    """
    Extracts top keywords from text using TF-IDF-like scoring.
    
    Args:
        text: Input text
        top_n: Number of top keywords to return
        pos_filter: Filter by POS tags (e.g., ["NOUN", "VERB"])
    
    Returns:
        List of (keyword, score) tuples
    """
    nlp = get_nlp()
    doc = nlp(text)
    
    if pos_filter is None:
        pos_filter = ["NOUN", "PROPN", "VERB"]
    
    # Count word frequencies
    word_freq = {}
    for token in doc:
        if token.pos_ in pos_filter and not token.is_stop and token.is_alpha:
            lemma = token.lemma_.lower()
            word_freq[lemma] = word_freq.get(lemma, 0) + 1
    
    # Sort by frequency
    sorted_words = sorted(
        word_freq.items(),
        key=lambda x: x[1],
        reverse=True
    )
    
    # Normalize scores
    max_freq = sorted_words[0][1] if sorted_words else 1
    keywords = [
        (word, freq / max_freq)
        for word, freq in sorted_words[:top_n]
    ]
    
    return keywords


# ══════════════════════════════════════════════════════════════════
# PREPROCESSING UTILITIES
# ══════════════════════════════════════════════════════════════════

def remove_stopwords(text: str) -> str:
    """
    Removes stopwords from text.
    
    Returns:
        Text with stopwords removed
    """
    nlp = get_nlp()
    doc = nlp(text)
    
    filtered = [token.text for token in doc if not token.is_stop and not token.is_punct]
    
    return " ".join(filtered)


def lemmatize_text(text: str) -> str:
    """
    Lemmatizes text (converts words to base form).
    
    Example: "running ran runs" → "run run run"
    
    Returns:
        Lemmatized text
    """
    nlp = get_nlp()
    
    # Re-enable lemmatizer
    if "lemmatizer" not in nlp.pipe_names:
        nlp.add_pipe("lemmatizer")
    
    doc = nlp(text)
    
    lemmatized = [token.lemma_ for token in doc if not token.is_space]
    
    # Disable lemmatizer again
    nlp.disable_pipes(["lemmatizer"])
    
    return " ".join(lemmatized)