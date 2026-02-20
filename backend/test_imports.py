# test_imports.py

print("🧪 Testing imports...\n")

# Test each module
tests = [
    ("Config", "from app.config.settings import settings"),
    ("Database", "from app.config.database import db"),
    ("Auth Middleware", "from app.middleware.auth_middleware import verify_token"),
    ("JWT Utils", "from app.utils.jwt_utils import create_access_token"),
    ("Hash Utils", "from app.utils.hash_utils import hash_password"),
    ("User Model", "from app.models.user_model import UserRegisterRequest"),
    ("Contract Model", "from app.models.contract_model import ContractResponse"),
    ("Auth Controller", "from app.controllers.auth_controller import register_user"),
    ("Extractor Service", "from app.services.extractor_service import extract_text_from_file"),
    ("NLP Pipeline", "from app.ai.nlp_pipeline import load_spacy_model"),
    ("Embeddings", "from app.ai.embeddings import encode_text"),
    ("RAG Pipeline", "from app.ai.rag_pipeline import is_vector_store_ready"),
]

passed = 0
failed = 0

for name, import_stmt in tests:
    try:
        exec(import_stmt)
        print(f"✅ {name}")
        passed += 1
    except Exception as e:
        print(f"❌ {name}: {str(e)[:50]}")
        failed += 1

print(f"\n📊 Results: {passed} passed, {failed} failed")

if failed > 0:
    print("\n⚠️  Fix import errors before proceeding")
    exit(1)
else:
    print("\n✅ All imports successful!")