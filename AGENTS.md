# AGENTS.md - Obsidian RAG Repository Guidelines

## Project Overview
Full-stack RAG app: Obsidian vaults -> searchable AI assistant
- **Backend**: FastAPI + ChromaDB + SQLModel (Python 3.12+)
- **Frontend**: Next.js 16 + React 19 + Tailwind CSS + shadcn/ui

## Project Structure
```
src/
  api/              # FastAPI routers (main.py entry point)
  core/domain/      # SQLModel entities (Project, Session, Topic, Message)
  core/llm/         # LLM strategies (OpenAI, Gemini, Ollama) via Protocol pattern
  core/rag/         # RAGChain, Retriever, PromptBuilder
  core/sync/        # Folder scanner, incremental syncer
  db/               # ChromaStore, SQLModel engine
  tasktests/        # Phased tests (phase1, phase2, phase2_5, phase3)

front/
  app/              # Next.js App Router pages
  components/       # React components (shadcn/ui based)
  lib/              # API clients, utilities, types
```

## Build, Test, and Development Commands

### Backend (Python)
```bash
uvicorn api.main:app --reload --app-dir src          # Start dev server

pytest src/                                           # Run ALL tests
pytest src/tasktests/phase2/                          # Run phase tests
pytest src/tasktests/phase2/test_api_chat.py -v       # Single test file
pytest src/tasktests/phase2/test_api_chat.py::TestChatEndpoint::test_chat_returns_valid_response -v  # Single test
pytest src/ -k "chat" -v                              # Pattern match
pytest src/tasktests/phase2/test_api_chat.py -v -s    # With output
```

### Frontend (Next.js)
```bash
cd front
npm install       # Install dependencies
npm run dev       # Start dev server
npm run build     # Production build
npm run lint      # ESLint
```

## Python Code Style

### Formatting
- 4 spaces indentation, ~100 char line length
- Imports: stdlib -> third-party -> local (blank lines between)

### Naming
- `snake_case`: functions, variables, modules
- `PascalCase`: classes
- `_prefix`: private attributes (e.g., `self._retriever`)

### Type Hints (Required)
```python
from typing import Iterator, List, Optional, Protocol

class LLMStrategy(Protocol):
    def generate(self, messages: List[Message], *, temperature: float = 0.7) -> LLMResponse: ...
```

### SQLModel Entities
```python
class Project(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    path: str = Field(unique=True, index=True, description="Relative path in vault")
```

## TypeScript/React Code Style

### Formatting
- `"use client"` for client components
- ESLint: `next/core-web-vitals`, `next/typescript`
- Unused vars with `_` prefix allowed

### Naming
- `camelCase`: variables, functions
- `PascalCase`: components, types
- File names: `kebab-case.tsx`

### Imports
```typescript
import { Button } from "@/components/ui/button";  // Use @/ alias
```

## Architecture Patterns

### Strategy Pattern (LLM/Embedding)
- `LLMStrategy` Protocol in `core/llm/strategy.py`
- Implementations: `OpenAILLM`, `GeminiLLM`, `OllamaLLM`, `FakeLLM`
- Factory: `core/llm/factory.py`

### RAG Pipeline
```
Retriever -> PromptBuilder -> LLMStrategy -> RAGResponse
```

### Dependency Injection
- `AppState` in `api/deps.py` holds services
- Injected via FastAPI lifespan
- Tests mock `AppState` for isolation

## Testing

### Organization
- `phase1/`: Preprocessing, storage, sync
- `phase2/`: API, RAG chain, LLM
- `phase2_5/`: Session/topic CRUD
- `phase3/`: Project management

### Patterns
```python
@pytest.fixture
def client(mock_app_state):
    with patch.dict('sys.modules', {'chromadb': MagicMock(), 'openai': MagicMock()}):
        from api.main import create_app
        app = create_app()
        app.state.deps = mock_app_state
        return TestClient(app)
```

## API Endpoints
- `/chat`, `/chat/stream`, `/chat/history`
- `/sync`, `/health`
- `/topics`, `/sessions`, `/projects`

## Environment Variables
```bash
OPENAI_API_KEY=       # OpenAI
GOOGLE_API_KEY=       # Gemini
EMBEDDING_API_KEY=    # Optional (defaults to LLM key)
```

## Security
- Never commit API keys
- CORS `allow_origins=["*"]` is dev-only
- Validate inputs via Pydantic/Zod

## Quick Reference
| Task | Command |
|------|---------|
| Backend dev | `uvicorn api.main:app --reload --app-dir src` |
| Frontend dev | `cd front && npm run dev` |
| All tests | `pytest src/` |
| Single test | `pytest path/to/test.py::TestClass::test_method -v` |
| Lint frontend | `cd front && npm run lint` |
