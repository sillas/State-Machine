"""
Exemplo de como utilizar as funções cached geradas pelo parser
"""

import importlib.util
from parser import parse_cond, _load_cache_metadata, create_jsonpath_wrapper
from logger import _i


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


def main():
    """Demonstrate usage of cached functions"""

    _i("=== Demo: Using Cached Functions ===")

    # Generate or get cached function
    choice_name = "user-evaluation"
    conditions = [
        "when $.user.age gte 18 and $.user.status eq 'active' then #adult-active",
        "when $.user.age lt 18 then #minor",
        "when $.user.status eq 'inactive' then #inactive-user",
        "#default"
    ]

    states = {
        "adult-active": {"name": "adult_active_state"},
        "minor": {"name": "minor_state"},
        "inactive-user": {"name": "inactive_user_state"},
        "default": {"name": "default_state"}
    }

    # Parse and cache the function
    _i("\n--- Generating/Loading cached function ---")
    cache_file_path = parse_cond(choice_name, conditions, states)

    # === METHOD 1: Old way - using specific parameters ===
    _i("\n=== METHOD 1: Direct parameter usage (old way) ===")
    function_name = choice_name.replace('-', '_')
    try:
        cached_function = load_cached_function(cache_file_path, function_name)
        _i(f"Successfully loaded function: {function_name}")

        # Test the function with different inputs
        test_cases_old = [
            {"user_age": 25, "user_status": "active",
                "expected": "adult_active_state"},
            {"user_age": 16, "user_status": "active", "expected": "minor_state"},
            {"user_age": 30, "user_status": "inactive",
                "expected": "inactive_user_state"},
            {"user_age": 20, "user_status": "pending", "expected": "default_state"}
        ]

        _i("\n--- Testing cached function (old way) ---")
        for i, test_case in enumerate(test_cases_old, 1):
            result = cached_function(
                test_case["user_age"],
                test_case["user_status"]
            )

            status = "✓" if result == test_case["expected"] else "✗"
            _i(f"Test {i}: age={test_case['user_age']}, status='{test_case['user_status']}' → {result} {status}")

    except Exception as e:
        _i(f"Error loading cached function: {e}")

    # === METHOD 2: New way - using JSONPath wrapper ===
    _i("\n=== METHOD 2: JSONPath wrapper usage (new way) ===")
    try:
        jsonpath_wrapper = load_cached_function_with_jsonpath(choice_name)
        _i("Successfully loaded function with JSONPath wrapper")

        # Test with raw data objects - much more intuitive!
        test_data_cases = [
            {
                "data": {"user": {"age": 25, "status": "active"}},
                "expected": "adult_active_state"
            },
            {
                "data": {"user": {"age": 16, "status": "active"}},
                "expected": "minor_state"
            },
            {
                "data": {"user": {"age": 30, "status": "inactive"}},
                "expected": "inactive_user_state"
            },
            {
                "data": {"user": {"age": 20, "status": "pending"}},
                "expected": "default_state"
            }
        ]

        _i("\n--- Testing JSONPath wrapper function ---")
        for i, test_case in enumerate(test_data_cases, 1):
            data = test_case["data"]
            result = jsonpath_wrapper(data)

            status = "✓" if result == test_case["expected"] else "✗"
            _i(f"Test {i}: data={data} → {result} {status}")

    except Exception as e:
        _i(f"Error using JSONPath wrapper: {e}")


if __name__ == "__main__":
    main()
