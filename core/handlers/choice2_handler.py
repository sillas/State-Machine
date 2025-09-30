from typing import Any
from core.utils.state_base import State, StateType
from core.utils.parser import CacheHandler


class Choice2(State):

    jsonpath_wrapper = None

    def __init__(self, name: str, statements: list[str], states: dict[str, Any]) -> None:

        self._data = None
        self._operations = statements
        self.cache_handler = CacheHandler(name, statements, states)

        super().__init__(name=name, next_state=None, type=StateType.CHOICE, timeout=1)

        while self.jsonpath_wrapper is None:

            try:
                self.jsonpath_wrapper = self.cache_handler.load_cached_function()
                break

            except Exception:
                from core.utils.parser import ConditionParser
                condition_handler = ConditionParser(self.cache_handler)
                condition_handler.parse()

    def handler(self, event: Any, context: dict[str, Any]) -> Any:

        if self.jsonpath_wrapper:
            return self.jsonpath_wrapper(event)

        raise Exception("Choice2 jsonpath_wrapper not loaded.")
