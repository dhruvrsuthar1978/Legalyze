# Legalyze Backend Requirements Document

## Table of Contents
1. [Overview](#overview)
2. [Technology Stack](#technology-stack)
3. [Architecture](#architecture)
4. [Database Schema](#database-schema)
5. [API Endpoints](#api-endpoints)
6. [Authentication & Authorization](#authentication--authorization)
7. [File Processing](#file-processing)
8. [AI/ML Integration](#aiml-integration)
9. [Third-Party Services](#third-party-services)
10. [Security Requirements](#security-requirements)
11. [Performance Requirements](#performance-requirements)
12. [Deployment](#deployment)

---

## Overview

Legalyze is an AI-powered legal contract analysis platform that enables users to:
- Upload and analyze legal contracts
- Extract key clauses and detect risks
- Generate balanced contracts
- Compare multiple contracts
- Apply digital signatures
- Manage contract history

---

## Technology Stack

### Recommended Backend Stack

**Option 1: Node.js/Express Stack** (Recommended)
- **Runtime**: Node.js v20+
- **Framework**: Express.js or Fastify
- **Language**: TypeScript
- **ORM**: Prisma or Drizzle
- **Database**: PostgreSQL 15+
- **Cache**: Redis
- **File Storage**: AWS S3 or MinIO
- **Search**: Elasticsearch (optional for full-text search)

**Option 2: Python/FastAPI Stack**
- **Runtime**: Python 3.11+
- **Framework**: FastAPI
- **ORM**: SQLAlchemy or Tortoise ORM
- **Database**: PostgreSQL 15+
- **Cache**: Redis
- **File Storage**: AWS S3
- **ML Framework**: LangChain, OpenAI API

**Option 3: Laravel/PHP Stack**
- **Runtime**: PHP 8.2+
- **Framework**: Laravel 11
- **ORM**: Eloquent
- **Database**: PostgreSQL or MySQL 8+
- **Cache**: Redis
- **File Storage**: Laravel Storage (S3)

---

## Architecture

### System Architecture
```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│   Frontend  │─────▶│   API GW    │─────▶│   Backend   │
│   (React)   │      │  (Optional) │      │  Services   │
└─────────────┘      └─────────────┘      └─────────────┘
                                                  │
                          ┌──────────────────────┼──────────────────────┐
                          │                      │                      │
                    ┌─────▼─────┐        ┌──────▼──────┐      ┌───────▼────────┐
                    │ PostgreSQL │        │    Redis    │      │   File Store   │
                    │  Database  │        │    Cache    │      │  (S3/MinIO)    │
                    └────────────┘        └─────────────┘      └────────────────┘
                                                  │
                                          ┌───────▼────────┐
                                          │  AI/ML Service │
                                          │  (OpenAI/etc)  │
                                          └────────────────┘
```

### Microservices (Optional - For Scale)
1. **Auth Service**: User authentication and authorization
2. **Contract Service**: Contract CRUD operations
3. **Analysis Service**: AI-powered contract analysis
4. **Document Service**: File upload, parsing, and storage
5. **Signature Service**: Digital signature management
6. **Notification Service**: Email and in-app notifications

---

## Database Schema

### Users Table
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    phone VARCHAR(50),
    company VARCHAR(255),
    role VARCHAR(50) DEFAULT 'Lawyer',
    avatar_url TEXT,
    email_verified BOOLEAN DEFAULT FALSE,
    theme_preference VARCHAR(20) DEFAULT 'light',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);
```

### User Preferences Table
```sql
CREATE TABLE user_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    email_notifications BOOLEAN DEFAULT TRUE,
    contract_uploaded_notification BOOLEAN DEFAULT TRUE,
    analysis_complete_notification BOOLEAN DEFAULT TRUE,
    risk_alerts_notification BOOLEAN DEFAULT TRUE,
    weekly_report_notification BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_preferences_user_id ON user_preferences(user_id);
```

### API Keys Table
```sql
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    key_name VARCHAR(255) NOT NULL,
    api_key VARCHAR(255) UNIQUE NOT NULL,
    api_secret_hash VARCHAR(255) NOT NULL,
    permissions JSONB DEFAULT '["read"]'::JSONB,
    last_used_at TIMESTAMP,
    expires_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_api_keys_user_id ON api_keys(user_id);
CREATE INDEX idx_api_keys_key ON api_keys(api_key);
```

### Contracts Table
```sql
CREATE TABLE contracts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(500) NOT NULL,
    file_url TEXT NOT NULL,
    file_type VARCHAR(50) NOT NULL, -- 'pdf', 'docx'
    file_size BIGINT NOT NULL,
    status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'analyzing', 'completed', 'failed'
    risk_level VARCHAR(50), -- 'low', 'medium', 'high'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    analyzed_at TIMESTAMP
);

CREATE INDEX idx_contracts_user_id ON contracts(user_id);
CREATE INDEX idx_contracts_status ON contracts(status);
CREATE INDEX idx_contracts_created_at ON contracts(created_at DESC);
```

### Clauses Table
```sql
CREATE TABLE clauses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contract_id UUID NOT NULL REFERENCES contracts(id) ON DELETE CASCADE,
    type VARCHAR(100) NOT NULL, -- 'termination', 'payment', 'liability', etc.
    content TEXT NOT NULL,
    risk_score INTEGER DEFAULT 0, -- 0-100
    ai_suggestion TEXT,
    start_position INTEGER,
    end_position INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_clauses_contract_id ON clauses(contract_id);
CREATE INDEX idx_clauses_type ON clauses(type);
```

### Contract Analysis Table
```sql
CREATE TABLE contract_analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contract_id UUID NOT NULL REFERENCES contracts(id) ON DELETE CASCADE,
    overall_risk_score INTEGER, -- 0-100
    summary TEXT,
    key_points JSONB,
    recommendations JSONB,
    compliance_issues JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_analyses_contract_id ON contract_analyses(contract_id);
```

### Generated Contracts Table
```sql
CREATE TABLE generated_contracts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    contract_type VARCHAR(100) NOT NULL,
    party1_name VARCHAR(255),
    party2_name VARCHAR(255),
    duration_months INTEGER,
    parameters JSONB,
    content TEXT NOT NULL,
    file_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_generated_contracts_user_id ON generated_contracts(user_id);
```

### Signatures Table
```sql
CREATE TABLE signatures (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contract_id UUID REFERENCES contracts(id) ON DELETE CASCADE,
    generated_contract_id UUID REFERENCES generated_contracts(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    signature_data TEXT NOT NULL, -- Base64 encoded signature
    ip_address VARCHAR(45),
    user_agent TEXT,
    signed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    verified BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_signatures_contract_id ON signatures(contract_id);
CREATE INDEX idx_signatures_user_id ON signatures(user_id);
```

### Contract Comparisons Table
```sql
CREATE TABLE contract_comparisons (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    contract1_id UUID NOT NULL REFERENCES contracts(id) ON DELETE CASCADE,
    contract2_id UUID NOT NULL REFERENCES contracts(id) ON DELETE CASCADE,
    differences JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_comparisons_user_id ON contract_comparisons(user_id);
```

### Audit Log Table
```sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100),
    resource_id UUID,
    ip_address VARCHAR(45),
    user_agent TEXT,
    details JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at DESC);
```

---

## API Endpoints

### Authentication
```
POST   /api/auth/register          - Register new user
POST   /api/auth/login             - Login user
POST   /api/auth/logout            - Logout user
POST   /api/auth/refresh           - Refresh access token
POST   /api/auth/forgot-password   - Send password reset email
POST   /api/auth/reset-password    - Reset password with token
GET    /api/auth/verify-email      - Verify email address
GET    /api/auth/me                - Get current user
PUT    /api/auth/profile           - Update user profile (name, email, phone, company)
PUT    /api/auth/password          - Change password
PUT    /api/auth/theme             - Update theme preference
```

### User Preferences & Settings
```
GET    /api/preferences            - Get user preferences
PUT    /api/preferences            - Update user preferences
PUT    /api/preferences/notifications - Update notification settings
```

### API Keys
```
POST   /api/api-keys               - Generate new API key
GET    /api/api-keys               - List user's API keys
GET    /api/api-keys/:id           - Get API key details
PUT    /api/api-keys/:id           - Update API key (name, permissions)
DELETE /api/api-keys/:id           - Revoke/delete API key
POST   /api/api-keys/:id/regenerate - Regenerate API key secret
```

### Account Management
```
DELETE /api/account                - Delete user account (with confirmation)
POST   /api/account/export         - Export user data (GDPR compliance)
```

### Contracts
```
POST   /api/contracts              - Upload contract
GET    /api/contracts              - List user's contracts (with pagination)
GET    /api/contracts/:id          - Get contract details
DELETE /api/contracts/:id          - Delete contract
GET    /api/contracts/:id/download - Download contract file
POST   /api/contracts/:id/analyze  - Trigger AI analysis
GET    /api/contracts/:id/analysis - Get analysis results
```

### Clauses
```
GET    /api/contracts/:id/clauses           - Get all clauses
GET    /api/contracts/:id/clauses/:clauseId - Get clause details
PUT    /api/contracts/:id/clauses/:clauseId - Update clause (add notes)
```

### Contract Generation
```
POST   /api/generate/contracts     - Generate new contract
GET    /api/generate/contracts     - List generated contracts
GET    /api/generate/contracts/:id - Get generated contract
DELETE /api/generate/contracts/:id - Delete generated contract
POST   /api/generate/contracts/:id/download - Download generated contract
GET    /api/generate/templates     - List available templates
```

### Contract Comparison
```
POST   /api/compare                - Compare two contracts
GET    /api/compare                - List comparison history
GET    /api/compare/:id            - Get comparison details
DELETE /api/compare/:id            - Delete comparison
```

### Digital Signatures
```
POST   /api/signatures             - Create signature
GET    /api/signatures             - List signatures
GET    /api/signatures/:id         - Get signature details
POST   /api/signatures/:id/verify  - Verify signature
DELETE /api/signatures/:id         - Delete signature
```

### Admin
```
GET    /api/admin/users            - List all users
GET    /api/admin/users/:id        - Get user details
PUT    /api/admin/users/:id        - Update user
DELETE /api/admin/users/:id        - Delete user
GET    /api/admin/stats            - Get platform statistics
GET    /api/admin/audit-logs       - Get audit logs
```

### File Management
```
POST   /api/files/upload           - Upload file (with pre-signed URL)
GET    /api/files/:id              - Get file metadata
DELETE /api/files/:id              - Delete file
```

---

## Authentication & Authorization

### JWT Implementation
```javascript
// Token Structure
{
  "access_token": {
    "sub": "user_id",
    "email": "user@example.com",
    "role": "Lawyer",
    "exp": 1234567890 // 15 minutes
  },
  "refresh_token": {
    "sub": "user_id",
    "exp": 1234567890 // 7 days
  }
}
```

### Role-Based Access Control (RBAC)
- **User/Lawyer**: Can manage own contracts
- **Admin**: Full platform access
- **API Client**: Limited machine-to-machine access

### Security Headers
```javascript
{
  "X-Content-Type-Options": "nosniff",
  "X-Frame-Options": "DENY",
  "X-XSS-Protection": "1; mode=block",
  "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
  "Content-Security-Policy": "default-src 'self'"
}
```

---

## File Processing

### File Upload Flow
1. Frontend requests pre-signed URL from backend
2. Backend generates S3 pre-signed URL (15-minute expiry)
3. Frontend uploads directly to S3
4. Frontend notifies backend of successful upload
5. Backend creates contract record and triggers analysis

### File Processing Pipeline
1. **Validation**: Check file type, size, and format
2. **Storage**: Upload to S3/MinIO with encryption
3. **Parsing**: Extract text using:
   - **PDF**: pdf-parse (Node.js) or PyPDF2 (Python)
   - **DOCX**: mammoth.js (Node.js) or python-docx (Python)
4. **Text Extraction**: Clean and normalize text
5. **Queue Analysis**: Add to processing queue (Redis/Bull)

### File Size Limits
- Maximum file size: 10 MB per upload
- Supported formats: PDF, DOCX

---

## AI/ML Integration

### OpenAI GPT Integration (Recommended)
```javascript
// Contract Analysis Prompt
const analysisPrompt = `
Analyze the following legal contract and provide:
1. Overall risk assessment (Low/Medium/High)
2. Key clauses identification
3. Potential risks and red flags
4. Compliance issues
5. Recommendations for improvement

Contract text:
${contractText}

Return response in JSON format.
`;

// API Call
const response = await openai.chat.completions.create({
  model: "gpt-4-turbo-preview",
  messages: [{ role: "user", content: analysisPrompt }],
  response_format: { type: "json_object" },
  temperature: 0.3
});
```

### Alternative: LangChain Framework
```javascript
import { ChatOpenAI } from "@langchain/openai";
import { StructuredOutputParser } from "langchain/output_parsers";

const parser = StructuredOutputParser.fromNamesAndDescriptions({
  riskLevel: "Overall risk level (low/medium/high)",
  clauses: "Array of key clauses found",
  recommendations: "Array of improvement recommendations"
});

const chain = ChatOpenAI
  .pipe(parser);
```

### Clause Extraction
Use Named Entity Recognition (NER) to identify:
- Termination clauses
- Payment terms
- Liability limitations
- Confidentiality provisions
- Intellectual property rights
- Non-compete agreements

### Contract Generation
```javascript
const generationPrompt = `
Generate a ${contractType} contract with:
- Party 1: ${party1Name}
- Party 2: ${party2Name}
- Duration: ${durationMonths} months
- Additional parameters: ${JSON.stringify(parameters)}

Create a balanced, legally sound contract.
`;
```

---

## Third-Party Services

### Required Services

1. **OpenAI API**
   - Purpose: Contract analysis, generation
   - Pricing: Pay-per-token
   - Alternative: Anthropic Claude, Google Gemini

2. **AWS Services**
   - **S3**: File storage
   - **CloudFront**: CDN for file delivery
   - **SES**: Email notifications
   - **CloudWatch**: Logging and monitoring

3. **SendGrid/Mailgun**
   - Purpose: Transactional emails
   - Use cases: Welcome emails, password resets, notifications

4. **Stripe/PayPal**
   - Purpose: Payment processing (if offering paid plans)
   - Integration: Subscription management

5. **Sentry**
   - Purpose: Error tracking and monitoring
   - Real-time error alerts

6. **Google Analytics / Mixpanel**
   - Purpose: User analytics
   - Track usage patterns

---

## Security Requirements

### Data Encryption
- **At Rest**: AES-256 encryption for stored files
- **In Transit**: TLS 1.3 for all API communications
- **Database**: Encrypted database fields for sensitive data

### Input Validation
- Sanitize all user inputs
- Validate file uploads (type, size, content)
- Use parameterized queries to prevent SQL injection
- Implement rate limiting

### GDPR Compliance
- Data retention policies (e.g., delete after 90 days)
- User data export functionality
- Right to be forgotten (account deletion)
- Clear privacy policy and terms of service

### Security Best Practices
- Bcrypt/Argon2 for password hashing (min 10 rounds)
- CSRF protection with tokens
- CORS configuration for allowed origins
- API rate limiting (e.g., 100 requests per minute)
- Failed login attempt throttling
- Secure session management

---

## Performance Requirements

### Response Time Targets
- API endpoints: < 200ms (95th percentile)
- File upload: < 5s for 10MB file
- Contract analysis: < 30s (async processing)
- Database queries: < 100ms

### Scalability
- Support 1,000 concurrent users
- Handle 10,000 contracts per month
- Process 500 GB of files per month

### Caching Strategy
```javascript
// Redis Cache Examples
- User sessions: 24-hour TTL
- Contract metadata: 1-hour TTL
- Analysis results: 7-day TTL
- API responses: 5-minute TTL (where appropriate)
```

### Database Optimization
- Use database indexing on frequently queried fields
- Implement connection pooling (max 20 connections)
- Use read replicas for analytics queries
- Implement query result pagination (20 items per page)

---

## Deployment

### Environment Configuration
```env
# App Configuration
NODE_ENV=production
PORT=3000
APP_URL=https://api.legalyze.com

# Database
DATABASE_URL=postgresql://user:pass@host:5432/legalyze
DATABASE_POOL_SIZE=20

# Redis
REDIS_URL=redis://host:6379
REDIS_PASSWORD=secret

# JWT
JWT_SECRET=your-256-bit-secret
JWT_ACCESS_EXPIRY=15m
JWT_REFRESH_EXPIRY=7d

# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4-turbo-preview

# AWS
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_S3_BUCKET=legalyze-contracts

# Email
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASS=...
FROM_EMAIL=noreply@legalyze.com

# Sentry
SENTRY_DSN=https://...@sentry.io/...

# Rate Limiting
RATE_LIMIT_WINDOW=15m
RATE_LIMIT_MAX=100
```

### Docker Deployment
```dockerfile
FROM node:20-alpine

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .

EXPOSE 3000
CMD ["node", "dist/index.js"]
```

### Docker Compose (Development)
```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "3000:3000"
    environment:
      DATABASE_URL: postgresql://postgres:postgres@db:5432/legalyze
      REDIS_URL: redis://redis:6379
    depends_on:
      - db
      - redis

  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: legalyze
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

### Production Deployment Options

**Option 1: AWS ECS/Fargate**
- Container orchestration
- Auto-scaling based on CPU/memory
- Load balancer (ALB)

**Option 2: Kubernetes (GKE/EKS)**
- Full container orchestration
- Advanced deployment strategies
- Monitoring with Prometheus

**Option 3: Platform-as-a-Service**
- **Railway**: Quick deployment, auto-scaling
- **Render**: Managed PostgreSQL, Redis
- **Fly.io**: Edge deployment
- **Heroku**: Simple deployment, add-ons

### CI/CD Pipeline
```yaml
# GitHub Actions example
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: npm test
      - name: Build Docker image
        run: docker build -t legalyze-api .
      - name: Push to registry
        run: docker push legalyze-api
      - name: Deploy to production
        run: kubectl apply -f k8s/
```

---

## Monitoring & Logging

### Application Metrics
- Request rate and response times
- Error rates by endpoint
- Database query performance
- Cache hit/miss ratio
- File upload success rate

### Logging Strategy
```javascript
// Structured logging with Winston/Pino
logger.info({
  type: 'contract_analysis',
  userId: req.user.id,
  contractId: contract.id,
  duration: analysisTime,
  riskLevel: result.riskLevel
});
```

### Health Checks
```javascript
GET /health
{
  "status": "healthy",
  "services": {
    "database": "connected",
    "redis": "connected",
    "s3": "accessible"
  },
  "timestamp": "2024-01-11T12:00:00Z"
}
```

---

## Development Workflow

### Local Setup
```bash
# Install dependencies
npm install

# Setup database
npx prisma migrate dev

# Seed database
npm run seed

# Start development server
npm run dev
```

### Testing
```bash
# Unit tests
npm run test

# Integration tests
npm run test:integration

# E2E tests
npm run test:e2e

# Coverage
npm run test:coverage
```

### Code Quality
- ESLint for linting
- Prettier for formatting
- Husky for pre-commit hooks
- TypeScript for type safety

---

## API Documentation

### Auto-generated Documentation
Use Swagger/OpenAPI for API documentation:

```javascript
/**
 * @swagger
 * /api/contracts:
 *   post:
 *     summary: Upload a contract
 *     tags: [Contracts]
 *     security:
 *       - bearerAuth: []
 *     requestBody:
 *       required: true
 *       content:
 *         multipart/form-data:
 *           schema:
 *             type: object
 *             properties:
 *               file:
 *                 type: string
 *                 format: binary
 *     responses:
 *       201:
 *         description: Contract uploaded successfully
 */
```

---

## Cost Estimation (Monthly)

### Small Scale (< 100 users)
- **Hosting**: Railway/Render - $20-50
- **Database**: PostgreSQL (512MB) - $7
- **Redis**: 256MB - $3
- **OpenAI API**: ~$100-200 (depending on usage)
- **S3 Storage**: $5
- **Email**: SendGrid free tier
- **Total**: ~$135-265/month

### Medium Scale (1000 users)
- **Hosting**: AWS ECS - $150-300
- **Database**: RDS PostgreSQL (db.t3.medium) - $75
- **Redis**: ElastiCache (cache.t3.small) - $30
- **OpenAI API**: ~$500-1000
- **S3 + CloudFront**: $50
- **Email**: SendGrid - $15
- **Total**: ~$820-1470/month

---

## Implementation Priority

### Phase 1: Foundation (Week 1-2)
- User authentication (register, login, JWT)
- User profile management
- Database setup with PostgreSQL
- Basic API structure with Express/FastAPI
- Error handling and logging

### Phase 2: File Management (Week 2-3)
- File upload to S3
- PDF/DOCX parsing
- Contract CRUD operations
- File metadata storage

### Phase 3: AI Integration (Week 3-4)
- OpenAI API integration
- Contract analysis pipeline
- Clause extraction
- Risk detection
- Queue system for async processing

### Phase 4: Advanced Features (Week 4-5)
- Contract generation with custom requirements
- Contract comparison
- AI suggestions

### Phase 5: Additional Features (Week 5-6)
- Digital signatures
- User preferences & settings
- API key management
- Notification system

### Phase 6: Polish & Deploy (Week 6-7)
- Testing (unit, integration, E2E)
- Performance optimization
- Security audit
- Deployment to production

## Quick Start Backend Setup

### Option 1: Node.js/Express Setup
```bash
# Initialize project
mkdir legalyze-backend && cd legalyze-backend
npm init -y

# Install dependencies
npm install express cors dotenv bcryptjs jsonwebtoken
npm install pg prisma @prisma/client
npm install multer aws-sdk openai
npm install bull redis
npm install winston morgan
npm install express-rate-limit helmet
npm install -D nodemon typescript @types/node @types/express

# Setup Prisma
npx prisma init

# Create basic structure
mkdir -p src/{controllers,routes,middleware,services,utils,models}
touch src/index.ts src/app.ts
```

### Option 2: Python/FastAPI Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install fastapi uvicorn sqlalchemy psycopg2-binary
pip install pydantic pydantic-settings
pip install python-jose[cryptography] passlib[bcrypt]
pip install python-multipart boto3 openai
pip install celery redis
pip install alembic

# Create structure
mkdir -p app/{api,core,models,schemas,services,utils}
touch app/main.py app/__init__.py
```

### Environment Variables Template
```env
# App Configuration
NODE_ENV=development
PORT=3000
APP_URL=http://localhost:3000
FRONTEND_URL=http://localhost:5173

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/legalyze
DATABASE_POOL_SIZE=20

# JWT
JWT_SECRET=your-super-secret-jwt-key-change-in-production
JWT_ACCESS_EXPIRY=15m
JWT_REFRESH_EXPIRY=7d

# OpenAI
OPENAI_API_KEY=sk-your-openai-key
OPENAI_MODEL=gpt-4-turbo-preview
OPENAI_MAX_TOKENS=4000

# AWS S3
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_S3_BUCKET=legalyze-contracts

# Redis
REDIS_URL=redis://localhost:6379
REDIS_PASSWORD=

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASS=your-app-password
FROM_EMAIL=noreply@legalyze.com

# Rate Limiting
RATE_LIMIT_WINDOW=15m
RATE_LIMIT_MAX=100
```

---

## Additional Resources

- [Express.js Documentation](https://expressjs.com/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Laravel Documentation](https://laravel.com/docs)
- [Prisma Documentation](https://www.prisma.io/docs)
- [OpenAI API Documentation](https://platform.openai.com/docs)
- [AWS S3 Documentation](https://docs.aws.amazon.com/s3/)
- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)

---

**Document Version**: 1.0
**Last Updated**: 2024-01-11
**Author**: Legalyze Development Team