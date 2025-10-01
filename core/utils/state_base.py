from typing import Any, Optional
from enum import Enum


class StateType(Enum):
    IF = "if_statement"
    CHOICE = "choice"
    LAMBDA = "lambda"
    PARALLEL = "parallel"


class State:

    def __init__(self, name: str, next_state: str | None, type: StateType, timeout: Optional[int] = None) -> None:
        self.name = name
        self.type = type.value
        self.next_state = next_state
        self.timeout = timeout if timeout else 60

    def handler(self, event: Any, context: dict[str, Any]) -> Any:
        raise NotImplementedError(
            "Handler method must be implemented by subclasses.")
