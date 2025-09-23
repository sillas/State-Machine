import re
from typing import Any
from jsonpath_ng import parse

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


class ConditionalEvaluator:
    """
    C = $.item (JSONPath) | 'literal string' | literal_number | [] | [C*]
    op = gt | lt | eq | neq | gte | lte | contains | starts_with | ends_with
    bool_op = and | or
    comparison = C op C
    condition = comparison | condition bool_op condition | not condition | (condition)
    sttm = [when condition] then [sttm | C else sttm | C]
    """

    _data = None

    def __init__(self, data: dict[str, Any]) -> None:
        self._data = data

    def evaluate(self, operations: list[str]) -> Any:

        for ops in operations:
            sttm_parts = ops.split(' then ', 1)

            if len(sttm_parts) < 2:
                condition = sttm_parts[0]

                if len(condition) > 0:
                    return self._parse_condition(sttm_parts[0].strip())

                raise ValueError("Invalid operation format: ", ops)

            left, then = sttm_parts
            result = self._parse_condition(left.replace("when", '').strip())

            if result:
                if ' else ' in then:
                    return then.split(' else ')[0].strip()

                if "then" in then:
                    then = self.evaluate([then])

                return then

            if ' else ' in then:
                result = self.evaluate([then.split(' else ', 1)[1].strip()])
                if result is None:
                    continue

                return result

        print("OPS!!! 4")
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

        if '(' in condition:
            # condition = condition.split('(')[1].split(')')[0]
            condition = self._extract_parentheses_content(condition)

        if ' not ' in condition:  # not
            not_condition = condition.split('not ')[1]

            if not_condition is None or not_condition.strip() == "":
                raise ValueError(f"Wrong condition value: {not_condition}")

            return not self._parse_condition(not_condition.strip())

        if ' and ' in condition or ' or ' in condition:  # cond bool_op cond
            op = ' and ' if ' and ' in condition else ' or '

            left, right = condition.split(op, 1)

            left = self._parse_condition(left)
            right = self._parse_condition(right)

            if op == ' and ':  # 1
                return left and right

            return left or right

        if ' ' in condition.strip():
            for op, func in OPERATORS.items():
                if op in condition:
                    left, right = condition.split(op, 1)
                    left = self._parse_condition(left.strip())
                    right = self._parse_condition(right.strip())
                    return func(left, right)

        if "'" in condition:
            return condition.replace("'", '', 2)  # literal string
        if "[]" in condition:
            return []
        if "[" in condition:
            cond_list = condition.split('[')[1].split(']')[0].split(',')
            return [self._parse_condition(item) for item in cond_list]
        if "$." in condition:
            return self._jsonpath_query(self._data, condition)

        try:
            if "." in condition:
                return float(condition)

            return int(condition)

        except ValueError:
            raise ValueError(f"Valor não é um número válido: {condition}")

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


if __name__ == "__main__":

    # Dados de teste
    test_data = {
        "user": {
            "name": "Jonas Silva",
            "age": 12,
            "items": ["apple", "banana"]
        },
        "price": 171,
        "empty_list": []
    }
    evaluator = ConditionalEvaluator(test_data)

    # Lista de operações
    operations = [
        "when $.user.age gt 36 then 'senior' else when $.user.age lt 10 then 'children' else 'young'",
        # "when $.user.name starts_with 'João' or $.user.name starts_with 'Jonas' then 'matched name'",
        # "when $.user.items contains 'uva' then 'has apple'",
        # "when ($.price gte 100) then 'expensive'",
        # "when $.empty_list eq [] then 'list is empty'",
        "'default value'"

        # "when $.value gt 10 and $.value lt 53 or $.value eq 100 then 'certo'",
        # "when $.value neq 99 then 'errado'",
        # "'none!'"
    ]

    # Testa a avaliação
    result = evaluator.evaluate(operations)
    print(f"Resultado X: {result}")
