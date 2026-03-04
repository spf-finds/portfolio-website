# Scotia iTrade Agent - File Guide

Complete breakdown of every file in the project and its purpose.

---

## Core Application Files

### [main.py](cci:7://file:///Users/hamadsultan/Downloads/gettintesty-main/main.py:0:0-0:0) (65 lines)
**FastAPI Web Server**

**Purpose**: Handles all HTTP requests and routes them to appropriate modules.

**Endpoints**:
- `GET /` → Serves the HTML UI
- `POST /chat` → Receives user questions, calls agent.py, streams AI responses
- `POST /scrape` → Triggers the web scraper
- `GET /status` → Returns document count from knowledge base

**Dependencies**: [agent.py](cci:7://file:///Users/hamadsultan/Downloads/gettintesty-main/agent.py:0:0-0:0), [simple_store.py](cci:7://file:///Users/hamadsultan/Downloads/gettintesty-main/simple_store.py:0:0-0:0)

**How to run**: `uvicorn main:app --reload --port 8000`

---

### [agent.py](cci:7://file:///Users/hamadsultan/Downloads/gettintesty-main/agent.py:0:0-0:0) (105 lines)
**LLM Logic & RAG Implementation**

**Purpose**: Handles all AI/LLM interactions and retrieval-augmented generation.

**Main Flow**:
1. Takes user question from main.py
2. Searches `simple_store` for relevant chunks using keyword matching
3. Builds prompt with:
   - System instructions (Scotia iTrade domain expert)
   - Retrieved context chunks (top 6 matches)
   - Chat history (last 10 messages)
   - User's current question
4. Calls OpenAI GPT-4o (or Azure OpenAI) with streaming
5. Yields response tokens back to user

**Key Functions**:
- [stream_response(user_message, chat_history)](cci:1://file:///Users/hamadsultan/Downloads/gettintesty-main/agent.py:24:0-35:5) → Generator - Main chat function
- [_get_client()](cci:1://file:///Users/hamadsultan/Downloads/gettintesty-main/agent.py:0:0-7:55) → Returns OpenAI or AzureOpenAI client based on env vars
- [_get_embedding(text)](cci:1://file:///Users/hamadsultan/Downloads/gettintesty-main/agent.py:57:0-68:19) → Currently unused (switched to keyword search)

**Features**:
- Supports both OpenAI and Azure OpenAI (auto-switches via `USE_AZURE` env var)
- Streaming responses for better UX
- Temperature set to 0.3 for consistent, factual answers

---

### [simple_store.py](cci:7://file:///Users/hamadsultan/Downloads/gettintesty-main/simple_store.py:0:0-0:0) (61 lines)
**Simple Keyword-Based Knowledge Store**

**Purpose**: Stores and retrieves scraped website content using simple keyword matching (no embeddings).

**Storage**: Plain JSON file (`knowledge_base.json`)

**Functions**:
- [add_documents(documents, metadatas)](cci:1://file:///Users/hamadsultan/Downloads/gettintesty-main/vectorstore.py:34:0-52:17) → Appends text chunks to JSON file
- [query(query_text, n_results=6)](cci:1://file:///Users/hamadsultan/Downloads/gettintesty-main/vectorstore.py:55:0-68:54) → Finds relevant chunks by keyword overlap
- [get_count()](cci:1://file:///Users/hamadsultan/Downloads/gettintesty-main/simple_store.py:48:0-54:21) → Returns total number of stored chunks
- [clear()](cci:1://file:///Users/hamadsultan/Downloads/gettintesty-main/simple_store.py:56:0-59:29) → Deletes all stored data

**Storage Format**:
```json
[
  {
    "text": "Scotia iTrade offers commission-free trading...",
    "metadata": {"url": "https://...", "chunk_index": 0}
  }
]