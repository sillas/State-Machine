from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any
from jsonpath_ng import parse

if TYPE_CHECKING:
    from core.blocks.choice_handler import Choice


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
    def can_parse(self) -> bool:
        return "'" in self.condition

    def parse(self, evaluator: 'Choice') -> Any:
        # Apenas as duas primeiras aspas simples devem ser removidas, as demais devem ser mantias.
        return self.condition.replace("'", '', 2)


class EmptyListParser(ConditionParser):
    def can_parse(self) -> bool:
        return "[]" in self.condition

    def parse(self, evaluator: 'Choice') -> Any:
        return []


class ListParser(ConditionParser):
    def can_parse(self) -> bool:
        return "[" in self.condition

    def parse(self, evaluator: 'Choice') -> Any:
        cond_list = self.condition.split('[')[1].split(']')[0].split(',')
        return [evaluator._parse_condition(item) for item in cond_list]


class JsonPathParser(ConditionParser):
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
    def can_parse(self) -> bool:
        if '.' in self.condition:
            condition = self.condition.replace('.', '')

        return self.condition.isnumeric()

    def parse(self, evaluator: 'Choice') -> Any:
        try:
            if '.' in self.condition:
                return float(self.condition)

            return int(self.condition)

        except ValueError:
            return float('nan')


PARSERS = [
    EmptyListParser,
    LiteralStringParser,
    JsonPathParser,
    ListParser,
    NumberParser
]
