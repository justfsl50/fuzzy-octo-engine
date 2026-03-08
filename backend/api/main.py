from __future__ import annotations

import os

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from agent.nanobot_agent import NanoBotAgent


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, description="User query text")
    session_id: str | None = Field(default=None, description="Optional conversation session identifier")


class Message(BaseModel):
    role: str
    content: str


class QueryResponse(BaseModel):
    session_id: str
    intent: str
    answer: str
    provider: str
    memory: list[Message]
    raw: dict


app = FastAPI(title="NanoBot API", version="0.2.0")
agent = NanoBotAgent(sqlite_path=os.getenv("NANOBOT_MEMORY_DB"))


@app.post("/query", response_model=QueryResponse)
async def query_endpoint(payload: QueryRequest) -> QueryResponse:
    try:
        result = agent.handle_query(query=payload.query, session_id=payload.session_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=f"NanoBot runtime error: {exc}") from exc

    return QueryResponse(**result)
