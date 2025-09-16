from typing import Any, Optional
from enum import Enum


class StateType(Enum):
    IF = "if_statement"
    LAMBDA = "lambda"
    PARALLEL = "parallel"


class State:

    name: str
    type: str
    next_state: str | None
    timeout: int = 60  # seconds

    def __init__(self, name: str, next_state: str | None, type: str, timeout: Optional[int] = None) -> None:
        self.name = name
        self.type = type
        self.next_state = next_state
        if timeout is not None:
            self.timeout = timeout

    def handler(self, event: Any, context: dict[str, Any]) -> Any:
        raise NotImplementedError(
            "Handler method must be implemented by subclasses.")
