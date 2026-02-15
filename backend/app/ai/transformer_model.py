# app/ai/transformer_model.py

from transformers import (
    AutoTokenizer,
    AutoModelForSeq2SeqLM,
    AutoModelForCausalLM,
    pipeline,
    Pipeline
)
from typing import Optional, Dict, Any
import torch
import logging

logger = logging.getLogger("legalyze.transformers")

# ── Global Model Cache ────────────────────────────────────────────
_models: Dict[str, Any] = {}
_tokenizers: Dict[str, Any] = {}
_pipelines: Dict[str, Pipeline] = {}


# ══════════════════════════════════════════════════════════════════
# DEVICE DETECTION
# ══════════════════════════════════════════════════════════════════

def get_device() -> str:
    """
    Detects optimal device (cuda, mps, or cpu).
    
    Returns:
        Device string for PyTorch
    """
    if torch.cuda.is_available():
        device = "cuda"
        logger.info(f"✅ CUDA available | GPU: {torch.cuda.get_device_name(0)}")
    elif torch.backends.mps.is_available():
        device = "mps"  # Apple Silicon GPU
        logger.info("✅ MPS (Apple Silicon) available")
    else:
        device = "cpu"
        logger.info("⚠️ Using CPU (GPU not available)")
    
    return device


DEVICE = get_device()


# ══════════════════════════════════════════════════════════════════
# LOAD MODEL & TOKENIZER
# ══════════════════════════════════════════════════════════════════

def load_model(
    model_name: str,
    model_type: str = "seq2seq"
) -> tuple:
    """
    Loads a HuggingFace model and tokenizer.
    
    Args:
        model_name: Model identifier (e.g., "facebook/bart-large-cnn")
        model_type: "seq2seq" or "causal"
    
    Returns:
        Tuple of (model, tokenizer)
    """
    cache_key = f"{model_name}_{model_type}"
    
    # Check cache
    if cache_key in _models and cache_key in _tokenizers:
        logger.info(f"Model already loaded: {model_name}")
        return _models[cache_key], _tokenizers[cache_key]
    
    logger.info(f"Loading model: {model_name} (type: {model_type})")
    
    try:
        # Load tokenizer
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        
        # Load model based on type
        if model_type == "seq2seq":
            model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
        else:  # causal
            model = AutoModelForCausalLM.from_pretrained(model_name)
        
        # Move to device
        model = model.to(DEVICE)
        model.eval()  # Set to evaluation mode
        
        # Cache
        _models[cache_key] = model
        _tokenizers[cache_key] = tokenizer
        
        logger.info(
            f"✅ Model loaded successfully | "
            f"parameters={sum(p.numel() for p in model.parameters()):,}, "
            f"device={DEVICE}"
        )
        
        return model, tokenizer
    
    except Exception as e:
        logger.error(f"Failed to load model '{model_name}': {e}")
        raise


# ══════════════════════════════════════════════════════════════════
# TEXT GENERATION PIPELINE
# ══════════════════════════════════════════════════════════════════

def get_generation_pipeline(
    model_name: str = "gpt2",
    task: str = "text-generation"
) -> Pipeline:
    """
    Creates a HuggingFace pipeline for text generation.
    
    Args:
        model_name: Model identifier
        task: Pipeline task type
    
    Returns:
        HuggingFace Pipeline object
    """
    cache_key = f"{task}_{model_name}"
    
    if cache_key in _pipelines:
        return _pipelines[cache_key]
    
    logger.info(f"Creating pipeline: {task} with {model_name}")
    
    try:
        pipe = pipeline(
            task,
            model=model_name,
            device=0 if DEVICE == "cuda" else -1,
            torch_dtype=torch.float16 if DEVICE == "cuda" else torch.float32
        )
        
        _pipelines[cache_key] = pipe
        
        logger.info(f"✅ Pipeline created: {task}")
        
        return pipe
    
    except Exception as e:
        logger.error(f"Failed to create pipeline: {e}")
        raise


# ══════════════════════════════════════════════════════════════════
# GENERATE TEXT (Main Function)
# ══════════════════════════════════════════════════════════════════

def generate_text(
    prompt: str,
    model_name: str = "gpt2",
    max_tokens: int = 200,
    temperature: float = 0.7,
    top_p: float = 0.9,
    top_k: int = 50,
    num_return_sequences: int = 1,
    do_sample: bool = True
) -> str:
    """
    Generates text using a language model.
    
    Args:
        prompt: Input prompt
        model_name: Model to use
        max_tokens: Maximum tokens to generate
        temperature: Sampling temperature (0.0 = deterministic, 1.0+ = creative)
        top_p: Nucleus sampling threshold
        top_k: Top-k sampling
        num_return_sequences: Number of sequences to generate
        do_sample: Whether to use sampling (False = greedy)
    
    Returns:
        Generated text string
    """
    pipe = get_generation_pipeline(model_name)
    
    logger.debug(
        f"Generating text | "
        f"prompt_length={len(prompt)}, "
        f"max_tokens={max_tokens}"
    )
    
    try:
        outputs = pipe(
            prompt,
            max_new_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            num_return_sequences=num_return_sequences,
            do_sample=do_sample,
            pad_token_id=pipe.tokenizer.eos_token_id
        )
        
        # Extract generated text (remove prompt)
        generated = outputs[0]["generated_text"]
        
        # Remove prompt from output
        if generated.startswith(prompt):
            generated = generated[len(prompt):].strip()
        
        logger.debug(f"Text generated | output_length={len(generated)}")
        
        return generated
    
    except Exception as e:
        logger.error(f"Text generation failed: {e}")
        raise


# ══════════════════════════════════════════════════════════════════
# SUMMARIZATION
# ══════════════════════════════════════════════════════════════════

def summarize_text(
    text: str,
    model_name: str = "facebook/bart-large-cnn",
    max_length: int = 150,
    min_length: int = 50
) -> str:
    """
    Summarizes text using a seq2seq model.
    
    Args:
        text: Text to summarize
        model_name: Summarization model
        max_length: Maximum summary length (tokens)
        min_length: Minimum summary length (tokens)
    
    Returns:
        Summary string
    """
    model, tokenizer = load_model(model_name, model_type="seq2seq")
    
    logger.debug(f"Summarizing text | input_length={len(text)}")
    
    try:
        # Tokenize
        inputs = tokenizer(
            text,
            max_length=1024,
            truncation=True,
            return_tensors="pt"
        ).to(DEVICE)
        
        # Generate summary
        with torch.no_grad():
            summary_ids = model.generate(
                inputs["input_ids"],
                max_length=max_length,
                min_length=min_length,
                num_beams=4,
                early_stopping=True
            )
        
        # Decode
        summary = tokenizer.decode(
            summary_ids[0],
            skip_special_tokens=True
        )
        
        logger.debug(f"Summary generated | output_length={len(summary)}")
        
        return summary
    
    except Exception as e:
        logger.error(f"Summarization failed: {e}")
        raise


# ══════════════════════════════════════════════════════════════════
# QUESTION ANSWERING
# ══════════════════════════════════════════════════════════════════

def answer_question(
    question: str,
    context: str,
    model_name: str = "distilbert-base-cased-distilled-squad"
) -> Dict[str, Any]:
    """
    Answers a question based on a given context.
    
    Args:
        question: Question to answer
        context: Context containing the answer
        model_name: QA model
    
    Returns:
        Dict with 'answer', 'score', 'start', 'end'
    """
    pipe = pipeline(
        "question-answering",
        model=model_name,
        device=0 if DEVICE == "cuda" else -1
    )
    
    try:
        result = pipe(question=question, context=context)
        
        logger.debug(
            f"Question answered | "
            f"answer='{result['answer']}', "
            f"score={result['score']:.3f}"
        )
        
        return result
    
    except Exception as e:
        logger.error(f"Question answering failed: {e}")
        raise


# ══════════════════════════════════════════════════════════════════
# ZERO-SHOT CLASSIFICATION
# ══════════════════════════════════════════════════════════════════

def classify_text(
    text: str,
    labels: list,
    model_name: str = "facebook/bart-large-mnli"
) -> Dict[str, Any]:
    """
    Classifies text into one of the provided labels (zero-shot).
    
    Args:
        text: Text to classify
        labels: List of candidate labels
        model_name: Zero-shot classification model
    
    Returns:
        Dict with 'labels', 'scores'
    """
    pipe = pipeline(
        "zero-shot-classification",
        model=model_name,
        device=0 if DEVICE == "cuda" else -1
    )
    
    try:
        result = pipe(text, candidate_labels=labels)
        
        logger.debug(
            f"Text classified | "
            f"top_label={result['labels'][0]}, "
            f"score={result['scores'][0]:.3f}"
        )
        
        return result
    
    except Exception as e:
        logger.error(f"Classification failed: {e}")
        raise


# ══════════════════════════════════════════════════════════════════
# CLEANUP
# ══════════════════════════════════════════════════════════════════

def clear_model_cache():
    """
    Clears all cached models and pipelines to free memory.
    """
    global _models, _tokenizers, _pipelines
    
    logger.info("Clearing model cache...")
    
    _models.clear()
    _tokenizers.clear()
    _pipelines.clear()
    
    # Force garbage collection
    import gc
    gc.collect()
    
    if DEVICE == "cuda":
        torch.cuda.empty_cache()
    
    logger.info("✅ Model cache cleared")   