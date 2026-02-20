# test_ai_models.py

print("🧪 Testing AI models (this may take a few minutes)...\n")

# Test spaCy
print("1️⃣ Testing spaCy...")
try:
    from app.ai.nlp_pipeline import load_spacy_model, segment_sentences
    
    nlp = load_spacy_model()
    print(f"✅ spaCy loaded: {nlp.meta['name']}")
    
    sentences = segment_sentences("This is a test. This is another test.")
    if len(sentences) == 2:
        print(f"✅ Sentence segmentation works: {sentences}")
    else:
        print(f"⚠️  Unexpected sentence count: {len(sentences)}")
except Exception as e:
    print(f"❌ spaCy test failed: {e}")

# Test embeddings
print("\n2️⃣ Testing embeddings...")
try:
    from app.ai.embeddings import load_embedding_model, encode_text
    
    model = load_embedding_model()
    print(f"✅ Embedding model loaded: {model.get_sentence_embedding_dimension()}D")
    
    embedding = encode_text("This is a test sentence.")
    print(f"✅ Text encoded: shape {embedding.shape}")
except Exception as e:
    print(f"❌ Embeddings test failed: {e}")

# Test transformers (lightweight)
print("\n3️⃣ Testing transformers...")
try:
    from app.ai.transformer_model import get_device
    
    device = get_device()
    print(f"✅ Device detected: {device}")
except Exception as e:
    print(f"❌ Transformer test failed: {e}")

print("\n✅ AI model tests complete!")