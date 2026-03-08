# AI Desktop Agent

## Overview

This scaffold sets up a desktop-agent monorepo with:

- **Frontend UI** (`frontend/`) for web-based interface.
- **Tauri UI shell** (`tauri-ui/`) for native desktop packaging.
- **Backend API** (`backend/api/main.py`) as a FastAPI entrypoint.
- **Agent core** (`agent/nanobot_agent.py`) for orchestration.
- **Skill modules** (`skills/`) for user-facing actions.
- **MCP servers** (`mcp/`) for filesystem, search, and system integrations.
- **Indexer** (`indexer/`) for scanning and file watching.
- **Vector layer** (`vector/`) for embedding storage abstractions.
- **Model wrappers** (`models/`) for embedding generation.
- **Database directory** (`database/`) for runtime-created SQLite files.

> SQLite database files should be created at runtime inside `database/` and are not committed by default.

## Project Structure

```text
ai-desktop-agent/
├── agent/
├── backend/
│   └── api/
├── database/
├── frontend/
├── indexer/
├── mcp/
├── models/
├── skills/
├── tauri-ui/
├── vector/
└── requirements.txt
```

## Run Commands

### Backend

```bash
cd ai-desktop-agent
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn backend.api.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd ai-desktop-agent/frontend
npm install
npm run dev
```

### Tauri UI (placeholder scaffold)

```bash
cd ai-desktop-agent/tauri-ui
npm install
npm run dev
```

## Architecture Flow

1. Frontend/Tauri UI sends requests to the FastAPI backend.
2. Backend delegates tasks to `NanobotAgent`.
3. Agent invokes skill modules and MCP servers as needed.
4. Indexer scans/watches files and updates vector storage.
5. Embeddings are generated through `models/embedding_model.py` and stored through `vector/vector_db.py`.
