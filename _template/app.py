#!/usr/bin/env python3
"""
Example Tool - Web adapter (FastAPI).
Only handles HTTP concerns (uploads, responses) and delegates to core/.
"""

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from core.logic import greet

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="Example Tool")


class GreetRequest(BaseModel):
    name: str
    shout: bool = False


@app.get("/", response_class=HTMLResponse)
def index():
    return (BASE_DIR / "templates" / "index.html").read_text(encoding="utf-8")


@app.post("/api/greet")
def greet_endpoint(req: GreetRequest):
    return {"message": greet(req.name, shout=req.shout)}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=os.environ.get("HOST", "127.0.0.1"), port=int(os.environ.get("PORT", 8005)))
