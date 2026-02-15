# 🏛️ Legalyze API

**AI-Powered Legal Contract Analysis Platform**

Legalyze uses advanced NLP, transformer models, and RAG to analyze legal contracts, identify risky clauses, generate fair alternatives, and enable digital signatures.

---

## � Project Background

### The Challenge
Legal contracts form the foundation of modern commerce, yet remain paradoxically inaccessible to those they bind. The average commercial contract spans 20-50 pages of dense legal terminology, creating a fundamental asymmetry: corporations employ legal departments to scrutinize every clause, while individual consumers and small businesses routinely sign contracts they do not fully understand. According to a 2023 legal technology study, over 68% of small businesses sign contracts without legal review due to cost constraints.

### The Solution
Legalyze addresses these challenges through a purpose-built AI architecture combining NLP precision with legal domain expertise. Unlike generic LLM wrappers, Legalyze implements:

*   **Retrieval-Augmented Generation (RAG)**: Grounds analysis in verified legal principles to prevent hallucinations.
*   **Specialized NLP Pipeline**: Uses spaCy for intelligent clause extraction and semantic classification.
*   **Risk Scoring**: Evaluates clauses based on fairness metrics and detects exploitative provisions.
*   **Plain-English Translation**: Preserves legal nuance while making terms accessible.
*   **Integrated Workflow**: Combines analysis, negotiation (AI suggestions), and execution (digital signatures) in one platform.

This system democratizes legal understanding, allowing users to identify risks and negotiate fair terms without the prohibitive cost of traditional counsel.

---

## �🚀 Features

✅ **Contract Upload & Extraction**  
- PDF/DOCX support with OCR for scanned documents
- Cloud storage (AWS S3) with signed URLs

✅ **AI-Powered Analysis**  
- Clause extraction using spaCy NLP (18 clause types)
- Risk assessment with pattern matching
- Plain-English simplification using BART
- RAG context enrichment with FAISS vector store

✅ **Smart Suggestions**  
- AI-generated fair clause alternatives
- Accept/reject/edit workflow
- Regeneration for different options

✅ **Contract Generation**  
- Create balanced contracts with accepted suggestions
- Version control and history tracking
- PDF/DOCX export with risk visualization

✅ **Digital Signatures**  
- RSA-PSS + SHA-256 cryptographic signing
- Countersignature workflow
- Tamper detection and verification
- Complete audit trail

✅ **Security & Performance**  
- JWT authentication with token blacklisting
- Role-based access control
- Rate limiting (slowapi)
- Comprehensive logging and error handling

---

## 📋 Prerequisites

- **Python 3.9+**
- **MongoDB** (local or Atlas)
- **AWS Account** (for S3 file storage)
- **SMTP Server** (for emails)

**Optional:**
- CUDA-capable GPU for faster AI processing
- Tesseract OCR for scanned documents

---

## 🛠️ Installation

### 1. Clone Repository
```bash
git clone https://github.com/yourusername/legalyze-backend.git
cd legalyze-backend
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Download spaCy Model
```bash
python -m spacy download en_core_web_lg
```

### 5. Install Tesseract (for OCR)

**macOS:**
```bash
brew install tesseract
```

**Ubuntu/Debian:**
```bash
sudo apt-get install tesseract-ocr
```

**Windows:**  
Download from: https://github.com/UB-Mannheim/tesseract/wiki

### 6. Setup Environment Variables
```bash
cp .env.example .env
```

Edit `.env` and fill in your credentials:
- MongoDB connection string
- JWT secret key (generate with `openssl rand -hex 32`)
- AWS S3 credentials
- SMTP server details

### 7. Create Required Directories
```bash
mkdir -p logs uploads generated vector_store
```

---

## 🚀 Running the Application

### Development
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Running Tests (Docker recommended)

On Windows the Python dependencies such as `PyMuPDF` or `Pillow` may require native build tools.
To avoid local build issues, run the test suite inside Docker which uses Linux prebuilt wheels:

```bash
cd backend
docker compose -f docker-compose.test.yml up --build --abort-on-container-exit --exit-code-from api
```

The `api` service builds an image with system dependencies, runs `pip install -r requirements.txt`, and executes `pytest` against a temporary `mongo` service.


### Production
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

Or using Gunicorn:
```bash
gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

---

## 📚 API Documentation

Once running, access the interactive API docs:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/api/openapi.json

---

## 🧪 Testing

Run tests with pytest:
```bash
pytest tests/ -v
```

With coverage:
```bash
pytest tests/ --cov=app --cov-report=html
```

---

## 📂 Project Structure
```
legalyze-backend/
├── app/
│   ├── routes/              # API endpoints
│   ├── controllers/         # Business logic
│   ├── models/              # Pydantic schemas
│   ├── services/            # Core services
│   ├── ai/                  # AI/NLP pipeline
│   ├── middleware/          # Auth, errors, logging
│   ├── utils/               # JWT, hashing, etc.
│   └── config/              # Settings, database
├── logs/                    # Application logs
├── uploads/                 # Temporary uploads
├── generated/               # Generated contracts
├── vector_store/            # FAISS index
├── tests/                   # Test suite
├── main.py                  # Application entry
├── requirements.txt         # Dependencies
├── .env.example             # Environment template
└── README.md                # This file
```

---

## 🔐 Authentication

All protected endpoints require a JWT token:
```bash
# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password123"}'

# Use token
curl -X GET http://localhost:8000/api/contracts \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

## 🌐 Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `MONGODB_URI` | MongoDB connection string | ✅ |
| `JWT_SECRET` | Secret key for JWT signing | ✅ |
| `AWS_ACCESS_KEY` | AWS access key | ✅ |
| `AWS_SECRET_KEY` | AWS secret key | ✅ |
| `S3_BUCKET` | S3 bucket name | ✅ |
| `SMTP_SERVER` | SMTP server hostname | ✅ |
| `SMTP_USERNAME` | SMTP username | ✅ |
| `SMTP_PASSWORD` | SMTP password | ✅ |
| `OPENAI_API_KEY` | OpenAI API key | ❌ |

See `.env.example` for complete list.

---

## 📊 Database Indexes

Indexes are automatically created on startup:

- `users.email` (unique)
- `contracts.user_id + uploaded_at`
- `analyses.contract_id` (unique)
- `signatures.contract_id`
- Full-text search on `contracts.filename, extracted_text, tags`

---

## 🤖 AI Models Used

| Purpose | Model | Size |
|---------|-------|------|
| Clause Extraction | spaCy `en_core_web_lg` | 560 MB |
| Simplification | BART `facebook/bart-large-cnn` | 1.6 GB |
| Embeddings | Sentence-BERT `all-MiniLM-L6-v2` | 80 MB |
| Text Generation | GPT-2 (or custom) | 548 MB |

---

## 🐳 Docker Deployment
```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy model
RUN python -m spacy download en_core_web_lg

# Copy application
COPY . .

# Create directories
RUN mkdir -p logs uploads generated vector_store

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```
```yaml
# docker-compose.yml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - MONGODB_URI=mongodb://mongo:27017
      - DB_NAME=legalyze_db
    env_file:
      - .env
    depends_on:
      - mongo
    volumes:
      - ./uploads:/app/uploads
      - ./generated:/app/generated
      - ./logs:/app/logs

  mongo:
    image: mongo:7
    ports:
      - "27017:27017"
    volumes:
      - mongo_data:/data/db

volumes:
  mongo_data:
```

---

## 🔒 Security Best Practices

✅ Use strong JWT secrets (min 32 chars)  
✅ Enable HTTPS in production  
✅ Set `DEBUG=False` in production  
✅ Use environment variables for secrets  
✅ Implement rate limiting  
✅ Regularly update dependencies  
✅ Enable MongoDB authentication  
✅ Use IAM roles for AWS (avoid hardcoded keys)  
✅ Sanitize all user inputs  
✅ Log security events  

---

## 📈 Performance Optimization

- **Model Caching**: AI models lazy-load and cache in memory
- **Database Indexing**: Proper indexes on frequent queries
- **Connection Pooling**: Motor async MongoDB client
- **Async I/O**: All file and database operations are async
- **Rate Limiting**: Prevents abuse and DoS
- **CDN**: Serve static files via CDN (CloudFront, Cloudflare)

---

## 🐛 Troubleshooting

**MongoDB Connection Fails:**
```bash
# Check MongoDB is running
mongosh

# Or start MongoDB
brew services start mongodb-community  # macOS
sudo systemctl start mongod            # Linux
```

**spaCy Model Not Found:**
```bash
python -m spacy download en_core_web_lg
```

**Import Errors:**
```bash
pip install -r requirements.txt --upgrade
```

**OCR Not Working:**
```bash
# Install Tesseract
brew install tesseract  # macOS
```

---

## 📝 License

MIT License - see [LICENSE](LICENSE) file

---

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

---

## 📧 Support

For issues and questions:
- GitHub Issues: https://github.com/yourusername/legalyze-backend/issues
- Email: support@legalyze.com

---

**Built with ❤️ using FastAPI, MongoDB, and Transformers**