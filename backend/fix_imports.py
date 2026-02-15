import os
import re

# Files to fix
files = [
    r"app\controllers\analysis_controller.py",
    r"app\controllers\contract_controller.py",
    r"app\controllers\generation_controller.py",
    r"app\controllers\signature_controller.py",
    r"app\controllers\suggestion_controller.py",
]

for file_path in files:
    full_path = os.path.join(r"C:\legalzye\backend", file_path)
    
    with open(full_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace import
    content = content.replace(
        "from app.config.database import db",
        "from app.config.database import get_database"
    )
    
    # Add db = get_database() at start of each async function
    # This is a simple pattern - add after function definition
    content = re.sub(
        r'(async def \w+\([^)]*\)[^:]*:\s*"""[^"]*"""\s*)',
        r'\1\n    db = get_database()\n    ',
        content
    )
    
    with open(full_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Fixed: {file_path}")

print("All imports fixed!")
