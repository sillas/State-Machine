import re
import os
import json
import hashlib
import importlib.util
from pathlib import Path
from typing import Any
from jsonpath_ng import parse
from logging_config import _i, _w


class Utils:

    @staticmethod
    def _match(pattern, text) -> list[str]:
        matches = re.findall(pattern, text)
        return matches

    @staticmethod
    def extract_constants(text: str) -> list[str]:
        """
        Extracts all constants from the given text that match the pattern of a '#' followed by non-whitespace characters.
        """

        pattern = r'\#\S*'
        return Utils._match(pattern, text)

    @staticmethod
    def extract_jsonpath_variables(text: str) -> list[str]:
        """
        Extracts all unique JSONPath variables from the given text.
        """
        pattern = r'\$\.\S*'
        return list(set(Utils._match(pattern, text)))

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
            mapping[param_name] = jsonpath

        return mapping

    @staticmethod
    def remove_single_word_parentheses(text):
        """Remove parentheses that surround only a single word (with optional whitespace)"""
        pattern = r'\(\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\)'
        return re.sub(pattern, r'\1', text)

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
                    _w(f"Utils - create_jsonpath_wrapper - wrapper - Warning: Could not extract {jsonpath_expr}: {e}")
                    params[param_name] = None

            return cached_function(**params)

        return wrapper


class CacheHandler:
    """
    CacheHandler is responsible for managing the caching of dynamically generated Python functions based on specific choice configurations.

    Attributes:
        name (str): The name of the choice or function to be cached.
        conditions (list[str]): A list of conditions that define the choice configuration.
        states (dict[str, Any]): A dictionary representing the states relevant to the choice.
        content_hash (str): The SHA256 hash representing the current configuration for cache validation.
    """

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

        json_str = json.dumps(data_to_hash, sort_keys=True)

        # Generate SHA256 hash
        self.content_hash = hashlib.sha256(json_str.encode()).hexdigest()

    def get_path_from_cache(self) -> str | None:
        """Returns the cache file path if a valid cached version exists, otherwise None."""

        metadata = self.is_cache_valid()

        if metadata:
            cache_file_path = metadata['cache_file']
            cached_code = self._load_from_cache(cache_file_path)
            if cached_code:
                _i(f"CacheHandler - get_path_from_cache - Using cached function for '{self.name}' (hash: {self.content_hash[:8]})")
                return cache_file_path

        return None

    def _load_from_cache(self, cache_file_path) -> str:
        """Load the cached function code"""

        try:
            with open(cache_file_path, 'r') as f:
                return f.read()
        except FileNotFoundError:
            return ""

    def is_cache_valid(self) -> dict[str, Any] | None:
        """Check if cache is valid for the given choice and hash"""

        cache_file_path = self._get_cache_file_path()

        if not os.path.exists(cache_file_path):
            return None

        metadata_path = self._get_path("metadata.json")
        try:
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)

            return metadata if metadata.get('hash') == self.content_hash else None
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
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

        os.makedirs(cache_dir, exist_ok=True)

        cache_file_path = self._get_cache_file_path()
        metadata_path = self._get_path("metadata.json")

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
                        _i(f"CacheHandler - _cleanup_old_cache - Removed old cache file: {old_file_path}")
                    except OSError:
                        pass

    def clear_all_cache(self) -> None:
        """Remove the entire cache directory and all its contents"""
        import shutil

        cache_dir = Path(__file__).parent / 'conditions_cache'

        if cache_dir.exists():
            try:
                shutil.rmtree(cache_dir)
                _i(f"CacheHandler - clear_all_cache - Removed entire cache directory: {cache_dir}")
            except OSError as e:
                _w(f"CacheHandler - clear_all_cache - Failed to remove cache directory: {e}")

    def load_cached_function(self):
        """
        Load a cached function from a Python file
        """
        metadata = self.is_cache_valid()
        if metadata is None:
            raise FileNotFoundError(
                f"CacheHandler - load_cached_function - No metadata found for choice: {self.name}")

        cache_file_path = metadata['cache_file']

        spec = importlib.util.spec_from_file_location(
            "cached_module", cache_file_path)

        if spec is None or spec.loader is None:
            raise ImportError(
                f"CacheHandler - load_cached_function - Could not load spec from {cache_file_path}")

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
    - op: gt | lt | eq | neq | gte | lte | contains | starts_with | ends_with.
    - bool_op: and | or.
    - comparison: term op term
    - condition: comparison | condition bool_op condition | not condition | exist JSONPath | (condition)
    - sttm: literal string | when condition then [sttm | term | else term]
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

        paramns = list(set(paramns))

        # Build JSONPath to parameter mapping
        function_signature = self._build_function_signature(paramns)
        function_constants = self._constants_builder(constants)

        proto_function = f"{function_signature}{function_constants}"
        function_builder = self._if_then_else_builder(proto_function)
        jsonpath_params = Utils.build_jsonpath_params_mapping(paramns)

        cache_file_path = self.cache._save_to_cache(
            function_builder,
            jsonpath_params
        )

        _i(f"ConditionParser - parser - Generated function - cached at: {cache_file_path}")

        return cache_file_path

    def _build_function_signature(self, paramns) -> str:
        """
        Builds a Python function signature string using sanitized parameter names.
        """

        unique_params = []

        for p in paramns:
            param_name = re.sub(r'[^a-zA-Z0-9_]', '_', p[1:])
            unique_params.append(param_name)

        return f"\ndef {self.name.replace('-', '_')}({', '.join(unique_params)}):\n"

    def _constants_builder(self, constants) -> str:
        """Build constants declarations"""

        unique_constants = list(
            dict.fromkeys(cte[1:] for cte in constants)
        )

        const_lines = [
            f"    {c.replace('-', '_')} = '{self.states[c]['name']}'\n"
            for c in unique_constants
        ]

        return '\n' + ''.join(const_lines) + '\n'

    def _if_then_else_builder(self, function_builder) -> str:
        """Build if-then-else statements for all conditions"""

        conditions = self.conditions
        condition_size = len(conditions) - 1
        for i, condition in enumerate(conditions):

            if i == condition_size:
                then_count = condition.count('then ')

                if then_count == 1:
                    if not ' else ' in condition:
                        raise Exception(
                            f'Malformation of the last condition: {condition}')

                if then_count > 1:
                    raise Exception(
                        f'The final condition has nested conditions, without a default value: {condition}')

            function_builder += "\n" + self._process_statement(condition, 1)

        return function_builder

    def add_constants_or_literals(self, indent, statement) -> str | None:

        if statement.startswith('#'):
            return f"{indent}return {statement[1:].replace('-', '_')}\n"

        if statement[0] == "'" and statement[-1] == "'":
            if not "'" in statement[1:-1]:
                return f"{indent}return {statement}\n"

        return None

    def _process_statement(self, statement: str, indent_level: int = 1) -> str:
        """Process a single statement (could be nested) and return Python code"""
        indent = "    " * indent_level

        # If it's just a constant, return it
        result = self.add_constants_or_literals(indent, statement)
        if result:
            return result

        condition, then_part = self._extract_nested_statement_parts(statement)
        condition = self._op_substitution(condition)

        while 'exist ' in condition:
            i = condition.index('exist ')
            js_path = condition[i+6:].split(' ', 1)[0]
            term = f"{js_path} != '__not_matches__'"
            subst = f"exist {js_path}"
            condition = condition.replace(subst, term)

        condition = Utils.remove_single_word_parentheses(condition)

        result = f"{indent}if {condition}:\n"

        if self._is_nested_statement(then_part):
            result += self._process_statement(then_part, indent_level + 1)

        elif ' else ' in then_part:
            _then, _else = then_part.split(' else ')

            _then = _then[1:].replace('-', '_') if _then.startswith('#') else _then  # nopep8
            _else = _else[1:].replace('-', '_') if _else.startswith('#') else _else  # nopep8

            result += f"{indent}    return {_then}\n{indent}return {_else}\n"

        else:
            ctes_ltr = self.add_constants_or_literals(indent, then_part)
            if ctes_ltr:
                result += f"    {ctes_ltr}"

        return result

    def _extract_nested_statement_parts(self, statement: str) -> tuple[str, str]:
        """
        Extract condition and then-part from a when-then statement
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

        # Find all JSONPath expressions - match $.word but stop at non-word characters
        jsonpath_pattern = r'\$\.([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)'

        def replace_jsonpath(match):
            jsonpath_content = match.group(1)  # Get the part after $.
            # Convert user.name -> _user_name (replace dots with underscores)
            param_name = '_' + jsonpath_content.replace('.', '_')
            return param_name

        condition = re.sub(jsonpath_pattern, replace_jsonpath, condition)

        terms = {' true': ' True', ' false': ' False', ' null': ' None'}
        for term, new_term in terms.items():
            condition = condition.replace(term, new_term)

        return condition

    def _is_nested_statement(self, then_part: str) -> bool:
        """Check if the then part contains another when-then statement"""
        return 'when' in then_part

    def _op_substitution(self, condition) -> str:
        """Convert custom operators to Python operators"""

        # First convert JSONPath expressions to parameter names
        text = self._convert_jsonpath_to_params(condition)

        # Handle complex operators first (contains, starts_with, ends_with)
        # Pattern to match: variable/expression operator literal/expression
        # More robust pattern that handles variables, strings, and parentheses

        # Handle contains: X contains Y -> Y in X
        pattern = r'(.+?)\s+contains\s+(.+)'
        match = re.match(pattern, text.strip())
        if match:
            term_1 = match.group(1).strip()
            term_2 = match.group(2).strip()
            # Troca os termos e substitui 'contains' por 'in'
            text = f"{term_2} in {term_1}"

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
