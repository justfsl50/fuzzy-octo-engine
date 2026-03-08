# Fuzzy Octo Engine

A local-first workspace assistant scaffold with:

- A **FastAPI backend** for query handling and NanoBot orchestration.
- A **NanoBot agent layer** with intent routing and session memory.
- **Indexer + MCP-style utility modules** for file scanning and local tooling.
- A **Tauri + React UI** for a desktop search assistant experience.

## Repository layout

```text
.
├── agent/                 # NanoBot orchestration + runtime adapter
├── backend/api/           # FastAPI app entrypoint
├── indexer/               # File scan + watch utilities
├── mcp/                   # Filesystem/search/system helper servers
├── models/                # Embedding model abstraction
├── shared/                # Shared safety/confirmation helpers
├── skills/                # User-facing skill modules
├── tauri-ui/              # React + Tauri desktop UI
├── vector/                # Vector DB abstraction
└── ai-desktop-agent/      # Nested copy/scaffold of a similar project
```

## Backend quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install fastapi uvicorn pydantic
uvicorn backend.api.main:app --reload --host 0.0.0.0 --port 8000
```

### API

- `POST /query`
  - Request body:
    ```json
    { "query": "search my project for auth", "session_id": "optional" }
    ```
  - Returns:
    - routed `intent` (`tool` or `skill`)
    - model/runtime `answer`
    - `provider`
    - session `memory`
    - raw runtime payload

## Tauri UI quick start

```bash
cd tauri-ui
npm install
npm run dev
```

The UI currently sends requests to `http://127.0.0.1:8000/query`, so run the backend first.

## NanoBot runtime integration

The agent supports three runtime modes:

1. `NANOBOT_COMMAND` (highest priority): shell command template using placeholders
   - `{query}`
   - `{session_id}`
   - `{intent}`
   - `{history_json}`
2. `NANOBOT_REPO_PATH` (+ optional `NANOBOT_ENTRYPOINT`, default `main.py`)
3. Local deterministic fallback response when neither is configured

### Example

```bash
export NANOBOT_COMMAND='python /path/to/runtime.py --query {query} --session-id {session_id} --intent {intent} --history-json {history_json}'
```

## Notes

- Session memory can be persisted to SQLite by setting `NANOBOT_MEMORY_DB`.
- The nested `ai-desktop-agent/` directory includes a separate scaffold and its own README.
