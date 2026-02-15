# 🚀 Legalyze - Complete Setup Guide

## 📋 Prerequisites

- Python 3.11+
- Node.js 18+
- MongoDB (optional - can use Docker)
- Redis (optional - can use Docker)

## 🔧 Backend Setup

### Option 1: Quick Start (Development)

```bash
# Navigate to backend
cd legalzye-backend

# Install dependencies
pip install fastapi uvicorn pydantic pydantic-settings sqlalchemy redis motor httpx aiofiles

# Create .env file
cp .env.example .env

# Edit .env with your settings
# Minimal required:
# SECRET_KEY=your-secret-key-here
# DATABASE_URL=sqlite:///./legalyze.db
# MONGODB_URL=mongodb://localhost:27017/legalyze

# Start server
python start_server.py
```

Backend runs on: **http://localhost:8000**
API Docs: **http://localhost:8000/docs**

### Option 2: Docker Setup

```bash
cd legalzye-backend

# Start all services (MongoDB, Redis, API)
docker-compose up -d

# View logs
docker-compose logs -f api
```

### Option 3: Full Installation

```bash
cd legalzye-backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install all dependencies
pip install -r requirements.txt

# Download spaCy model (optional for full AI features)
python -m spacy download en_core_web_sm

# Setup environment
cp .env.example .env
# Edit .env with your credentials

# Run migrations (if using PostgreSQL)
alembic upgrade head

# Start server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 🎨 Frontend Setup

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Create .env file
echo "VITE_API_URL=http://localhost:8000" > .env

# Start development server
npm run dev
```

Frontend runs on: **http://localhost:5173**

## 🚀 Quick Start (Both Services)

### Terminal 1 - Backend
```bash
cd legalzye-backend
python start_server.py
```

### Terminal 2 - Frontend
```bash
cd frontend
npm run dev
```

### Access Application
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## 📦 Environment Variables

### Backend (.env)
```env
# Required
SECRET_KEY=your-super-secret-key-change-in-production
DATABASE_URL=sqlite:///./legalyze.db
MONGODB_URL=mongodb://localhost:27017/legalyze

# Optional
REDIS_URL=redis://localhost:6379/0
OPENAI_API_KEY=your-openai-key
AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret
```

### Frontend (.env)
```env
VITE_API_URL=http://localhost:8000
VITE_APP_NAME=Legalyze
VITE_MAX_FILE_SIZE=10485760
```

## 🧪 Testing the Integration

1. **Start Backend**: `cd legalzye-backend && python start_server.py`
2. **Start Frontend**: `cd frontend && npm run dev`
3. **Open Browser**: http://localhost:5173
4. **Register Account**: Click "Get Started"
5. **Upload Contract**: Upload a PDF/DOCX file
6. **View Analysis**: See AI-powered analysis results

## 🐳 Docker Deployment

### Full Stack with Docker Compose

```bash
# Backend
cd legalzye-backend
docker-compose up -d

# Frontend (build for production)
cd frontend
npm run build

# Serve with nginx or any static server
npx serve -s dist -p 3000
```

## 📊 Project Structure

```
legalzye/
├── legalyze-backend/          # Python FastAPI Backend
│   ├── app/
│   │   ├── api/               # API endpoints
│   │   ├── services/          # Business logic & AI
│   │   ├── models/            # Database models
│   │   └── core/              # Configuration
│   ├── start_server.py        # Development server
│   ├── test_api.py            # Simple test API
│   └── requirements.txt       # Python dependencies
│
├── frontend/                  # React Frontend
│   ├── src/
│   │   ├── pages/             # Page components
│   │   ├── components/        # UI components
│   │   ├── services/          # API integration
│   │   └── store/             # Redux state
│   └── package.json           # Node dependencies
│
└── INTEGRATION_GUIDE.md       # This file
```

## 🔍 Troubleshooting

### Backend Issues

**Port 8000 already in use:**
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:8000 | xargs kill -9
```

**Import errors:**
```bash
# Verify Python interpreter
python --version

# Reinstall dependencies
pip install --upgrade pip
pip install -r requirements-minimal.txt
```

### Frontend Issues

**Port 5173 already in use:**
```bash
# Kill process
npx kill-port 5173

# Or use different port
npm run dev -- --port 3000
```

**API connection errors:**
- Check backend is running on port 8000
- Verify VITE_API_URL in .env
- Check CORS settings in backend

## 🎯 Features Available

### ✅ Implemented & Working
- User authentication (register/login)
- Contract upload (PDF/DOCX)
- AI-powered clause extraction
- Risk assessment (Low/Medium/High)
- Text simplification
- Digital signatures
- Contract comparison
- RAG-powered Q&A
- Contract generation
- Dashboard analytics

### 🔄 Backend API Status
- ✅ Authentication endpoints
- ✅ Contract management
- ✅ Analysis endpoints
- ✅ RAG/AI endpoints
- ✅ Signature endpoints
- ✅ Admin endpoints

### 🎨 Frontend Status
- ✅ Modern UI with Tailwind CSS
- ✅ Responsive design
- ✅ API integration
- ✅ State management (Redux)
- ✅ File upload with progress
- ✅ Real-time updates

## 📝 Default Credentials

For testing, you can create an account through the registration page.

**Admin Access** (if seeded):
- Email: admin@legalyze.com
- Password: admin123

## 🚀 Production Deployment

### Backend
```bash
# Build Docker image
docker build -t legalyze-backend .

# Run container
docker run -p 8000:8000 --env-file .env legalyze-backend
```

### Frontend
```bash
# Build for production
npm run build

# Deploy dist/ folder to:
# - Vercel
# - Netlify
# - AWS S3 + CloudFront
# - Any static hosting
```

## 📚 Additional Resources

- **API Documentation**: http://localhost:8000/docs
- **Backend README**: legalyze-backend/README.md
- **Frontend README**: frontend/README.md
- **Integration Guide**: INTEGRATION_GUIDE.md

## ✅ Status: FULLY INTEGRATED & READY

Both frontend and backend are complete, integrated, and production-ready! 🎉

## 🆘 Support

For issues or questions:
1. Check troubleshooting section above
2. Review API documentation at /docs
3. Check browser console for frontend errors
4. Check backend logs for API errors

---

**Happy Coding! 🚀**