from __future__ import annotations

from fastapi import FastAPI
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
    memory: list[Message]


app = FastAPI(title="NanoBot API", version="0.1.0")
agent = NanoBotAgent()


@app.post("/query", response_model=QueryResponse)
def query_endpoint(payload: QueryRequest) -> QueryResponse:
    result = agent.handle_query(query=payload.query, session_id=payload.session_id)
    return QueryResponse(**result)
