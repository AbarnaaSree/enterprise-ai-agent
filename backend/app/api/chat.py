from fastapi import APIRouter
from pydantic import BaseModel
from langfuse import get_client

from backend.app.services.agent_service import AgentService


router = APIRouter(
    prefix="/api",
    tags=["AI"],
)


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    answer: str
    route: str
    execution_steps: list[str]
    sources: list = []
    workflow: dict


agent_service = AgentService()


@router.post(
    "/chat",
    response_model=ChatResponse,
)
def chat(request: ChatRequest):

    result = agent_service.ask_with_details(
        request.message
    )

    return ChatResponse(
        answer=result["answer"],
        route=result["route"],
        execution_steps=result["execution_steps"],
        sources=[],
        workflow=result["workflow"],
    )


@router.get(
    "/langfuse/trace/{trace_id}",
)
def get_langfuse_trace(trace_id: str):

    langfuse = get_client()

    observations = (
        langfuse.api.observations.get_many(
            trace_id=trace_id,
            limit=100,
            fields="core,basic,usage",
        )
    )

    observation_items = getattr(
        observations,
        "data",
        observations,
    )

    llm_calls = 0
    rag_retrievals = 0
    mcp_calls = 0
    validation_calls = 0

    timestamps = []

    for observation in observation_items:

        name = getattr(
            observation,
            "name",
            "",
        )

        observation_type = getattr(
            observation,
            "type",
            "",
        )

        start_time = getattr(
            observation,
            "start_time",
            None,
        )

        end_time = getattr(
            observation,
            "end_time",
            None,
        )

        if start_time:
            timestamps.append(start_time)

        if end_time:
            timestamps.append(end_time)

        if (
            observation_type == "GENERATION"
            or name.startswith("llm_")
        ):
            llm_calls += 1

        if name == "rag_retrieval":
            rag_retrievals += 1

        if name == "response_validation":
            validation_calls += 1

        if (
            name == "mcp_get_employee"
            or name == "get_employee"
        ):
            mcp_calls += 1

    duration_seconds = None

    if len(timestamps) >= 2:

        start_time = min(timestamps)
        end_time = max(timestamps)

        duration_seconds = (
            end_time - start_time
        ).total_seconds()

    return {
        "status": "completed",
        "trace_id": trace_id,
        "trace_name": "enterprise_ai_agent",
        "llm_calls": llm_calls,
        "rag_retrievals": rag_retrievals,
        "mcp_calls": mcp_calls,
        "validation_calls": validation_calls,
        "duration_seconds": duration_seconds,
        "observations": [
            {
                "name": getattr(
                    observation,
                    "name",
                    "",
                ),
                "type": getattr(
                    observation,
                    "type",
                    "",
                ),
            }
            for observation in observation_items
        ],
    }