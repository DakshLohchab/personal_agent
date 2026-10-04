"""Typed failures emitted by the agent workflow."""


class AgentError(RuntimeError):
    """Base class for bounded agent workflow failures."""


class AgentTimeoutError(AgentError):
    pass


class ModelProviderFailure(AgentError):
    pass


class MalformedAgentOutput(AgentError):
    pass


class ToolFailure(AgentError):
    pass


class ResearchFailure(AgentError):
    pass


class OrchestrationFailure(AgentError):
    pass


class BackgroundJobFailure(AgentError):
    pass
