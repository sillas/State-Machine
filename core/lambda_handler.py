from typing import Any, Optional
from time import time
from enum import Enum
from pathlib import Path
import importlib.util

from core.statement_evaluator import StatementEvaluator


class LambdaTypes(Enum):
    IF = "if_statement"
    LAMBDA = "lambda"


class Lambda:
    name: str
    type: str
    next_state: str | None
    statements: Optional[list]
    _handler = None
    timeout = 60  # seconds

    def __init__(self, name: str, next_state: str | None, type: LambdaTypes = LambdaTypes.LAMBDA, statements: Optional[list] = None, timeout: Optional[int] = None) -> None:
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


class IF(Lambda):

    def __init__(self, name: str, statements: list) -> None:
        self.evaluator = StatementEvaluator(statements)
        super().__init__(name, None, LambdaTypes.LAMBDA, timeout=1)

    def handler(self, event: Any, context: dict[str, Any]) -> Any:
        context["timestamp"] = time()
        self.next_state = self.evaluator.evaluate(event)
        return event
