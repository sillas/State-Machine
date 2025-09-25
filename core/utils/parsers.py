from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any
from jsonpath_ng import parse

if TYPE_CHECKING:
    from core.handlers.choice_handler import Choice


class ConditionParser(ABC):
    """Interface para parsers de condição."""

    def __init__(self, condition: str):
        self.condition = condition

    @abstractmethod
    def can_parse(self) -> bool:
        pass

    @abstractmethod
    def parse(self, evaluator: 'Choice') -> Any:
        pass


class LiteralStringParser(ConditionParser):
    """Parses conditions containing single quotes (literal string) by removing the first two occurrences."""

    def can_parse(self) -> bool:
        return "'" in self.condition

    def parse(self, evaluator: 'Choice') -> Any:
        # Only the first two single quotes should be removed, the others should be kept.
        return self.condition.replace("'", '', 2)


class EmptyListParser(ConditionParser):
    """Parses conditions representing empty lists and returns an empty list."""

    def can_parse(self) -> bool:
        return "[]" in self.condition

    def parse(self, evaluator: 'Choice') -> Any:
        return []


class ListParser(ConditionParser):
    """Parses list conditions from a string and evaluates each item using the provided evaluator."""

    def can_parse(self) -> bool:
        return "[" in self.condition

    def parse(self, evaluator: 'Choice') -> Any:
        cond_list = self.condition.split('[')[1].split(']')[0].split(',')
        return [evaluator._parse_condition(item) for item in cond_list]


class JsonPathParser(ConditionParser):
    """Parses and evaluates JSONPath expressions against a given JSON-like object."""

    def can_parse(self) -> bool:
        return "$." in self.condition

    def parse(self, evaluator: 'Choice') -> Any:
        return self._jsonpath_query(evaluator._data, self.condition)

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

    def parse(self, evaluator: 'Choice') -> Any:

        condition = self.condition

        try:
            if '.' in condition:
                return float(condition)

            return int(condition)

        except ValueError:
            raise ValueError(f"Cannot parse '{condition}' as a number")


PARSERS = [
    EmptyListParser,
    LiteralStringParser,
    JsonPathParser,
    ListParser,
    NumberParser
]
