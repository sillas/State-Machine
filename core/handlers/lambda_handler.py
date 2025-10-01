from typing import Any, Optional
from time import time
from pathlib import Path
import importlib.util

from core.utils.state_base import State, StateType


class Lambda(State):
    """
    Represents a Lambda function handler that dynamically loads and executes a Python module as a Lambda.

    Args:
        name (str): The name of the Lambda function.
        next_state (str | None): The next state to transition to after execution.
        timeout (Optional[int], optional): Timeout for Lambda execution in seconds.

    Attributes:
        _handler (callable | None): Cached handler function for the Lambda.
    """

    def __init__(self, name: str, next_state: str | None, lambda_path: str, timeout: Optional[int] = None) -> None:
        super().__init__(
            name=name,
            next_state=next_state,
            type=StateType.LAMBDA,
            timeout=timeout
        )
        self._handler = None
        self._load_lambda(lambda_path)

    def handler(self, event: Any, context: dict[str, Any]) -> Any:
        """
        Handles an incoming event and context for a Lambda-like function.

        Args:
            event (Any): The event data passed to the handler.
            context (dict[str, Any]): The context dictionary containing metadata about the invocation.

        Returns:
            Any: The result of the handler execution.
        """

        context["timestamp"] = time()
        _handler = self._handler

        if _handler is None:
            raise FileNotFoundError(
                f"Lambda - handler - {self.name} not found!")

        return _handler(event, context)

    def _load_lambda(self, lambda_path: str) -> None:
        """
        Loads a lambda handler module dynamically based on the instance's name attribute.

        This method constructs the path to the lambda's main.py file, checks for its existence,
        and imports the module using importlib. If the module or its loader cannot be found,
        appropriate exceptions are raised. Once loaded, the method retrieves the `lambda_handler`
        function from the module and assigns it to the instance's `_handler` attribute.

        Returns:
            Callable: The loaded lambda handler function.

        Raises:
            ModuleNotFoundError: If the lambda module file does not exist.
            ImportError: If the module cannot be loaded or its loader is unavailable.
        """

        lambda_name = self.name
        full_path = Path(lambda_path) / lambda_name / "main.py"
        lambda_file_path = Path(full_path)

        if not lambda_file_path.exists():
            raise ModuleNotFoundError(
                f"Lambda - _load_lambda - {full_path} não encontrado")

        spec = importlib.util.spec_from_file_location(
            lambda_name, lambda_file_path)

        if spec is None or spec.loader is None:
            raise ImportError(
                f"Lambda - _load_lambda - Não foi possível carregar o módulo para {lambda_name}")

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        handler = module.lambda_handler
        self._handler = handler
