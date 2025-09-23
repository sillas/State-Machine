from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any
from jsonpath_ng import parse

if TYPE_CHECKING:
    from core.blocks.choice_handler import Choice


class ConditionParser(ABC):
    """Interface para parsers de condição."""

    @abstractmethod
    def can_parse(self, condition: str) -> bool:
        pass

    @abstractmethod
    def parse(self, evaluator: 'Choice', condition: str) -> Any:
        pass


class LiteralStringParser(ConditionParser):
    def can_parse(self, condition: str) -> bool:
        return "'" in condition

    def parse(self, evaluator: 'Choice', condition: str) -> Any:
        # Apenas as duas primeiras aspas simples devem ser removidas, as demais devem ser mantias.
        return condition.replace("'", '', 2)


class EmptyListParser(ConditionParser):
    def can_parse(self, condition: str) -> bool:
        return "[]" in condition

    def parse(self, evaluator: 'Choice', condition: str) -> Any:
        return []


class ListParser(ConditionParser):
    def can_parse(self, condition: str) -> bool:
        return "[" in condition

    def parse(self, evaluator: 'Choice', condition: str) -> Any:
        cond_list = condition.split('[')[1].split(']')[0].split(',')
        return [evaluator._parse_condition(item) for item in cond_list]


class JsonPathParser(ConditionParser):
    def can_parse(self, condition: str) -> bool:
        return "$." in condition

    def parse(self, evaluator: 'Choice', condition: str) -> Any:
        return self._jsonpath_query(evaluator._data, condition)

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
    def can_parse(self, condition: str) -> bool:
        if '.' in condition:
            condition = condition.replace('.', '')

        return condition.isnumeric()

    def parse(self, evaluator: 'Choice', condition: str) -> Any:
        try:
            if '.' in condition:
                return float(condition)

            return int(condition)

        except ValueError:
            return float('nan')


PARSERS = [
    EmptyListParser,
    LiteralStringParser,
    JsonPathParser,
    ListParser,
    NumberParser
]
