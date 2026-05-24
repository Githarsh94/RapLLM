# LLM Inference Logging System

A four-part system: chatbot, inference SDK, ingestion pipeline, and Supabase database.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Browser (Next.js :3000)                                 │
│  - List / create / resume / cancel conversations         │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTP
┌──────────────────────▼──────────────────────────────────┐
│  Chatbot Backend (FastAPI :8000)                         │
│  - Manages conversations + messages in Supabase          │
│  - Calls Gemini via llm_logger SDK wrapper               │
└──────┬───────────────────────────────────────────────────┘
       │ async fire-and-forget (non-blocking)
┌──────▼───────────────────────────────────────────────────┐
│  Ingestion Service (FastAPI :8001)                        │
│  - Validates InferenceLogPayload                         │
│  - Writes to inference_logs table in Supabase            │
└──────────────────────────────────────────────────────────┘
```

## Project Structure

```
.
├── database/
│   └── migrations/
│       └── 001_initial_schema.sql   # Run this in Supabase SQL editor
├── sdk/
│   └── llm_logger/                  # pip-installable Python package
│       ├── __init__.py
│       ├── models.py                # InferenceLogPayload schema
│       ├── dispatcher.py            # Async HTTP log sender
│       └── wrapper.py               # LLMLogger wraps Gemini calls
├── ingestion/
│   └── app/                         # FastAPI service (port 8001)
│       ├── models.py
│       ├── database.py
│       ├── routes.py
│       └── main.py
└── chatbot/
    ├── backend/
    │   └── app/                     # FastAPI service (port 8000)
    │       ├── models.py
    │       ├── database.py
    │       ├── gemini_client.py
    │       ├── routes.py
    │       └── main.py
    └── frontend/                    # Next.js app (port 3000)
        ├── app/
        ├── components/
        └── lib/
```

## Setup

> Each Python service gets its own isolated virtual environment (`.venv`).
> This prevents dependency conflicts between services.

### 1. Supabase

1. Create a new project at [supabase.com](https://supabase.com)
2. Go to **SQL Editor** and run the contents of `database/migrations/001_initial_schema.sql`
3. Copy your **Project URL** and **service_role key** from Project Settings → API

### 2. SDK

```bash
cd sdk
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e .
```

The `-e` flag installs in **editable mode** — any changes to the SDK source are reflected immediately without reinstalling.

### 3. Ingestion Service

```bash
cd ingestion
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # fill in SUPABASE_URL and SUPABASE_SERVICE_KEY
python -m app.main
# runs on http://localhost:8001
```

### 4. Chatbot Backend

```bash
cd chatbot/backend
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -e ../../sdk         # install the local SDK into this venv
cp .env.example .env             # fill in all four variables
python -m app.main
# runs on http://localhost:8000
```

> **Note:** The SDK must be installed into the chatbot backend's own venv separately,
> even if you already installed it in the `sdk/` venv. Each venv is independent.

### 5. Chatbot Frontend

```bash
cd chatbot/frontend
npm install
cp .env.local.example .env.local
npm run dev
# runs on http://localhost:3000
```

Open [http://localhost:3000](http://localhost:3000).

### Activating venvs in future sessions

Whenever you open a new terminal to run a service, activate its venv first:

```bash
# Ingestion service
cd ingestion && source .venv/bin/activate && python -m app.main

# Chatbot backend
cd chatbot/backend && source .venv/bin/activate && python -m app.main
```

## Environment Variables

### `ingestion/.env`
| Variable | Description |
|---|---|
| `SUPABASE_URL` | Your Supabase project URL |
| `SUPABASE_SERVICE_KEY` | service_role key (not anon key) |

### `chatbot/backend/.env`
| Variable | Description |
|---|---|
| `GEMINI_API_KEY` | Google AI Studio API key |
| `SUPABASE_URL` | Your Supabase project URL |
| `SUPABASE_SERVICE_KEY` | service_role key |
| `INGESTION_URL` | `http://localhost:8001` |

## Schema Design

**conversations** — one row per chat session. `status` is `active` or `cancelled`.

**messages** — append-only log of turns. `role` is `user` or `assistant`. Cascades on conversation delete.

**inference_logs** — one row per LLM API call. Stores latency, token counts, timestamps, previews, and error info. Foreign keys to both conversation and triggering message, but both are nullable (SET NULL) so log history survives conversation deletion.

Indexes on `conversation_id` for fast message/log lookups, and on `created_at DESC` for recency-ordered queries.

## Logging Flow

1. Chatbot backend saves user message → builds conversation history → calls `LLMLogger.call()`
2. `LLMLogger` times the Gemini API call and captures `usage_metadata`
3. On completion (success or error), it fires `asyncio.create_task()` — non-blocking, never delays the response to the user
4. `LogDispatcher` POSTs the payload to `POST /ingest/log` on the ingestion service
5. Ingestion validates with Pydantic, inserts into `inference_logs` in Supabase

Log dispatch failures are printed to stderr only — they never propagate to the user.

## API Reference

### Chatbot Backend (`:8000`)

| Method | Path | Description |
|---|---|---|
| `POST` | `/conversations` | Create conversation |
| `GET` | `/conversations` | List all conversations |
| `GET` | `/conversations/{id}` | Get conversation + messages |
| `POST` | `/conversations/{id}/messages` | Send message, get AI reply |
| `PATCH` | `/conversations/{id}/cancel` | Cancel a conversation |

### Ingestion Service (`:8001`)

| Method | Path | Description |
|---|---|---|
| `POST` | `/ingest/log` | Receive inference log |
| `GET` | `/health` | Health check |
