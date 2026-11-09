"""Custom exceptions for KAIROS Code."""


class KairosError(Exception):
    """Base exception for all KAIROS errors."""


class ConfigError(KairosError):
    """Configuration-related errors."""


class ProviderError(KairosError):
    """LLM provider errors."""


class AgentError(KairosError):
    """Agent execution errors."""


class ToolError(KairosError):
    """Tool execution errors."""


class WorkflowError(KairosError):
    """Workflow orchestration errors."""


class SecurityError(KairosError):
    """Security policy violation."""


class BudgetExceededError(KairosError):
    """Token or cost budget exceeded."""


class TimeoutError(KairosError):
    """Operation timed out."""


class ApprovalRequiredError(KairosError):
    """Human approval is required to proceed."""
    def __init__(self, action: str, details: str = ""):
        self.action = action
        self.details = details
        super().__init__(f"Approval required for: {action}. {details}")
