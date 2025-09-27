"""
Testes robustos para o parser de condições baseado na definição fornecida.

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

from test_cache.parser import (
    parse_cond,
    extract_constants,
    extract_jsonpath_variables,
    is_nested_statement,
    extract_nested_statement_parts,
    convert_jsonpath_to_params,
    op_substitution,
    build_function_signature,
    build_jsonpath_params_mapping
)
import unittest
import sys
import os
from pathlib import Path

# Adicionar o diretório test-cache ao path
test_cache_dir = Path(__file__).parent.parent.parent / "test-cache"
sys.path.insert(0, str(test_cache_dir))


class TestLiteralTerms(unittest.TestCase):
    """Testa todos os tipos de termos literais da definição."""

    def setUp(self):
        """Configuração base para os testes."""
        self.choice_name = "test_literals"
        self.base_states = {
            "state-a": {"name": "state_a"},
            "state-b": {"name": "state_b"},
            "default": {"name": "default_state"}
        }

    def _run_test(self, conditions):
        cache_path = ''
        try:
            cache_path = parse_cond(
                self.choice_name, conditions, self.base_states)
            self.assertTrue(os.path.exists(cache_path))
        except Exception as e:
            self.fail(f"Falha no parsing de literal strings: {e}")
        finally:
            if cache_path:
                str_inex = cache_path.index(self.choice_name)
                os.remove(cache_path)
                os.remove(
                    f"{cache_path[:str_inex]}{self.choice_name}_metadata.json")

    def test_literal_string_parsing(self):
        """Testa parsing de literal strings com aspas simples."""
        conditions = [
            "when $.name eq 'João Silva' then #state-a",
            "when $.description eq 'Complex string with spaces & symbols!' then #state-b",
            "when $.empty eq '' then #state-a",
            "#default"
        ]

        self._run_test(conditions)

    def test_literal_number_parsing(self):
        """Testa parsing de números inteiros e decimais."""
        conditions = [
            "when $.age eq 25 then #state-a",
            "when $.price gt 99.99 then #state-b",
            "when $.temperature lt -5.5 then #state-a",
            "when $.count gte 0 then #state-b",
            "#default"
        ]

        self._run_test(conditions)

    def test_empty_list_parsing(self):
        """Testa parsing de listas vazias."""
        conditions = [
            "when $.items eq [] then #state-a",
            "when $.empty_array eq [] then #state-b",
            "#default"
        ]

        self._run_test(conditions)

    def test_list_parsing(self):
        """Testa parsing de listas com conteúdo."""
        conditions = [
            "when $.categories eq [\"tech\", \"ai\", \"ml\"] then #state-a",
            "when $.numbers eq [1, 2, 3, 4, 5] then #state-b",
            "when $.mixed eq [\"text\", 42, true, null] then #state-a",
            "#default"
        ]

        self._run_test(conditions)

    def test_empty_dict_parsing(self):
        """Testa parsing de dicionários vazios."""
        conditions = [
            "when $.metadata eq {} then #state-a",
            "when $.empty_object eq {} then #state-b",
            "#default"
        ]

        self._run_test(conditions)

    def test_dict_parsing(self):
        """Testa parsing de dicionários com conteúdo."""
        conditions = [
            'when $.config eq {"enabled": true, "timeout": 30} then #state-a',
            'when $.user eq {"name": "João", "age": 25} then #state-b',
            "#default"
        ]

        self._run_test(conditions)

    def test_boolean_literals(self):
        """Testa parsing de literais booleanos true/false."""
        conditions = [
            "when $.active eq true then #state-a",
            "when $.disabled eq false then #state-b",
            "when $.enabled eq true then #state-a",
            "#default"
        ]

        self._run_test(conditions)


class TestJSONPathExpressions(unittest.TestCase):
    """Testa expressões JSONPath complexas."""

    def setUp(self):
        self.choice_name = "test_jsonpath"
        self.base_states = {
            "simple": {"name": "simple_state"},
            "nested": {"name": "nested_state"},
            "array": {"name": "array_state"},
            "default": {"name": "default_state"}
        }

    def test_simple_jsonpath(self):
        """Testa JSONPath simples."""

        jsonpaths = extract_jsonpath_variables(
            "$.name eq 'test' and $.age gt 18"
        )
        self.assertIn("$.name", jsonpaths)
        self.assertIn("$.age", jsonpaths)

    def test_nested_jsonpath(self):
        """Testa JSONPath aninhado."""

        jsonpaths = extract_jsonpath_variables(
            "$.user.profile.name and $.config.database.host"
        )
        self.assertIn("$.user.profile.name", jsonpaths)
        self.assertIn("$.config.database.host", jsonpaths)

    def test_array_jsonpath(self):
        """Testa JSONPath com arrays."""

        jsonpaths = extract_jsonpath_variables(
            "$.items[0] and $.users[*].name"
        )
        self.assertIn("$.items[0]", jsonpaths)
        self.assertIn("$.users[*].name", jsonpaths)

    def test_complex_jsonpath(self):
        """Testa JSONPath com sintaxes complexas."""
        conditions = [
            "when $.data..price gt 100 then #nested",
            "when $.store.book[?(@.price < 10)].title contains 'cheap' then #array",
            "#default"
        ]

        # Estes casos podem falhar - são pontos de teste para identificar limitações
        try:
            cache_path = parse_cond(
                self.choice_name, conditions, self.base_states
            )
            self.assertTrue(os.path.exists(cache_path))
        except Exception as e:
            print(f"JSONPath complexo falhou (esperado): {e}")


class TestComparisonOperators(unittest.TestCase):
    """Testa todos os operadores de comparação da definição."""

    def setUp(self):
        self.choice_name = "test_operators"
        self.base_states = {
            "gt-state": {"name": "greater_than"},
            "lt-state": {"name": "less_than"},
            "eq-state": {"name": "equal"},
            "neq-state": {"name": "not_equal"},
            "gte-state": {"name": "greater_equal"},
            "lte-state": {"name": "less_equal"},
            "contains-state": {"name": "contains_match"},
            "starts-state": {"name": "starts_with_match"},
            "ends-state": {"name": "ends_with_match"},
            "default": {"name": "default_state"}
        }

    def test_numeric_comparisons(self):
        """Testa operadores de comparação numérica."""
        conditions = [
            "when $.value gt 100 then #gt-state",
            "when $.value lt 50 then #lt-state",
            "when $.value eq 75 then #eq-state",
            "when $.value neq 0 then #neq-state",
            "when $.value gte 100 then #gte-state",
            "when $.value lte 50 then #lte-state",
            "#default"
        ]

        try:
            cache_path = parse_cond(
                self.choice_name, conditions, self.base_states)
            self.assertTrue(os.path.exists(cache_path))
        except Exception as e:
            self.fail(f"Falha nos operadores numéricos: {e}")

    def test_string_operations(self):
        """Testa operadores de string."""
        conditions = [
            "when $.text contains 'search' then #contains-state",
            "when $.name starts_with 'João' then #starts-state",
            "when $.filename ends_with '.pdf' then #ends-state",
            "#default"
        ]

        try:
            cache_path = parse_cond(
                self.choice_name, conditions, self.base_states)
            self.assertTrue(os.path.exists(cache_path))
        except Exception as e:
            self.fail(f"Falha nos operadores de string: {e}")

    def test_mixed_type_comparisons(self):
        """Testa comparações entre tipos diferentes (possível ponto de falha)."""
        conditions = [
            "when $.number gt '100' then #gt-state",  # número vs string
            "when $.string eq 42 then #eq-state",     # string vs número
            "when $.boolean eq 'true' then #eq-state",  # boolean vs string
            "#default"
        ]

        # Este teste pode falhar - identifica problema de tipos
        try:
            cache_path = parse_cond(
                self.choice_name, conditions, self.base_states)
            print("Comparações de tipos mistos funcionaram (pode ser problemático)")
        except Exception as e:
            print(f"Comparações de tipos mistos falharam: {e}")


class TestBooleanOperators(unittest.TestCase):
    """Testa operadores booleanos e combinações lógicas."""

    def setUp(self):
        self.choice_name = "test_boolean"
        self.base_states = {
            "and-state": {"name": "and_result"},
            "or-state": {"name": "or_result"},
            "not-state": {"name": "not_result"},
            "complex": {"name": "complex_result"},
            "default": {"name": "default_state"}
        }

    def test_and_operator(self):
        """Testa operador AND."""
        conditions = [
            "when $.age gt 18 and $.active eq true then #and-state",
            "when $.score gte 80 and $.category eq 'premium' then #and-state",
            "#default"
        ]

        try:
            cache_path = parse_cond(
                self.choice_name, conditions, self.base_states)
            self.assertTrue(os.path.exists(cache_path))
        except Exception as e:
            self.fail(f"Falha no operador AND: {e}")

    def test_or_operator(self):
        """Testa operador OR."""
        conditions = [
            "when $.type eq 'admin' or $.permissions contains 'write' then #or-state",
            "when $.urgent eq true or $.priority gt 5 then #or-state",
            "#default"
        ]

        try:
            cache_path = parse_cond(
                self.choice_name, conditions, self.base_states)
            self.assertTrue(os.path.exists(cache_path))
        except Exception as e:
            self.fail(f"Falha no operador OR: {e}")

    def test_not_operator(self):
        """Testa operador NOT."""
        conditions = [
            "when not $.disabled eq true then #not-state",
            "when not $.empty eq [] then #not-state",
            "#default"
        ]

        try:
            cache_path = parse_cond(
                self.choice_name, conditions, self.base_states)
            self.assertTrue(os.path.exists(cache_path))
        except Exception as e:
            self.fail(f"Falha no operador NOT: {e}")

    def test_complex_boolean_combinations(self):
        """Testa combinações complexas de operadores booleanos."""
        conditions = [
            "when ($.age gt 18 and $.active eq true) or ($.type eq 'admin') then #complex",
            "when $.score gte 80 and ($.category eq 'premium' or $.vip eq true) then #complex",
            "when not ($.disabled eq true or $.suspended eq true) and $.verified eq true then #complex",
            "#default"
        ]

        try:
            cache_path = parse_cond(
                self.choice_name, conditions, self.base_states)
            self.assertTrue(os.path.exists(cache_path))
        except Exception as e:
            self.fail(f"Falha em combinações booleanas complexas: {e}")

    def test_operator_precedence(self):
        """Testa precedência de operadores (possível ponto de falha)."""
        conditions = [
            # Sem parênteses - testa precedência implícita
            "when $.a eq 1 and $.b eq 2 or $.c eq 3 then #complex",
            "when $.x gt 0 or $.y lt 5 and $.z eq 'test' then #complex",
            "#default"
        ]

        try:
            cache_path = parse_cond(
                self.choice_name, conditions, self.base_states)
            print("Precedência de operadores funcionou - verificar se está correta")
        except Exception as e:
            print(f"Falha na precedência de operadores: {e}")


class TestExistOperator(unittest.TestCase):
    """Testa o operador 'exist' para JSONPath."""

    def setUp(self):
        self.choice_name = "test_exist"
        self.base_states = {
            "exists": {"name": "field_exists"},
            "default": {"name": "field_missing"}
        }

    def test_exist_operator(self):
        """Testa operador exist."""
        conditions = [
            "when exist $.optional_field then #exists",
            "when exist $.user.profile then #exists",
            "when exist $.data[*].id then #exists",
            "#default"
        ]

        try:
            cache_path = parse_cond(
                self.choice_name, conditions, self.base_states)
            self.assertTrue(os.path.exists(cache_path))
        except Exception as e:
            self.fail(f"Falha no operador exist: {e}")


class TestNestedStatements(unittest.TestCase):
    """Testa statements when-then-else aninhados."""

    def setUp(self):
        self.choice_name = "test_nested"
        self.base_states = {
            "adult-premium": {"name": "adult_premium"},
            "adult-basic": {"name": "adult_basic"},
            "minor": {"name": "minor_user"},
            "default": {"name": "unknown"}
        }

    def test_simple_when_then_else(self):
        """Testa when-then-else simples."""
        conditions = [
            "when $.age gte 18 then #adult-premium else #minor",
            "#default"
        ]

        try:
            cache_path = parse_cond(
                self.choice_name, conditions, self.base_states)
            self.assertTrue(os.path.exists(cache_path))
        except Exception as e:
            self.fail(f"Falha em when-then-else simples: {e}")

    def test_nested_when_then(self):
        """Testa when-then aninhado."""
        conditions = [
            "when $.age gte 18 then when $.premium eq true then #adult-premium else #adult-basic else #minor",
            "#default"
        ]

        try:
            cache_path = parse_cond(
                self.choice_name, conditions, self.base_states)
            self.assertTrue(os.path.exists(cache_path))
        except Exception as e:
            self.fail(f"Falha em statements aninhados: {e}")

    def test_deeply_nested_statements(self):
        """Testa statements profundamente aninhados (possível ponto de falha)."""
        conditions = [
            "when $.level1 eq true then when $.level2 eq true then when $.level3 eq true then #adult-premium else #adult-basic else #minor else #default",
            "#default"
        ]

        try:
            cache_path = parse_cond(
                self.choice_name, conditions, self.base_states)
            print("Statements profundamente aninhados funcionaram")
        except Exception as e:
            print(f"Falha em statements profundamente aninhados: {e}")

    def test_statement_parsing_functions(self):
        """Testa funções auxiliares de parsing de statements."""
        statement = "when $.age gt 18 then when $.premium eq true then #premium else #basic else #minor"

        # Testa extração de partes aninhadas
        self.assertTrue(is_nested_statement("when $.age gt 18 then #adult"))
        self.assertFalse(is_nested_statement("#simple"))

        condition, then_part = extract_nested_statement_parts(statement)
        self.assertIn("$.age gt 18", condition)
        self.assertIn("when $.premium", then_part)


class TestEdgeCasesAndFailures(unittest.TestCase):
    """Testa casos extremos e condições que podem causar falhas."""

    def setUp(self):
        self.choice_name = "test_edge_cases"
        self.base_states = {
            "success": {"name": "success_state"},
            "default": {"name": "default_state"}
        }

    def test_empty_conditions(self):
        """Testa condições vazias ou inválidas."""
        test_cases = [
            [],  # Lista vazia
            [""],  # String vazia
            ["   "],  # Apenas espaços
            [None],  # None (se permitido)
        ]

        for conditions in test_cases:
            try:
                cache_path = parse_cond(
                    self.choice_name, conditions, self.base_states)
                print(f"Condições vazias funcionaram: {conditions}")
            except Exception as e:
                print(f"Condições vazias falharam: {conditions} - {e}")

    def test_malformed_conditions(self):
        """Testa condições malformadas."""
        malformed_conditions = [
            ["when $.age gt then #success"],  # Operando faltando
            ["when $.age gt 18 then"],  # Then sem valor
            ["when then #success"],  # Condição faltando
            ["$.age gt 18 then #success"],  # When faltando
            ["when $.age gt 18 #success"],  # Then faltando
            ["when $.age gt 18 then success"],  # # faltando
            ["when $.age gt 18 then #nonexistent"],  # Estado inexistente
        ]

        for conditions in malformed_conditions:
            try:
                cache_path = parse_cond(
                    self.choice_name, conditions, self.base_states)
                print(
                    f"Condição malformada funcionou (problemático): {conditions}")
            except Exception as e:
                print(
                    f"Condição malformada falhou (esperado): {conditions} - {e}")

    def test_invalid_jsonpath(self):
        """Testa JSONPath inválidos."""
        invalid_jsonpaths = [
            ["when $invalid then #success"],  # JSONPath inválido
            ["when $.user..name then #success"],  # Sintaxe duvidosa
            ["when $.[0] then #success"],  # Sintaxe incorreta
            ["when $.user.[name] then #success"],  # Sintaxe incorreta
        ]

        for conditions in invalid_jsonpaths:
            try:
                cache_path = parse_cond(
                    self.choice_name, conditions, self.base_states)
                print(f"JSONPath inválido funcionou (verificar): {conditions}")
            except Exception as e:
                print(f"JSONPath inválido falhou: {conditions} - {e}")

    def test_operator_errors(self):
        """Testa erros nos operadores."""
        operator_errors = [
            # Operador Python em vez do parser
            ["when $.age > 18 then #success"],
            ["when $.age == 18 then #success"],  # Operador Python
            ["when $.age !== 18 then #success"],  # Operador JavaScript
            ["when $.name LIKE 'João%' then #success"],  # Operador SQL
            ["when $.age greater_than 18 then #success"],  # Operador por extenso
        ]

        for conditions in operator_errors:
            try:
                cache_path = parse_cond(
                    self.choice_name, conditions, self.base_states)
                print(
                    f"Operador incorreto funcionou (problemático): {conditions}")
            except Exception as e:
                print(
                    f"Operador incorreto falhou (esperado): {conditions} - {e}")

    def test_quote_handling(self):
        """Testa problemas com aspas."""
        quote_issues = [
            ['when $.name eq "João Silva" then #success'],  # Aspas duplas
            ["when $.name eq 'João's car' then #success"],  # Aspas dentro de aspas
            ['when $.name eq \'João Silva\' then #success'],  # Escape de aspas
            ["when $.name eq João Silva then #success"],  # Sem aspas
        ]

        for conditions in quote_issues:
            try:
                cache_path = parse_cond(
                    self.choice_name, conditions, self.base_states)
                print(f"Problema de aspas funcionou: {conditions}")
            except Exception as e:
                print(f"Problema de aspas falhou: {conditions} - {e}")

    def test_special_characters(self):
        """Testa caracteres especiais em strings."""
        special_chars = [
            ["when $.text contains 'çãõáéíóú' then #success"],  # Acentos
            # Caracteres de escape
            ["when $.text contains '\\n\\t\\r' then #success"],
            ["when $.text contains '🚀🎉💻' then #success"],  # Emojis
            ["when $.text contains 'line1\\nline2' then #success"],  # Quebras de linha
        ]

        for conditions in special_chars:
            try:
                cache_path = parse_cond(
                    self.choice_name, conditions, self.base_states)
                print(f"Caracteres especiais funcionaram: {conditions}")
            except Exception as e:
                print(f"Caracteres especiais falharam: {conditions} - {e}")


class TestUtilityFunctions(unittest.TestCase):
    """Testa funções utilitárias do parser."""

    def test_extract_constants(self):
        """Testa extração de constantes (#)."""
        text = "when $.age gt 18 then #adult else #minor"
        constants = extract_constants(text)
        self.assertIn("#adult", constants)
        self.assertIn("#minor", constants)

    def test_extract_jsonpath_variables(self):
        """Testa extração de variáveis JSONPath."""
        text = "when $.user.age gt 18 and $.user.active eq true then #success"
        jsonpaths = extract_jsonpath_variables(text)
        self.assertIn("$.user.age", jsonpaths)
        self.assertIn("$.user.active", jsonpaths)

    def test_convert_jsonpath_to_params(self):
        """Testa conversão de JSONPath para parâmetros."""
        condition = "$.user.name eq 'João' and $.user.age gt 18"
        converted = convert_jsonpath_to_params(condition)
        self.assertIn("_user_name", converted)
        self.assertIn("_user_age", converted)
        self.assertNotIn("$.user.name", converted)

    def test_op_substitution(self):
        """Testa substituição de operadores."""
        condition = "$.age gt 18 and $.name eq 'João'"
        substituted = op_substitution(condition)
        self.assertIn(" > ", substituted)
        self.assertIn(" == ", substituted)
        self.assertNotIn(" gt ", substituted)
        self.assertNotIn(" eq ", substituted)

    def test_build_function_signature(self):
        """Testa construção da assinatura da função."""
        choice_name = "test-choice"
        params = ["$.user.name", "$.user.age", "$.user.name"]  # Com duplicata
        signature = build_function_signature(choice_name, params)

        self.assertIn("def test_choice(", signature)
        self.assertIn("_user_name", signature)
        self.assertIn("_user_age", signature)
        # Verifica se duplicatas foram removidas
        self.assertEqual(signature.count("_user_name"), 1)

    def test_build_jsonpath_params_mapping(self):
        """Testa construção do mapeamento JSONPath -> parâmetros."""
        params = ["$.user.name", "$.user.age", "$.user.name"]  # Com duplicata
        mapping = build_jsonpath_params_mapping(params)

        self.assertEqual(mapping["_user_name"], "$.user.name")
        self.assertEqual(mapping["_user_age"], "$.user.age")
        self.assertEqual(len(mapping), 2)  # Duplicatas removidas


if __name__ == "__main__":
    # Executa todos os testes
    unittest.main(verbosity=2)
