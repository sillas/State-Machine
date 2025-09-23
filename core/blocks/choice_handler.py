import logging
import re
from time import time
from typing import Any
from core.utils.parsers import PARSERS, ConditionParser
from core.utils.state_base import State, StateType


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


class Choice(State):
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

    def __init__(self, name: str, statements: list[str]) -> None:
        self._operations = statements
        super().__init__(name=name, next_state=None, type=StateType.CHOICE, timeout=1)

    def handler(self, event: Any, context: dict[str, Any]):
        self._data = event
        context["timestamp"] = time()
        self.next_state = self._evaluate(self._operations)
        return event

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

                ops = ops.replace('  ', ' ').strip()

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
                        then = then.split(' else ', 1)[0].strip()

                    return self._evaluate([then])

                if ' else ' in then:
                    else_sttm = then.split(' else ', 1)[1].strip()
                    result = self._evaluate([else_sttm])
                    if result is None:
                        continue

                    return result

            except Exception as e:
                logging.warning(
                    f"Exception occurred while evaluating operation '{ops}': {e}", exc_info=True)
                continue

        return None

    def _extract_parentheses_content(self, condition: str) -> str:
        """
        Extracts the content within the outermost parentheses from the given condition string.

        If the condition contains logical operators ('and' or 'or'), the original string is returned.
        Otherwise, if the condition is enclosed in parentheses, the content inside the parentheses is returned.
        If there are no parentheses, the original string is returned.

        Args:
            condition (str): The condition string to extract content from.

        Returns:
            str: The content inside the outermost parentheses, or the original string if no parentheses are found or if logical operators are present.
        """

        if ' and ' in condition or ' or ' in condition:
            return condition

        # Remove external parentheses if they exist
        match = re.search(r'\((.*)\)', condition)
        if match:
            return match.group(1)

        return condition

    def _parse_condition(self, condition: str | None) -> Any:
        """
        Parses and evaluates a logical or comparison condition expressed as a string.

        Supports the following condition formats:
            - Parenthesized conditions (e.g., "(condition)")
            - Negation using 'not' (e.g., "not condition")
            - Logical operations 'and'/'or' (e.g., "cond1 and cond2", "cond1 or cond2")
            - Comparisons using supported operators (e.g., "a eq b", "x bt y")
            - Custom condition parsing via registered PARSERS

        Args:
            condition (str | None): The condition string to parse and evaluate.

        Returns:
            Any: The result of evaluating the parsed condition.

        Raises:
            ValueError: If the condition is None, empty, or malformed.
        """

        if condition is None or condition == '':
            raise ValueError("Condition cannot be empty or None!")

        if '(' in condition:  # (condition)
            condition = self._extract_parentheses_content(condition)

        if condition.startswith('not '):  # not condition
            not_condition = condition[4:].strip()

            if not not_condition:
                raise ValueError(f"Wrong condition value: {not_condition}")

            return not self._parse_condition(not_condition)

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
            p: ConditionParser = parser(condition)
            if p.can_parse():
                return p.parse(self)
