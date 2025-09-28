import importlib.util
from typing import Any
from core.utils.state_base import State, StateType
from test_cache.logger import _i
from test_cache.parser import _load_cache_metadata, create_jsonpath_wrapper, parse_cond


def load_cached_function(cache_file_path: str, function_name: str):
    """
    Load a cached function from a Python file
    """
    spec = importlib.util.spec_from_file_location(
        "cached_module", cache_file_path)

    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load spec from {cache_file_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return getattr(module, function_name)


def load_cached_function_with_jsonpath(choice_name: str):
    """
    Load a cached function and create a JSONPath wrapper for easy usage

    Args:
        choice_name: Name of the choice to load

    Returns:
        A wrapper function that accepts raw data and uses JSONPath extraction
    """
    # Load metadata
    metadata = _load_cache_metadata(choice_name)
    if not metadata:
        raise ValueError(f"No metadata found for choice: {choice_name}")

    cache_file_path = metadata.get('cache_file')
    jsonpath_params = metadata.get('jsonpath_params', {})

    if not cache_file_path:
        raise ValueError(
            f"No cache file path in metadata for choice: {choice_name}")

    # Load the raw cached function
    function_name = choice_name.replace('-', '_')
    cached_function = load_cached_function(cache_file_path, function_name)

    # Create JSONPath wrapper
    wrapper = create_jsonpath_wrapper(cached_function, jsonpath_params)

    _i(f"Loaded cached function with JSONPath mapping: {jsonpath_params}")

    return wrapper


class Choice2(State):

    jsonpath_wrapper = None

    def __init__(self, name: str, statements: list[str], states: dict[str, Any]) -> None:
        self._data = None
        self._operations = statements
        super().__init__(name=name, next_state=None, type=StateType.CHOICE, timeout=1)

        while self.jsonpath_wrapper is None:
            try:
                self.jsonpath_wrapper = load_cached_function_with_jsonpath(
                    name
                )
                break
            except Exception:
                parse_cond(name, statements, states)

    def handler(self, event: Any, context: dict[str, Any]) -> Any:
        if self.jsonpath_wrapper:
            return self.jsonpath_wrapper(event)

        raise
