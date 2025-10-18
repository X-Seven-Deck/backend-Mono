# X-sevenAI Phase 2 - Quick Start Guide

**Version:** 1.0.0  
**Date:** October 4, 2025  
**Status:** Phase 2 Complete - Ready for Testing

---

## 🚀 Getting Started in 10 Minutes

This guide will help you get X-sevenAI Phase 2 up and running quickly.

---

## Prerequisites

### Required Software
- **Python 3.11+** - Modern Python with async support
- **Docker & Docker Compose** - For infrastructure services
- **Git** - Version control
- **Redis** - Caching (via Docker)
- **PostgreSQL** - Database (via Supabase or Docker)

### API Keys Needed
- **OpenAI API Key** - For LLM operations
- **Supabase URL & Key** - For database
- **Groq API Key** (optional) - Alternative LLM
- **Anthropic API Key** (optional) - Alternative LLM

---

## Step 1: Clone and Setup Environment

```bash
# Navigate to project
cd /Users/naveen/Desktop/x7AI

# Copy environment template
cp .env.example .env

# Edit .env with your API keys
nano .env
```

### Required Environment Variables

```bash
# Core Settings
ENVIRONMENT=development
LOG_LEVEL=INFO

# OpenAI (Required)
OPENAI_API_KEY=sk-your-key-here

# Supabase (Required)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-key

# Redis (Local)
REDIS_HOST=localhost
REDIS_PORT=6379

# Optional: Alternative LLMs
GROQ_API_KEY=your-groq-key
ANTHROPIC_API_KEY=your-anthropic-key
```

---

## Step 2: Start Infrastructure Services

```bash
# Start Redis, PostgreSQL, and other services
docker-compose up -d redis postgres

# Verify services are running
docker-compose ps
```

Expected output:
```
NAME                STATUS              PORTS
x7ai-redis          Up 10 seconds       0.0.0.0:6379->6379/tcp
x7ai-postgres       Up 10 seconds       0.0.0.0:5432->5432/tcp
```

---

## Step 3: Initialize Database Schema

```bash
# Connect to Supabase and run schema
# Option 1: Via Supabase Dashboard
# - Go to SQL Editor
# - Copy contents of docs/supabase_schema.sql
# - Execute

# Option 2: Via psql (if using local PostgreSQL)
psql -h localhost -U postgres -d x7ai -f docs/supabase_schema.sql
```

---

## Step 4: Install Dependencies

### AI Orchestration Service

```bash
cd services/ai-orchestration-service

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Verify installation
python -c "import langgraph, haystack, dspy; print('All imports successful!')"
```

### Global Chat Service

```bash
cd ../global-chat-service

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Business Logic Service

```bash
cd ../business-logic-service

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

## Step 5: Start Services

### Terminal 1: AI Orchestration Service (Port 8020)

```bash
cd services/ai-orchestration-service
source venv/bin/activate
python -m app.main
```

Expected output:
```
INFO: Starting AI Orchestration Service
INFO: Redis connected successfully
INFO: OpenAI client ready
INFO: Uvicorn running on http://0.0.0.0:8020
```

### Terminal 2: Global Chat Service (Port 8050)

```bash
cd services/global-chat-service
source venv/bin/activate
python -m app.main
```

Expected output:
```
INFO: Starting global-chat-service
INFO: Crew AI agents initialized successfully
INFO: Uvicorn running on http://0.0.0.0:8050
```

### Terminal 3: Business Logic Service (Port 8030)

```bash
cd services/business-logic-service
source venv/bin/activate
python -m app.main
```

---

## Step 6: Test the Services

### Test 1: Health Check

```bash
# AI Orchestration Service
curl http://localhost:8020/health

# Expected response:
# {"status":"healthy","service":"ai-orchestration-service","timestamp":"..."}

# Global Chat Service
curl http://localhost:8050/health

# Business Logic Service
curl http://localhost:8030/health
```

### Test 2: RAG System (Haystack)

```bash
# Index a document
curl -X POST http://localhost:8020/api/v1/rag/index \
  -H "Content-Type: application/json" \
  -d '[
    {
      "content": "Pizza Palace is an Italian restaurant serving authentic Neapolitan pizza with fresh ingredients.",
      "metadata": {"business_id": "123", "category": "restaurant"}
    }
  ]'

# Query the RAG system
curl -X POST http://localhost:8020/api/v1/rag/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Tell me about Italian restaurants"
  }'

# Expected response:
# {
#   "answer": "Pizza Palace is an Italian restaurant...",
#   "sources": [...],
#   "confidence": 0.85
# }
```

### Test 3: Crew AI Agents

```bash
# Process a query with Crew AI
curl -X POST http://localhost:8050/api/v1/chat/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Find Italian restaurants near me",
    "user_id": "test_user",
    "session_id": "test_session"
  }'

# Expected response:
# {
#   "status": "success",
#   "response": "I found several Italian restaurants...",
#   "intent": "search",
#   "agents_used": ["Business Search Specialist"]
# }
```

### Test 4: DSPy Prompts

```bash
# Generate text with DSPy optimization
curl -X POST http://localhost:8020/api/v1/generation/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Recommend Italian restaurants for a family dinner",
    "provider": "openai",
    "temperature": 0.7
  }'
```

### Test 5: LangGraph Workflow

```bash
# Execute a workflow
curl -X POST http://localhost:8020/api/v1/orchestration/execute \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_name": "business_onboarding",
    "message": "I want to register my restaurant",
    "session_id": "test_session"
  }'
```

---

## Step 7: Monitor Services

### View Logs

```bash
# AI Orchestration Service logs
tail -f services/ai-orchestration-service/logs/app.log

# Or view in terminal where service is running
```

### Prometheus Metrics

```bash
# View metrics
curl http://localhost:8020/metrics

# Expected output:
# ai_orchestration_requests_total{method="POST",endpoint="/api/v1/rag/query",status="200"} 5.0
# ai_orchestration_request_duration_seconds_bucket{...} 0.5
```

### Check RAG Stats

```bash
curl http://localhost:8020/api/v1/rag/stats

# Expected response:
# {
#   "status": "operational",
#   "document_count": 1,
#   "embedding_model": "sentence-transformers/all-MiniLM-L6-v2"
# }
```

---

## Common Use Cases

### Use Case 1: Document Q&A with RAG

```python
import httpx

# Index business documents
documents = [
    {
        "content": "Our restaurant serves Italian cuisine with fresh pasta and wood-fired pizza.",
        "metadata": {"business_id": "rest_001", "type": "description"}
    },
    {
        "content": "Menu items: Margherita Pizza $12, Carbonara Pasta $15, Tiramisu $8",
        "metadata": {"business_id": "rest_001", "type": "menu"}
    }
]

response = httpx.post(
    "http://localhost:8020/api/v1/rag/index",
    json=documents
)

# Query
query_response = httpx.post(
    "http://localhost:8020/api/v1/rag/query",
    json={"query": "What pasta dishes are available?"}
)

print(query_response.json()["answer"])
```

### Use Case 2: Multi-Agent Chat

```python
import httpx

# Process user query with Crew AI
response = httpx.post(
    "http://localhost:8050/api/v1/chat/query",
    json={
        "query": "I want to book a table for 4 people tomorrow at 7pm",
        "user_id": "user_123",
        "session_id": "session_456"
    }
)

result = response.json()
print(f"Intent: {result['intent']}")
print(f"Response: {result['response']}")
print(f"Agents used: {result['agents_used']}")
```

### Use Case 3: Business Search

```python
import httpx

# Search businesses
response = httpx.post(
    "http://localhost:8050/api/v1/chat/search-businesses",
    json={
        "query": "Italian restaurants",
        "category": "restaurant",
        "location": "downtown",
        "limit": 10
    }
)

businesses = response.json()["businesses"]
```

---

## Troubleshooting

### Issue: Service won't start

**Error:** `ModuleNotFoundError: No module named 'langgraph'`

**Solution:**
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Issue: Redis connection failed

**Error:** `Failed to connect to Redis`

**Solution:**
```bash
# Check if Redis is running
docker-compose ps redis

# Restart Redis
docker-compose restart redis

# Verify connection
redis-cli ping
# Expected: PONG
```

### Issue: OpenAI API error

**Error:** `AuthenticationError: Invalid API key`

**Solution:**
```bash
# Check .env file
cat .env | grep OPENAI_API_KEY

# Ensure key is set correctly
export OPENAI_API_KEY=sk-your-actual-key

# Restart service
```

### Issue: Supabase connection error

**Error:** `Failed to initialize Supabase client`

**Solution:**
```bash
# Verify Supabase credentials
echo $SUPABASE_URL
echo $SUPABASE_KEY

# Test connection
curl $SUPABASE_URL/rest/v1/ \
  -H "apikey: $SUPABASE_KEY"
```

---

## Development Workflow

### Making Changes

1. **Edit code** in your preferred editor
2. **Service auto-reloads** (if running with `reload=True`)
3. **Test changes** with curl or Postman
4. **Check logs** for errors
5. **Commit changes** to Git

### Adding New Features

```bash
# Create new branch
git checkout -b feature/new-feature

# Make changes
# ...

# Test thoroughly
# ...

# Commit and push
git add .
git commit -m "Add new feature"
git push origin feature/new-feature
```

---

## Next Steps

### 1. Explore API Documentation

```bash
# Open in browser
open http://localhost:8020/docs  # AI Orchestration
open http://localhost:8050/docs  # Global Chat
open http://localhost:8030/docs  # Business Logic
```

### 2. Run Integration Tests

```bash
# Coming soon - test suite
python -m pytest tests/
```

### 3. Deploy to Staging

```bash
# Build Docker images
docker-compose build

# Deploy to Kubernetes
kubectl apply -f infra/kubernetes/
```

### 4. Read Full Documentation

- **Phase 2 Report:** `docs/PHASE2_IMPLEMENTATION_REPORT.md`
- **Completion Report:** `docs/PHASE2_COMPLETION_REPORT.md`
- **Architecture:** `docs/micorstcuture.md`
- **Database Schema:** `docs/supabase_schema.sql`

---

## Performance Tips

### 1. Enable Caching

```python
# Redis caching is automatic for:
# - LangGraph state
# - Session data
# - Frequently accessed queries
```

### 2. Optimize RAG Queries

```python
# Use appropriate top_k
result = await rag_service.query(
    query="...",
    top_k=3  # Fewer documents = faster response
)
```

### 3. Monitor Resource Usage

```bash
# Check service memory
docker stats

# Monitor Redis
redis-cli info memory
```

---

## Support & Resources

### Documentation
- **Full Phase 2 Report:** `docs/PHASE2_COMPLETION_REPORT.md`
- **API Docs:** Visit `/docs` endpoint on each service
- **Database Schema:** `docs/supabase_schema.sql`

### Community
- **GitHub Issues:** Report bugs and request features
- **Discussions:** Ask questions and share ideas

### Contact
- **Technical Support:** Check documentation first
- **Bug Reports:** Create GitHub issue with logs

---

## Summary

You now have:

✅ **AI Orchestration Service** running with RAG, DSPy, and LangGraph  
✅ **Global Chat Service** running with Crew AI agents  
✅ **Business Logic Service** running with Temporal workflows  
✅ **Database** initialized with complete schema  
✅ **Redis** caching operational  

**Next:** Start building features, run tests, and deploy to production!

---

**Quick Start Guide Version:** 1.0.0  
**Last Updated:** October 4, 2025  
**Phase 2 Status:** ✅ Complete - Ready for Testing

---

*Happy Building! 🚀*
