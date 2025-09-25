import json
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any
from jsonpath_ng import parse

if TYPE_CHECKING:
    from core.handlers.choice_handler import Choice


class ConditionParser(ABC):
    """Interface para parsers de condição."""

    def __init__(self, condition: str):
        self.data = None
        self.condition = condition.strip()

    @abstractmethod
    def can_parse(self) -> bool:
        pass

    @abstractmethod
    def parse(self) -> Any:
        pass


class LiteralStringParser(ConditionParser):
    """Parses conditions containing single quotes (literal string) by removing the first two occurrences."""

    def can_parse(self) -> bool:
        return "'" in self.condition

    def parse(self) -> Any:
        # Only the first two single quotes should be removed, the others should be kept.
        return self.condition.replace("'", '', 2)


class EmptyListParser(ConditionParser):
    """Parses conditions representing empty lists and returns an empty list."""

    def can_parse(self) -> bool:
        return "[]" in self.condition

    def parse(self) -> Any:
        return []


class EmptyDictParser(ConditionParser):
    """Parses conditions representing empty dicts and returns an empty dict."""

    def can_parse(self) -> bool:
        return "{}" in self.condition

    def parse(self) -> Any:
        return {}


class LiteralListParser(ConditionParser):
    """Parses list conditions from a string and evaluates each item using the provided evaluator."""
    # TODO tentar usar json.loads

    def can_parse(self) -> bool:
        return self.condition.startswith("[") and self.condition.endswith("]")

    def parse(self) -> Any:
        return json.loads(self.condition)


class LiteralDictParser(ConditionParser):  # TODO Parse dict with JSON.
    def can_parse(self) -> bool:
        return self.condition.startswith("{") and self.condition.endswith("}")

    def parse(self) -> Any:
        return json.loads(self.condition)


class JsonPathParser(ConditionParser):
    """Parses and evaluates JSONPath expressions against a given JSON-like object."""

    def can_parse(self) -> bool:
        return self.condition.startswith('$.')

    def parse(self) -> Any:
        data = self.data

        if not isinstance(data, (dict, list)):
            raise ValueError("JsonPathParser: 'data' must be a dict or list")

        return self._jsonpath_query(data, self.condition)

    def _jsonpath_query(self, obj: Any, expr: str) -> Any:
        """
        Takes a JSON object (Python dict/list) and a JSONPath expression,
        returns a list with the values found or a single value if only one match.
        """
        try:
            jsonpath_expr = parse(expr)

        except Exception as e:
            raise ValueError(f"Invalid JSONPath expression: {expr}") from e

        matches = jsonpath_expr.find(obj)
        if not matches:
            raise ValueError(f"JSONPath expression not matches: {expr}")

        result = [match.value for match in matches]

        if len(result) == 1:
            return result[0]

        return result


class NumberParser(ConditionParser):
    """Parses numeric string conditions, supporting both integer and float representations."""

    def can_parse(self) -> bool:
        condition = self.condition

        if '.' in condition:
            condition = condition.replace('.', '')

        return condition.isnumeric()

    def parse(self) -> Any:

        condition = self.condition

        try:
            if '.' in condition:
                return float(condition)

            return int(condition)

        except ValueError:
            raise ValueError(f"Cannot parse '{condition}' as a number")


PARSERS = [
    EmptyListParser,
    EmptyDictParser,
    LiteralStringParser,
    JsonPathParser,
    LiteralDictParser,
    LiteralListParser,
    NumberParser
]
