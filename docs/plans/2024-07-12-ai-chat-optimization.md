# AI Chat System Optimization Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Systematically optimize AI chat functionality to achieve DeepSeek-level performance with <3s response times, <5% error rate, and streaming character-by-character output.

**Architecture:** Multi-layered optimization including performance monitoring, priority-based request scheduling, Redis caching, WebSocket streaming, and multi-dimensional content validation.

**Tech Stack:** FastAPI, Redis, WebSocket, Prometheus/Sentry, GLM-4.5-Air, Vue 3 streaming

---

## Task 1: Performance Monitoring Setup

**Files:**
- Create: `backend/app/middleware/tracing.py`
- Modify: `backend/main.py:20-35`
- Test: `tests/test_tracing.py`

**Step 1: Write the failing test**

```python
# tests/test_tracing.py
import pytest
from unittest.mock import Mock
from app.middleware.tracing import PerformanceTracer

def test_tracer_measures_request_time():
    tracer = PerformanceTracer()
    with tracer.measure("chat_request"):
        import time
        time.sleep(0.1)
    
    metrics = tracer.get_metrics()
    assert "chat_request" in metrics
    assert metrics["chat_request"]["duration"] > 0.05
```

**Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_tracing.py::test_tracer_measures_request_time -v`
Expected: FAIL with "PerformanceTracer not defined"

**Step 3: Write minimal implementation**

```python
# backend/app/middleware/tracing.py
import time
from contextlib import contextmanager
from typing import Dict, Any
import threading

class PerformanceTracer:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'metrics'):
            self.metrics = {}
            self._lock = threading.Lock()
    
    @contextmanager
    def measure(self, operation: str):
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            with self._lock:
                if operation not in self.metrics:
                    self.metrics[operation] = []
                self.metrics[operation].append({
                    "duration": duration,
                    "timestamp": time.time()
                })
    
    def get_metrics(self) -> Dict[str, Any]:
        return self.metrics
```

**Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/test_tracing.py::test_tracer_measures_request_time -v`
Expected: PASS

**Step 5: Commit**

```bash
cd backend
git add app/middleware/tracing.py tests/test_tracing.py
git commit -m "feat: add performance tracing middleware"
```

---

## Task 2: Redis Cache Implementation

**Files:**
- Create: `backend/app/services/cache.py`
- Create: `backend/app/services/cache_manager.py`
- Test: `tests/test_cache.py`

**Step 1: Write the failing test**

```python
# tests/test_cache.py
import pytest
from app.services.cache import CacheService

def test_cache_set_and_get():
    cache = CacheService()
    cache.set("test_key", "test_value", ttl=300)
    value = cache.get("test_key")
    assert value == "test_value"
```

**Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_cache.py::test_cache_set_and_get -v`
Expected: FAIL with "CacheService not defined"

**Step 3: Write minimal implementation**

```python
# backend/app/services/cache.py
import redis
import json
from typing import Any, Optional
from datetime import timedelta

class CacheService:
    def __init__(self, host="localhost", port=6379, db=0):
        self.redis = redis.Redis(host=host, port=port, db=db, decode_responses=True)
    
    def set(self, key: str, value: Any, ttl: int = 300):
        """Set cache value with TTL"""
        self.redis.setex(key, ttl, json.dumps(value))
    
    def get(self, key: str) -> Any:
        """Get cached value"""
        value = self.redis.get(key)
        return json.loads(value) if value else None
    
    def delete(self, key: str):
        """Delete cached value"""
        self.redis.delete(key)
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        return self.redis.exists(key) > 0
```

**Step 4: Update main.py to integrate tracing**

```python
# backend/main.py (after line 35)
from app.middleware.tracing import PerformanceTracer

# Add tracer instance
tracer = PerformanceTracer()
```

**Step 5: Run test to verify it passes**

Run: `cd backend && pytest tests/test_cache.py::test_cache_set_and_get -v`
Expected: PASS

**Step 6: Commit**

```bash
cd backend
git add app/services/cache.py app/services/cache_manager.py tests/test_cache.py
git commit -m "feat: implement Redis cache service"
```

---

## Task 3: Request Priority Scheduler

**Files:**
- Create: `backend/app/scheduler/priority_scheduler.py`
- Modify: `backend/main.py:265`
- Test: `tests/test_scheduler.py`

**Step 1: Write the failing test**

```python
# tests/test_scheduler.py
import pytest
from app.scheduler.priority_scheduler import PriorityScheduler

async def test_priority_scheduler():
    scheduler = PriorityScheduler()
    await scheduler.enqueue("user123", "test message", priority="P1")
    task = await scheduler.get_next_task()
    assert task.user_id == "user123"
    assert task.content == "test message"
```

**Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_scheduler.py::test_priority_scheduler -v`
Expected: FAIL with "PriorityScheduler not defined"

**Step 3: Write minimal implementation**

```python
# backend/app/scheduler/priority_scheduler.py
import asyncio
from dataclasses import dataclass
from typing import Dict, List
import heapq
from enum import Enum

class Priority(Enum):
    P0 = 0  # Highest
    P1 = 1  # Normal
    P2 = 2  # Lowest

@dataclass
class Task:
    user_id: str
    content: str
    priority: Priority
    timestamp: float
    task_id: str

class PriorityScheduler:
    def __init__(self):
        self.queues: Dict[Priority, List[Task]] = {
            Priority.P0: [],
            Priority.P1: [],
            Priority.P2: []
        }
        self.task_counter = 0
    
    async def enqueue(self, user_id: str, content: str, priority: str = "P1"):
        """Add task to appropriate queue"""
        priority_enum = Priority[priority]
        task = Task(
            user_id=user_id,
            content=content,
            priority=priority_enum,
            timestamp=asyncio.get_event_loop().time(),
            task_id=f"task_{self.task_counter}"
        )
        self.task_counter += 1
        
        # Simple heapq implementation for each priority
        heapq.heappush(self.queues[priority_enum], task)
    
    async def get_next_task(self) -> Task:
        """Get next task based on priority"""
        # Check P0 first, then P1, then P2
        for priority in [Priority.P0, Priority.P1, Priority.P2]:
            if self.queues[priority]:
                return heapq.heappop(self.queues[priority])
        return None
```

**Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/test_scheduler.py::test_priority_scheduler -v`
Expected: PASS

**Step 5: Commit**

```bash
cd backend
git add app/scheduler/priority_scheduler.py tests/test_scheduler.py
git commit -m "feat: implement priority task scheduler"
```

---

## Task 4: WebSocket Streaming Implementation

**Files:**
- Create: `backend/app/websocket/streaming.py`
- Modify: `backend/main.py:264`
- Test: `tests/test_streaming.py`

**Step 1: Write the failing test**

```python
# tests/test_streaming.py
import pytest
from fastapi import WebSocket
from app.websocket.streaming import StreamingHandler

async def test_streaming_handler():
    handler = StreamingHandler()
    # Mock WebSocket
    mock_ws = Mock(spec=WebSocket)
    await handler.send_stream(mock_ws, "test message", "session123")
    mock_ws.send_text.assert_called()
```

**Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_streaming.py::test_streaming_handler -v`
Expected: FAIL with "StreamingHandler not defined"

**Step 3: Write minimal implementation**

```python
# backend/app/websocket/streaming.py
import asyncio
from fastapi import WebSocket
from typing import AsyncGenerator
import json

class StreamingHandler:
    async def send_stream(self, websocket: WebSocket, content: str, session_id: str):
        """Send content character by character over WebSocket"""
        await websocket.accept()
        
        for char in content:
            # Send each character with streaming format
            message = {
                "type": "stream",
                "session_id": session_id,
                "data": {
                    "delta": char,
                    "full_content": content[:content.index(char) + 1],
                    "status": "streaming"
                }
            }
            await websocket.send_text(json.dumps(message))
            await asyncio.sleep(0.01)  # Small delay for readability
        
        # Send final message
        final_message = {
            "type": "stream",
            "session_id": session_id,
            "data": {
                "delta": "",
                "full_content": content,
                "status": "complete"
            }
        }
        await websocket.send_text(json.dumps(final_message))
        await websocket.close()
```

**Step 4: Update chat endpoint for streaming**

```python
# backend/main.py (modify chat endpoint at line 264)
@app.post("/api/v1/ai/chat/stream")
async def chat_stream(request: ChatRequest, websocket: WebSocket):
    try:
        with tracer.measure("chat_stream"):
            # Process with priority scheduler
            # (Implementation will be added in later tasks)
            
            # For now, return simple streaming
            streaming_handler = StreamingHandler()
            await streaming_handler.send_stream(
                websocket, 
                f"Streaming response for: {request.userMessage}",
                "temp_session"
            )
    except Exception as e:
        await websocket.close(code=1000, reason=str(e))
```

**Step 5: Run test to verify it passes**

Run: `cd backend && pytest tests/test_streaming.py::test_streaming_handler -v`
Expected: PASS

**Step 6: Commit**

```bash
cd backend
git add app/websocket/streaming.py tests/test_streaming.py
git commit -m "feat: implement WebSocket streaming handler"
```

---

## Task 5: Enhanced Chat API with Priority and Cache

**Files:**
- Modify: `backend/main.py:265-287`
- Create: `backend/app/services/chat_service.py`
- Test: `tests/test_chat_service.py`

**Step 1: Write the failing test**

```python
# tests/test_chat_service.py
import pytest
from app.services.chat_service import ChatService

def test_chat_with_cache():
    service = ChatService()
    response = service.generate_response("Hello", "test_user")
    assert "Hello" in response
    # Check if cached
    cached = service.cache.get(f"response:test_user:Hello")
    assert cached is not None
```

**Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_chat_service.py::test_chat_with_cache -v`
Expected: FAIL with "ChatService not defined"

**Step 3: Write minimal implementation**

```python
# backend/app/services/chat_service.py
from app.services.cache import CacheService
from app.scheduler.priority_scheduler import PriorityScheduler, Priority
import hashlib

class ChatService:
    def __init__(self):
        self.cache = CacheService()
        self.scheduler = PriorityScheduler()
        self.cache_key_prefix = "chat_response"
    
    async def generate_response(self, user_message: str, user_id: str, system_prompt: str = None) -> str:
        """Generate response with caching and priority"""
        # Create cache key
        message_hash = hashlib.md5(f"{user_id}:{user_message}".encode()).hexdigest()
        cache_key = f"{self.cache_key_prefix}:{message_hash}"
        
        # Check cache first
        cached_response = self.cache.get(cache_key)
        if cached_response:
            return cached_response
        
        # Generate new response (simplified for now)
        response = f"Processed: {user_message}"
        
        # Cache the response
        self.cache.set(cache_key, response, ttl=3600)
        
        return response
```

**Step 4: Update main.py to use ChatService**

```python
# backend/main.py (after imports)
from app.services.chat_service import ChatService

chat_service = ChatService()

@app.post("/api/v1/ai/chat")
async def chat(request: ChatRequest):
    try:
        with tracer.measure("chat_request"):
            ai_response = await chat_service.generate_response(
                request.userMessage, 
                "default_user",  # In real app, get from auth
                request.systemPrompt
            )
            
            return APIResponse(
                success=True,
                message="Chat generated successfully",
                data={"content": ai_response},
                timestamp=datetime.utcnow().isoformat()
            )
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

**Step 5: Run test to verify it passes**

Run: `cd backend && pytest tests/test_chat_service.py::test_chat_with_cache -v`
Expected: PASS

**Step 6: Commit**

```bash
cd backend
git add app/services/chat_service.py tests/test_chat_service.py main.py
git commit -m "feat: enhance chat API with caching and priority"
```

---

## Task 6: Frontend Streaming Component

**Files:**
- Create: `frontend/src/composables/useStreamingChat.ts`
- Modify: `frontend/src/pages/ChatPage.vue:100-200`
- Test: `frontend/tests/StreamingChat.spec.ts`

**Step 1: Write the failing test**

```typescript
// frontend/tests/StreamingChat.spec.ts
import { useStreamingChat } from '@/composables/useStreamingChat'

describe('useStreamingChat', () => {
  it('should stream response character by character', async () => {
    const { content, startStream } = useStreamingChat()
    
    await startStream('Hello')
    expect(content.value.length).toBeGreaterThan(0)
  })
})
```

**Step 2: Run test to verify it fails**

Run: `cd frontend && npm run test:unit StreamingChat.spec.ts`
Expected: FAIL with "useStreamingChat not defined"

**Step 3: Write minimal implementation**

```typescript
// frontend/src/composables/useStreamingChat.ts
import { ref, onUnmounted } from 'vue'

interface StreamMessage {
  type: 'stream'
  session_id: string
  data: {
    delta: string
    full_content: string
    status: 'streaming' | 'complete'
  }
}

export function useStreamingChat() {
  const content = ref('')
  const buffer = ref('')
  let abortController: AbortController | null = null
  let ws: WebSocket | null = null

  async function startStream(prompt: string, sessionId: string = 'temp') {
    abortController = new AbortController()
    
    return new Promise<void>((resolve, reject) => {
      // WebSocket connection
      ws = new WebSocket('ws://localhost:8000/api/v1/ai/chat/stream')
      
      ws.onopen = () => {
        // Send initial message
        ws!.send(JSON.stringify({
          userMessage: prompt,
          systemPrompt: '',
          messages: [],
          session_id: sessionId
        }))
      }
      
      ws.onmessage = (event) => {
        try {
          const message: StreamMessage = JSON.parse(event.data)
          if (message.type === 'stream') {
            buffer.value += message.data.delta
            content.value = buffer.value
            
            if (message.data.status === 'complete') {
              ws!.close()
              resolve()
            }
          }
        } catch (error) {
          reject(error)
        }
      }
      
      ws.onerror = (error) => {
        reject(error)
      }
      
      ws.onclose = () => {
        resolve()
      }
    })
  }

  function stopStream() {
    if (abortController) {
      abortController.abort()
    }
    if (ws) {
      ws.close()
    }
    content.value = ''
    buffer.value = ''
  }

  onUnmounted(() => {
    stopStream()
  })

  return {
    content,
    startStream,
    stopStream
  }
}
```

**Step 4: Update ChatPage.vue to use streaming**

```vue
<!-- frontend/src/pages/ChatPage.vue (after line 200) -->
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useStreamingChat } from '@/composables/useStreamingChat'

// Add streaming chat
const { content: streamingContent, startStream: startStreaming } = useStreamingChat()

// Add method to handle streaming chat
const handleStreamingChat = async (message: string) => {
  try {
    await startStreaming(message, currentConversationId.value)
    // Add to conversation history
    addMessage('user', message)
    addMessage('assistant', streamingContent.value)
  } catch (error) {
    console.error('Streaming error:', error)
  }
}
</script>

<template>
  <!-- Update send button to support streaming -->
  <button @click="handleStreamingChat(inputMessage)">
    发送流式消息
  </button>
  
  <!-- Show streaming content -->
  <div v-if="streamingContent" class="streaming-content">
    {{ streamingContent }}
  </div>
</template>
```

**Step 5: Run test to verify it passes**

Run: `cd frontend && npm run test:unit StreamingChat.spec.ts`
Expected: PASS

**Step 6: Commit**

```bash
cd frontend
git src/composables/useStreamingChat.ts tests/StreamingChat.spec.ts pages/ChatPage.vue
git commit -m "feat: implement frontend streaming chat component"
```

---

## Task 7: Content Validation System

**Files:**
- Create: `backend/app/services/validator.py`
- Modify: `backend/app/services/chat_service.py`
- Test: `tests/test_validator.py`

**Step 1: Write the failing test**

```python
# tests/test_validator.py
from app.services.validator import ContentValidator

def test_fact_checker():
    validator = ContentValidator()
    result = validator.check_facts("The capital of France is Paris")
    assert result["is_valid"] == True

def test_logic_checker():
    validator = ContentValidator()
    result = validator.check_logic("I am 25 years old", {"age": "25"})
    assert result["is_valid"] == True
```

**Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_validator.py::test_fact_checker -v`
Expected: FAIL with "ContentValidator not defined"

**Step 3: Write minimal implementation**

```python
# backend/app/services/validator.py
import re
from typing import Dict, Any, List
from datetime import datetime

class ContentValidator:
    def __init__(self):
        self.fact_patterns = {
            'date': r'\d{4}-\d{2}-\d{2}',
            'time': r'\d{2}:\d{2}',
            'email': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
            'phone': r'1[3-9]\d{9}'
        }
        
        self.logic_rules = {
            'age_consistency': self._check_age_consistency,
            'date_consistency': self._check_date_consistency
        }
    
    def check_facts(self, content: str) -> Dict[str, Any]:
        """Check factual accuracy of content"""
        issues = []
        
        # Check for potential factual issues
        for fact_type, pattern in self.fact_patterns.items():
            matches = re.findall(pattern, content)
            if matches:
                issues.append({
                    "type": fact_type,
                    "matches": matches,
                    "note": f"Found {fact_type} patterns"
                })
        
        return {
            "is_valid": len(issues) == 0 or self._is_minor(issues),
            "issues": issues,
            "score": self._calculate_fact_score(content)
        }
    
    def check_logic(self, content: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Check logical consistency"""
        issues = []
        
        for rule_name, rule_func in self.logic_rules.items():
            try:
                result = rule_func(content, context)
                if not result["valid"]:
                    issues.append(result)
            except Exception as e:
                issues.append({
                    "rule": rule_name,
                    "error": str(e),
                    "severity": "high"
                })
        
        return {
            "is_valid": len(issues) == 0,
            "issues": issues,
            "score": self._calculate_logic_score(content, context)
        }
    
    def check_coherence(self, content: str, history: List[str]) -> Dict[str, Any]:
        """Check contextual coherence"""
        # Simple coherence check - in production, use NLP models
        sentences = content.split('.')
        if len(sentences) < 2:
            return {
                "is_valid": False,
                "issues": [{"type": "too_short", "message": "Response too brief"}],
                "score": 0.3
            }
        
        return {
            "is_valid": True,
            "issues": [],
            "score": 0.8
        }
    
    def validate_response(self, content: str, context: Dict[str, Any] = None, history: List[str] = None) -> Dict[str, Any]:
        """Comprehensive validation"""
        if context is None:
            context = {}
        if history is None:
            history = []
        
        fact_check = self.check_facts(content)
        logic_check = self.check_logic(content, context)
        coherence_check = self.check_coherence(content, history)
        
        overall_valid = all([
            fact_check["is_valid"],
            logic_check["is_valid"],
            coherence_check["is_valid"]
        ])
        
        return {
            "is_valid": overall_valid,
            "fact_check": fact_check,
            "logic_check": logic_check,
            "coherence_check": coherence_check,
            "overall_score": (fact_check["score"] + logic_check["score"] + coherence_check["score"]) / 3
        }
    
    def _is_minor(self, issues: List[Dict]) -> bool:
        """Determine if issues are minor"""
        return len(issues) <= 2 and all(issue.get("severity", "low") == "low" for issue in issues)
    
    def _calculate_fact_score(self, content: str) -> float:
        """Calculate factual accuracy score"""
        # Simplified scoring
        base_score = 1.0
        penalty = 0.1 * len(re.findall(r'\d+', content))  # Penalize excessive numbers
        return max(0.0, base_score - penalty)
    
    def _calculate_logic_score(self, content: str, context: Dict[str, Any]) -> float:
        """Calculate logical consistency score"""
        # Simplified scoring
        return 0.8 if len(content) > 10 else 0.5
    
    def _check_age_consistency(self, content: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Check age consistency in context"""
        if "age" in context:
            age = int(context["age"])
            if age < 18 and "adult" in content.lower():
                return {"valid": False, "issue": "Age inconsistency"}
        return {"valid": True}
    
    def _check_date_consistency(self, content: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Check date consistency"""
        # Basic date validation
        dates = re.findall(r'\d{4}-\d{2}-\d{2}', content)
        if dates:
            try:
                for date_str in dates:
                    datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                return {"valid": False, "issue": "Invalid date format"}
        return {"valid": True}
```

**Step 4: Update ChatService to use validator**

```python
# backend/app/services/chat_service.py (update generate_response method)
async def generate_response(self, user_message: str, user_id: str, system_prompt: str = None) -> str:
    """Generate response with caching, validation and priority"""
    # Create cache key
    message_hash = hashlib.md5(f"{user_id}:{user_message}".encode()).hexdigest()
    cache_key = f"{self.cache_key_prefix}:{message_hash}"
    
    # Check cache first
    cached_response = self.cache.get(cache_key)
    if cached_response:
        return cached_response
    
    # Generate new response (simplified for now)
    response = f"Processed: {user_message}"
    
    # Validate response
    validator = ContentValidator()
    validation_result = validator.validate_response(response)
    
    if not validation_result["is_valid"]:
        # Fallback to safe response
        response = "I understand your message. Let me provide a helpful response."
    
    # Cache the validated response
    self.cache.set(cache_key, response, ttl=3600)
    
    return response
```

**Step 5: Run test to verify it passes**

Run: `cd backend && pytest tests/test_validator.py::test_fact_checker -v`
Expected: PASS

**Step 6: Commit**

```bash
cd backend
git add app/services/validator.py tests/test_validator.py
git commit -m "feat: implement content validation system"
```

---

## Task 8: Redis Session Management

**Files:**
- Create: `backend/app/services/session_manager.py`
- Create: `backend/app/models/session.py`
- Test: `tests/test_session_manager.py`

**Step 1: Write the failing test**

```python
# tests/test_session_manager.py
import pytest
from app.services.session_manager import SessionManager

async def test_session_creation():
    manager = SessionManager()
    session = await manager.create_session("user123", "comp456")
    assert session.user_id == "user123"
    assert session.companion_id == "comp456"
    assert session.session_id is not None
```

**Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_session_manager.py::test_session_creation -v`
Expected: FAIL with "SessionManager not defined"

**Step 3: Write minimal implementation**

```python
# backend/app/models/session.py
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
import uuid

@dataclass
class Session:
    session_id: str
    user_id: str
    companion_id: str
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int = 0
    messages: List[dict] = None
    
    def __post_init__(self):
        if self.messages is None:
            self.messages = []
        if not isinstance(self.created_at, datetime):
            self.created_at = datetime.fromisoformat(self.created_at)
        if not isinstance(self.updated_at, datetime):
            self.updated_at = datetime.fromisoformat(self.updated_at)

@dataclass
class Message:
    message_id: str
    session_id: str
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime
    
    def __post_init__(self):
        if not isinstance(self.timestamp, datetime):
            self.timestamp = datetime.fromisoformat(self.timestamp)
```

```python
# backend/app/services/session_manager.py
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from app.models.session import Session, Message
from app.services.cache import CacheService

class SessionManager:
    def __init__(self):
        self.redis = CacheService()
        self.session_ttl = 30 * 24 * 3600  # 30 days
        self.max_messages_per_session = 1000
    
    async def create_session(self, user_id: str, companion_id: str, title: str = None) -> Session:
        """Create a new session"""
        session_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        if not title:
            title = f"Conversation with {companion_id} - {now.strftime('%Y-%m-%d')}"
        
        session = Session(
            session_id=session_id,
            user_id=user_id,
            companion_id=companion_id,
            title=title,
            created_at=now,
            updated_at=now
        )
        
        # Store in Redis
        await self._store_session(session)
        
        return session
    
    async def get_session(self, session_id: str) -> Optional[Session]:
        """Get session by ID"""
        session_data = await self._get_session_data(session_id)
        if not session_data:
            return None
        
        return self._deserialize_session(session_data)
    
    async def add_message(self, session_id: str, role: str, content: str) -> Message:
        """Add message to session"""
        session = await self.get_session(session_id)
        if not session:
            raise ValueError("Session not found")
        
        message = Message(
            message_id=str(uuid.uuid4()),
            session_id=session_id,
            role=role,
            content=content,
            timestamp=datetime.utcnow()
        )
        
        # Add to session messages
        session.messages.append(message.__dict__)
        session.message_count += 1
        session.updated_at = datetime.utcnow()
        
        # Check message limit
        if len(session.messages) > self.max_messages_per_session:
            # Remove oldest messages
            session.messages = session.messages[-self.max_messages_per_session:]
            session.message_count = len(session.messages)
        
        # Update session
        await self._store_session(session)
        
        return message
    
    async def get_user_sessions(self, user_id: str, limit: int = 50) -> List[Session]:
        """Get all sessions for a user"""
        pattern = f"session:user:{user_id}:*"
        keys = self.redis.redis.keys(pattern)
        
        sessions = []
        for key in keys:
            session_data = self.redis.redis.hgetall(key)
            if session_data:
                session = self._deserialize_session(session_data)
                sessions.append(session)
        
        # Sort by updated_at
        sessions.sort(key=lambda s: s.updated_at, reverse=True)
        return sessions[:limit]
    
    async def cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        # In production, implement LRU cleanup logic
        pass
    
    async def _store_session(self, session: Session):
        """Store session in Redis"""
        key = f"session:{session.session_id}"
        data = self._serialize_session(session)
        
        # Store as hash
        pipe = self.redis.redis.pipeline()
        pipe.hset(key, mapping=data)
        pipe.expire(key, self.session_ttl)
        pipe.execute()
    
    async def _get_session_data(self, session_id: str) -> Dict:
        """Get session data from Redis"""
        key = f"session:{session_id}"
        return self.redis.redis.hgetall(key)
    
    def _serialize_session(self, session: Session) -> Dict:
        """Serialize session to dict"""
        data = {
            "session_id": session.session_id,
            "user_id": session.user_id,
            "companion_id": session.companion_id,
            "title": session.title,
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat(),
            "message_count": str(session.message_count)
        }
        
        # Store messages separately
        messages_key = f"messages:{session.session_id}"
        messages_json = [json.dumps(msg, default=str) for msg in session.messages]
        self.redis.redis.delete(messages_key)  # Clear existing
        if messages_json:
            self.redis.redis.rpush(messages_key, *messages_json)
        
        return data
    
    def _deserialize_session(self, data: Dict) -> Session:
        """Deserialize session from dict"""
        messages_key = f"messages:{data['session_id']}"
        messages = []
        
        # Get messages
        message_data = self.redis.redis.lrange(messages_key, 0, -1)
        for msg_str in message_data:
            msg = json.loads(msg_str)
            msg['timestamp'] = datetime.fromisoformat(msg['timestamp'])
            messages.append(msg)
        
        session = Session(
            session_id=data['session_id'],
            user_id=data['user_id'],
            companion_id=data['companion_id'],
            title=data['title'],
            created_at=datetime.fromisoformat(data['created_at']),
            updated_at=datetime.fromisoformat(data['updated_at']),
            message_count=int(data['message_count']),
            messages=messages
        )
        
        return session
```

**Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/test_session_manager.py::test_session_creation -v`
Expected: PASS

**Step 5: Commit**

```bash
cd backend
git add app/models/session.py app/services/session_manager.py tests/test_session_manager.py
git commit -m "feat: implement Redis session management"
```

---

## Task 9: Enhanced Chat API with Sessions

**Files:**
- Modify: `backend/main.py:264-287`
- Create: `backend/app/api/session_api.py`
- Test: `tests/test_session_api.py`

**Step 1: Write the failing test**

```python
# tests/test_session_api.py
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_create_session():
    response = client.post("/api/v1/sessions", json={
        "user_id": "test123",
        "companion_id": "comp456"
    })
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data["data"]
```

**Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_session_api.py::test_create_session -v`
Expected: FAIL (need to add session endpoint)

**Step 3: Add session API endpoints**

```python
# backend/app/api/session_api.py
from fastapi import APIRouter, HTTPException
from app.services.session_manager import SessionManager
from typing import List

router = APIRouter()
session_manager = SessionManager()

@router.post("/api/v1/sessions")
async def create_session(request: dict):
    """Create new chat session"""
    try:
        session = await session_manager.create_session(
            user_id=request["user_id"],
            companion_id=request["companion_id"]
        )
        return {
            "success": True,
            "data": {
                "session_id": session.session_id,
                "title": session.title
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/v1/sessions/{user_id}")
async def get_user_sessions(user_id: str, limit: int = 50):
    """Get all sessions for a user"""
    try:
        sessions = await session_manager.get_user_sessions(user_id, limit)
        return {
            "success": True,
            "data": [
                {
                    "session_id": s.session_id,
                    "title": s.title,
                    "message_count": s.message_count,
                    "updated_at": s.updated_at.isoformat()
                } for s in sessions
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

**Step 4: Update main.py to include session endpoints**

```python
# backend/main.py (add after line 264)
from app.api import session_api

app.include_router(session_api.router)
```

**Step 5: Update chat endpoint to use sessions**

```python
# backend/main.py (modify chat endpoint)
@app.post("/api/v1/ai/chat")
async def chat(request: ChatRequest):
    try:
        with tracer.measure("chat_request"):
            # Get or create session
            session_id = getattr(request, 'session_id', 'default')
            if session_id == 'default':
                # Create new session
                from app.services.session_manager import SessionManager
                session_manager = SessionManager()
                session = await session_manager.create_session(
                    user_id="default_user",  # In real app, get from auth
                    companion_id=request.messages[-1].content if request.messages else "default"
                )
                session_id = session.session_id
            
            # Generate response with context
            # (Context loading will be implemented in later tasks)
            ai_response = await chat_service.generate_response(
                request.userMessage, 
                "default_user",  # In real app, get from auth
                request.systemPrompt
            )
            
            # Store message in session
            if session_id != 'default':
                await session_manager.add_message(session_id, "user", request.userMessage)
                await session_manager.add_message(session_id, "assistant", ai_response)
            
            return APIResponse(
                success=True,
                message="Chat generated successfully",
                data={
                    "content": ai_response,
                    "session_id": session_id
                },
                timestamp=datetime.utcnow().isoformat()
            )
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

**Step 6: Run test to verify it passes**

Run: `cd backend && pytest tests/test_session_api.py::test_create_session -v`
Expected: PASS

**Step 7: Commit**

```bash
cd backend
git add app/api/session_api.py tests/test_session_api.py main.py
git commit -m "feat: add session management to chat API"
```

---

## Task 10: Load Testing and Performance Validation

**Files:**
- Create: `tests/performance/load_test.py`
- Create: `tests/performance/test_results.md`
- Test: `tests/performance/test_runner.py`

**Step 1: Write the failing test**

```python
# tests/performance/test_runner.py
import subprocess
import pytest

def test_load_test_script():
    """Test that load test script can be executed"""
    result = subprocess.run(
        ["python", "performance/load_test.py", "--help"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert "usage:" in result.stdout
```

**Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/performance/test_runner.py::test_load_test_script -v`
Expected: FAIL with "load_test.py not found"

**Step 3: Write minimal load test**

```python
# tests/performance/load_test.py
import argparse
import asyncio
import aiohttp
import time
import statistics
from typing import List, Dict
import json

class LoadTester:
    def __init__(self, base_url: str, concurrent_users: int = 10):
        self.base_url = base_url
        self.concurrent_users = concurrent_users
        self.results = []
    
    async def run_test(self, duration_seconds: int = 60):
        """Run load test for specified duration"""
        async with aiohttp.ClientSession() as session:
            tasks = []
            start_time = time.time()
            end_time = start_time + duration_seconds
            
            # Create user tasks
            for i in range(self.concurrent_users):
                task = asyncio.create_task(
                    self.user_session(session, i, start_time, end_time)
                )
                tasks.append(task)
            
            # Wait for all tasks to complete
            await asyncio.gather(*tasks)
        
        return self.analyze_results()
    
    async def user_session(self, session: aiohttp.ClientSession, user_id: int, start_time: float, end_time: float):
        """Simulate a user session"""
        message_count = 0
        
        while time.time() < end_time:
            # Send chat request
            response_time = await self.send_chat_request(session, f"Test message {message_count} from user {user_id}")
            
            if response_time:
                self.results.append({
                    "user_id": user_id,
                    "message_number": message_count,
                    "response_time": response_time,
                    "timestamp": time.time() - start_time
                })
            
            message_count += 1
            # Simulate thinking time
            await asyncio.sleep(0.5)
    
    async def send_chat_request(self, session: aiohttp.ClientSession, message: str) -> float:
        """Send a chat request and measure response time"""
        payload = {
            "userMessage": message,
            "systemPrompt": "",
            "messages": []
        }
        
        start_time = time.time()
        try:
            async with session.post(f"{self.base_url}/api/v1/ai/chat", json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    return time.time() - start_time
        except Exception as e:
            print(f"Request failed: {e}")
        
        return None
    
    def analyze_results(self) -> Dict:
        """Analyze test results"""
        response_times = [r["response_time"] for r in self.results if r["response_time"]]
        
        if not response_times:
            return {"error": "No successful requests"}
        
        return {
            "total_requests": len(self.results),
            "successful_requests": len(response_times),
            "success_rate": len(response_times) / len(self.results),
            "avg_response_time": statistics.mean(response_times),
            "min_response_time": min(response_times),
            "max_response_time": max(response_times),
            "p95_response_time": statistics.quantiles(response_times, n=20)[18] if len(response_times) >= 20 else max(response_times),
            "total_messages": len(self.results)
        }

def main():
    parser = argparse.ArgumentParser(description="Load Test for AI Chat API")
    parser.add_argument("--url", default="http://localhost:8000", help="API base URL")
    parser.add_argument("--users", type=int, default=10, help="Number of concurrent users")
    parser.add_argument("--duration", type=int, default=60, help="Test duration in seconds")
    
    args = parser.parse_args()
    
    tester = LoadTester(args.url, args.users)
    results = asyncio.run(tester.run_test(args.duration))
    
    print("\\n=== Load Test Results ===")
    print(json.dumps(results, indent=2))
    
    # Save results
    with open("test_results.md", "w") as f:
        f.write("# Load Test Results\\n\\n")
        f.write(f"**Base URL:** {args.url}\\n")
        f.write(f"**Concurrent Users:** {args.users}\\n")
        f.write(f"**Duration:** {args.duration} seconds\\n\\n")
        f.write("## Summary\\n")
        f.write(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()
```

**Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/performance/test_runner.py::test_load_test_script -v`
Expected: PASS

**Step 5: Commit**

```bash
cd backend
git add tests/performance/load_test.py tests/performance/test_runner.py tests/performance/test_results.md
git commit -m "feat: add load testing framework"
```

---

## Task 11: Performance Monitoring Dashboard

**Files:**
- Create: `frontend/src/components/PerformanceMonitor.vue`
- Create: `frontend/src/composables/usePerformanceMetrics.ts`
- Test: `frontend/tests/PerformanceMonitor.spec.ts`

**Step 1: Write the failing test**

```typescript
// frontend/tests/PerformanceMonitor.spec.ts
import { mount } from '@vue/test-utils'
import PerformanceMonitor from '@/components/PerformanceMonitor.vue'

describe('PerformanceMonitor', () => {
  it('displays performance metrics', () => {
    const wrapper = mount(PerformanceMonitor)
    expect(wrapper.text()).toContain('Response Time')
  })
})
```

**Step 2: Run test to verify it fails**

Run: `cd frontend && npm run test:unit PerformanceMonitor.spec.ts`
Expected: FAIL with "PerformanceMonitor not defined"

**Step 3: Write minimal implementation**

```vue
<!-- frontend/src/components/PerformanceMonitor.vue -->
<template>
  <div class="performance-monitor">
    <h3>Performance Metrics</h3>
    
    <div class="metric">
      <span class="label">Average Response Time:</span>
      <span class="value">{{ metrics.avgResponseTime?.toFixed(2) || '0' }}ms</span>
    </div>
    
    <div class="metric">
      <span class="label">95th Percentile:</span>
      <span class="value">{{ metrics.p95ResponseTime?.toFixed(2) || '0' }}ms</span>
    </div>
    
    <div class="metric">
      <span class="label">Success Rate:</span>
      <span class="value">{{ (metrics.successRate * 100).toFixed(1) || '0' }}%</span>
    </div>
    
    <div class="metric">
      <span class="label">Total Requests:</span>
      <span class="value">{{ metrics.totalRequests || 0 }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { usePerformanceMetrics } from '@/composables/usePerformanceMetrics'

const metrics = ref({})
const { fetchMetrics } = usePerformanceMetrics()

onMounted(async () => {
  metrics.value = await fetchMetrics()
  
  // Auto-refresh every 5 seconds
  setInterval(async () => {
    metrics.value = await fetchMetrics()
  }, 5000)
})
</script>

<style scoped>
.performance-monitor {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  padding: 16px;
  backdrop-filter: blur(10px);
}

.metric {
  display: flex;
  justify-content: space-between;
  margin: 8px 0;
  font-size: 14px;
}

.label {
  color: #94a3b8;
}

.value {
  font-weight: bold;
  color: #e2e8f0;
}
</style>
```

```typescript
// frontend/src/composables/usePerformanceMetrics.ts
import { ref } from 'vue'

export function usePerformanceMetrics() {
  const metrics = ref({
    avgResponseTime: 0,
    p95ResponseTime: 0,
    successRate: 0,
    totalRequests: 0
  })

  async function fetchMetrics() {
    try {
      const response = await fetch('http://localhost:8000/api/v1/metrics')
      if (response.ok) {
        const data = await response.json()
        metrics.value = data.data
      }
    } catch (error) {
      console.error('Failed to fetch metrics:', error)
    }
    
    return metrics.value
  }

  return {
    metrics,
    fetchMetrics
  }
}
```

**Step 4: Update main.py to include metrics endpoint**

```python
# backend/main.py (add after health check)
@app.get("/api/v1/metrics", tags=["Metrics"])
async def get_metrics():
    """Get performance metrics"""
    from app.middleware.tracing import PerformanceTracer
    
    tracer = PerformanceTracer()
    metrics = tracer.get_metrics()
    
    # Calculate summary statistics
    summary = {}
    for operation, data in metrics.items():
        if data:
            durations = [item["duration"] for item in data]
            summary[operation] = {
                "avg_response_time": sum(durations) / len(durations),
                "total_requests": len(durations),
                "min_response_time": min(durations),
                "max_response_time": max(durations)
            }
    
    return APIResponse(
        success=True,
        message="Metrics retrieved successfully",
        data=summary,
        timestamp=datetime.utcnow().isoformat()
    )
```

**Step 5: Run test to verify it passes**

Run: `cd frontend && npm run test:unit PerformanceMonitor.spec.ts`
Expected: PASS

**Step 6: Commit**

```bash
cd frontend
git add components/PerformanceMonitor.vue composables/usePerformanceMetrics.ts tests/PerformanceMonitor.spec.ts
git commit -m "feat: implement performance monitoring dashboard"
```

---

## Task 12: Production Readiness

**Files:**
- Create: `backend/docker-compose.prod.yml`
- Create: `backend/nginx.conf`
- Create: `frontend/nginx.conf`
- Update: `backend/.env.example`

**Step 1: Add production configurations**

```yaml
# backend/docker-compose.prod.yml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - REDIS_URL=redis://redis:6379/1
      - ZHIPU_API_KEY=${ZHIPU_API_KEY}
    depends_on:
      - redis
    restart: unless-stopped
    
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    restart: unless-stopped
    
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./frontend/dist:/usr/share/nginx/html
    depends_on:
      - app
    restart: unless-stopped

volumes:
  redis_data:
```

```nginx
# backend/nginx.conf
events {
    worker_connections 1024;
}

http {
    upstream app {
        server app:8000;
    }
    
    server {
        listen 80;
        
        location / {
            proxy_pass http://app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
        
        location /ws {
            proxy_pass http://app;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
        }
    }
}
```

**Step 2: Update environment example**

```env
# backend/.env.example
# Production Environment Variables

# AI Model Configuration
ZHIPU_API_KEY=your_production_api_key_here
ZHIPU_MODEL=GLM-4.5-Air
ZHIPU_IMAGE_MODEL=cogview-3

# Database Configuration (if using)
DATABASE_URL=postgresql://user:password@localhost:5432/ai_companion

# Redis Configuration
REDIS_URL=redis://localhost:6379/1

# JWT Configuration
JWT_SECRET_KEY=your-super-secret-jwt-key-change-this-in-production
JWT_EXPIRATION=7200000  # 2 hours
JWT_REFRESH_EXPIRATION=604800000  # 7 days

# Performance Configuration
ENABLE_METRICS=true
CACHE_TTL=3600
SESSION_TTL=2592000  # 30 days

# Security Configuration
CORS_ORIGINS=https://yourdomain.com
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_PERIOD=60
```

**Step 3: Create production deployment script**

```bash
#!/bin/bash
# deploy.sh

echo "🚀 Starting production deployment..."

# Build frontend
cd frontend
npm run build
cd ..

# Build backend
cd backend
docker build -t ai-chat-backend .

# Stop existing containers
docker-compose -f docker-compose.prod.yml down

# Start production stack
docker-compose -f docker-compose.prod.yml up -d

echo "✅ Deployment complete!"
echo "Frontend: http://localhost"
echo "Backend API: http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
```

**Step 4: Commit production configurations**

```bash
cd backend
git add docker-compose.prod.yml nginx.conf .env.example deploy.sh
git commit -m "feat: add production deployment configurations"
```

---

## Plan Complete and Next Steps

**Plan complete and saved to `docs/plans/2024-07-12-ai-chat-optimization.md`. Two execution options:**

**1. Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

**Which approach?**

**If Subagent-Driven chosen:**
- **REQUIRED SUB-SKILL:** Use superpowers:subagent-driven-development
- Stay in this session
- Fresh subagent per task + code review

**If Parallel Session chosen:**
- Guide them to open new session in worktree
- **REQUIRED SUB-SKILL:** New session uses superpowers:executing-plans