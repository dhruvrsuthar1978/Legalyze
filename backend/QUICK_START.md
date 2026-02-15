# 🚀 Backend Quick Start Guide

## Current Status

✅ All Python packages installed (14/14)
✅ Environment configuration created
⚠️ MongoDB required for full backend

## Option 1: Simple Test Server (No MongoDB Required)

Perfect for testing if FastAPI works and frontend can connect:

```bash
cd C:\legalzye\backend
python simple_server.py
```

Then visit:
- http://localhost:8000 - Root endpoint
- http://localhost:8000/docs - API documentation
- http://localhost:8000/health - Health check

## Option 2: Full Backend (Requires MongoDB)

### Step 1: Install MongoDB

**Download MongoDB Community Server:**
https://www.mongodb.com/try/download/community

**Or use MongoDB Atlas (Cloud - Free):**
1. Go to https://www.mongodb.com/cloud/atlas/register
2. Create free cluster
3. Get connection string
4. Update `.env` file with connection string

### Step 2: Start MongoDB (if installed locally)

```bash
# MongoDB should auto-start after installation
# Or manually start:
net start MongoDB
```

### Step 3: Update .env (if using Atlas)

Edit `C:\legalzye\backend\.env`:
```
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/
```

### Step 4: Start Full Backend

```bash
cd C:\legalzye\backend
python -m uvicorn app.main:app --reload --port 8000
```

## Troubleshooting

### Error: "cannot import name 'connect_to_mongo'"
✅ FIXED - database.py updated with required functions

### Error: "Field required" for MONGODB_URI
✅ FIXED - .env file created with default values

### Error: MongoDB connection failed
- Install MongoDB Community Server OR
- Use MongoDB Atlas (cloud) OR
- Use simple_server.py for testing

### Pylance Import Errors in VS Code
✅ FIXED - .vscode/settings.json created
- Reload VS Code window: Ctrl+Shift+P → "Reload Window"

## Next Steps

1. **Test Simple Server First:**
   ```bash
   python simple_server.py
   ```

2. **Start Frontend:**
   ```bash
   cd C:\legalzye\frontend
   npm install
   npm run dev
   ```

3. **Install MongoDB** (when ready for full features)

4. **Start Full Backend** (after MongoDB is running)

## Package Verification

Run anytime to verify all packages work:
```bash
python verify_install.py
```

## Files Created

- ✅ `.env` - Environment configuration
- ✅ `simple_server.py` - Test server (no MongoDB)
- ✅ `verify_install.py` - Package verification
- ✅ `.vscode/settings.json` - VS Code Pylance fix
- ✅ `app/config/database.py` - Updated with connection functions
- ✅ `app/config/settings.py` - Updated with all required fields

## MongoDB Installation (Windows)

1. Download: https://www.mongodb.com/try/download/community
2. Run installer (choose "Complete" installation)
3. Install as Windows Service (check the box)
4. Install MongoDB Compass (GUI tool - optional)
5. MongoDB will auto-start on port 27017

Verify MongoDB is running:
```bash
mongosh
# Should connect to mongodb://localhost:27017
```
