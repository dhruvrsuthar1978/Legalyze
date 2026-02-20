import logging
import os
from typing import Optional, Tuple

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer


logger = logging.getLogger("legalyze.clause_classifier")

_model = None
_tokenizer = None
_id2label = {}
_loaded = False


CLAUSE_LABEL_MAP = {
    "confidentiality": "Confidentiality",
    "non disclosure": "Confidentiality",
    "nondisclosure": "Confidentiality",
    "payment": "Payment",
    "fees": "Payment",
    "fee": "Payment",
    "termination": "Termination",
    "liability": "Liability",
    "limitation of liability": "Liability",
    "intellectual property": "Intellectual Property",
    "ip": "Intellectual Property",
    "governing law": "Governing Law",
    "choice of law": "Governing Law",
    "dispute resolution": "Dispute Resolution",
    "arbitration": "Dispute Resolution",
    "force majeure": "Force Majeure",
    "amendment": "Amendment",
    "warranty": "Warranty",
    "warranties": "Warranty",
    "indemnification": "Indemnification",
    "indemnity": "Indemnification",
    "non compete": "Non-Compete",
    "non-compete": "Non-Compete",
    "non solicitation": "Non-Solicitation",
    "non-solicitation": "Non-Solicitation",
    "data privacy": "Data Privacy",
    "privacy": "Data Privacy",
    "assignment": "Assignment",
    "severability": "Severability",
    "entire agreement": "Entire Agreement",
}


def _normalize(text: str) -> str:
    return " ".join(text.strip().lower().replace("-", " ").replace("_", " ").split())


def _canonical_label(raw_label: str) -> Optional[str]:
    key = _normalize(raw_label)
    return CLAUSE_LABEL_MAP.get(key)


def _load_if_available() -> None:
    global _model, _tokenizer, _id2label, _loaded
    if _loaded:
        return

    _loaded = True
    model_path = os.getenv("CLAUSE_CLASSIFIER_MODEL_PATH", "").strip()
    if not model_path:
        logger.info("CLAUSE_CLASSIFIER_MODEL_PATH not set; using keyword clause classifier")
        return

    if not os.path.isdir(model_path):
        logger.warning(f"Clause classifier path not found: {model_path}")
        return

    try:
        _tokenizer = AutoTokenizer.from_pretrained(model_path)
        _model = AutoModelForSequenceClassification.from_pretrained(model_path)
        _model.eval()
        _id2label = _model.config.id2label or {}
        logger.info(f"Loaded clause classifier model from {model_path}")
    except Exception as exc:
        logger.warning(f"Failed to load clause classifier model: {exc}")
        _model = None
        _tokenizer = None
        _id2label = {}


def predict_clause_type(text: str) -> Optional[Tuple[str, float]]:
    _load_if_available()
    if _model is None or _tokenizer is None:
        return None

    min_conf = float(os.getenv("CLAUSE_CLASSIFIER_MIN_CONFIDENCE", "0.55"))

    try:
        encoded = _tokenizer(
            text,
            truncation=True,
            max_length=256,
            return_tensors="pt",
        )
        with torch.no_grad():
            logits = _model(**encoded).logits
            probs = torch.softmax(logits, dim=-1)[0]
            score, idx = torch.max(probs, dim=-1)
            label = _id2label.get(int(idx), str(int(idx)))

        canonical = _canonical_label(label)
        confidence = float(score.item())
        if canonical and confidence >= min_conf:
            return canonical, confidence
    except Exception as exc:
        logger.warning(f"Clause classifier prediction failed: {exc}")

    return None

