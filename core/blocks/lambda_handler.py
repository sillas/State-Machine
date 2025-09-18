from typing import Any, Optional
from time import time
from pathlib import Path
import importlib.util

from core.state_base import State, StateType


class Lambda(State):
    """
    Represents a Lambda function handler that dynamically loads and executes a Python module as a Lambda.

    Args:
        name (str): The name of the Lambda function.
        next_state (str | None): The next state to transition to after execution.
        timeout (Optional[int], optional): Timeout for Lambda execution in seconds.

    Attributes:
        _handler (callable | None): Cached handler function for the Lambda.

    Methods:
        handler(event: Any, context: dict[str, Any]) -> Any:
            Executes the Lambda handler.
            Updates the context with a timestamp.

        _load_lambda() -> callable:
            Loads the Lambda handler from the corresponding module file.
            Caches the handler for subsequent invocations.
            Raises ModuleNotFoundError if the Lambda module is not found.
            Raises ImportError if the module cannot be loaded.
    """

    _handler = None

    def __init__(self, name: str, next_state: str | None, timeout: Optional[int] = None) -> None:
        super().__init__(
            name=name,
            next_state=next_state,
            type=StateType.LAMBDA,
            timeout=timeout
        )

        self._load_lambda()  # pre-load the lambda handler

    def handler(self, event: Any, context: dict[str, Any]) -> Any:
        """
        Handles an incoming event and context for a Lambda-like function.

        Args:
            event (Any): The event data passed to the handler.
            context (dict[str, Any]): The context dictionary containing metadata about the invocation.

        Returns:
            Any: The result of the handler execution.

        Side Effects:
            Updates the 'timestamp' key in the context dictionary with the current time.

        Behavior:
            - If a custom handler (`self._handler`) is set, it delegates execution to it.
            - Otherwise, it loads the lambda handler and executes it.
        """

        context["timestamp"] = time()
        _handler = self._handler

        if _handler is None:
            _handler = self._load_lambda()

        return _handler(event, context)

    def _load_lambda(self):
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
        return handler
