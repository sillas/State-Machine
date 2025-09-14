from enum import Enum
from typing import Any, Dict, List, Optional
from .jsonpath_query import jsonpath_query


class Operator(Enum):
    """Enum defining the supported comparison operators."""
    GT = "gt"   # greater than
    LT = "lt"   # less than
    EQ = "eq"   # equal
    NEQ = "neq" # not equal
    GTE = "gte" # greater than or equal
    LTE = "lte" # less than or equal
    CONTAINS = "contains" # for strings/lists
    STARTS_WITH = "starts_with" # for strings
    ENDS_WITH = "ends_with" # for strings


class BooleanOperator(Enum):
    """Enum defining the supported boolean operators."""
    AND = "AND"
    OR = "OR"


class StatementEvaluator:
    """
    Class for evaluating conditional statements and determining the next state.
    
    The statements are defined in a structure where each statement has:
    - sttm: List of condition expressions or None for default case
    - then: The next state to transition to if the condition is true
    - bool_ops: Boolean operator to chain with the next statement (AND, OR, None)
    """
    
    def __init__(self, statements: Optional[List[Dict[str, Any]]]):
        """
        Initialize the evaluator with a list of conditional statements.
        
        Args:
            statements: List of statement dictionaries defining the conditions and next states
        
        Raises:
            ValueError: If the statements structure is invalid
        """
        if statements is None:
            raise ValueError("Statements cannot be None")
        
        self._validate_statements(statements)
        self.statements = statements
    
    def _validate_statements(self, statements: List[Dict[str, Any]]) -> None:
        """
        Validate the statements structure for correctness.
        
        Args:
            statements: List of statement dictionaries to validate
            
        Raises:
            ValueError: If the structure is invalid
        """
        if not statements:
            raise ValueError("Statements list cannot be empty")
        
        # Check if the last statement is a default case
        last_statement = statements[-1]
        if last_statement.get("sttm") is not None:
            raise ValueError("Last statement must be a default case with sttm=None")
        
        if "then" not in last_statement:
            raise ValueError("Default statement must have a 'then' value")
        
        # Validate each statement
        for i, statement in enumerate(statements):
            if "sttm" not in statement:
                raise ValueError(f"Statement {i} missing 'sttm' key")
            
            if i < len(statements) - 1:  # Skip validation for default case
                if statement["sttm"] is None:
                    raise ValueError(f"Only the last statement can have sttm=None")
                
                if "then" not in statement and "bool_ops" not in statement:
                    raise ValueError(f"Statement {i} must have either 'then' or 'bool_ops'")
                
                bool_ops = statement.get("bool_ops")
                if bool_ops is not None and bool_ops not in [op.value for op in BooleanOperator]:
                    raise ValueError(f"Invalid bool_ops value in statement {i}: {bool_ops}")
    
    def _get_value(self, value_expr: Any, data: Dict[str, Any]) -> Any:
        """
        Extract a value from data based on expression or return literal value.
        
        Args:
            value_expr: String or literal value. If string starts with "$.", treated as JSON path
            data: The data object to extract values from
            
        Returns:
            The extracted value or the literal value
        """
        # If not a string or doesn't start with "$.", treat as literal
        if not isinstance(value_expr, str) or not value_expr.startswith("$."):
            return value_expr
        
        try:
            # Use the existing jsonpath_query function
            return jsonpath_query(data, value_expr)
        except Exception as e:
            raise ValueError(f"Error extracting value at path '{value_expr}': {str(e)}")
    
    def _apply_operator(self, left: Any, op: str, right: Any) -> bool:
        """
        Apply the operator between left and right values.
        
        Args:
            left: Left operand
            op: Operator string (from Operator enum)
            right: Right operand
            
        Returns:
            Boolean result of the operation
            
        Raises:
            ValueError: If the operator is unsupported or types are incompatible
        """
        try:
            if op == Operator.GT.value:
                return left > right
            elif op == Operator.LT.value:
                return left < right
            elif op == Operator.EQ.value:
                return left == right
            elif op == Operator.NEQ.value:
                return left != right
            elif op == Operator.GTE.value:
                return left >= right
            elif op == Operator.LTE.value:
                return left <= right
            elif op == Operator.CONTAINS.value:
                return right in left
            elif op == Operator.STARTS_WITH.value:
                return left.startswith(right) if isinstance(left, str) else False
            elif op == Operator.ENDS_WITH.value:
                return left.endswith(right) if isinstance(left, str) else False
            else:
                raise ValueError(f"Unsupported operator: {op}")
        except TypeError:
            raise ValueError(f"Type mismatch for operation '{op}' between {type(left)} and {type(right)}")
    
    def _parse_condition(self, condition_str: str) -> Dict[str, Any]:
        """
        Parse a condition string in the format "$.a op1 $.b" into components.
        
        Args:
            condition_str: The condition string to parse
            
        Returns:
            Dictionary with left, op, and right components
        """
        parts = condition_str.split()
        if len(parts) != 3:
            raise ValueError(f"Invalid condition format: {condition_str}. Expected 'left op right'")
        
        left, op, right = parts
        
        # Validate operator
        if op not in [op.value for op in Operator]:
            raise ValueError(f"Invalid operator in condition: {op}")
            
        # Try to convert right to a number if it's not a path
        if not right.startswith("$."):
            try:
                # Try to convert to int
                if right.isdigit() or (right[0] == '-' and right[1:].isdigit()):
                    right = int(right)
                # Try to convert to float
                elif '.' in right and right.replace('.', '', 1).replace('-', '', 1).isdigit():
                    right = float(right)
                # Handle boolean values
                elif right.lower() == 'true':
                    right = True
                elif right.lower() == 'false':
                    right = False
            except ValueError:
                # Keep as string if conversion fails
                pass
        
        return {
            "left": left,
            "op": op,
            "right": right
        }
    
    def _evaluate_condition(self, statement: Dict[str, Any], data: Dict[str, Any]) -> bool:
        """
        Evaluate a condition statement against the provided data.
        
        Args:
            statement: The statement dictionary with sttm, then, and bool_ops
            data: The data object to evaluate against
            
        Returns:
            Boolean result of the condition evaluation
        """
        if statement.get("sttm") is None:
            return True  # Default case always evaluates to True
        
        conditions = statement["sttm"]
        results = []
        
        for condition_str in conditions:
            parsed = self._parse_condition(condition_str)
            left = self._get_value(parsed["left"], data)
            right = self._get_value(parsed["right"], data)
            result = self._apply_operator(left, parsed["op"], right)
            results.append(result)
        
        # Combine results based on AND operation (default)
        return all(results)
    
    def evaluate(self, data: Dict[str, Any]) -> Optional[str]:
        """
        Evaluate the statements against the provided data and return the next state.
        
        Args:
            data: The data object to evaluate against
            
        Returns:
            The next state as a string, or None if no condition matches
            
        Raises:
            ValueError: If there's an error in the evaluation process
        """
        i = 0
        while i < len(self.statements):
            statement = self.statements[i]
            
            # Evaluate the current statement
            result = self._evaluate_condition(statement, data)
            
            # If this statement has a boolean operator
            if statement.get("bool_ops") is not None:
                bool_op = statement.get("bool_ops")
                
                # Make sure we're not at the end
                if i + 1 >= len(self.statements):
                    raise ValueError("Boolean operation requested but no next statement exists")
                
                next_statement = self.statements[i + 1]
                next_result = self._evaluate_condition(next_statement, data)
                
                # Apply boolean operation
                if bool_op == BooleanOperator.AND.value:
                    combined_result = result and next_result
                elif bool_op == BooleanOperator.OR.value:
                    combined_result = result or next_result
                else:
                    raise ValueError(f"Unsupported boolean operator: {bool_op}")
                
                # If we have a combined result
                if combined_result:
                    return next_statement.get("then")
                
                # Skip the next statement since we already evaluated it
                i += 2
                continue
            
            # No boolean operator, just check the result
            if result:
                return statement.get("then")
            
            # Move to the next statement
            i += 1
        
        # If we get here, return the default case (last statement)
        return self.statements[-1].get("then")
