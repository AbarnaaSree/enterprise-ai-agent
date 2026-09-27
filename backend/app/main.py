from fastapi import FastAPI

from backend.app.api.chat import router as chat_router


app = FastAPI(
    title="Enterprise AI Knowledge and Data Agent",
    description="An AI agent combining LLM, RAG, tools, MCP and LangGraph.",
    version="0.1.0",
)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "enterprise-ai-agent",
    }


app.include_router(chat_router)