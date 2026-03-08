"""FastAPI entrypoint for the desktop agent backend."""

from fastapi import FastAPI

app = FastAPI(title="AI Desktop Agent API")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
