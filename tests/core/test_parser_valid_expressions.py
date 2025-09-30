"""
Testes para o parser de condições focados em expressões VÁLIDAS.
Baseado na definição fornecida, testa se todas as expressões válidas são interpretadas corretamente.

Definição testada:
- literal string: 'any character, number, symbols, etc between simple quotes'.
- literal number: 10 | 15.5 # integer or decimal
- list: [] | Json-like list
- dict: {} | Json-like dict
- JSONPath: $.term # JSONPath string
- term: JSONPath | literal string | literal number | list | dict | true | false.
- op: Comparison operators (gt, lt, eq, neq, gte, lte, contains, starts_with, ends_with).
- bool_op: Boolean operators (and, or).
- comparison: term op term
- condition: comparison | condition bool_op condition | not condition | exist JSONPath | (condition)
- sttm: [when condition] then [sttm | term else sttm | term]
"""

from core.utils.parser import (  # type: ignore
    parse_cond,
    extract_constants,
    extract_jsonpath_variables,
    is_nested_statement,
    extract_nested_statement_parts,
    convert_jsonpath_to_params,
    op_substitution,
    build_function_signature,
    build_jsonpath_params_mapping,
    _load_cache_metadata,
    create_jsonpath_wrapper
)
import unittest
import sys
import os
import importlib.util
from pathlib import Path

# Adicionar o diretório test-cache ao path
test_cache_dir = Path(__file__).parent.parent.parent / "test-cache"
sys.path.insert(0, str(test_cache_dir))


def load_and_test_cached_function(choice_name: str, test_data: dict, expected_result: str):
    """Carrega uma função cached e testa com dados específicos."""
    metadata = _load_cache_metadata(choice_name)
    cache_file_path = metadata.get('cache_file')
    jsonpath_params = metadata.get('jsonpath_params', {})

    if not cache_file_path or not os.path.exists(cache_file_path):
        raise FileNotFoundError(f"Cache file not found for {choice_name}")

    # Carrega a função cached
    spec = importlib.util.spec_from_file_location(
        "cached_module", cache_file_path)
    module = importlib.util.module_from_spec(spec)  # type: ignore
    spec.loader.exec_module(module)  # type: ignore

    function_name = choice_name.replace('-', '_')
    cached_function = getattr(module, function_name)

    # Cria wrapper JSONPath
    wrapper = create_jsonpath_wrapper(cached_function, jsonpath_params)

    # Testa a função
    result = wrapper(test_data)
    return result == expected_result


class TestValidLiteralStrings(unittest.TestCase):
    """Testa parsing correto de literal strings válidas."""

    def setUp(self):
        self.choice_name = "valid_strings"
        self.states = {
            "match": {"name": "string_match"},
            "no-match": {"name": "no_match"},
            "default": {"name": "default_state"}
        }

    def test_simple_string_literals(self):
        """Testa strings literais simples com aspas simples."""
        conditions = [
            "when $.name eq 'João Silva' then #match",
            "when $.title eq 'Machine Learning Engineer' then #match",
            "#default"
        ]

        cache_path = parse_cond(self.choice_name, conditions, self.states)
        self.assertTrue(os.path.exists(cache_path))

        # Testa execução
        test_cases = [
            ({"name": "João Silva"}, "string_match"),
            ({"title": "Machine Learning Engineer"}, "string_match"),
            ({"name": "Other Name"}, "default_state")
        ]

        for test_data, expected in test_cases:
            result = load_and_test_cached_function(
                self.choice_name, test_data, expected)
            self.assertTrue(result, f"Failed for {test_data}")

    def test_strings_with_special_characters(self):
        """Testa strings com caracteres especiais válidos."""
        conditions = [
            "when $.text contains 'çãõáéíóú' then #match",
            "when $.message eq 'Hello, World! 🌍' then #match",
            "when $.path eq '/home/user/file.txt' then #match",
            "#default"
        ]

        cache_path = parse_cond(self.choice_name, conditions, self.states)
        self.assertTrue(os.path.exists(cache_path))

    def test_empty_string(self):
        """Testa string vazia válida."""
        conditions = [
            "when $.empty eq '' then #match",
            "#default"
        ]

        cache_path = parse_cond(self.choice_name, conditions, self.states)
        self.assertTrue(os.path.exists(cache_path))

        result = load_and_test_cached_function(
            self.choice_name, {"empty": ""}, "string_match")
        self.assertTrue(result)


class TestValidLiteralNumbers(unittest.TestCase):
    """Testa parsing correto de números válidos."""

    def setUp(self):
        self.choice_name = "valid_numbers"
        self.states = {
            "positive": {"name": "positive_number"},
            "negative": {"name": "negative_number"},
            "zero": {"name": "zero_value"},
            "decimal": {"name": "decimal_value"},
            "default": {"name": "default_state"}
        }

    def test_integer_numbers(self):
        """Testa números inteiros válidos."""
        conditions = [
            "when $.age eq 25 then #positive",
            "when $.temperature eq -5 then #negative",
            "when $.count eq 0 then #zero",
            "#default"
        ]

        cache_path = parse_cond(self.choice_name, conditions, self.states)
        self.assertTrue(os.path.exists(cache_path))

        test_cases = [
            ({"age": 25}, "positive_number"),
            ({"temperature": -5}, "negative_number"),
            ({"count": 0}, "zero_value")
        ]

        for test_data, expected in test_cases:
            result = load_and_test_cached_function(
                self.choice_name, test_data, expected)
            self.assertTrue(result, f"Failed for {test_data}")

    def test_decimal_numbers(self):
        """Testa números decimais válidos."""
        conditions = [
            "when $.price eq 99.99 then #decimal",
            "when $.rate eq 0.5 then #decimal",
            "when $.pi eq 3.14159 then #decimal",
            "#default"
        ]

        cache_path = parse_cond(self.choice_name, conditions, self.states)
        self.assertTrue(os.path.exists(cache_path))

        result = load_and_test_cached_function(
            self.choice_name, {"price": 99.99}, "decimal_value")
        self.assertTrue(result)


class TestValidLists(unittest.TestCase):
    """Testa parsing correto de listas válidas."""

    def setUp(self):
        self.choice_name = "valid_lists"
        self.states = {
            "empty": {"name": "empty_list"},
            "strings": {"name": "string_list"},
            "numbers": {"name": "number_list"},
            "mixed": {"name": "mixed_list"},
            "default": {"name": "default_state"}
        }

    def test_empty_list(self):
        """Testa lista vazia válida."""
        conditions = [
            "when $.items eq [] then #empty",
            "#default"
        ]

        cache_path = parse_cond(self.choice_name, conditions, self.states)
        self.assertTrue(os.path.exists(cache_path))

        result = load_and_test_cached_function(
            self.choice_name, {"items": []}, "empty_list")
        self.assertTrue(result)

    def test_string_lists(self):
        """Testa listas de strings válidas."""
        conditions = [
            'when $.tags eq ["python", "ai", "ml"] then #strings',
            "#default"
        ]

        cache_path = parse_cond(self.choice_name, conditions, self.states)
        self.assertTrue(os.path.exists(cache_path))

        result = load_and_test_cached_function(
            self.choice_name, {"tags": ["python", "ai", "ml"]}, "string_list")
        self.assertTrue(result)

    def test_number_lists(self):
        """Testa listas de números válidas."""
        conditions = [
            "when $.scores eq [85, 92, 78, 95] then #numbers",
            "#default"
        ]

        cache_path = parse_cond(self.choice_name, conditions, self.states)
        self.assertTrue(os.path.exists(cache_path))

        result = load_and_test_cached_function(
            self.choice_name, {"scores": [85, 92, 78, 95]}, "number_list")
        self.assertTrue(result)

    def test_mixed_lists(self):
        """Testa listas mistas válidas."""
        conditions = [
            'when $.data eq ["text", 42, true, null] then #mixed',
            "#default"
        ]

        cache_path = parse_cond(self.choice_name, conditions, self.states)
        self.assertTrue(os.path.exists(cache_path))


class TestValidDictionaries(unittest.TestCase):
    """Testa parsing correto de dicionários válidos."""

    def setUp(self):
        self.choice_name = "valid_dicts"
        self.states = {
            "empty": {"name": "empty_dict"},
            "simple": {"name": "simple_dict"},
            "nested": {"name": "nested_dict"},
            "default": {"name": "default_state"}
        }

    def test_empty_dictionary(self):
        """Testa dicionário vazio válido."""
        conditions = [
            "when $.metadata eq {} then #empty",
            "#default"
        ]

        cache_path = parse_cond(self.choice_name, conditions, self.states)
        self.assertTrue(os.path.exists(cache_path))

        result = load_and_test_cached_function(
            self.choice_name, {"metadata": {}}, "empty_dict")
        self.assertTrue(result)

    def test_simple_dictionary(self):
        """Testa dicionário simples válido."""
        conditions = [
            'when $.config eq {"enabled": true, "timeout": 30} then #simple',
            "#default"
        ]

        cache_path = parse_cond(self.choice_name, conditions, self.states)
        self.assertTrue(os.path.exists(cache_path))

        result = load_and_test_cached_function(
            self.choice_name,
            {"config": {"enabled": True, "timeout": 30}},
            "simple_dict"
        )
        self.assertTrue(result)


class TestValidBooleans(unittest.TestCase):
    """Testa parsing correto de valores booleanos válidos."""

    def setUp(self):
        self.choice_name = "valid_booleans"
        self.states = {
            "true-case": {"name": "true_value"},
            "false-case": {"name": "false_value"},
            "default": {"name": "default_state"}
        }

    def test_boolean_literals(self):
        """Testa literais booleanos válidos."""
        conditions = [
            "when $.active eq true then #true-case",
            "when $.disabled eq false then #false-case",
            "#default"
        ]

        cache_path = parse_cond(self.choice_name, conditions, self.states)
        self.assertTrue(os.path.exists(cache_path))

        test_cases = [
            ({"active": True}, "true_value"),
            ({"disabled": False}, "false_value")
        ]

        for test_data, expected in test_cases:
            result = load_and_test_cached_function(
                self.choice_name, test_data, expected)
            self.assertTrue(result, f"Failed for {test_data}")


class TestValidJSONPath(unittest.TestCase):
    """Testa parsing correto de expressões JSONPath válidas."""

    def setUp(self):
        self.choice_name = "valid_jsonpath"
        self.states = {
            "simple": {"name": "simple_path"},
            "nested": {"name": "nested_path"},
            "array": {"name": "array_path"},
            "default": {"name": "default_state"}
        }

    def test_simple_jsonpath(self):
        """Testa JSONPath simples válido."""
        conditions = [
            "when $.name eq 'João' then #simple",
            "when $.age gt 18 then #simple",
            "#default"
        ]

        cache_path = parse_cond(self.choice_name, conditions, self.states)
        self.assertTrue(os.path.exists(cache_path))

        # Verifica extração de JSONPath
        jsonpaths = extract_jsonpath_variables(
            "$.name eq 'João' and $.age gt 18")
        self.assertIn("$.name", jsonpaths)
        self.assertIn("$.age", jsonpaths)

    def test_nested_jsonpath(self):
        """Testa JSONPath aninhado válido."""
        conditions = [
            "when $.user.profile.name eq 'João' then #nested",
            "when $.config.database.host eq 'localhost' then #nested",
            "#default"
        ]

        cache_path = parse_cond(self.choice_name, conditions, self.states)
        self.assertTrue(os.path.exists(cache_path))

        result = load_and_test_cached_function(
            self.choice_name,
            {"user": {"profile": {"name": "João"}}},
            "nested_path"
        )
        self.assertTrue(result)

    def test_array_jsonpath(self):
        """Testa JSONPath com arrays válido."""
        conditions = [
            "when $.items[0] eq 'first' then #array",
            "#default"
        ]

        cache_path = parse_cond(self.choice_name, conditions, self.states)
        self.assertTrue(os.path.exists(cache_path))


class TestValidComparisonOperators(unittest.TestCase):
    """Testa todos os operadores de comparação válidos da definição."""

    def setUp(self):
        self.choice_name = "valid_operators"
        self.states = {
            "gt": {"name": "greater_than"},
            "lt": {"name": "less_than"},
            "eq": {"name": "equal"},
            "neq": {"name": "not_equal"},
            "gte": {"name": "greater_equal"},
            "lte": {"name": "less_equal"},
            "contains": {"name": "contains_match"},
            "starts": {"name": "starts_with_match"},
            "ends": {"name": "ends_with_match"},
            "default": {"name": "default_state"}
        }

    def test_numeric_comparison_operators(self):
        """Testa operadores de comparação numérica válidos."""
        conditions = [
            "when $.value gt 100 then #gt",
            "when $.value lt 50 then #lt",
            "when $.value eq 75 then #eq",
            "when $.value neq 0 then #neq",
            "when $.value gte 100 then #gte",
            "when $.value lte 50 then #lte",
            "#default"
        ]

        cache_path = parse_cond(self.choice_name, conditions, self.states)
        self.assertTrue(os.path.exists(cache_path))

        test_cases = [
            ({"value": 150}, "greater_than"),
            ({"value": 25}, "less_than"),
            ({"value": 75}, "equal"),
            ({"value": 5}, "not_equal"),
            ({"value": 100}, "greater_equal"),
            ({"value": 50}, "less_equal")
        ]

        for test_data, expected in test_cases:
            result = load_and_test_cached_function(
                self.choice_name, test_data, expected)
            self.assertTrue(result, f"Failed for {test_data} -> {expected}")

    def test_string_operators(self):
        """Testa operadores de string válidos."""
        conditions = [
            "when $.text contains 'search' then #contains",
            "when $.name starts_with 'João' then #starts",
            "when $.filename ends_with '.pdf' then #ends",
            "#default"
        ]

        cache_path = parse_cond(self.choice_name, conditions, self.states)
        self.assertTrue(os.path.exists(cache_path))

        test_cases = [
            ({"text": "search and find"}, "contains_match"),
            ({"name": "João Silva"}, "starts_with_match"),
            ({"filename": "document.pdf"}, "ends_with_match")
        ]

        for test_data, expected in test_cases:
            result = load_and_test_cached_function(
                self.choice_name, test_data, expected)
            self.assertTrue(result, f"Failed for {test_data}")


class TestValidBooleanOperators(unittest.TestCase):
    """Testa operadores booleanos válidos da definição."""

    def setUp(self):
        self.choice_name = "valid_boolean_ops"
        self.states = {
            "and-result": {"name": "and_condition"},
            "or-result": {"name": "or_condition"},
            "not-result": {"name": "not_condition"},
            "default": {"name": "default_state"}
        }

    def test_and_operator(self):
        """Testa operador AND válido."""
        conditions = [
            "when $.age gt 18 and $.active eq true then #and-result",
            "#default"
        ]

        cache_path = parse_cond(self.choice_name, conditions, self.states)
        self.assertTrue(os.path.exists(cache_path))

        test_cases = [
            ({"age": 25, "active": True}, "and_condition"),
            ({"age": 25, "active": False}, "default_state"),
            ({"age": 15, "active": True}, "default_state")
        ]

        for test_data, expected in test_cases:
            result = load_and_test_cached_function(
                self.choice_name, test_data, expected)
            self.assertTrue(result, f"Failed for {test_data}")

    def test_or_operator(self):
        """Testa operador OR válido."""
        conditions = [
            "when $.type eq 'admin' or $.permissions contains 'write' then #or-result",
            "#default"
        ]

        cache_path = parse_cond(self.choice_name, conditions, self.states)
        self.assertTrue(os.path.exists(cache_path))

        test_cases = [
            ({"type": "admin", "permissions": "read"}, "or_condition"),
            ({"type": "user", "permissions": "write access"}, "or_condition"),
            ({"type": "user", "permissions": "read"}, "default_state")
        ]

        for test_data, expected in test_cases:
            result = load_and_test_cached_function(
                self.choice_name, test_data, expected)
            self.assertTrue(result, f"Failed for {test_data}")

    def test_not_operator(self):
        """Testa operador NOT válido."""
        conditions = [
            "when not $.disabled eq true then #not-result",
            "#default"
        ]

        cache_path = parse_cond(self.choice_name, conditions, self.states)
        self.assertTrue(os.path.exists(cache_path))

        test_cases = [
            ({"disabled": False}, "not_condition"),
            ({"disabled": True}, "default_state")
        ]

        for test_data, expected in test_cases:
            result = load_and_test_cached_function(
                self.choice_name, test_data, expected)
            self.assertTrue(result, f"Failed for {test_data}")


class TestValidComplexConditions(unittest.TestCase):
    """Testa condições complexas válidas com múltiplos operadores."""

    def setUp(self):
        self.choice_name = "valid_complex"
        self.states = {
            "complex-match": {"name": "complex_condition"},
            "parentheses": {"name": "parentheses_condition"},
            "default": {"name": "default_state"}
        }

    def test_complex_boolean_combinations(self):
        """Testa combinações booleanas complexas válidas."""
        conditions = [
            "when $.age gt 18 and $.active eq true and $.verified eq true then #complex-match",
            "when $.score gte 80 and $.category eq 'premium' or $.vip eq true then #complex-match",
            "#default"
        ]

        cache_path = parse_cond(self.choice_name, conditions, self.states)
        self.assertTrue(os.path.exists(cache_path))

        test_cases = [
            ({"age": 25, "active": True, "verified": True}, "complex_condition"),
            ({"score": 85, "category": "premium"}, "complex_condition"),
            ({"score": 60, "vip": True}, "complex_condition"),
            ({"age": 15, "active": True, "verified": True}, "default_state")
        ]

        for test_data, expected in test_cases:
            result = load_and_test_cached_function(
                self.choice_name, test_data, expected)
            self.assertTrue(result, f"Failed for {test_data}")

    def test_parentheses_grouping(self):
        """Testa agrupamento com parênteses válido."""
        conditions = [
            "when ($.age gt 18 and $.active eq true) or ($.type eq 'admin') then #parentheses",
            "#default"
        ]

        cache_path = parse_cond(self.choice_name, conditions, self.states)
        self.assertTrue(os.path.exists(cache_path))

        test_cases = [
            ({"age": 25, "active": True, "type": "user"}, "parentheses_condition"),
            ({"age": 15, "active": False, "type": "admin"}, "parentheses_condition"),
            ({"age": 15, "active": False, "type": "user"}, "default_state")
        ]

        for test_data, expected in test_cases:
            result = load_and_test_cached_function(
                self.choice_name, test_data, expected)
            self.assertTrue(result, f"Failed for {test_data}")


class TestValidExistOperator(unittest.TestCase):
    """Testa operador exist válido."""

    def setUp(self):
        self.choice_name = "valid_exist"
        self.states = {
            "exists": {"name": "field_exists"},
            "default": {"name": "field_missing"}
        }

    def test_exist_operator(self):
        """Testa operador exist com JSONPath válido."""
        conditions = [
            "when exist $.optional_field then #exists",
            "when exist $.user.profile then #exists",
            "#default"
        ]

        cache_path = parse_cond(self.choice_name, conditions, self.states)
        self.assertTrue(os.path.exists(cache_path))


class TestValidStatements(unittest.TestCase):
    """Testa statements when-then-else válidos."""

    def setUp(self):
        self.choice_name = "valid_statements"
        self.states = {
            "adult": {"name": "adult_user"},
            "minor": {"name": "minor_user"},
            "premium": {"name": "premium_user"},
            "basic": {"name": "basic_user"},
            "default": {"name": "default_state"}
        }

    def test_simple_when_then_else(self):
        """Testa statement when-then-else simples válido."""
        conditions = [
            "when $.age gte 18 then #adult else #minor",
            "#default"
        ]

        cache_path = parse_cond(self.choice_name, conditions, self.states)
        self.assertTrue(os.path.exists(cache_path))

        test_cases = [
            ({"age": 25}, "adult_user"),
            ({"age": 16}, "minor_user")
        ]

        for test_data, expected in test_cases:
            result = load_and_test_cached_function(
                self.choice_name, test_data, expected)
            self.assertTrue(result, f"Failed for {test_data}")

    def test_nested_when_then_statements(self):
        """Testa statements aninhados válidos."""
        conditions = [
            "when $.age gte 18 then when $.premium eq true then #premium else #basic else #minor",
            "#default"
        ]

        cache_path = parse_cond(self.choice_name, conditions, self.states)
        self.assertTrue(os.path.exists(cache_path))

        test_cases = [
            ({"age": 25, "premium": True}, "premium_user"),
            ({"age": 25, "premium": False}, "basic_user"),
            ({"age": 16, "premium": True}, "minor_user")
        ]

        for test_data, expected in test_cases:
            result = load_and_test_cached_function(
                self.choice_name, test_data, expected)
            self.assertTrue(result, f"Failed for {test_data}")

    def test_multiple_conditions_list(self):
        """Testa lista de múltiplas condições válidas."""
        conditions = [
            "when $.score gte 90 then #premium",
            "when $.score gte 70 then #basic",
            "when $.age lt 18 then #minor",
            "#default"
        ]

        cache_path = parse_cond(self.choice_name, conditions, self.states)
        self.assertTrue(os.path.exists(cache_path))

        test_cases = [
            ({"score": 95}, "premium_user"),
            ({"score": 75}, "basic_user"),
            ({"score": 60, "age": 16}, "minor_user"),
            ({"score": 60, "age": 25}, "default_state")
        ]

        for test_data, expected in test_cases:
            result = load_and_test_cached_function(
                self.choice_name, test_data, expected)
            self.assertTrue(result, f"Failed for {test_data}")


class TestValidUtilityFunctions(unittest.TestCase):
    """Testa funções utilitárias com entradas válidas."""

    def test_extract_constants_valid(self):
        """Testa extração de constantes válidas."""
        text = "when $.age gt 18 then #adult else #minor"
        constants = extract_constants(text)
        self.assertEqual(len(constants), 2)
        self.assertIn("#adult", constants)
        self.assertIn("#minor", constants)

    def test_extract_jsonpath_variables_valid(self):
        """Testa extração de variáveis JSONPath válidas."""
        text = "when $.user.age gt 18 and $.user.active eq true then #success"
        jsonpaths = extract_jsonpath_variables(text)
        self.assertEqual(len(jsonpaths), 2)
        self.assertIn("$.user.age", jsonpaths)
        self.assertIn("$.user.active", jsonpaths)

    def test_convert_jsonpath_to_params_valid(self):
        """Testa conversão válida de JSONPath para parâmetros."""
        condition = "$.user.name eq 'João' and $.user.age gt 18"
        converted = convert_jsonpath_to_params(condition)

        self.assertIn("_user_name", converted)
        self.assertIn("_user_age", converted)
        self.assertNotIn("$.user.name", converted)
        self.assertNotIn("$.user.age", converted)

    def test_op_substitution_valid(self):
        """Testa substituição válida de operadores."""
        test_cases = [
            ("$.age gt 18", "_age > 18"),
            ("$.age lt 18", "_age < 18"),
            ("$.age eq 18", "_age == 18"),
            ("$.age neq 18", "_age != 18"),
            ("$.age gte 18", "_age >= 18"),
            ("$.age lte 18", "_age <= 18"),
            ("$.text contains 'hello'", "'hello' in _text"),
            ("$.name starts_with 'João'", "_name.startswith('João')"),
            ("$.file ends_with '.pdf'", "_file.endswith('.pdf')")
        ]

        for original, expected in test_cases:
            result = op_substitution(original)
            self.assertEqual(
                result, expected, f"Failed: {original} -> {result} (expected {expected})")

    def test_build_function_signature_valid(self):
        """Testa construção válida da assinatura da função."""
        choice_name = "test-choice"
        params = ["$.user.name", "$.user.age", "$.config.timeout"]
        signature = build_function_signature(choice_name, params)

        self.assertIn("def test_choice(", signature)
        self.assertIn("_user_name", signature)
        self.assertIn("_user_age", signature)
        self.assertIn("_config_timeout", signature)

    def test_build_jsonpath_params_mapping_valid(self):
        """Testa construção válida do mapeamento JSONPath -> parâmetros."""
        params = ["$.user.name", "$.user.age", "$.config.timeout"]
        mapping = build_jsonpath_params_mapping(params)

        expected_mapping = {
            "_user_name": "$.user.name",
            "_user_age": "$.user.age",
            "_config_timeout": "$.config.timeout"
        }

        self.assertEqual(mapping, expected_mapping)

    def test_nested_statement_functions_valid(self):
        """Testa funções de parsing de statements aninhados válidos."""
        # Testa detecção de statements aninhados
        self.assertTrue(is_nested_statement("when $.age gt 18 then #adult"))
        self.assertFalse(is_nested_statement("#simple"))

        # Testa extração de partes de statements aninhados
        statement = "when $.age gt 18 then when $.premium eq true then #premium else #basic else #minor"
        condition, then_part = extract_nested_statement_parts(statement)

        self.assertIn("$.age gt 18", condition)
        self.assertIn("when $.premium", then_part)


class TestValidRealWorldScenarios(unittest.TestCase):
    """Testa cenários do mundo real com expressões válidas complexas."""

    def setUp(self):
        self.choice_name = "real_world"
        self.states = {
            "premium-adult": {"name": "premium_adult"},
            "basic-adult": {"name": "basic_adult"},
            "premium-student": {"name": "premium_student"},
            "basic-student": {"name": "basic_student"},
            "blocked": {"name": "blocked_user"},
            "default": {"name": "default_state"}
        }

    def test_complex_user_classification(self):
        """Testa classificação complexa de usuário válida."""
        conditions = [
            "when $.age gte 18 and $.subscription eq 'premium' and $.active eq true then #premium-adult",
            "when $.age gte 18 and $.subscription eq 'basic' and $.active eq true then #basic-adult",
            "when $.age lt 18 and $.subscription eq 'premium' and $.active eq true then #premium-student",
            "when $.age lt 18 and $.subscription eq 'basic' and $.active eq true then #basic-student",
            "when $.active eq false or $.blocked eq true then #blocked",
            "#default"
        ]

        cache_path = parse_cond(self.choice_name, conditions, self.states)
        self.assertTrue(os.path.exists(cache_path))

        test_cases = [
            ({"age": 25, "subscription": "premium", "active": True}, "premium_adult"),
            ({"age": 25, "subscription": "basic", "active": True}, "basic_adult"),
            ({"age": 16, "subscription": "premium",
             "active": True}, "premium_student"),
            ({"age": 16, "subscription": "basic", "active": True}, "basic_student"),
            ({"age": 25, "subscription": "premium", "active": False}, "blocked_user"),
            ({"age": 25, "subscription": "premium",
             "active": True, "blocked": True}, "blocked_user")
        ]

        for test_data, expected in test_cases:
            result = load_and_test_cached_function(
                self.choice_name, test_data, expected)
            self.assertTrue(
                result, f"Failed for {test_data} expecting {expected}")

    def test_ecommerce_pricing_logic(self):
        """Testa lógica de preços de e-commerce válida."""
        conditions = [
            "when $.total gt 1000 and $.customer.tier eq 'gold' then #premium-adult",
            "when $.total gt 500 and $.customer.tier eq 'silver' then #basic-adult",
            "when $.items contains 'electronics' and $.customer.age gte 21 then #premium-student",
            "when $.total gt 100 then #basic-student",
            "#default"
        ]

        cache_path = parse_cond(self.choice_name, conditions, self.states)
        self.assertTrue(os.path.exists(cache_path))


if __name__ == "__main__":
    # Configuração para mostrar mais detalhes nos testes
    unittest.main(verbosity=2, buffer=True)
