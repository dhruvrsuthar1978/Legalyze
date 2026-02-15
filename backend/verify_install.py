"""
Verify all required packages are installed and working
"""

print("Checking package installations...\n")

packages = {
    "fastapi": "FastAPI",
    "uvicorn": "Uvicorn",
    "pydantic": "Pydantic",
    "sqlalchemy": "SQLAlchemy",
    "motor": "Motor (MongoDB)",
    "pymongo": "PyMongo",
    "redis": "Redis",
    "spacy": "spaCy",
    "transformers": "Transformers",
    "torch": "PyTorch",
    "sentence_transformers": "Sentence Transformers",
    "faiss": "FAISS",
    "numpy": "NumPy",
    "sklearn": "scikit-learn",
    "fitz": "PyMuPDF (PDF processing)",
    "pytesseract": "Pytesseract (OCR)",
    "PIL": "Pillow (Image processing)",
    "reportlab": "ReportLab (PDF generation)"
}

success = []
failed = []

for package, name in packages.items():
    try:
        __import__(package)
        success.append(f"[OK] {name}")
    except ImportError as e:
        failed.append(f"[FAIL] {name}: {str(e)}")

print("\n".join(success))
if failed:
    print("\n" + "\n".join(failed))
    
print(f"\n{'='*50}")
print(f"Total: {len(success)}/{len(packages)} packages working")
print(f"{'='*50}")

if len(success) == len(packages):
    print("\n*** All packages installed successfully! ***")
    print("\nYou can now start the backend server:")
    print("  cd legalzye-backend")
    print("  python -m uvicorn app.main:app --reload")
else:
    print(f"\nWARNING: {len(failed)} package(s) failed to import")
