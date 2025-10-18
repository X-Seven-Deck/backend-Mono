# Phase 2 Integration Checklist

## 🎯 Remaining Work to Complete Phase 2

This checklist covers the integrations needed to move from 85% to 100% completion.

---

## Week 1: AI & RAG Integrations

### 1. Haystack RAG Pipeline ⏱️ 2-3 days

**File:** `services/ai-orchestration-service/app/services/rag_pipeline.py`

- [ ] Install and configure Pinecone or pgvector
- [ ] Create document store connection
- [ ] Implement document indexing pipeline
  ```python
  from haystack import Pipeline
  from haystack.components.retrievers import InMemoryBM25Retriever
  from haystack.components.generators import OpenAIGenerator
  ```
- [ ] Create retrieval pipeline
- [ ] Integrate with existing RAG endpoints
- [ ] Test with sample business data
- [ ] Add caching for frequent queries

**Files to Update:**
- `services/ai-orchestration-service/app/routes/rag.py`
- `services/ai-orchestration-service/app/services/rag_pipeline.py` (NEW)

---

### 2. Crew AI Agents ⏱️ 2-3 days

**File:** `services/global-chat-service/app/services/crew_agents.py`

- [ ] Define agent roles:
  - [ ] Search Agent (business queries)
  - [ ] Recommendation Agent (suggestions)
  - [ ] Booking Agent (reservations)
  - [ ] Order Agent (purchases)
- [ ] Create agent tools
- [ ] Define crew workflows
- [ ] Integrate with Global Chat endpoints
- [ ] Test multi-agent collaboration

**Example:**
```python
from crewai import Agent, Task, Crew

search_agent = Agent(
    role='Business Search Specialist',
    goal='Find relevant businesses based on user queries',
    backstory='Expert at understanding user needs',
    tools=[search_tool, filter_tool]
)
```

**Files to Update:**
- `services/global-chat-service/app/services/crew_agents.py` (NEW)
- `services/global-chat-service/app/routes/chat.py`

---

### 3. DSPy Prompt Optimization ⏱️ 1-2 days

**File:** `services/ai-orchestration-service/app/services/dspy_prompts.py`

- [ ] Define DSPy modules for common tasks
- [ ] Create training examples
- [ ] Implement prompt optimization
- [ ] Add prompt versioning
- [ ] Integrate with LLM provider
- [ ] Test prompt quality

**Example:**
```python
import dspy

class BusinessQuery(dspy.Signature):
    """Answer business-related questions accurately."""
    question = dspy.InputField()
    context = dspy.InputField()
    answer = dspy.OutputField()

class RAGPipeline(dspy.Module):
    def __init__(self):
        self.retrieve = dspy.Retrieve(k=5)
        self.generate = dspy.ChainOfThought(BusinessQuery)
```

**Files to Update:**
- `services/ai-orchestration-service/app/services/dspy_prompts.py` (NEW)

---

### 4. PyABSA Sentiment Analysis ⏱️ 1 day

**File:** `services/ai-orchestration-service/app/services/sentiment_analyzer.py`

- [ ] Load PyABSA model
- [ ] Create sentiment analysis endpoint
- [ ] Integrate with chat services
- [ ] Add aspect extraction
- [ ] Test with customer reviews

**Example:**
```python
from pyabsa import AspectSentimentTripletExtraction as ASTE

model = ASTE.ATEPCCheckpointManager.get_checkpoint('english')

def analyze_sentiment(text: str):
    result = model.predict(text)
    return result
```

**Files to Update:**
- `services/ai-orchestration-service/app/services/sentiment_analyzer.py` (NEW)
- `services/ai-orchestration-service/app/routes/sentiment.py` (NEW)

---

## Week 2: Workflows & Events

### 5. Temporal Workflows ⏱️ 2-3 days

**Files:** `services/business-logic-service/app/workflows/`

- [ ] Set up Temporal worker
- [ ] Define order workflow
  ```python
  @workflow.defn
  class OrderWorkflow:
      @workflow.run
      async def run(self, order_data: dict) -> str:
          # Validate order
          # Process payment
          # Update inventory
          # Send notifications
          # Return order ID
  ```
- [ ] Define reservation workflow
- [ ] Define payment workflow
- [ ] Add workflow activities
- [ ] Test workflow execution
- [ ] Add error handling and retries

**Files to Create:**
- `services/business-logic-service/app/workflows/__init__.py`
- `services/business-logic-service/app/workflows/order_workflow.py`
- `services/business-logic-service/app/workflows/reservation_workflow.py`
- `services/business-logic-service/app/workflows/activities.py`
- `services/business-logic-service/app/workers/temporal_worker.py`

---

### 6. Kafka Event Streaming ⏱️ 2 days

**Files:** `services/*/app/events/`

- [ ] Configure Kafka topics
  - [ ] orders
  - [ ] reservations
  - [ ] analytics
  - [ ] notifications
- [ ] Implement producers
  ```python
  from aiokafka import AIOKafkaProducer
  
  async def publish_order_event(order_data: dict):
      producer = AIOKafkaProducer(bootstrap_servers='localhost:9092')
      await producer.start()
      await producer.send('orders', json.dumps(order_data).encode())
  ```
- [ ] Implement consumers
- [ ] Add event schemas
- [ ] Test event flow
- [ ] Add error handling

**Files to Create:**
- `services/business-logic-service/app/events/producer.py`
- `services/analytics-dashboard-service/app/events/consumer.py`
- `shared/schemas/events.py`

---

## Week 3: Voice & Communication

### 7. ElevenLabs Integration ⏱️ 1-2 days

**File:** `services/chat-communication-service/app/services/voice_service.py`

- [ ] Set up ElevenLabs client
- [ ] Implement text-to-speech
  ```python
  from elevenlabs import generate, Voice
  
  async def text_to_speech(text: str, voice_id: str = "default"):
      audio = generate(
          text=text,
          voice=Voice(voice_id=voice_id),
          model="eleven_monolingual_v1"
      )
      return audio
  ```
- [ ] Add voice selection
- [ ] Implement audio streaming
- [ ] Test voice quality
- [ ] Add caching for common phrases

**Files to Update:**
- `services/chat-communication-service/app/services/voice_service.py` (NEW)
- `services/chat-communication-service/app/routes/voice.py`

---

### 8. Whisper Speech-to-Text ⏱️ 1 day

**File:** `services/chat-communication-service/app/services/transcription_service.py`

- [ ] Load Whisper model
- [ ] Implement transcription
  ```python
  import whisper
  
  model = whisper.load_model("base")
  
  async def transcribe_audio(audio_file):
      result = model.transcribe(audio_file)
      return result["text"]
  ```
- [ ] Add language detection
- [ ] Optimize for real-time
- [ ] Test accuracy

**Files to Update:**
- `services/chat-communication-service/app/services/transcription_service.py` (NEW)
- `services/chat-communication-service/app/routes/voice.py`

---

### 9. LiveKit WebRTC ⏱️ 2 days

**File:** `services/chat-communication-service/app/services/livekit_service.py`

- [ ] Deploy LiveKit server (Docker)
- [ ] Implement room creation
  ```python
  from livekit import api
  
  async def create_room(room_name: str):
      livekit_api = api.LiveKitAPI(
          url=settings.livekit_url,
          api_key=settings.livekit_api_key,
          api_secret=settings.livekit_api_secret
      )
      room = await livekit_api.room.create_room(
          api.CreateRoomRequest(name=room_name)
      )
      return room
  ```
- [ ] Implement token generation
- [ ] Add participant management
- [ ] Implement AI handover
- [ ] Test video/audio calls

**Files to Update:**
- `services/chat-communication-service/app/services/livekit_service.py` (NEW)
- `services/chat-communication-service/app/routes/webrtc.py`

---

## Week 4: Data & Database

### 10. PDF Processing ⏱️ 2-3 days

**File:** `services/analytics-dashboard-service/app/services/pdf_processor.py`

- [ ] Implement PDF text extraction
  ```python
  import pdfplumber
  
  async def extract_text(pdf_path: str):
      with pdfplumber.open(pdf_path) as pdf:
          text = ""
          for page in pdf.pages:
              text += page.extract_text()
      return text
  ```
- [ ] Implement image extraction
- [ ] Add OCR for scanned PDFs (Tesseract)
- [ ] Implement AI categorization (OpenAI)
- [ ] Add structured data extraction
- [ ] Test with sample menus

**Files to Update:**
- `services/analytics-dashboard-service/app/services/pdf_processor.py` (NEW)
- `services/analytics-dashboard-service/app/routes/pdf.py`

---

### 11. Supabase Queries ⏱️ 2-3 days

**Files:** `services/*/app/repositories/`

- [ ] Create repository classes
  ```python
  from supabase import create_client
  
  class BusinessRepository:
      def __init__(self):
          self.client = create_client(url, key)
      
      async def get_business(self, business_id: str):
          response = self.client.table('businesses').select('*').eq('id', business_id).execute()
          return response.data
  ```
- [ ] Implement CRUD operations for all tables
- [ ] Add query optimization
- [ ] Implement real-time subscriptions
- [ ] Test with sample data

**Files to Create:**
- `services/business-logic-service/app/repositories/order_repository.py`
- `services/business-logic-service/app/repositories/reservation_repository.py`
- `services/global-chat-service/app/repositories/business_repository.py`
- `services/analytics-dashboard-service/app/repositories/analytics_repository.py`

---

### 12. Apply Database Schema ⏱️ 1 hour

- [ ] Go to Supabase dashboard
- [ ] Open SQL Editor
- [ ] Copy `docs/supabase_schema.sql`
- [ ] Execute SQL
- [ ] Verify all tables created
- [ ] Test RLS policies
- [ ] Insert sample data

---

## Testing & Quality Assurance

### 13. Unit Tests ⏱️ 3-4 days

**Files:** `services/*/tests/`

- [ ] Test AI Orchestration workflows
- [ ] Test LLM provider fallback
- [ ] Test WebSocket connections
- [ ] Test Temporal workflows
- [ ] Test Kafka events
- [ ] Test database operations
- [ ] Aim for >80% coverage

**Example:**
```python
import pytest
from app.services.langgraph_orchestrator import langgraph_orchestrator

@pytest.mark.asyncio
async def test_business_onboarding_workflow():
    result = await langgraph_orchestrator.execute_workflow(
        workflow_name="business_onboarding",
        initial_message="I want to register my restaurant",
        session_id="test_123"
    )
    assert result["status"] == "success"
```

---

### 14. Integration Tests ⏱️ 2 days

- [ ] Test end-to-end workflows
- [ ] Test service communication
- [ ] Test event flow (Kafka)
- [ ] Test database transactions
- [ ] Test API endpoints

---

### 15. Load Testing ⏱️ 1-2 days

- [ ] Set up Locust
- [ ] Create load test scenarios
- [ ] Test 1,000 concurrent users
- [ ] Measure response times
- [ ] Identify bottlenecks
- [ ] Optimize as needed

**Example:**
```python
from locust import HttpUser, task, between

class X7AIUser(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def generate_text(self):
        self.client.post("/api/v1/generation/generate", json={
            "prompt": "Test prompt",
            "provider": "openai"
        })
```

---

## Documentation & Deployment

### 16. API Documentation ⏱️ 1 day

- [ ] Review auto-generated docs
- [ ] Add examples to all endpoints
- [ ] Create Postman collection
- [ ] Write integration guides
- [ ] Document authentication flow

---

### 17. Kubernetes Manifests ⏱️ 2 days

**Files:** `services/*/k8s/`

- [ ] Update deployment.yaml for each service
- [ ] Add resource limits
- [ ] Configure health checks
- [ ] Set up ConfigMaps
- [ ] Create Secrets
- [ ] Test deployments

---

### 18. CI/CD Pipeline ⏱️ 1-2 days

**File:** `.github/workflows/ci.yml`

- [ ] Set up GitHub Actions
- [ ] Add automated testing
- [ ] Add Docker image builds
- [ ] Add deployment automation
- [ ] Test pipeline

---

## Priority Order

### High Priority (Week 1-2)
1. ✅ Haystack RAG Pipeline
2. ✅ Crew AI Agents
3. ✅ Temporal Workflows
4. ✅ Kafka Events
5. ✅ Supabase Queries

### Medium Priority (Week 3)
6. ✅ ElevenLabs Voice
7. ✅ Whisper STT
8. ✅ LiveKit WebRTC
9. ✅ PDF Processing

### Lower Priority (Week 4)
10. ✅ DSPy Optimization
11. ✅ PyABSA Sentiment
12. ✅ Testing
13. ✅ Documentation

---

## Estimated Timeline

| Week | Focus | Hours |
|------|-------|-------|
| Week 1 | AI & RAG | 40h |
| Week 2 | Workflows & Events | 40h |
| Week 3 | Voice & Communication | 40h |
| Week 4 | Testing & Docs | 40h |
| **Total** | **Full Integration** | **160h** |

---

## Quick Wins (Can Do Today)

1. ✅ Apply Supabase schema (30 min)
2. ✅ Set up Kafka topics (1 hour)
3. ✅ Deploy LiveKit with Docker (1 hour)
4. ✅ Test existing endpoints (1 hour)
5. ✅ Add sample data to database (1 hour)

---

## Resources Needed

### API Keys
- [ ] OpenAI API key
- [ ] Groq API key (optional)
- [ ] Anthropic API key (optional)
- [ ] ElevenLabs API key
- [ ] Pinecone API key (or use pgvector)

### Infrastructure
- [ ] Supabase project
- [ ] Redis instance
- [ ] Kafka cluster
- [ ] Temporal server
- [ ] LiveKit server

### Tools
- [ ] Docker Desktop
- [ ] Python 3.11+
- [ ] Postman (testing)
- [ ] Locust (load testing)

---

## Success Criteria

### Phase 2 Complete When:
- ✅ All integrations working
- ✅ 80%+ test coverage
- ✅ Load test passes (1k users)
- ✅ Documentation complete
- ✅ All services deployed locally
- ✅ No critical bugs

---

## Notes

- Start with high-priority items
- Test each integration before moving to next
- Keep documentation updated
- Commit frequently
- Ask for help when stuck

---

**Last Updated:** October 4, 2025  
**Status:** Ready to start integrations  
**Target Completion:** 4 weeks
