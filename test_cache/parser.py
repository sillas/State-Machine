import re
import os
import json
import hashlib
import importlib.util
from typing import Any
from jsonpath_ng import parse
from test_cache.logger import _i


class Utils:

    @staticmethod
    def _match(pattern, text) -> list[str]:

        matches = re.findall(pattern, text)
        return matches

    @staticmethod
    def extract_constants(text: str) -> list[str]:

        pattern = r'\#\S*'
        return Utils._match(pattern, text)

    @staticmethod
    def extract_jsonpath_variables(text: str) -> list[str]:
        pattern = r'\$\.\S*'
        return Utils._match(pattern, text)

    @staticmethod
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

    @staticmethod
    def build_jsonpath_params_mapping(paramns: list[str]) -> dict[str, str]:
        """Build mapping from parameter name to original JSONPath"""
        mapping = {}

        for jsonpath in paramns:
            param_name = re.sub(r'[^a-zA-Z0-9_]', '_', jsonpath[1:])
            # Only add unique mappings
            if param_name not in mapping:
                mapping[param_name] = jsonpath

        return mapping

    @staticmethod
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
            """
            params = {}

            for param_name, jsonpath_expr in jsonpath_params.items():
                try:
                    value = Utils.jsonpath_query(data, jsonpath_expr)
                    params[param_name] = value

                except ValueError as e:
                    # Handle missing values - you might want to use default values or raise
                    _i(f"Warning: Could not extract {jsonpath_expr}: {e}")
                    params[param_name] = None

            return cached_function(**params)

        return wrapper


class CacheHandler:
    def __init__(self, name: str, conditions: list[str], states: dict[str, Any]) -> None:
        self.name = name
        self.conditions = conditions
        self.states = states
        self.content_hash = ''

    def generate_hash(self) -> None:
        """Generate a hash for the choice configuration to detect changes"""
        # Create a hashable representation of the input
        data_to_hash = {
            'choice_name': self.name,
            'conditions': self.conditions
        }

        # Convert to JSON string for consistent hashing
        json_str = json.dumps(data_to_hash, sort_keys=True)

        # Generate SHA256 hash
        self.content_hash = hashlib.sha256(json_str.encode()).hexdigest()

    def get_path_from_cache(self) -> str | None:
        cache_file_path = self.is_cache_valid()

        if cache_file_path:
            cached_code = self._load_from_cache(cache_file_path)
            if cached_code:
                _i(f"Using cached function for '{self.name}' (hash: {self.content_hash[:8]})")
                _i("Cached function code:")
                _i(cached_code)
                return cache_file_path

        return None

    def _load_from_cache(self, cache_file_path) -> str:
        """Load the cached function code"""

        try:
            with open(cache_file_path, 'r') as f:
                return f.read()
        except FileNotFoundError:
            return ""

    def is_cache_valid(self) -> str | None:
        """Check if cache is valid for the given choice and hash"""

        metadata_path = self._get_path("metadata.json")
        cache_file_path = self._get_cache_file_path()

        # Check if both metadata and cache file exist
        if not os.path.exists(metadata_path) or not os.path.exists(cache_file_path):
            return None

        try:
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)

            return cache_file_path if metadata.get('hash') == self.content_hash else None
        except (json.JSONDecodeError, KeyError):
            return None

    def _get_cache_file_path(self) -> str:
        """Get the path for the cached function file"""
        return self._get_path(f"{self.content_hash[:8]}.py")

    def _get_path(self, filename) -> str:

        cache_dir: str = os.path.join(
            os.path.dirname(__file__),
            'conditions_cache'
        )

        safe_choice_name: str = self.name.replace('-', '_')
        filename = f"{safe_choice_name}_{filename}"

        return os.path.join(cache_dir, filename)

    def _save_to_cache(self, function_code: str, jsonpath_params: dict[str, str] | None = None) -> str:
        """Save the generated function to cache and return the file path"""
        name = self.name
        cache_dir = os.path.join(os.path.dirname(__file__), 'conditions_cache')

        # Ensure cache directory exists
        os.makedirs(cache_dir, exist_ok=True)

        cache_file_path = self._get_cache_file_path()
        metadata_path = self._get_path("metadata.json")

        # Clean up old cache files for this choice
        self._cleanup_old_cache()

        # Save the function code
        with open(cache_file_path, 'w') as f:
            f.write(function_code)

        # Save metadata
        metadata = {
            'hash': self.content_hash,
            'choice_name': name,
            'cache_file': cache_file_path,
            'created_at': str(os.path.getctime(cache_file_path)) if os.path.exists(cache_file_path) else None,
            'jsonpath_params': jsonpath_params or {}
        }

        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)

        return cache_file_path

    def _cleanup_old_cache(self) -> None:
        """Remove old cache files for the same choice"""

        cache_dir = os.path.join(os.path.dirname(__file__), 'conditions_cache')
        safe_choice_name = self.name.replace('-', '_')

        if not os.path.exists(cache_dir):
            return

        # Find and remove old cache files
        for filename in os.listdir(cache_dir):
            if filename.startswith(f"{safe_choice_name}_") and filename.endswith('.py'):
                if not filename.startswith(f"{safe_choice_name}_{self.content_hash[:8]}"):
                    old_file_path = os.path.join(cache_dir, filename)
                    try:
                        os.remove(old_file_path)
                        _i(f"Removed old cache file: {old_file_path}")
                    except OSError:
                        pass

    def _load_cache_metadata(self) -> dict[str, Any]:
        """Load the cache metadata for a choice"""
        metadata_path = self._get_path("metadata.json")

        try:
            with open(metadata_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def load_cached_function(self):
        """
        Load a cached function from a Python file
        """

        metadata = self._load_cache_metadata()
        if not metadata:
            raise ValueError(f"No metadata found for choice: {self.name}")

        cache_file_path = metadata['cache_file']

        spec = importlib.util.spec_from_file_location(
            "cached_module", cache_file_path)

        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load spec from {cache_file_path}")

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        function_name = self.name.replace('-', '_')
        cached_function = getattr(module, function_name)

        jsonpath_params = metadata.get('jsonpath_params', {})

        return Utils.create_jsonpath_wrapper(cached_function, jsonpath_params)


class ConditionParser:
    """
    - literal string: 'any character, number, symbols, etc between simple quotes'.
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

    def __init__(self, cache_handler: 'CacheHandler') -> None:
        self.name = cache_handler.name
        self.conditions = cache_handler.conditions
        self.states = cache_handler.states
        self.cache = cache_handler

    def parse(self) -> str:
        """
        Parse conditions and generate a Python function, using cache when possible.
        Returns the path to the cached function file.
        """
        conditions = self.conditions

        # Generate hash for cache validation
        self.cache.generate_hash()
        cache_file_path = self.cache.get_path_from_cache()
        if cache_file_path:
            return cache_file_path

        paramns = []
        constants = []

        for cond in conditions:
            paramns += Utils.extract_jsonpath_variables(cond)
            constants += Utils.extract_constants(cond)

        # Build JSONPath to parameter mapping

        function_signature = self._build_function_signature(paramns)
        function_constants = self._constants_builder(constants)

        proto_function = f"{function_signature}{function_constants}"
        function_builder = self._if_then_builder(proto_function)
        jsonpath_params = Utils.build_jsonpath_params_mapping(paramns)

        cache_file_path = self.cache._save_to_cache(
            function_builder,
            jsonpath_params
        )

        _i(f"Generated function - cached at: {cache_file_path}")

        return cache_file_path

    def _build_function_signature(self, paramns) -> str:
        # Remove duplicates while preserving order
        unique_params = []

        for p in paramns:
            param_name = re.sub(r'[^a-zA-Z0-9_]', '_', p[1:])

            if param_name not in unique_params:
                unique_params.append(param_name)

        return f"\ndef {self.name.replace('-', '_')}({', '.join(unique_params)}):\n"

    def _constants_builder(self, constants) -> str:
        # Remove duplicates while preserving order
        unique_constants = list(dict.fromkeys(
            cte[1:] for cte in constants))

        # Build constants declarations
        const_lines = [
            f"    {c.replace('-', '_')} = '{self.states[c]['name']}'\n"
            for c in unique_constants
        ]

        return '\n' + ''.join(const_lines) + '\n'

    def _if_then_builder(self, function_builder) -> str:
        """Build if-then statements for all conditions"""

        conditions = self.conditions
        condition_size = len(conditions) - 1
        for i, condition in enumerate(conditions):

            # Check if this is the last condition and doesn't have 'when' (default case)
            if i == condition_size and 'when' not in condition:
                # This is the default return
                default_value = condition if condition.startswith(
                    '#') else f"'{condition}'"

                function_builder += "\n    # default\n"\
                    f"    return {default_value.replace('#', '').replace('-', '_')}\n"
                break

            if 'when' not in condition:
                continue

            # Process the statement (which may be nested)
            function_builder += "\n" + self._process_statement(condition, 1)

        return function_builder

    def _process_statement(self, statement: str, indent_level: int = 1) -> str:
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
                    condition = self._op_substitution(condition)
                    result = f"{indent}if {condition}:\n"
                    result += self._process_statement(
                        then_part, indent_level + 1)
                    return result

                # Main-level else
                condition = self._op_substitution(condition)
                result = f"{indent}if {condition}:\n"

                if self._is_nested_statement(then_part):
                    result += self._process_statement(
                        then_part, indent_level + 1)
                else:
                    result += f"{indent}    return {then_part.replace('#', '').replace('-', '_')}\n"

                result += f"{indent}else:\n"

                if self._is_nested_statement(else_part):
                    result += self._process_statement(
                        else_part, indent_level + 1)
                else:
                    result += f"{indent}    return {else_part.replace('#', '').replace('-', '_')}\n"

                return result

        # Regular when-then statement
        condition, then_part = self._extract_nested_statement_parts(statement)
        condition = self._op_substitution(condition)

        while 'exist ' in condition:
            i = condition.index('exist ')
            js_path = condition[i+6:].split(' ', 1)[0]
            term = f"{js_path} != '__not_matches__'"
            subst = f"exist {js_path}"
            condition = condition.replace(subst, term)

        result = f"{indent}if {condition}:\n"

        if self._is_nested_statement(then_part):
            result += self._process_statement(then_part, indent_level + 1)
        else:
            result += f"{indent}    return {then_part.replace('#', '').replace('-', '_')}\n"

        return result

    def _extract_nested_statement_parts(self, statement: str) -> tuple[str, str]:
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
                condition = self._convert_jsonpath_to_params(condition)

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

    def _convert_jsonpath_to_params(self, condition) -> str:
        """Convert JSONPath expressions ($.) to parameter names"""

        # Find all JSONPath expressions
        jsonpath_pattern = r'\$\.\S*'  # r'\$\.[a-zA-Z_][a-zA-Z0-9_.-]*'

        def replace_jsonpath(match):
            jsonpath = match.group(0)
            # Convert $.user.name -> _user_name
            param_name = re.sub(r'[^a-zA-Z0-9_]', '_', jsonpath[1:])
            return param_name

        condition = re.sub(jsonpath_pattern, replace_jsonpath, condition)

        terms = {' true': ' True', ' false': ' False', ' null': ' None'}
        for term, new_term in terms.items():
            condition = condition.replace(term, new_term)

        return condition

    def _is_nested_statement(self, then_part: str) -> bool:
        """Check if the then part contains another when-then statement"""
        return 'when' in then_part and 'then' in then_part

    def _op_substitution(self, condition) -> str:
        """Convert custom operators to Python operators"""

        # First convert JSONPath expressions to parameter names
        condition = self._convert_jsonpath_to_params(condition)

        # Handle complex operators first (contains, starts_with, ends_with)
        # Pattern to match: variable/expression operator literal/expression
        # More robust pattern that handles variables, strings, and parentheses

        # Handle contains: X contains Y -> Y in X
        text = re.sub(
            r'(\w+)\s+contains\s+(\'[^\']*\')', r'\2 in \1', condition)
        text = re.sub(r'(\w+)\s+contains\s+(\w+)', r'\2 in \1', text)

        # Handle starts_with: X starts_with Y -> X.startswith(Y)
        text = re.sub(
            r'(\w+)\s+starts_with\s+(\'[^\']*\')', r'\1.startswith(\2)', text)
        text = re.sub(r'(\w+)\s+starts_with\s+(\w+)',
                      r'\1.startswith(\2)', text)

        # Handle ends_with: X ends_with Y -> X.endswith(Y)
        text = re.sub(
            r'(\w+)\s+ends_with\s+(\'[^\']*\')', r'\1.endswith(\2)', text)
        text = re.sub(r'(\w+)\s+ends_with\s+(\w+)',
                      r'\1.endswith(\2)', text)

        # Basic comparison operators
        text = re.sub(r'\s+gt\s+', ' > ', text)
        text = re.sub(r'\s+lt\s+', ' < ', text)
        text = re.sub(r'\s+eq\s+', ' == ', text)
        text = re.sub(r'\s+neq\s+', ' != ', text)
        text = re.sub(r'\s+gte\s+', ' >= ', text)
        text = re.sub(r'\s+lte\s+', ' <= ', text)

        return text
