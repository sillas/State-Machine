from typing import Any
from time import time

from core.utils.state_base import State, StateType
from core.statement_evaluator import StatementEvaluator


class IF(State):
    """
    IF (flux-control) is a subclass of State that evaluates a list of statements to determine the next state.

    Attributes:
        evaluator (StatementEvaluator): Evaluates the provided statements.
        next_state: Stores the result of the evaluation.

    Args:
        name (str): The name of this IF-state.
        statements (list): A list of statements to be evaluated.

    Methods:
        handler(event, context):
            Updates the context with the current timestamp, evaluates the event using the provided statements,
            sets the next state, and returns the event.
    """

    def __init__(self, name: str, statements: list) -> None:
        self.evaluator = StatementEvaluator(statements)

        super().__init__(name=name, next_state=None, type=StateType.IF, timeout=1)

    def handler(self, event: Any, context: dict[str, Any]) -> Any:
        """
        Handles an incoming event by updating the context with the current timestamp,
        evaluating the next state based on the event, and returning the event.

        Args:
            event (Any): The event to be handled.
            context (dict[str, Any]): The context dictionary to be updated.

        Returns:
            Any: Bypass the input event.
        """
        context["timestamp"] = time()
        self.next_state = self.evaluator.evaluate(event)
        return event
