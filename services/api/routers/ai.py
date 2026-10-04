"""AI-assisted decision interpretation endpoint."""

from typing import Annotated

from fastapi import APIRouter, Depends

from packages.api_models.ai import AgentRunResponse, AIRequest, AIResponse
from services.agents.jobs import LocalJobQueue
from services.agents.orchestrator import DecisionOrchestrator
from services.api.dependencies import get_ai_service, get_decision_orchestrator, get_settings
from services.application.ai_service import AIService

router = APIRouter(prefix="/api/v1/ai", tags=["ai"])
job_queue = LocalJobQueue[AgentRunResponse]()


@router.post("/interpret", response_model=AIResponse)
def interpret_decision(
    request: AIRequest,
    service: Annotated[AIService, Depends(get_ai_service)],
) -> AIResponse:
    settings = get_settings()
    result = service.interpret(
        request.decision,
        context=request.context,
        model=request.model or settings.nebius_model,
    )
    return AIResponse.model_validate(result)


@router.post("/run", response_model=AgentRunResponse)
def run_decision(
    request: AIRequest,
    service: Annotated[AIService, Depends(get_ai_service)],
    orchestrator: Annotated[DecisionOrchestrator, Depends(get_decision_orchestrator)],
) -> AgentRunResponse:
    settings = get_settings()
    interpretation = request.interpretation
    if interpretation is None:
        interpreted = service.interpret(
            request.decision,
            context=request.context,
            model=request.model or settings.nebius_model,
        )
        interpretation = interpreted["interpretation"]
    if request.background:
        job_id = job_queue.submit(
            lambda: AgentRunResponse.model_validate(
                orchestrator.run(
                    interpretation,
                    model=request.model or settings.nebius_model,
                )
            )
        )
        return AgentRunResponse(run_id=job_id, status="queued")
    return AgentRunResponse.model_validate(
        orchestrator.run(interpretation, model=request.model or settings.nebius_model)
    )


@router.get("/run/{job_id}", response_model=AgentRunResponse)
def get_run(job_id: str) -> AgentRunResponse:
    from uuid import UUID

    parsed_id = UUID(job_id)
    status = job_queue.status(parsed_id)
    if status == "unknown":
        raise KeyError(f"unknown job: {parsed_id}")
    if status == "running":
        return AgentRunResponse(run_id=parsed_id, status=status)
    return job_queue.result(parsed_id)
