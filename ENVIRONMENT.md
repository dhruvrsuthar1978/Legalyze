# Environment & Run Guide

This file documents the environment variables and quick run instructions for the Legalyze frontend and backend used in development.

## Frontend

- VITE_API_URL: Base URL for backend API used by the frontend (example: `http://localhost:8000`).

Create a `.env` file in the `frontend/` folder with:

```
VITE_API_URL=http://localhost:8000
```

Run frontend (development):

```powershell
cd frontend
npm install
npm run dev
```

The frontend dev server runs at http://localhost:5173 by default.

## Backend

Core environment variables (see `backend/.env.example` for full list):

- MONGODB_URI — MongoDB connection string (required)
- JWT_SECRET — Secret to sign JWT tokens (required)
- AWS_ACCESS_KEY — AWS access key (if using S3)
- AWS_SECRET_KEY — AWS secret key (if using S3)
- S3_BUCKET — S3 bucket name (if using S3)
- SMTP_SERVER, SMTP_USERNAME, SMTP_PASSWORD — Email settings
- OPENAI_API_KEY / HUGGINGFACE_API_KEY — Optional model API keys

Run backend (development):

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

API docs: http://localhost:8000/docs

## CORS

Ensure the backend allows CORS from the frontend origin during development. Add `http://localhost:5173` to the allowed origins in backend settings. In FastAPI you can set this via `app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], ...)` or via an environment-driven list.

## Notes / Next Steps

- For production, set proper origins, enable HTTPS, and restrict API keys.
- Store secrets in a secrets manager (AWS Secrets Manager, Azure Key Vault, or similar) instead of `.env` files.
- Accessibility: basic ARIA attributes were added to file inputs and key buttons; a formal accessibility audit is recommended.
