from fastapi import FastAPI
from .agent import run_agent

app = FastAPI()


@app.get("/health")
def health():
    return {"status": "ok"}
