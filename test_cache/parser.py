from typing import Any
import re
import hashlib
import os
import json
from jsonpath_ng import parse

from test_cache.logger import _i


def jsonpath_query(obj: Any, expr: str) -> Any:
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
        # raise JSONPathNotFound(f"JSONPath expression not matches: {expr}")
        return '__not_matches__'

    result = [match.value for match in matches]

    if len(result) == 1:
        return result[0]

    return result

# Cache management functions


def _generate_hash(choice_name: str, conditions: list[str], states: dict) -> str:
    """Generate a hash for the choice configuration to detect changes"""
    # Create a hashable representation of the input
    data_to_hash = {
        'choice_name': choice_name,
        'conditions': conditions,
        # Ensure states is hashable
        'states': {k: v for k, v in states.items()}
    }

    # Convert to JSON string for consistent hashing
    json_str = json.dumps(data_to_hash, sort_keys=True)

    # Generate SHA256 hash
    return hashlib.sha256(json_str.encode()).hexdigest()


def _get_cache_file_path(choice_name: str, content_hash: str) -> str:
    """Get the path for the cached function file"""
    cache_dir = os.path.join(os.path.dirname(__file__), 'conditions_cache')
    safe_choice_name = choice_name.replace('-', '_')
    filename = f"{safe_choice_name}_{content_hash[:8]}.py"
    return os.path.join(cache_dir, filename)


def _get_cache_metadata_path(choice_name: str) -> str:
    """Get the path for the cache metadata file"""
    cache_dir = os.path.join(os.path.dirname(__file__), 'conditions_cache')
    safe_choice_name = choice_name.replace('-', '_')
    filename = f"{safe_choice_name}_metadata.json"
    return os.path.join(cache_dir, filename)


def _is_cache_valid(choice_name: str, content_hash: str) -> bool:
    """Check if cache is valid for the given choice and hash"""
    metadata_path = _get_cache_metadata_path(choice_name)
    cache_file_path = _get_cache_file_path(choice_name, content_hash)

    # Check if both metadata and cache file exist
    if not os.path.exists(metadata_path) or not os.path.exists(cache_file_path):
        return False

    try:
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)

        # Check if the hash matches
        return metadata.get('hash') == content_hash
    except (json.JSONDecodeError, KeyError):
        return False


def _save_to_cache(choice_name: str, content_hash: str, function_code: str, jsonpath_params: dict[str, str] | None = None) -> str:
    """Save the generated function to cache and return the file path"""
    cache_dir = os.path.join(os.path.dirname(__file__), 'conditions_cache')

    # Ensure cache directory exists
    os.makedirs(cache_dir, exist_ok=True)

    cache_file_path = _get_cache_file_path(choice_name, content_hash)
    metadata_path = _get_cache_metadata_path(choice_name)

    # Clean up old cache files for this choice
    _cleanup_old_cache(choice_name, content_hash)

    # Save the function code
    with open(cache_file_path, 'w') as f:
        f.write(function_code)

    # Save metadata
    metadata = {
        'hash': content_hash,
        'choice_name': choice_name,
        'cache_file': cache_file_path,
        'created_at': str(os.path.getctime(cache_file_path)) if os.path.exists(cache_file_path) else None,
        'jsonpath_params': jsonpath_params or {}
    }

    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)

    return cache_file_path


def _cleanup_old_cache(choice_name: str, current_hash: str) -> None:
    """Remove old cache files for the same choice"""
    cache_dir = os.path.join(os.path.dirname(__file__), 'conditions_cache')
    safe_choice_name = choice_name.replace('-', '_')

    if not os.path.exists(cache_dir):
        return

    # Find and remove old cache files
    for filename in os.listdir(cache_dir):
        if filename.startswith(f"{safe_choice_name}_") and filename.endswith('.py'):
            if not filename.startswith(f"{safe_choice_name}_{current_hash[:8]}"):
                old_file_path = os.path.join(cache_dir, filename)
                try:
                    os.remove(old_file_path)
                    _i(f"Removed old cache file: {old_file_path}")
                except OSError:
                    pass


def _load_from_cache(choice_name: str, content_hash: str) -> str:
    """Load the cached function code"""
    cache_file_path = _get_cache_file_path(choice_name, content_hash)

    try:
        with open(cache_file_path, 'r') as f:
            return f.read()
    except FileNotFoundError:
        return ""


def _load_cache_metadata(choice_name: str) -> dict[str, Any]:
    """Load the cache metadata for a choice"""
    metadata_path = _get_cache_metadata_path(choice_name)

    try:
        with open(metadata_path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def create_jsonpath_wrapper(cached_function, jsonpath_params: dict[str, str]):
    """
    Create a wrapper function that accepts raw data and uses JSONPath to extract parameters

    Args:
        cached_function: The cached function that expects specific parameters
        jsonpath_params: Mapping from parameter name to JSONPath expression

    Returns:
        A wrapper function that accepts raw data and applies JSONPath extraction
    """
    def wrapper(data: dict[str, Any]) -> Any:
        """
        Wrapper function that extracts data using JSONPath and calls the cached function

        Args:
            data: Raw data dictionary to extract values from

        Returns:
            Result from the cached function
        """
        params = {}

        for param_name, jsonpath_expr in jsonpath_params.items():
            try:
                value = jsonpath_query(data, jsonpath_expr)
                params[param_name] = value

            except ValueError as e:
                # Handle missing values - you might want to use default values or raise
                _i(f"Warning: Could not extract {jsonpath_expr}: {e}")
                params[param_name] = None

        return cached_function(**params)

    return wrapper


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


def convert_jsonpath_to_params(condition) -> str:
    """Convert JSONPath expressions ($.) to parameter names"""
    import re

    # Find all JSONPath expressions
    jsonpath_pattern = r'\$\.\S*'  # r'\$\.[a-zA-Z_][a-zA-Z0-9_.-]*'

    def replace_jsonpath(match):
        jsonpath = match.group(0)
        # Convert $.user.name -> _user_name
        param_name = re.sub(r'[^a-zA-Z0-9_]', '_', jsonpath[1:])
        return param_name

    condition = re.sub(jsonpath_pattern, replace_jsonpath, condition)

    # Convert boolean literals
    condition = condition.replace(' true', ' True')
    condition = condition.replace(' false', ' False')
    condition = condition.replace(' null', ' None')

    return condition


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

        if '$.' in condition:
            condition = convert_jsonpath_to_params(condition)

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
        param_name = re.sub(r'[^a-zA-Z0-9_]', '_', p[1:])

        if param_name not in unique_params:
            unique_params.append(param_name)

    return f"\ndef {choice_name.replace('-', '_')}({', '.join(unique_params)}):\n"


def build_jsonpath_params_mapping(paramns: list[str]) -> dict[str, str]:
    """Build mapping from parameter name to original JSONPath"""
    mapping = {}

    for jsonpath in paramns:
        param_name = re.sub(r'[^a-zA-Z0-9_]', '_', jsonpath[1:])
        # Only add unique mappings
        if param_name not in mapping:
            mapping[param_name] = jsonpath

    return mapping


def subs(c, states) -> str:
    return states[c[1:]]['name']


def constants_builder(constants, states) -> str:
    # Remove duplicates while preserving order
    unique_constants = list(dict.fromkeys(
        cte[1:] for cte in constants))

    # Build constants declarations
    const_lines = [
        f"    {c.replace('-', '_')} = '{states[c]['name']}'\n"
        for c in unique_constants
    ]

    return '\n' + ''.join(const_lines) + '\n'


def op_substitution(condition) -> str:
    """Convert custom operators to Python operators"""
    import re

    # First convert JSONPath expressions to parameter names
    condition = convert_jsonpath_to_params(condition)

    # Function to handle operator replacements with proper precedence
    def replace_operators(text):
        # Handle complex operators first (contains, starts_with, ends_with)
        # Pattern to match: variable/expression operator literal/expression
        # More robust pattern that handles variables, strings, and parentheses

        # Handle contains: X contains Y -> Y in X
        text = re.sub(r'(\w+)\s+contains\s+(\'[^\']*\')', r'\2 in \1', text)
        text = re.sub(r'(\w+)\s+contains\s+(\w+)', r'\2 in \1', text)

        # Handle starts_with: X starts_with Y -> X.startswith(Y)
        text = re.sub(
            r'(\w+)\s+starts_with\s+(\'[^\']*\')', r'\1.startswith(\2)', text)
        text = re.sub(r'(\w+)\s+starts_with\s+(\w+)',
                      r'\1.startswith(\2)', text)

        # Handle ends_with: X ends_with Y -> X.endswith(Y)
        text = re.sub(
            r'(\w+)\s+ends_with\s+(\'[^\']*\')', r'\1.endswith(\2)', text)
        text = re.sub(r'(\w+)\s+ends_with\s+(\w+)', r'\1.endswith(\2)', text)

        # Basic comparison operators
        text = re.sub(r'\s+gt\s+', ' > ', text)
        text = re.sub(r'\s+lt\s+', ' < ', text)
        text = re.sub(r'\s+eq\s+', ' == ', text)
        text = re.sub(r'\s+neq\s+', ' != ', text)
        text = re.sub(r'\s+gte\s+', ' >= ', text)
        text = re.sub(r'\s+lte\s+', ' <= ', text)

        # # Boolean operators
        # text = re.sub(r'\s+and\s+', ' and ', text)
        # text = re.sub(r'\s+or\s+', ' or ', text)
        # text = re.sub(r'\s+not\s+', ' not ', text)

        return text

    return replace_operators(condition)


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

    while 'exist ' in condition:
        i = condition.index('exist ')
        js_path = condition[i+6:].split(' ', 1)[0]
        term = f"{js_path} != '__not_matches__'"
        subst = f"exist {js_path}"
        condition = condition.replace(subst, term)

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
            function_builder += "\n    # default\n"\
                f"    return {default_value.replace('#', '').replace('-', '_')}\n"
            break

        # Skip conditions without 'when'
        if 'when' not in condition:
            continue

        # Process the statement (which may be nested)
        function_builder += "\n" + process_statement(condition, 1)

    return function_builder


"""
- literal string: 'any character, number, symbols, etc betwen simple quotes'.
- literal number: 10 | 15.5 # integer or decimal
- list: [] | Json-like list
- dict: {} | Json-like dict
- JSONPath: $.term # JSONPath string
- term: JSONPath | literal string | literal number | list | dict | true | false | null.
- op: Comparison operators (gt, lt, eq, neq, gte, lte, contains, starts_with, ends_with).
- bool_op: Boolean operators (and, or).
- comparison: term op term
- condition: comparison | condition bool_op condition | not condition | exist JSONPath | (condition)
- sttm: [when condition] then [sttm | term else sttm | term]
"""


def parse_cond(choice_name: str, conditions: list[str], states: dict[str, Any]) -> str:
    """
    Parse conditions and generate a Python function, using cache when possible.
    Returns the path to the cached function file.
    """
    # Generate hash for cache validation
    content_hash = _generate_hash(choice_name, conditions, states)

    # Check if cache is valid
    if _is_cache_valid(choice_name, content_hash):
        cached_code = _load_from_cache(choice_name, content_hash)
        if cached_code:
            _i(f"Using cached function for '{choice_name}' (hash: {content_hash[:8]})")
            _i("Cached function code:")
            _i(cached_code)
            return _get_cache_file_path(choice_name, content_hash)

    # Cache miss or invalid - generate new function
    _i(f"Generating new function for '{choice_name}' (hash: {content_hash[:8]})")

    # get parameters
    paramns = []
    constants = []

    for cond in conditions:
        paramns += extract_jsonpath_variables(cond)
        constants += extract_constants(cond)

    # Build JSONPath to parameter mapping
    jsonpath_params = build_jsonpath_params_mapping(paramns)

    function_builder = build_function_signature(choice_name, paramns)
    function_builder += constants_builder(constants, states)
    function_builder = if_then_builder(function_builder, conditions)

    # Show the generated function
    _i("Generated function code:")
    _i(function_builder)

    # Save to cache with JSONPath mapping
    cache_file_path = _save_to_cache(
        choice_name, content_hash, function_builder, jsonpath_params)
    _i(f"Function cached at: {cache_file_path}")
    _i(f"JSONPath parameters mapping: {jsonpath_params}")

    return cache_file_path
