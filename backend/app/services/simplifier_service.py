# app/services/simplifier_service.py

import re
from typing import List, Optional
from transformers import pipeline, Pipeline
import logging

logger = logging.getLogger("legalyze.simplifier")

# ── Lazy-load transformer pipeline ────────────────────────────────
_simplifier: Optional[Pipeline] = None

MODEL_NAME = "facebook/bart-large-cnn"

# Word thresholds for BART
BART_MIN_INPUT_WORDS  = 15
BART_MAX_INPUT_CHARS  = 1024     # BART token limit guard
SUMMARY_MAX_LENGTH    = 120      # max summary tokens
SUMMARY_MIN_LENGTH    = 30       # min summary tokens


def _get_simplifier() -> Pipeline:
    """Lazy-loads the BART summarizer pipeline on first call."""
    global _simplifier
    if _simplifier is None:
        logger.info(f"Loading summarizer model: {MODEL_NAME}")
        _simplifier = pipeline(
            "summarization",
            model=MODEL_NAME,
            tokenizer=MODEL_NAME,
            device=-1            # -1 = CPU; set 0 for GPU
        )
        logger.info("Summarizer model loaded successfully")
    return _simplifier


# ══════════════════════════════════════════════════════════════════
# PUBLIC ENTRY POINT
# ══════════════════════════════════════════════════════════════════

def simplify_clauses(clauses: List[dict]) -> List[dict]:
    """
    Converts each clause's original legal text into plain English.

    Strategy:
        - Short clauses (< 15 words): Use rule-based simplification
        - Medium clauses (15–400 words): Use BART summarizer
        - Long clauses (> 400 words): Chunk → summarize → recombine
        - All outputs are post-processed for readability

    Returns:
        Updated clauses with 'simplified_text' field populated
    """
    logger.info(f"Starting simplification of {len(clauses)} clauses")
    simplifier = _get_simplifier()

    for i, clause in enumerate(clauses):
        original = clause["original_text"]
        word_count = len(original.split())

        try:
            if word_count < BART_MIN_INPUT_WORDS:
                simplified = _rule_based_simplify(original)

            elif len(original) <= BART_MAX_INPUT_CHARS:
                simplified = _bart_simplify(simplifier, original)

            else:
                simplified = _chunked_simplify(simplifier, original)

            clause["simplified_text"] = _post_process(simplified)

        except Exception as e:
            logger.warning(
                f"Simplification failed for clause "
                f"{clause.get('clause_id', i)}: {e}"
            )
            # Fallback: truncated original + disclaimer
            clause["simplified_text"] = (
                f"[Simplification unavailable] "
                f"{original[:300]}..."
                if len(original) > 300
                else original
            )

        logger.debug(
            f"Clause {i+1} simplified | "
            f"original_words={word_count}, "
            f"simplified_words={len(clause['simplified_text'].split())}"
        )

    logger.info("Clause simplification complete")
    return clauses


# ══════════════════════════════════════════════════════════════════
# BART SUMMARIZER
# ══════════════════════════════════════════════════════════════════

def _bart_simplify(simplifier: Pipeline, text: str) -> str:
    """
    Uses BART to generate a plain-English summary of a legal clause.
    Prepends 'Explain in simple English: ' to guide the model.
    """
    prompt = f"Summarize in plain English: {text}"

    # Guard against exceeding BART's context window
    if len(prompt) > BART_MAX_INPUT_CHARS:
        prompt = prompt[:BART_MAX_INPUT_CHARS]

    input_word_count = len(text.split())
    dynamic_max = min(SUMMARY_MAX_LENGTH, max(SUMMARY_MIN_LENGTH, input_word_count // 2))

    result = simplifier(
        prompt,
        max_length=dynamic_max,
        min_length=SUMMARY_MIN_LENGTH,
        do_sample=False,
        truncation=True
    )

    return result[0]["summary_text"]


def _chunked_simplify(simplifier: Pipeline, text: str) -> str:
    """
    Splits very long clauses into manageable chunks,
    summarizes each chunk, then joins summaries into a final output.
    """
    chunks     = _chunk_text(text, max_chars=900)
    summaries  = []

    for chunk in chunks:
        if len(chunk.split()) >= BART_MIN_INPUT_WORDS:
            try:
                summary = _bart_simplify(simplifier, chunk)
                summaries.append(summary)
            except Exception as e:
                logger.warning(f"Chunk simplification failed: {e}")
                summaries.append(chunk[:200])

    combined = " ".join(summaries)

    # If combined summaries are still long, do one final summarization
    if len(combined.split()) > 80 and len(combined) <= BART_MAX_INPUT_CHARS:
        try:
            combined = _bart_simplify(simplifier, combined)
        except Exception:
            pass

    return combined


def _chunk_text(text: str, max_chars: int = 900) -> List[str]:
    """
    Splits text into chunks of max_chars, splitting at sentence boundaries.
    """
    chunks: List[str] = []
    sentences = re.split(r"(?<=[.!?])\s+", text)
    current = ""

    for sentence in sentences:
        if len(current) + len(sentence) + 1 <= max_chars:
            current += (" " if current else "") + sentence
        else:
            if current:
                chunks.append(current.strip())
            current = sentence

    if current:
        chunks.append(current.strip())

    return chunks


# ══════════════════════════════════════════════════════════════════
# RULE-BASED SIMPLIFIER (SHORT CLAUSES)
# ══════════════════════════════════════════════════════════════════

LEGAL_REPLACEMENTS = {
    r"\bhereinafter\b":          "from now on called",
    r"\bherein\b":               "in this agreement",
    r"\bthereto\b":              "to that",
    r"\bwhereof\b":              "of which",
    r"\bwhereas\b":              "given that",
    r"\bnotwithstanding\b":      "despite",
    r"\bpursuant to\b":         "according to",
    r"\bin accordance with\b":  "following",
    r"\binter alia\b":          "among other things",
    r"\bmutatis mutandis\b":    "with necessary changes",
    r"\bpari passu\b":          "equally",
    r"\bforce majeure\b":       "an unforeseeable event (like a disaster or war)",
    r"\bindemnif[a-z]+\b":      "compensate for losses",
    r"\bwithout prejudice\b":   "without giving up any rights",
    r"\binter partes\b":        "between the parties",
    r"\bin perpetuity\b":       "forever",
    r"\birrevocabl[a-z]+\b":    "cannot be reversed",
    r"\bexpress[a-z]* terms\b": "clearly stated conditions",
    r"\bsolely\b":               "only",
    r"\bshall\b":                "must",
    r"\bdeemed\b":               "considered",
    r"\bforegoing\b":            "the above",
    r"\bset forth\b":            "described",
    r"\bhereunder\b":            "under this agreement",
}


def _rule_based_simplify(text: str) -> str:
    """
    Applies regex-based legal term replacement for short clauses.
    More deterministic and faster than BART for simple sentences.
    """
    result = text

    for pattern, replacement in LEGAL_REPLACEMENTS.items():
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)

    return result


# ══════════════════════════════════════════════════════════════════
# POST PROCESSING
# ══════════════════════════════════════════════════════════════════

def _post_process(text: str) -> str:
    """
    Cleans up BART output:
    - Ensure sentence starts with capital letter
    - Ensure sentence ends with period
    - Remove duplicate whitespace
    - Capitalize 'i' standalone → 'I'
    """
    if not text:
        return ""

    # Capitalize first character
    text = text[0].upper() + text[1:] if len(text) > 1 else text.upper()

    # Ensure ends with period
    if text and text[-1] not in ".!?":
        text += "."

    # Fix standalone 'i'
    text = re.sub(r"\bi\b", "I", text)

    # Collapse whitespace
    text = re.sub(r" {2,}", " ", text).strip()

    return text