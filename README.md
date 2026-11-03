# GraphRAG — Retrieval-Augmented Generation with a Knowledge-Graph Memory

A production-shaped RAG service that answers questions over your own documents by
combining **dense vector retrieval** with **knowledge-graph traversal**. Instead
of stuffing the prompt with the nearest chunks only, the pipeline extracts
entities and relations during ingestion, links question entities into the graph,
expands two hops, and fuses graph evidence with vector evidence before the LLM
sees a single token.

Built end-to-end: FastAPI + MongoDB + Neo4j (or embedded Kuzu) + ChromaDB (or
NumPy) + LangGraph-style agent orchestration on the backend, and a React +
TypeScript dashboard with a live graph explorer, streaming chat, and analytics.

---

## Table of contents

1. [Why a graph?](#why-a-graph)
2. [Feature tour](#feature-tour)
3. [Architecture](#architecture)
4. [Quickstart — zero infrastructure](#quickstart--zero-infrastructure)
5. [Quickstart — production stack](#quickstart--production-stack)
6. [Configuration](#configuration)
7. [API](#api)
8. [Frontend](#frontend)
9. [Testing](#testing)
10. [Project layout](#project-layout)
11. [Design notes and trade-offs](#design-notes-and-trade-offs)
12. [Troubleshooting](#troubleshooting)

---

## Why a graph?

Flat vector RAG answers "what does the document say about X?" well, and
multi-hop questions badly:

> *Which supplier makes the actuator used by the robot that failed at the
> Rotterdam site?*

No single chunk contains that answer. The information is spread across a
platform overview, a supplier contract and an incident report. A graph makes the
hops explicit — `Atlas-7 →(USES)→ Helios actuator ←(SUPPLIES)← Kestrel Metals` —
and the retriever can walk them deterministically instead of hoping an embedding
lands nearby.

This project keeps both: vectors for recall over prose, the graph for precision
over relationships. The LLM gets a context window assembled from both, with
per-chunk provenance.

## Feature tour

**Ingestion**

- PDF, DOCX, TXT and Markdown parsing (PyMuPDF, python-docx) with paragraph-aware
  cleanup and boilerplate stripping.
- Token-aware chunking with overlap and heading context preserved per chunk.
- LLM entity/relation extraction with a deterministic regex/NER fallback, entity
  type normalisation, alias resolution and relation canonicalisation.
- Asynchronous, cancellable ingestion tasks with per-document progress, status
  (`pending → processing → ready | failed`) and a retry (`reingest`) endpoint.
- Chunks written to the vector store **and** to both the relational store and the
  graph (`MENTIONED_IN`, `MENTIONS`) so citations and entity mentions exist in
  one atomic-ish flow, with compensating deletes if a step fails.

**Retrieval**

- Hybrid retrieval running dense search, entity→chunk lookup and N-hop graph
  expansion concurrently.
- Weighted fusion of normalised vector score, reciprocal-rank contribution and
  graph confidence (`VECTOR_WEIGHT` / `GRAPH_WEIGHT`).
- Query rewriting (follow-up resolution), entity linking, and a confidence score
  derived from the fused evidence.
- Read-only Cypher endpoint with statement validation for the graph explorer.

**Answering**

- Multi-stage prompt chain: rewrite → plan → retrieve → synthesize →
  cite → verify → reflect.
- Inline `[n]` citations tied to chunk ids, document ids and sources
  (`vector` / `graph`), rendered in the UI and exportable.
- Confidence, reasoning trace, follow-up questions and graph paths returned with
  every answer.
- Conversation memory: rolling summaries plus long-term user/entity memories
  recalled on later questions.
- Server-Sent-Events streaming for token-by-token answers, plus feedback
  (👍/👎) per assistant message.

**Platform**

- JWT auth (access + refresh, bcrypt hashes), role-based access (`user`,
  `admin`), rate limiting, request ids, structured logs persisted for admins.
- Usage analytics per user: tokens, latency, daily volume, top documents,
  inventory.
- Admin console: user roles/activation/deletion, all documents, error logs,
  runtime configuration.
- Pluggable infrastructure — the same code runs fully offline (memory + Kuzu +
  NumPy + deterministic LLM) or on MongoDB + Neo4j + ChromaDB + OpenAI.

## Architecture

```text
┌──────────────────────────── React + Vite + Tailwind ───────────────────────────┐
│  Dashboard · Documents · Chat (SSE) · Graph explorer · Analytics · Admin       │
└───────────────────────────────────┬────────────────────────────────────────────┘
                                    │ REST + SSE (JWT bearer)
┌───────────────────────────────────▼────────────────────────────────────────────┐
│ FastAPI                                                                        │
│  routes/  auth · documents · search · chat · graph · analytics · admin         │
│  middleware/ request-id · rate-limit · error envelope                          │
│  services/                                                                     │
│    parsing → chunking → extraction ──────────────► ingestion (async tasks)      │
│    HybridRetriever  ── vectors (Chroma/NumPy)                                   │
│                     ── entity linking → graph expansion (Neo4j/Kuzu)            │
│                     ── fusion + memory recall                                   │
│    ChatService ── rewrite → retrieve → synthesize → cite → verify → reflect     │
│    GraphAgent (LangGraph StateGraph, with deterministic fallback)               │
└──────┬───────────────────────┬────────────────────────┬────────────────────────┘
       │                       │                        │
  MongoDB / memory        Neo4j / Kuzu            ChromaDB / NumPy
  users, documents,       entities, relations,    chunk embeddings,
  chunks, conversations,  MENTIONED_IN links      metadata filters
  messages, memories
```

### Ingestion pipeline

```text
upload → validate (type, size) → persist document (status=processing)
       → parse text → clean → chunk (size/overlap, heading aware)
       → embed chunks (batch) → upsert vectors
       → extract entities + relations (LLM JSON, regex fallback)
       → resolve/dedupe entities, canonicalise relation labels
       → upsert Entity nodes, typed relations, Document node,
         MENTIONED_IN (entity→chunk), MENTIONS (document→entity)
       → update counts + status=ready            (failure → status=failed)
```

### Retrieval and fusion

```text
question ─┬─ rewrite (resolve follow-ups against conversation summary)
          ├─ entity terms  ─→ graph.find_entities ─→ chunks_for_entities ─→ hops
          └─ embed ─→ vector search (top K×2)
                              │
        ┌─────────────────────┴─────────────────────┐
        │ fuse: w_v·(0.75·vector_norm + 0.25·rrf)   │
        │     + w_g·graph_confidence                │
        │ hydrate graph-only chunks from the vector  │
        │ store so every citation has text           │
        └─────────────────────┬─────────────────────┘
                              ▼
        prompt: system rules + citations + graph triplets + memories + history
                              ▼
        answer → verify citations → confidence → follow-ups → persist
```

### Data model (graph)

```cypher
(:User {id})-[:OWNS]->(:Document {id, title, status})
(:Document)-[:MENTIONS]->(:Entity)
(:Entity {id, name, type, description, user_id})
(:Entity)-[:MENTIONED_IN {confidence}]->(:Chunk {id, document_id, text})
(:Entity)-[:RELATION_TYPE {confidence, document_id}]->(:Entity)
```

Relations are stored with their canonical label (`SUPPLIES`, `USES`,
`REPORTS_TO`, `PART_OF`, …) rather than a generic edge, so Cypher queries read
like the domain. The API exposes only read-only Cypher (`MATCH`/`RETURN`, no
writes, no `CALL` side effects, row and length caps).

## Quickstart — zero infrastructure

Requires **Python 3.11+**, **Node 18+**, and optionally [uv](https://docs.astral.sh/uv/).
Nothing else — no Docker, no database server, no API key. The defaults run on
in-memory storage, embedded Kuzu (Cypher), a NumPy vector index, deterministic
hash embeddings and an offline extractive LLM.

```bash
# 1. configure (defaults already work; this just makes them explicit)
cp .env.example .env

# 2. backend
cd backend
uv venv --python 3.12 .venv
uv pip install --python .venv/Scripts/python.exe -r requirements.txt -r requirements-dev.txt
# macOS/Linux: uv pip install --python .venv/bin/python -r requirements.txt -r requirements-dev.txt

.venv/Scripts/python.exe -m uvicorn app.main:app --reload --port 8000
# macOS/Linux: .venv/bin/python -m uvicorn app.main:app --reload --port 8000

# 3. frontend (new terminal)
cd frontend
npm install
npm run dev            # http://localhost:5173
```

Open <http://localhost:5173>, sign in with the bootstrapped admin account:

| Email | Password |
| --- | --- |
| `admin@graphrag.ai` | `Admin12345!` |

Then upload `data/samples/*.md` on the **Documents** page and ask:

- *Which supplier manufactures the Helios actuator used by the Atlas-7?*
- *What happened in incident 4471 and which site was affected?*
- *How does Project Lighthouse reduce recalibration downtime?*

Or seed and smoke-test everything from the shell (API must be running):

```bash
cd backend && .venv/Scripts/python.exe scripts/seed_demo.py
# macOS/Linux: .venv/bin/python scripts/seed_demo.py
```

> The offline LLM is **extractive**: it composes answers from retrieved
> sentences and still exercises retrieval, citations, graph paths, memory and
> streaming. Set `LLM_PROVIDER=openai` + `LLM_API_KEY` for generative answers.

## Quickstart — production stack

```bash
cp .env.example .env
# edit .env: SECRET_KEY, LLM_API_KEY, EMBEDDING_PROVIDER=openai
docker compose up -d --build
```

| Service | URL |
| --- | --- |
| Web UI (nginx) | <http://localhost:8080> |
| API + OpenAPI | <http://localhost:8000/docs> |
| Neo4j browser | <http://localhost:7474> |
| MongoDB | `localhost:27017` |

The Compose stack wires `DOC_STORE=mongo`, `GRAPH_BACKEND=neo4j`,
`VECTOR_STORE=chroma`, `EMBEDDING_PROVIDER=openai`, `LLM_PROVIDER=openai`, and
nginx proxies `/api` to the API container (SSE buffering disabled).

**Embedding dimensions must match the store.** `text-embedding-3-small` is 1536
dimensions; set `EMBEDDING_DIM=1536` (Compose default). Changing embedding model
or dimension after ingesting requires re-ingesting documents — the vector store
validates the dimension and fails loudly rather than silently mixing spaces.

### Without Docker, with real models

```bash
# OpenAI-compatible LLM + embeddings (OpenAI, Groq, Together, vLLM, Ollama…)
LLM_PROVIDER=openai
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=sk-...
EMBEDDING_PROVIDER=openai

# or local sentence-transformers (install requirements-ml.txt first)
EMBEDDING_PROVIDER=sentence-transformers
EMBEDDING_MODEL=BAAI/bge-large-en-v1.5
```

To use hosted databases without Docker, point
`MONGO_URI`/`NEO4J_URI`/`CHROMA_PATH` at your instances and flip the three
backend switches.

## Configuration

All settings live in `backend/app/config/settings.py` and are read from `.env`.
The switches that matter most:

| Variable | Values | Default | Purpose |
| --- | --- | --- | --- |
| `DOC_STORE` | `memory`, `mongo` | `memory` | Metadata, users, chunks, chats, memories |
| `GRAPH_BACKEND` | `kuzu`, `neo4j` | `kuzu` | Embedded Cypher file vs. Neo4j server |
| `VECTOR_STORE` | `numpy`, `chroma` | `numpy` | Persistent NumPy index vs. ChromaDB |
| `EMBEDDING_PROVIDER` | `hash`, `openai`, `sentence-transformers` | `hash` | Offline hashing vs. hosted/local models |
| `EMBEDDING_DIM` | int | `1024` | Must match the embedding model |
| `EMBEDDING_MODEL` | str | `BAAI/bge-large-en-v1.5` | Model used by `sentence-transformers` |
| `LLM_PROVIDER` | `mock`, `openai` | `mock` | Deterministic offline vs. OpenAI-compatible |
| `RETRIEVAL_TOP_K` | int | `8` | Chunks passed to the prompt |
| `GRAPH_HOPS` | int | `2` | Neighbourhood expansion depth |
| `VECTOR_WEIGHT` / `GRAPH_WEIGHT` | float | `0.6` / `0.4` | Fusion weights (should sum to 1) |
| `CHUNK_SIZE` / `CHUNK_OVERLAP` | int | `900` / `150` | Chunking window |
| `USE_LLM_EXTRACTION` | bool | `true` | LLM extraction vs. regex-only fallback |
| `MAX_UPLOAD_MB` | int | `25` | Upload size cap |
| `RATE_LIMIT_PER_MINUTE` | int | `120` | Per-identity request budget |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | int | `720` | Access token lifetime |
| `BOOTSTRAP_ADMIN_EMAIL` / `_PASSWORD` | str | `admin@graphrag.ai` / `Admin12345!` | Seeded admin (change in production) |

`GET /health` reports the active backend for each layer, plus warnings when a
production deployment is still using dev defaults.

## API

Base path `/api`. Interactive docs at `/docs`. A ready-to-run Postman
collection is in [`postman/GraphRAG.postman_collection.json`](postman/GraphRAG.postman_collection.json).

| Method | Path | Description |
| --- | --- | --- |
| `POST` | `/auth/register` | Create an account, returns tokens |
| `POST` | `/auth/login` | Exchange credentials for access + refresh JWTs |
| `POST` | `/auth/refresh` | Rotate the access token |
| `POST` | `/auth/logout` | Client-side revocation |
| `GET` | `/auth/me` | Current profile |
| `PATCH` | `/auth/me` | Update name / preferences |
| `POST` | `/auth/me/password` | Change password |
| `POST` | `/documents` | Upload and ingest (multipart) |
| `GET` | `/documents` | List with status filter and counts |
| `GET` | `/documents/{id}` | Status, progress, counts |
| `POST` | `/documents/{id}/reingest` | Re-run ingestion |
| `DELETE` | `/documents/{id}` | Delete document, vectors, graph links |
| `POST` | `/search` | Hybrid search (no generation) |
| `POST` | `/chat` | Ask a question (full agent pipeline) |
| `POST` | `/chat/stream` | Same, as SSE (`meta`, `graph`, `token`, `done`, `error`) |
| `GET` | `/chats` | Conversations |
| `POST` | `/chats` | Create an empty conversation |
| `GET` | `/chats/{id}` | Conversation with messages |
| `GET` | `/chats/{id}/export` | Markdown/JSON export |
| `DELETE` | `/chats/{id}` | Delete conversation |
| `POST` | `/chat/messages/{id}/feedback` | 👍/👎 an answer |
| `GET` | `/graph/overview` | Sampled subgraph for visualisation |
| `GET` | `/graph/entities?q=` | Entity search |
| `GET` | `/graph/entities/{id}` | Entity, neighbours and mentions |
| `POST` | `/graph/cypher` | Read-only Cypher |
| `GET` | `/graph/stats` | Node/edge counts, type distribution |
| `GET` | `/analytics/usage?days=` | Tokens, latency, daily volume, top docs |
| `GET` | `/analytics/inventory` | Document/chunk/chat/memory counts |
| `GET` | `/admin/overview` | Instance-wide metrics (admin) |
| `GET` | `/admin/users` · `PATCH`/`DELETE` `/admin/users/{id}` | User management (admin) |
| `GET` | `/admin/documents` · `/admin/logs` | Corpus state and error logs (admin) |
| `GET` | `/health` | Liveness + dependency status (also `/api/health`) |

Errors use one envelope: `{"error": {"code", "message", "details", "request_id"}}`.
Every response carries `X-Request-ID` and `X-Process-Time-ms`.

```bash
TOKEN=$(curl -s localhost:8000/api/auth/login \
  -H 'content-type: application/json' \
  -d '{"email":"admin@graphrag.ai","password":"Admin12345!"}' | jq -r .access_token)

curl -s localhost:8000/api/chat \
  -H "authorization: Bearer $TOKEN" -H 'content-type: application/json' \
  -d '{"question":"Which supplier makes the Helios actuator?"}' | jq '{answer, confidence, citations: [.citations[].document_title], paths: .graph.triplets}'
```

## Frontend

React 18 + TypeScript + Vite, Tailwind with a hand-written shadcn-style
component set (no component-library runtime), React Router, React Flow for the
graph, Framer Motion for transitions.

| Page | What it does |
| --- | --- |
| **Dashboard** | Corpus stats, graph size, recent documents, quick actions |
| **Documents** | Drag-and-drop upload with progress, live status polling, reingest/delete |
| **Chat** | Streaming answers, inline citations with source badges, graph path drawer, confidence, follow-ups, feedback, conversation history, export |
| **Graph** | Interactive force layout coloured by entity type, search, hop control, entity details, Cypher console |
| **Analytics** | Daily volume, token spend, latency, event mix, top documents, inventory |
| **Admin** | Users (role/activation/delete), all documents, error logs, runtime config |
| **Profile** | Name, default answer style, password rotation, session info |

`VITE_API_URL` defaults to `/api` for the Docker build and is set to
`http://localhost:8000/api` by `.env.example` for local Vite development.

## Testing

```bash
cd backend
PYTHONPATH=. .venv/Scripts/python.exe -m pytest -q      # Windows
PYTHONPATH=. .venv/bin/python -m pytest -q              # macOS/Linux
```

The suite runs entirely offline (memory store, Kuzu in a temp dir, NumPy vectors,
mock LLM) and covers auth and token rotation, document upload/ingestion/deletion,
chunking and extraction, hybrid retrieval fusion, chat with citations and memory,
the graph API including Cypher guards, analytics and admin authorisation. Each
test gets an isolated app instance and temporary data directory.

End-to-end CLI check with the real HTTP stack:

```bash
cd backend && .venv/Scripts/python.exe scripts/seed_demo.py   # non-zero on failure
```

## Project layout

```text
.
├── backend/
│   ├── app/
│   │   ├── config/         settings + logging
│   │   ├── database/       store interface, in-memory store, MongoDB store, repositories
│   │   ├── middleware/     request ids, rate limiting, error envelope
│   │   ├── models/         pydantic request/response schemas
│   │   ├── prompts/        system, context, citation, memory, extraction, advanced
│   │   ├── routes/         auth, documents, search, chat, graph, analytics, admin, health
│   │   ├── services/
│   │   │   ├── agents/     graph agent (LangGraph plan/retrieve/reflect)
│   │   │   ├── graph/      GraphStore interface, Kuzu + Neo4j implementations
│   │   │   ├── llm/        LLM interface, OpenAI-compatible client, mock LLM
│   │   │   ├── vector/     VectorStore interface, NumPy + Chroma implementations
│   │   │   ├── auth, chat, embeddings, extraction, ingestion, memory,
│   │   │   │   parsing, presentation, retrieval
│   │   ├── utils/          crypto, text normalisation, common helpers
│   │   ├── container.py    dependency wiring / lifecycle
│   │   └── main.py         app factory
│   ├── scripts/seed_demo.py
│   ├── tests/
│   ├── Dockerfile
│   └── requirements*.txt
├── data/samples/           demo corpus (Atlas-7 / NX-204 / Lighthouse)
├── docs/ARCHITECTURE.md
├── frontend/
│   ├── src/{components,hooks,lib,pages}
│   ├── Dockerfile
│   └── nginx.conf
├── postman/GraphRAG.postman_collection.json
├── docker-compose.yml
├── .env.example
└── Makefile
```

## Design notes and trade-offs

- **Two implementations per layer, one interface.** Every store sits behind an
  abstract base (`GraphStore`, `VectorStore`, `Database`, `LLM`, `Embedder`), so
  the offline stack and the production stack exercise identical application code.
  Tests therefore cover the real pipeline, not a mock pipeline.
- **Offline defaults are honest.** The mock LLM is explicitly extractive and says
  so in `/health` warnings when used in production — no silent pretend-generation.
- **Graph writes are best-effort with compensating deletes.** Ingesting to three
  stores is not transactional; a failed graph write downgrades the answer path
  (vector-only + warning) rather than failing the upload. Document deletion
  removes vectors and graph links explicitly.
- **Retrieval degrades gracefully.** If the graph is unreachable, retrieval logs
  and returns vector-only results with `strategy="vector"`; chat still works.
- **Cypher is whitelisted, capped and read-only.** `MATCH`/`RETURN` only, write
  and procedure clauses rejected, rows/characters truncated, time-boxed.
- **Memory is scoped by user.** Entities, memories, chunks and conversations all
  carry `user_id`; graph traversals and vector searches filter on it.
- **Why Kuzu and NumPy by default?** To make the project runnable in a single
  command on a laptop, in CI, and in grading environments without Docker. The
  README's production section is the intended deployment; the embedded stack is
  the fast path to seeing it work.

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| `dimension mismatch` on search | `EMBEDDING_DIM` differs from what was ingested; align it and re-ingest |
| Answers say "I could not find…" | Documents still `processing`/`failed`, or no graph/vector hits; check `/documents` and `/health` |
| Neo4j connection refused | Wait for the container healthcheck (`docker compose ps`), verify `NEO4J_URI` and password |
| `chromadb` install fails | Needs a C++ toolchain; use Docker, or keep `VECTOR_STORE=numpy` |
| 429 responses | Rate limiter: raise `RATE_LIMIT_PER_MINUTE` or wait a minute |
| 401 loop in the UI | Access token expired and refresh failed — sign in again |
| PDF returns no text | Scanned/image-only PDFs need OCR, which is out of scope |

---

### Skills demonstrated

Async Python and FastAPI service design; knowledge-graph modelling and Cypher;
hybrid search and rank fusion; LLM prompt chaining and structured extraction;
embedding and vector-index engineering; agent orchestration; JWT auth and RBAC;
React/TypeScript UI with streaming and graph visualisation; Docker Compose,
nginx reverse proxying, and end-to-end testing.
