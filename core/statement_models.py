from enum import Enum
from typing import Any, Optional


class Operator(Enum):
    """Supported comparison operators."""
    GT = "gt"   # greater than
    LT = "lt"   # less than
    EQ = "eq"   # equal
    NEQ = "neq"  # not equal
    GTE = "gte"  # greater than or equal
    LTE = "lte"  # less than or equal
    CONTAINS = "contains"  # for strings/lists
    STARTS_WITH = "starts_with"  # for strings
    ENDS_WITH = "ends_with"  # for strings


class BooleanOperator(Enum):
    """Supported boolean operators."""
    AND = "AND"
    OR = "OR"


class Condition:
    """
    Represents an individual condition in the format "left op right".

    Example:
        condition = Condition("$.user.age", Operator.GT, 18)
    """

    def __init__(self, left: Operator | str, operator: Operator, right: Any):
        """
        Initializes a condition.

        Args:
            left: Left side of the condition, usually a JSONPath
            operator: Comparison operator
            right: Right side of the condition, can be a literal value or JSONPath
        """
        self.left = left

        if isinstance(operator, str):
            try:
                self.operator = Operator(operator)

            except ValueError:
                raise ValueError(f"Operador inválido: {operator}")
        else:
            self.operator = operator

        self.right = right

    def to_string(self) -> str:
        """Converts the condition to string format."""
        return f"{self.left} {self.operator.value} {self.right}"

    @classmethod
    def from_string(cls, condition_str: str) -> 'Condition':
        """
        Creates a condition from a string.

        Args:
            condition_str: String in the format "left op right"

        Returns:
            Condition object
        """
        parts = condition_str.split()
        if len(parts) != 3:
            raise ValueError(
                f"Formato de condição inválido: {condition_str}. Esperado 'left op right'")

        left, op, right = parts

        # Tenta converter o right para número ou booleano se não for um path
        if not right.startswith("$."):
            try:
                # Tenta converter para int
                if right.isdigit() or (right[0] == '-' and right[1:].isdigit()):
                    right = int(right)
                # Tenta converter para float
                elif '.' in right and right.replace('.', '', 1).replace('-', '', 1).isdigit():
                    right = float(right)
                # Trata valores booleanos
                elif right.lower() == 'true':
                    right = True
                elif right.lower() == 'false':
                    right = False
            except ValueError:
                # Mantém como string se a conversão falhar
                pass

        return cls(left, Operator(op), right)


class Statement:
    """
    Represents a complete statement with conditions and next state.

    Example:
        statement = Statement(
            conditions=[Condition("$.user.age", Operator.GT, 18)],
            next_state="adult_state",
            bool_op=None
        )
    """

    def __init__(
        self,
        conditions: Optional[list[Condition | str]] = None,
        next_state: Optional[str] = None,
        bool_op: Optional[BooleanOperator | str] = None
    ):
        """
        Initializes a statement.

        Args:
            conditions: list of conditions or None for default case
            next_state: Next state if the conditions are true
            bool_op: Boolean operator to chain with the next statement
        """
        # Processa as condições
        self.conditions = None
        if conditions:
            self.conditions = []
            for cond in conditions:
                if isinstance(cond, str):
                    self.conditions.append(Condition.from_string(cond))
                else:
                    self.conditions.append(cond)

        self.next_state = next_state

        # Processa o operador booleano
        if bool_op is None:
            self.bool_op = None
        elif isinstance(bool_op, str):
            try:
                self.bool_op = BooleanOperator(bool_op)
            except ValueError:
                raise ValueError(f"Operador booleano inválido: {bool_op}")
        else:
            self.bool_op = bool_op

    def to_dict(self) -> dict[str, Any]:
        """Converts the statement to dictionary format."""
        result = {
            "sttm": None if self.conditions is None else [c.to_string() for c in self.conditions],
            "then": self.next_state,
            "bool_ops": None if self.bool_op is None else self.bool_op.value
        }
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'Statement':
        """
        Creates a statement from a dictionary.

        Args:
            data: Dictionary with the keys 'sttm', 'then', and 'bool_ops'

        Returns:
            Statement object
        """
        conditions = data.get("sttm")
        next_state = data.get("then")
        bool_op = data.get("bool_ops")

        return cls(conditions, next_state, bool_op)


class StatementBuilder:
    """
    Fluent builder to create statements in a more readable way.

    Example:
        statement = (
            StatementBuilder()
            .when("$.user.age", Operator.GT, 18)
            .and_when("$.user.verified", Operator.EQ, True)
            .then("adult_verified_state")
            .build()
        )
    """

    def __init__(self):
        """Initializes the builder."""
        self.conditions = []
        self.next_state = None
        self.bool_op = None

    def when(self, left: str, operator: Operator, right: Any) -> 'StatementBuilder':
        """Adds a condition to the statement."""
        if self.conditions is None:
            self.conditions = []
        self.conditions.append(Condition(left, operator, right))
        return self

    def and_when(self, left: str, operator: Operator, right: Any) -> 'StatementBuilder':
        """Adds a condition with implicit AND."""
        return self.when(left, operator, right)

    def or_when(self, left: str, operator: Operator, right: Any) -> 'StatementBuilder':
        """
        Adds a condition and sets bool_op as OR for the next statement.
        """
        if self.conditions is None:
            self.conditions = []
        self.conditions.append(Condition(left, operator, right))
        self.bool_op = BooleanOperator.OR
        return self

    def and_next(self) -> 'StatementBuilder':
        """Sets that the next statement should be combined with AND."""
        self.bool_op = BooleanOperator.AND
        return self

    def or_next(self) -> 'StatementBuilder':
        """Sets that the next statement should be combined with OR."""
        self.bool_op = BooleanOperator.OR
        return self

    def then(self, next_state: str) -> 'StatementBuilder':
        """Sets the next state."""
        self.next_state = next_state
        return self

    def default(self, next_state: str) -> 'StatementBuilder':
        """Sets a default statement."""
        self.conditions = None
        self.next_state = next_state
        self.bool_op = None
        return self

    def build(self) -> Statement:
        """Builds and returns the Statement object."""
        return Statement(self.conditions, self.next_state, self.bool_op)


class DefaultStatements:

    @staticmethod
    def next_state(next_state: str) -> Statement:
        """Default statement."""
        return (
            StatementBuilder()
            .default(next_state)
            .build()
        )
