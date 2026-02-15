"""
Simple test server for Legalyze backend
Run this to test if basic FastAPI setup works
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

app = FastAPI(
    title="Legalyze API - Test Server",
    version="1.0.0",
    description="Minimal test server to verify FastAPI setup"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "name": "Legalyze API",
        "version": "1.0.0",
        "status": "operational",
        "message": "Test server running successfully!",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/test")
async def test():
    return {
        "message": "API endpoint working!",
        "data": {
            "features": [
                "Contract Upload",
                "AI Analysis",
                "Risk Assessment",
                "Digital Signatures"
            ]
        }
    }

if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("[START] Legalyze Test Server")
    print("="*60)
    print("Server: http://localhost:8000")
    print("Docs: http://localhost:8000/docs")
    print("="*60 + "\n")
    
    uvicorn.run(
        "simple_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
