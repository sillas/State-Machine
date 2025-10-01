from typing import Any
from time import time

from core.exceptions import ChoiceInitializationError
from core.utils.state_base import State, StateType
from core.utils.parser import CacheHandler


class Choice(State):
    """
    Choice state for flow control in a state machine.

    This class evaluates a set of conditional statements to determine the next state
    in the machine's execution flow. It caches dynamically created functions for efficient
    condition evaluation and uses a handler method to process input events.

    Attributes:
        jsonpath_wrapper (callable): Cached function for evaluating conditions.
        _data (Any): Internal data storage.
        _operations (list[str]): List of conditional statements.
        cache_handler (CacheHandler): Handles caching of condition functions.

    Args:
        name (str): Name of the state.
        statements (list[str]): List of conditional statements to evaluate.
        states (dict[str, Any]): Dictionary of possible states.

    Raises:
        Exception: If the condition evaluation function (jsonpath_wrapper) is not loaded.
    """

    jsonpath_wrapper = None

    def __init__(self, name: str, statements: list[str], states: dict[str, Any]) -> None:

        self._data = None
        self._operations = statements
        self.cache_handler = CacheHandler(name, statements, states)

        super().__init__(name=name, next_state=None, type=StateType.CHOICE, timeout=1)

        count = 0
        while count <= 1 and self.jsonpath_wrapper is None:

            try:
                self.jsonpath_wrapper = self.cache_handler.load_cached_function()
                return None

            except FileNotFoundError:
                from core.utils.parser import ConditionParser
                condition_handler = ConditionParser(self.cache_handler)
                condition_handler.parse()
                count += 1

            except Exception as e:
                raise ChoiceInitializationError(
                    f"Failed to initialize choice: {str(e)}") from e

    def handler(self, event: Any, context: dict[str, Any]) -> Any:

        context["timestamp"] = time()

        if self.jsonpath_wrapper:
            self.next_state = self.jsonpath_wrapper(event)
            return event

        raise Exception("Choice - handler - jsonpath_wrapper not loaded.")
