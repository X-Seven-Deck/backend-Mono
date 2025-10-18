# X-sevenAI Phase 2 - Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Prerequisites
- Python 3.11+
- Docker Desktop
- API Keys (OpenAI, Groq, or Anthropic)

### Step 1: Environment Setup

```bash
cd /Users/naveen/Desktop/x7AI

# Copy environment template
cp .env.example .env

# Edit .env and add your API keys (minimum required):
# OPENAI_API_KEY=your_key_here
# SUPABASE_URL=your_supabase_url
# SUPABASE_KEY=your_supabase_key
```

### Step 2: Start Infrastructure

```bash
# Start Redis (required for AI Orchestration)
docker-compose up -d redis

# Optional: Start full stack
docker-compose up -d redis kafka zookeeper temporal cassandra
```

### Step 3: Run AI Orchestration Service

```bash
cd services/ai-orchestration-service

# Install dependencies
pip install -r requirements.txt

# Run the service
python -m app.main
```

**Service will start on:** http://localhost:8020

### Step 4: Test the API

#### Health Check
```bash
curl http://localhost:8020/health
```

#### Execute a Workflow
```bash
curl -X POST http://localhost:8020/api/v1/orchestration/execute \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_name": "business_onboarding",
    "message": "I want to register my restaurant",
    "session_id": "test_123"
  }'
```

#### Generate Text with AI
```bash
curl -X POST http://localhost:8020/api/v1/generation/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Explain the benefits of AI for restaurants",
    "provider": "openai",
    "temperature": 0.7,
    "max_tokens": 500
  }'
```

### Step 5: Explore Other Services

#### Business Logic Service (Port 8030)
```bash
cd services/business-logic-service
pip install -r requirements.txt
python -m app.main
```

#### Chat & Communication Service (Port 8040)
```bash
cd services/chat-communication-service
pip install -r requirements.txt
python -m app.main

# Test WebSocket
# Use a WebSocket client to connect to: ws://localhost:8040/ws/chat/test_room
```

#### Global Chat Service (Port 8050)
```bash
cd services/global-chat-service
pip install -r requirements.txt
python -m app.main
```

#### Analytics Dashboard Service (Port 8060)
```bash
cd services/analytics-dashboard-service
pip install -r requirements.txt
python -m app.main
```

---

## 📊 Service Ports

| Service | Port | Purpose |
|---------|------|---------|
| AI Orchestration | 8020 | LangGraph workflows, LLM generation |
| Business Logic | 8030 | Orders, reservations, inventory |
| Chat & Communication | 8040 | WebSockets, voice, WebRTC |
| Global Chat | 8050 | Cross-business queries |
| Analytics Dashboard | 8060 | Analytics, PDF processing |
| Redis | 6379 | Caching & memory |
| Kafka | 9092 | Event streaming |
| Temporal | 7233 | Workflow orchestration |
| Prometheus | 9090 | Metrics |
| Grafana | 3000 | Dashboards |

---

## 🧪 Testing Workflows

### 1. Business Onboarding Workflow
```bash
curl -X POST http://localhost:8020/api/v1/orchestration/execute \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_name": "business_onboarding",
    "message": "I want to register my restaurant called Pizza Palace",
    "session_id": "onboard_001"
  }'
```

### 2. Customer Support Workflow
```bash
curl -X POST http://localhost:8020/api/v1/orchestration/execute \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_name": "customer_support",
    "message": "What are your business hours?",
    "session_id": "support_001"
  }'
```

### 3. Order Processing Workflow
```bash
curl -X POST http://localhost:8020/api/v1/orchestration/execute \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_name": "order_processing",
    "message": "I want to order 2 pizzas and 1 salad",
    "session_id": "order_001"
  }'
```

### 4. Get Session State
```bash
curl http://localhost:8020/api/v1/orchestration/session/test_123
```

---

## 🗄️ Database Setup

### Apply Supabase Schema

1. Go to your Supabase project dashboard
2. Navigate to SQL Editor
3. Copy the contents of `docs/supabase_schema.sql`
4. Execute the SQL

**Tables Created:**
- users, businesses, menu_categories, menu_items
- orders, order_items, reservations
- chat_sessions, chat_messages
- analytics_events, uploaded_documents
- workflow_states, knowledge_base (with pgvector)

---

## 📝 API Documentation

Once services are running, visit:

- **AI Orchestration:** http://localhost:8020/docs
- **Business Logic:** http://localhost:8030/docs
- **Chat Service:** http://localhost:8040/docs
- **Global Chat:** http://localhost:8050/docs
- **Analytics:** http://localhost:8060/docs

FastAPI automatically generates interactive API documentation!

---

## 🔍 Monitoring

### Prometheus Metrics
```bash
# View metrics
curl http://localhost:8020/metrics
```

### Grafana Dashboards
```bash
# Access Grafana
open http://localhost:3000
# Login: admin/admin
```

---

## 🐛 Troubleshooting

### Redis Connection Error
```bash
# Check if Redis is running
docker ps | grep redis

# Start Redis if not running
docker-compose up -d redis
```

### Import Errors
```bash
# Make sure you're in the service directory
cd services/ai-orchestration-service

# Install dependencies
pip install -r requirements.txt
```

### Port Already in Use
```bash
# Find process using port 8020
lsof -i :8020

# Kill the process
kill -9 <PID>
```

### LLM API Errors
- Check your API keys in `.env`
- Verify you have credits/quota
- Try a different provider (Groq is faster and cheaper)

---

## 📚 Next Steps

1. **Read the Full Report:** `docs/PHASE2_IMPLEMENTATION_REPORT.md`
2. **Review Architecture:** `docs/micorstcuture.md`
3. **Understand Workflows:** `docs/framework.md`
4. **Check Database Schema:** `docs/supabase_schema.sql`
5. **Explore Code:** Start with `services/ai-orchestration-service/app/main.py`

---

## 🎯 What Works Now

✅ **LangGraph Workflows** - 3 complete workflows  
✅ **Multi-LLM Support** - OpenAI, Groq, Anthropic with fallback  
✅ **Redis Caching** - State management and memory  
✅ **WebSocket Chat** - Real-time messaging  
✅ **Health Checks** - All services  
✅ **Prometheus Metrics** - Observability  
✅ **Structured Logging** - JSON logs with trace IDs  

## 🔧 What Needs Integration

🔧 **Haystack RAG** - Framework ready, needs pipeline  
🔧 **Crew AI Agents** - Framework ready, needs agent definitions  
🔧 **Temporal Workflows** - Client ready, needs workflow implementations  
🔧 **Kafka Events** - Infrastructure ready, needs topics  
🔧 **Voice Services** - Endpoints ready, needs API integration  
🔧 **LiveKit WebRTC** - Endpoints ready, needs server  
🔧 **PDF Processing** - Libraries ready, needs full implementation  

---

## 💡 Pro Tips

1. **Start with AI Orchestration Service** - It's the most complete
2. **Use Groq for Development** - Faster and cheaper than OpenAI
3. **Check Logs** - All services use structured JSON logging
4. **Monitor Metrics** - Prometheus tracks all requests
5. **Use Docker Compose** - Easier than running services individually

---

## 🆘 Need Help?

- **Documentation:** Check `/docs` folder
- **Code Examples:** Look at existing endpoints
- **API Docs:** Visit `/docs` endpoint on each service
- **Logs:** Check console output for errors

---

**Happy Coding! 🚀**
