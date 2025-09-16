from typing import Any, Optional
from time import time
from pathlib import Path
import importlib.util

from core.state_base import State, StateType
from core.statement_evaluator import StatementEvaluator


class Lambda(State):
    """
    Represents a Lambda function handler that dynamically loads and executes a Python module as a Lambda.

    Attributes:
        name (str): The name of the Lambda function.
        type (str): The type of the Lambda function.
        next_state (str | None): The next state to transition to after execution.
        statements (Optional[list]): Optional list of statements or configuration.
        _handler (callable | None): Cached handler function for the Lambda.
        timeout (int): Timeout for Lambda execution in seconds (default: 60).

    Args:
        name (str): The name of the Lambda function.
        next_state (str | None): The next state to transition to after execution.
        type (StateType, optional): The type of the Lambda function (default: StateType.LAMBDA).
        statements (Optional[list], optional): Optional list of statements or configuration.
        timeout (Optional[int], optional): Timeout for Lambda execution in seconds.

    Methods:
        handler(event: Any, context: dict[str, Any]) -> Any:
            Loads and executes the Lambda handler from the corresponding module file.
            Caches the handler for subsequent invocations.
            Updates the context with a timestamp.
            Raises ModuleNotFoundError if the Lambda module is not found.
            Raises ImportError if the module cannot be loaded.
    """

    statements: Optional[list]
    _handler = None

    def __init__(self, name: str, next_state: str | None, type: StateType = StateType.LAMBDA, statements: Optional[list] = None, timeout: Optional[int] = None) -> None:
        self.name = name
        self.type = type.value
        self.next_state = next_state
        self.statements = statements
        if timeout is not None:
            self.timeout = timeout

    def handler(self, event: Any, context: dict[str, Any]) -> Any:

        handler_cache = self._handler
        context["timestamp"] = time()

        if (handler_cache):
            return handler_cache(event, context)

        lambda_name = self.name
        lambda_path = Path(f"lambdas/{lambda_name}/main.py")

        if not lambda_path.exists():
            raise ModuleNotFoundError(f"Lambda {lambda_name} não encontrado")

        spec = importlib.util.spec_from_file_location(lambda_name, lambda_path)

        if spec is None or spec.loader is None:
            raise ImportError(
                f"Não foi possível carregar o módulo para {lambda_name}")

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        handler = module.lambda_handler
        self._handler = handler

        return handler(event, context)


class IF(State):
    """
    IF is a subclass of Lambda that evaluates a list of statements to determine the next state.

    Attributes:
        evaluator (StatementEvaluator): Evaluates the provided statements.
        next_state: Stores the result of the evaluation.

    Args:
        name (str): The name of the Lambda function.
        statements (list): A list of statements to be evaluated.

    Methods:
        handler(event, context):
            Updates the context with the current timestamp, evaluates the event using the provided statements,
            sets the next state, and returns the event.
    """

    def __init__(self, name: str, statements: list) -> None:
        self.name = name
        self.type = StateType.LAMBDA.value
        self.next_state = None
        self.timeout = 1

        self.evaluator = StatementEvaluator(statements)

    def handler(self, event: Any, context: dict[str, Any]) -> Any:
        context["timestamp"] = time()
        self.next_state = self.evaluator.evaluate(event)
        return event
