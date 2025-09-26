from logger import _i
import re


def _match(pattern, text) -> list[str]:

    matches = re.findall(pattern, text)
    return matches


def extract_constants(text: str) -> list[str]:

    pattern = r'\#\S*'
    return _match(pattern, text)


def extract_jsonpath_variables(text: str) -> list[str]:

    pattern = r'\$\.\S*'
    return _match(pattern, text)


def extract_when_then_term(text: str) -> str:
    pattern = r'when\s+(.*?)\s+then'
    matches = _match(pattern, text)
    return matches[0] if matches else ""


def is_nested_statement(then_part: str) -> bool:
    """Check if the then part contains another when-then statement"""
    return 'when' in then_part and 'then' in then_part


def extract_nested_statement_parts(statement: str) -> tuple[str, str]:
    """Extract condition and then-part from a when-then statement
    Returns (condition, then_part)
    """
    # Simple regex approach first - works for most cases
    # Pattern to match: when (condition) then (then_part)
    # But we need to be careful with nested statements

    match = re.search(r'when\s+(.*?)\s+then\s+(.*)', statement, re.DOTALL)
    if match:
        condition = match.group(1).strip()
        then_part = match.group(2).strip()

        # Check if the then_part contains another 'when' before any 'else'
        # If so, we need to be more careful about where the 'then' ends
        if 'when' in then_part:
            # This is a complex case - let's use a more sophisticated approach
            when_pos = statement.find('when')
            if when_pos == -1:
                return condition, then_part

            # Find the corresponding 'then'
            search_start = when_pos + 4  # after 'when'
            then_positions = []
            pos = search_start

            while True:
                then_pos = statement.find('then', pos)
                if then_pos == -1:
                    break
                then_positions.append(then_pos)
                pos = then_pos + 4

            if then_positions:
                # Take the first 'then' that follows our 'when'
                first_then = then_positions[0]
                condition = statement[when_pos + 4:first_then].strip()
                then_part = statement[first_then + 4:].strip()

        return condition, then_part

    return "", statement


def build_function_signature(choice_name, paramns) -> str:
    # Remove duplicates while preserving order
    unique_params = []

    for p in paramns:
        param_name = p[1:].replace('-', '_').replace('.', '_')

        if param_name not in unique_params:
            unique_params.append(param_name)

    return f"\ndef {choice_name.replace('-', '_')}({', '.join(unique_params)}):\n"


def subs(c, states) -> str:
    return states[c[1:]]['name']


def constants_builder(function_builder, constants, states) -> str:
    # Remove duplicates while preserving order
    unique_constants = list(dict.fromkeys(
        cte[1:] for cte in constants))

    # Build constants declarations
    const_lines = [
        f"    {c.replace('-', '_')} = '{states[c]['name']}'\n"
        for c in unique_constants
    ]

    return function_builder + '\n' + ''.join(const_lines) + '\n'


def convert_jsonpath_to_params(condition) -> str:
    """Convert JSONPath expressions ($.) to parameter names"""
    import re

    # Find all JSONPath expressions
    jsonpath_pattern = r'\$\.[a-zA-Z_][a-zA-Z0-9_.-]*'

    def replace_jsonpath(match):
        jsonpath = match.group(0)
        # Convert $.user.name -> _user_name
        param_name = jsonpath[1:].replace('-', '_').replace('.', '_')
        return param_name

    condition = re.sub(jsonpath_pattern, replace_jsonpath, condition)

    # Convert boolean literals
    condition = condition.replace(' true', ' True')
    condition = condition.replace(' false', ' False')

    return condition


def op_substitution(condition) -> str:
    """Convert custom operators to Python operators"""

    # First convert JSONPath expressions to parameter names
    condition = convert_jsonpath_to_params(condition)

    # Basic comparison operators
    if ' gt ' in condition:
        condition = condition.replace(' gt ', ' > ')
    if ' lt ' in condition:
        condition = condition.replace(' lt ', ' < ')
    if ' eq ' in condition:
        condition = condition.replace(' eq ', ' == ')
    if ' neq ' in condition:
        condition = condition.replace(' neq ', ' != ')
    if ' gte ' in condition:
        condition = condition.replace(' gte ', ' >= ')
    if ' lte ' in condition:
        condition = condition.replace(' lte ', ' <= ')

    # String and collection operations
    if ' contains ' in condition:
        # For contains: left contains right -> right in left
        parts = condition.split(' contains ')
        left = parts[0].strip()
        right = parts[1].strip()
        condition = f"{right} in {left}"

    if ' starts_with ' in condition:
        # For starts_with: left starts_with right -> left.startswith(right)
        parts = condition.split(' starts_with ')
        left = parts[0].strip()
        right = parts[1].strip()
        condition = f"{left}.startswith({right})"

    if ' ends_with ' in condition:
        # For ends_with: left ends_with right -> left.endswith(right)
        parts = condition.split(' ends_with ')
        left = parts[0].strip()
        right = parts[1].strip()
        condition = f"{left}.endswith({right})"

    # Handle 'in' operator for lists (e.g., _name in ['n1', 'n2', 'n3'])
    # This should already work with Python syntax

    return condition


def process_statement(statement: str, indent_level: int = 1) -> str:
    """Process a single statement (could be nested) and return Python code"""
    indent = "    " * indent_level

    # If it's just a constant, return it
    if statement.startswith('#'):
        return f"{indent}return {statement.replace('#', '').replace('-', '_')}\n"

    # If it doesn't contain 'when', it's a literal return
    if 'when' not in statement:
        return f"{indent}return {statement.replace('#', '').replace('-', '_')}\n"

    # Handle else clause - need to be careful about nested else
    if ' else ' in statement:
        # Find the position of else that corresponds to the main statement
        # We need to find the 'else' that's not inside a nested when-then

        # First, extract the main when-then part
        main_when_match = re.search(
            r'when\s+(.*?)\s+then\s+(.*?)(?:\s+else\s+(.*))?$', statement, re.DOTALL)
        if main_when_match:
            condition = main_when_match.group(1).strip()
            then_part = main_when_match.group(2).strip()
            else_part = main_when_match.group(
                3).strip() if main_when_match.group(3) else ""

            # Check if the then_part contains 'else' - if so, it's part of then_part
            if ' else ' in then_part and else_part == "":
                # The else is inside the then_part, not at the main level
                condition = op_substitution(condition)
                result = f"{indent}if {condition}:\n"
                result += process_statement(then_part, indent_level + 1)
                return result

            # Main-level else
            condition = op_substitution(condition)
            result = f"{indent}if {condition}:\n"

            if is_nested_statement(then_part):
                result += process_statement(then_part, indent_level + 1)
            else:
                result += f"{indent}    return {then_part.replace('#', '').replace('-', '_')}\n"

            result += f"{indent}else:\n"

            if is_nested_statement(else_part):
                result += process_statement(else_part, indent_level + 1)
            else:
                result += f"{indent}    return {else_part.replace('#', '').replace('-', '_')}\n"

            return result

    # Regular when-then statement
    condition, then_part = extract_nested_statement_parts(statement)
    condition = op_substitution(condition)

    result = f"{indent}if {condition}:\n"

    if is_nested_statement(then_part):
        result += process_statement(then_part, indent_level + 1)
    else:
        result += f"{indent}    return {then_part.replace('#', '').replace('-', '_')}\n"

    return result


def if_then_builder(function_builder, conditions) -> str:
    """Build if-then statements for all conditions"""

    for i, condition in enumerate(conditions):
        # Check if this is the last condition and doesn't have 'when' (default case)
        if i == len(conditions) - 1 and 'when' not in condition:
            # This is the default return
            default_value = condition if condition.startswith(
                '#') else f"'{condition}'"
            function_builder += f"""
    # default
    return {default_value.replace('#', '').replace('-', '_')}
"""
            break

        # Skip conditions without 'when'
        if 'when' not in condition:
            continue

        # Process the statement (which may be nested)
        function_builder += "\n" + process_statement(condition, 1)

    return function_builder

    """
    - term: JSONPath expression (e.g., $.item), literal string, literal number, empty list, or list of C true or false.
    - op: Comparison operators (gt, lt, eq, neq, gte, lte, contains, starts_with, ends_with).
    - bool_op: Boolean operators (and, or).
    - comparison: term op term
    - condition: comparison | condition bool_op condition | not condition | exist JSONPath-term | (condition)
    - sttm: [when condition] then [sttm | term else sttm | term]
    """


def parse_cond(choice_name, conditions: list[str], states) -> None:

    # get parameters
    paramns = []
    constants = []

    for cond in conditions:
        paramns += extract_jsonpath_variables(cond)
        constants += extract_constants(cond)

    function_builder = build_function_signature(choice_name, paramns)
    function_builder = constants_builder(function_builder, constants, states)
    function_builder = if_then_builder(function_builder, conditions)

    _i(function_builder)
