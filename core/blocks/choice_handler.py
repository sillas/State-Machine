import re
from typing import Any
from core.utils.parsers import PARSERS, ConditionParser


OPERATORS = {
    ' gt ': lambda l, r: l > r,
    ' lt ': lambda l, r: l < r,
    ' eq ': lambda l, r: l == r,
    ' neq ': lambda l, r: l != r,
    ' gte ': lambda l, r: l >= r,
    ' lte ': lambda l, r: l <= r,
    ' contains ': lambda l, r: r in l,
    ' starts_with ': lambda l, r: l.startswith(r),
    ' ends_with ': lambda l, r: l.endswith(r)
}


class Choice:
    """
    Choice is a class designed to parse and evaluate conditional expressions over structured data (typically dictionaries or JSON-like objects).
    Supported Syntax:
        - term: JSONPath expression (e.g., $.item), literal string, literal number, empty list, or list of C.
        - op: Comparison operators (gt, lt, eq, neq, gte, lte, contains, starts_with, ends_with).
        - bool_op: Boolean operators (and, or).
        - comparison: term op term
        - condition: comparison | condition bool_op condition | not condition | (condition)
        - sttm: [when condition] then [sttm | term else sttm | term]
    Main Methods:
        - __init__(data): Initializes the evaluator with a data dictionary.
        - evaluate(operations): Evaluates a list of conditional operation strings, returning the result of the first satisfied condition or None.
        - _parse_condition(condition): Parses and evaluates a single condition string.
        - _extract_parentheses_content(condition): Extracts content within parentheses from a condition string.
    Usage:
        Instantiate with a data dictionary, then call `evaluate()` with a list of conditional statements.
        The class supports nested conditions, boolean logic, and JSONPath queries for dynamic data extraction.
        ValueError: For invalid operation formats or empty conditions.
    """

    _data = None
    _operations = []

    def __init__(self, operations: list[str]) -> None:
        self._operations = operations

    def run(self, data: dict[str, Any]):
        self._data = data
        return self._evaluate(self._operations)

    def _evaluate(self, operations: list[str]) -> Any:
        """
        Evaluates a list of conditional operation strings and returns the result based on the first satisfied condition.

        Each operation string can be in the format:
            - "<condition>"
            - "when <condition> then <result>"
            - "when <condition> then <result> else <alternative>"

        The method parses and evaluates each operation in order. If a condition is met, it returns the corresponding result.
        If an 'else' clause is present and the condition is not met, it evaluates and returns the alternative result.
        If no conditions are met, returns None.

        Args:
            operations (list[str]): A list of operation strings to evaluate.

        Returns:
            Any: The result of the first satisfied condition, or None if no conditions are met.

        Raises:
            ValueError: If an operation string is in an invalid format.
        """

        for ops in operations:
            try:

                if not ops or not ops.strip():
                    continue

                ops = ops.strip()

                if ' then ' not in ops:
                    return self._parse_condition(ops)

                when_part, then = ops.split(' then ', 1)

                if when_part.strip().startswith('when '):
                    condition = when_part[5:]  # Remove 'when '
                else:
                    condition = when_part

                result = self._parse_condition(condition.strip())

                if result:
                    if ' else ' in then:
                        return then.split(' else ')[0].strip()

                    if "then" in then:
                        then = self._evaluate([then])

                    return then

                if ' else ' in then:
                    result = self._evaluate(
                        [then.split(' else ', 1)[1].strip()])
                    if result is None:
                        continue

                    return result

            except Exception as e:
                continue

        return None

    def _extract_parentheses_content(self, condition: str) -> str:
        """Extrai conteúdo entre parênteses de forma mais robusta."""
        match = re.search(r'\((.*)\)', condition)
        if match:
            return match.group(1)
        return condition

    def _parse_condition(self, condition: str | None) -> Any:

        if condition is None or condition == '':
            raise ValueError("Condition cannot be empty or None!")

        if '(' in condition:  # (condition)
            condition = self._extract_parentheses_content(condition)

        if condition.startswith('not '):  # not condition
            not_condition = condition[4:].strip()

            if not_condition is None or not_condition.strip() == "":
                raise ValueError(f"Wrong condition value: {not_condition}")

            return not self._parse_condition(not_condition.strip())

        if ' and ' in condition or ' or ' in condition:  # condition bool_op condition
            op = ' and ' if ' and ' in condition else ' or '

            left, right = condition.split(op, 1)
            left = self._parse_condition(left)
            right = self._parse_condition(right)

            return left and right if op == ' and ' else left or right

        if ' ' in condition.strip():  # comparison
            for op, func in OPERATORS.items():
                if op in condition:
                    left, right = condition.split(op, 1)
                    left = self._parse_condition(left.strip())
                    right = self._parse_condition(right.strip())
                    return func(left, right)

        for parser in PARSERS:
            p: ConditionParser = parser()
            if p.can_parse(condition):
                return p.parse(self, condition)


if __name__ == "__main__":

    # Dados de teste
    test_data = {
        "user": {
            "name": "Jonas Silva",
            "age": 37,
            "items": ["apple", "banana"]
        },
        "price": 170,
        "empty_list": []
    }

    # Lista de operações
    operations = [
        "when ($.user.age gt 36) then 'senior' else when ($.user.age lt 10) then 'children' else 'young'",
        "when $.user.name starts_with 'João' or $.user.name starts_with 'Jonas' then 'matched name'",
        "when $.user.items contains 'banana' then 'has banana'",
        "when $.price gte 100 then 'expensive'",
        "when (not $.price gte 180) then 'sheper'",
        "when $.empty_list eq [] then 'list is empty'",
        "'default value'"
    ]

    evaluator = Choice(operations)

    # Testa a avaliação
    result = evaluator.run(test_data)
    print(f"Resultado X: {result}")
