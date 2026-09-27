from fastapi import APIRouter
from pydantic import BaseModel

from backend.app.services.agent_service import AgentService


router = APIRouter(
    prefix="/api",
    tags=["AI"],
)


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    answer: str
    sources: list = []


agent_service = AgentService()


@router.post(
    "/chat",
    response_model=ChatResponse,
)
def chat(request: ChatRequest):

    answer = agent_service.ask(
        request.message
    )

    return ChatResponse(
        answer=answer,
        sources=[],
    )