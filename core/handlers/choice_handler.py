from typing import Any
from core.utils.state_base import State, StateType
from core.utils.parser import CacheHandler
from logging_config import _i


class Choice(State):

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
                break

            except Exception as e:
                from core.utils.parser import ConditionParser
                condition_handler = ConditionParser(self.cache_handler)
                condition_handler.parse()
                count += 1

    def handler(self, event: Any, context: dict[str, Any]) -> Any:

        if self.jsonpath_wrapper:
            self.next_state = self.jsonpath_wrapper(event)
            return event

        raise Exception("Choice jsonpath_wrapper not loaded.")
