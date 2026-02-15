# app/services/clause_service.py

import uuid
import re
import spacy
from typing import List, Dict, Optional
import logging

logger = logging.getLogger("legalyze.clause")

# ── Load spaCy model ───────────────────────────────────────────────
try:
    nlp = spacy.load("en_core_web_lg")         # Large model preferred
    logger.info("spaCy model 'en_core_web_lg' loaded")
except OSError:
    nlp = spacy.load("en_core_web_sm")         # Fallback to small
    logger.warning("Fallback to spaCy 'en_core_web_sm'")


# ══════════════════════════════════════════════════════════════════
# CLAUSE KEYWORD MAP
# Pattern: { ClauseType → [keyword_list] }
# ══════════════════════════════════════════════════════════════════

CLAUSE_KEYWORD_MAP: Dict[str, List[str]] = {
    "Confidentiality": [
        "confidential", "non-disclosure", "nda",
        "proprietary information", "trade secret", "secret",
        "disclose", "disclosure", "classified"
    ],
    "Payment": [
        "payment", "invoice", "fee", "amount due",
        "billing", "compensation", "remuneration", "salary",
        "cost", "price", "charges", "installment", "refund",
        "revenue share", "royalty"
    ],
    "Termination": [
        "terminat", "end of agreement", "cancel", "expir",
        "breach", "notice period", "wind down", "dissolution",
        "rescind", "void", "cessation"
    ],
    "Liability": [
        "liability", "liable", "damages", "indemnif",
        "hold harmless", "limitation of liability",
        "consequential", "punitive", "negligence"
    ],
    "Intellectual Property": [
        "intellectual property", "ip rights", "copyright",
        "trademark", "patent", "trade dress", "invention",
        "proprietary", "work for hire", "moral rights",
        "license", "assignment of rights"
    ],
    "Governing Law": [
        "governing law", "jurisdiction", "applicable law",
        "legal venue", "forum", "choice of law",
        "courts of", "state of", "laws of"
    ],
    "Dispute Resolution": [
        "arbitration", "mediation", "dispute",
        "resolution", "adr", "litigation",
        "legal proceedings", "claim", "settle"
    ],
    "Force Majeure": [
        "force majeure", "act of god", "unforeseen",
        "beyond control", "pandemic", "natural disaster",
        "war", "strike", "government order", "epidemic"
    ],
    "Amendment": [
        "amendment", "modification", "changes to",
        "update to agreement", "addendum", "supplement",
        "revised", "restate"
    ],
    "Warranty": [
        "warranty", "guarantee", "represent",
        "warrant", "merchantability", "fitness",
        "as-is", "no warranty", "disclaimer"
    ],
    "Indemnification": [
        "indemnif", "indemnity", "defend",
        "hold harmless", "third-party claims", "losses"
    ],
    "Non-Compete": [
        "non-compete", "non compete", "competition",
        "competing business", "restrictive covenant",
        "restraint of trade"
    ],
    "Non-Solicitation": [
        "non-solicitation", "solicit", "poach",
        "hire away", "recruit", "employees of"
    ],
    "Data Privacy": [
        "personal data", "gdpr", "ccpa", "data protection",
        "privacy policy", "data processing", "data subject",
        "pii", "data breach", "sensitive information"
    ],
    "Assignment": [
        "assignment", "assign", "transfer rights",
        "delegate", "novation", "successor"
    ],
    "Severability": [
        "severability", "severable", "invalid provision",
        "unenforceable", "remaining provisions"
    ],
    "Entire Agreement": [
        "entire agreement", "supersedes", "whole agreement",
        "prior understandings", "merger clause",
        "integration clause"
    ]
}

# Minimum sentence length (words) for a sentence to be a valid clause candidate
MIN_CLAUSE_WORDS = 8

# Maximum sentence length (words) — very long sentences split into chunks
MAX_CLAUSE_WORDS = 200


# ══════════════════════════════════════════════════════════════════
# PUBLIC ENTRY POINT
# ══════════════════════════════════════════════════════════════════

def extract_and_classify_clauses(text: str) -> List[dict]:
    """
    Master clause extraction pipeline:

    Steps:
        1. Preprocess text (normalize, remove page markers)
        2. Sentence segmentation using spaCy
        3. Filter sentences by length
        4. Classify each sentence against CLAUSE_KEYWORD_MAP
        5. Merge adjacent sentences of the same type
        6. Assign positional order
        7. Compute word count per clause

    Returns:
        List of clause dicts ready for risk analysis
    """
    logger.info(
        f"Starting clause extraction | "
        f"text_length={len(text)}, words={len(text.split())}"
    )

    # Step 1: Preprocess
    text = _preprocess_text(text)

    # Step 2 & 3: Segment + filter
    sentences = _segment_sentences(text)
    logger.info(f"Sentences after filtering: {len(sentences)}")

    # Step 4: Classify
    classified = _classify_sentences(sentences)
    logger.info(
        f"Classified sentences: {len(classified)} "
        f"({len(sentences) - len(classified)} unclassified)"
    )

    # Step 5: Merge consecutive same-type sentences
    merged = _merge_adjacent_clauses(classified)
    logger.info(f"Final clauses after merging: {len(merged)}")

    # Step 6 & 7: Assign metadata
    clauses = _assign_metadata(merged)

    return clauses


# ══════════════════════════════════════════════════════════════════
# PREPROCESSING
# ══════════════════════════════════════════════════════════════════

def _preprocess_text(text: str) -> str:
    """
    Prepares extracted contract text for NLP processing:
    - Removes page markers added by extractor ([PAGE N])
    - Normalizes quotes and dashes
    - Removes excessive whitespace
    """
    # Remove page markers
    text = re.sub(r"\[PAGE \d+\]\n?", "", text)

    # Normalize curly quotes to straight quotes
    text = text.replace("\u201c", '"').replace("\u201d", '"')
    text = text.replace("\u2018", "'").replace("\u2019", "'")

    # Normalize em dashes and en dashes
    text = text.replace("\u2014", " — ").replace("\u2013", " - ")

    # Collapse multiple whitespace
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


# ══════════════════════════════════════════════════════════════════
# SENTENCE SEGMENTATION
# ══════════════════════════════════════════════════════════════════

def _segment_sentences(text: str) -> List[str]:
    """
    Uses spaCy sentence boundary detection for accurate segmentation.
    Filters out sentences that are too short or too long.
    Splits oversized sentences at semicolons or commas if needed.
    """
    # Process in chunks to avoid memory issues with large contracts
    sentences: List[str] = []
    chunk_size = 100_000   # characters per spaCy pass

    for i in range(0, len(text), chunk_size):
        chunk = text[i: i + chunk_size]
        doc   = nlp(chunk)

        for sent in doc.sents:
            raw  = sent.text.strip()
            words = len(raw.split())

            if words < MIN_CLAUSE_WORDS:
                continue

            if words > MAX_CLAUSE_WORDS:
                # Split oversized sentence into sub-clauses
                sub = _split_long_sentence(raw)
                sentences.extend(sub)
            else:
                sentences.append(raw)

    return sentences


def _split_long_sentence(sentence: str) -> List[str]:
    """
    Splits an oversized sentence at semicolons, then at commas
    if still too long. Returns only sub-clauses meeting MIN length.
    """
    parts: List[str] = []

    # Try splitting at semicolons first
    semi_splits = [p.strip() for p in sentence.split(";") if p.strip()]
    for part in semi_splits:
        if len(part.split()) > MAX_CLAUSE_WORDS:
            # Further split at commas
            comma_splits = [p.strip() for p in part.split(",") if p.strip()]
            parts.extend([
                p for p in comma_splits
                if len(p.split()) >= MIN_CLAUSE_WORDS
            ])
        elif len(part.split()) >= MIN_CLAUSE_WORDS:
            parts.append(part)

    return parts if parts else [sentence[:500]]


# ══════════════════════════════════════════════════════════════════
# CLAUSE CLASSIFICATION
# ══════════════════════════════════════════════════════════════════

def _classify_sentences(sentences: List[str]) -> List[Dict]:
    """
    Classifies each sentence against CLAUSE_KEYWORD_MAP.
    Uses partial keyword matching (supports partial word roots).
    Returns only sentences that match at least one clause type.
    """
    classified: List[Dict] = []

    for sentence in sentences:
        clause_type  = _detect_clause_type(sentence)
        if clause_type:
            classified.append({
                "sentence": sentence,
                "clause_type": clause_type
            })

    return classified


def _detect_clause_type(sentence: str) -> Optional[str]:
    """
    Scores each clause type by keyword density.
    Returns the highest-scoring type or None if no match.
    """
    sentence_lower = sentence.lower()
    scores: Dict[str, int] = {}

    for clause_type, keywords in CLAUSE_KEYWORD_MAP.items():
        score = 0
        for kw in keywords:
            if kw in sentence_lower:
                score += 1

        if score > 0:
            scores[clause_type] = score

    if not scores:
        return None

    # Return type with highest keyword match score
    return max(scores, key=scores.get)


# ══════════════════════════════════════════════════════════════════
# CLAUSE MERGING
# ══════════════════════════════════════════════════════════════════

def _merge_adjacent_clauses(classified: List[Dict]) -> List[Dict]:
    """
    Merges consecutive sentences of the same clause type
    into a single clause block.

    E.g., 3 consecutive "Confidentiality" sentences
    → 1 single Confidentiality clause.
    """
    if not classified:
        return []

    merged: List[Dict] = []
    current_type = classified[0]["clause_type"]
    current_texts = [classified[0]["sentence"]]

    for item in classified[1:]:
        if item["clause_type"] == current_type:
            current_texts.append(item["sentence"])
        else:
            merged.append({
                "clause_type": current_type,
                "merged_text": " ".join(current_texts)
            })
            current_type  = item["clause_type"]
            current_texts = [item["sentence"]]

    # Flush last group
    merged.append({
        "clause_type": current_type,
        "merged_text": " ".join(current_texts)
    })

    return merged


# ══════════════════════════════════════════════════════════════════
# METADATA ASSIGNMENT
# ══════════════════════════════════════════════════════════════════

def _assign_metadata(merged: List[Dict]) -> List[dict]:
    """
    Converts merged clause dicts into the full ClauseSchema-compatible
    dict with all required fields initialized.
    """
    clauses: List[dict] = []

    for position, item in enumerate(merged, start=1):
        text       = item["merged_text"]
        word_count = len(text.split())

        clause = {
            "clause_id":         str(uuid.uuid4()),
            "clause_type":       item["clause_type"],
            "original_text":     text,
            "simplified_text":   None,
            "risk_level":        None,
            "risk_reason":       None,
            "risk_indicators":   [],
            "risk_score":        None,
            "rag_context":       None,
            "suggestion":        None,
            "suggestion_status": "pending",
            "edited_suggestion": None,
            "edit_log":          [],
            "position_in_document": position,
            "word_count":        word_count
        }

        clauses.append(clause)
        logger.debug(
            f"Clause {position}: type={item['clause_type']}, "
            f"words={word_count}"
        )

    return clauses


# ══════════════════════════════════════════════════════════════════
# UTILITY: GET CLAUSE TYPE DISTRIBUTION
# ══════════════════════════════════════════════════════════════════

def get_clause_type_distribution(clauses: List[dict]) -> Dict[str, int]:
    """Returns a dict of clause_type → count for statistics."""
    dist: Dict[str, int] = {}
    for clause in clauses:
        ct = clause["clause_type"]
        dist[ct] = dist.get(ct, 0) + 1
    return dist