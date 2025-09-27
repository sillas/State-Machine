"""
Testes focados na criação correta de funções para expressões válidas.
Este teste verifica se o parser gera código Python válido, sem executar as funções.
"""

from test_cache.parser import parse_cond, extract_constants, extract_jsonpath_variables, op_substitution  # type: ignore
import os
import sys
import unittest

# Adiciona o diretório test-cache ao path
cache_dir = os.path.join(os.path.dirname(
    os.path.dirname(os.path.dirname(__file__))), 'test-cache')
sys.path.append(cache_dir)


class TestParserValidExpressions(unittest.TestCase):
    """Testa se o parser cria funções válidas para expressões corretas."""

    def setUp(self):
        """Setup para cada teste."""
        self.states = {
            "result": {"name": "result_state"},
            "default": {"name": "default_state"},
            "adult": {"name": "adult"},
            "minor": {"name": "minor"},
            "premium": {"name": "premium"},
            "admin": {"name": "admin"},
            "moderator": {"name": "moderator"},
            "verified": {"name": "verified"},
        }

    def test_function_creation(self):
        """Testa se funções são criadas para várias expressões válidas."""
        test_cases = [
            # Literais básicos
            ("'hello' eq 'hello'", "String literal equality"),
            ("10 gt 5", "Number comparison"),
            ("true eq true", "Boolean equality"),

            # JSONPath simples
            ("$.name eq 'John'", "Simple JSONPath"),
            ("$.age gt 18", "JSONPath with number"),
            ("$.active eq true", "JSONPath with boolean"),

            # Operadores de string
            ("$.email contains '@'", "String contains"),
            ("$.name starts_with 'A'", "String starts with"),
            ("$.file ends_with '.pdf'", "String ends with"),

            # Operadores de comparação
            ("$.score gte 80", "Greater than or equal"),
            ("$.age lte 65", "Less than or equal"),
            ("$.status neq 'inactive'", "Not equal"),

            # Operadores booleanos simples
            ("$.premium eq true and $.active eq true", "AND operator"),
            ("$.role eq 'admin' or $.role eq 'moderator'", "OR operator"),
            ("not $.disabled eq true", "NOT operator"),

            # Listas e dicionários
            ("[] neq $.items", "Empty list comparison"),
            ("{} eq $.config", "Empty dict comparison"),

            # Statements when-then-else
            ("when $.age gte 18 then #adult else #minor", "Simple when-then-else"),
        ]

        for i, (condition, description) in enumerate(test_cases):
            with self.subTest(condition=condition, description=description):
                choice_name = f"test_condition_{i}"
                conditions = [f"when {condition} then #result", "#default"]
                cache_path = ''
                try:
                    # Tenta criar a função
                    cache_path = parse_cond(
                        choice_name, conditions, self.states)

                    # Verifica se o arquivo foi criado
                    self.assertTrue(os.path.exists(cache_path),
                                    f"Cache file not created for: {description}")

                    # Verifica se o arquivo contém código Python válido
                    with open(cache_path, 'r') as f:
                        content = f.read()
                        self.assertIn("def ", content,
                                      f"Function definition not found for: {description}")
                        self.assertIn("return ", content,
                                      f"Return statement not found for: {description}")

                    print(f"✅ {description}: Function created successfully")

                except Exception as e:
                    self.fail(
                        f"Failed to create function for {description}: {str(e)}")
                finally:
                    if cache_path:
                        json_file = cache_path.split(f'_{i}_')[0]
                        os.remove(cache_path)
                        os.remove(f"{json_file}_{i}_metadata.json")

    def test_parser_utility_functions(self):
        """Testa funções utilitárias do parser."""

        # Teste extract_constants
        constants = extract_constants(
            "when $.age gt 18 then #adult else #minor")
        self.assertIn("#adult", constants)
        self.assertIn("#minor", constants)

        # Teste extract_jsonpath_variables
        jsonpath_vars = extract_jsonpath_variables(
            "$.name eq 'John' and $.age gt 18")
        self.assertIn("$.name", jsonpath_vars)
        self.assertIn("$.age", jsonpath_vars)

        # Teste op_substitution para operadores básicos
        substituted = op_substitution("$.name eq 'John'")
        self.assertIn("==", substituted)  # eq deve ser substituído por ==

        substituted = op_substitution("$.age gt 18")
        self.assertIn(">", substituted)  # gt deve ser substituído por >

        substituted = op_substitution("$.text contains 'hello'")
        self.assertIn("in", substituted)  # contains deve usar 'in'

        print("✅ Parser utility functions work correctly")

    def test_complex_expressions_syntax(self):
        """Testa se expressões complexas geram sintaxe Python válida."""
        complex_cases = [
            "$.user.profile.name eq 'Admin'",
            "$.items[0].price gt 100",
            "$.config.enabled eq true and $.config.mode eq 'production'",
            "$.tags contains 'urgent' or $.priority eq 'high'",
            "not ($.disabled eq true or $.inactive eq true)",
        ]

        for i, condition in enumerate(complex_cases):
            with self.subTest(condition=condition):
                choice_name = f"complex_test_{i}"
                conditions = [f"when {condition} then #result", "#default"]

                cache_path = ''
                try:
                    cache_path = parse_cond(
                        choice_name, conditions, self.states)
                    self.assertTrue(os.path.exists(cache_path))

                    # Verifica se o código pode ser compilado (syntax check)
                    with open(cache_path, 'r') as f:
                        code = f.read()
                        # Irá levantar SyntaxError se inválido
                        compile(code, cache_path, 'exec')

                    print(f"✅ Complex expression syntax valid: {condition}")

                except SyntaxError as e:
                    self.fail(
                        f"Invalid Python syntax generated for '{condition}': {str(e)}")

                except Exception as e:
                    self.fail(
                        f"Failed to process complex condition '{condition}': {str(e)}")
                finally:
                    if cache_path:
                        json_file = cache_path.split(f'_{i}_')[0]
                        os.remove(cache_path)
                        os.remove(f"{json_file}_{i}_metadata.json")

    def test_when_then_else_statements(self):
        """Testa statements when-then-else válidos."""
        statement_cases = [
            # Statements simples
            ["when $.age gte 18 then #adult else #minor"],
            ["when $.premium eq true then #premium",
                "when $.age gte 18 then #adult", "#default"],

            # Múltiplas condições
            [
                "when $.role eq 'admin' then #admin",
                "when $.role eq 'moderator' then #moderator",
                "when $.verified eq true then #verified",
                "#default"
            ],
        ]

        for i, conditions in enumerate(statement_cases):
            with self.subTest(case=i):
                choice_name = f"statement_test_{i}"

                cache_path = ''
                try:
                    cache_path = parse_cond(
                        choice_name, conditions, self.states)

                    self.assertTrue(os.path.exists(cache_path))

                    with open(cache_path, 'r') as f:
                        code = f.read()
                        # Verifica sintaxe básica
                        self.assertIn("def ", code)
                        self.assertIn("if ", code)

                        compile(code, cache_path, 'exec')  # Syntax check

                    print(f"✅ Statement {i+1}: Valid syntax generated")

                except Exception as e:
                    self.fail(
                        f"Failed to process statement case {i+1}: {str(e)}")

                finally:
                    if cache_path:
                        json_file = cache_path.split(f'_{i}_')[0]
                        os.remove(cache_path)
                        os.remove(f"{json_file}_{i}_metadata.json")


if __name__ == '__main__':
    print("🧪 Testando criação de funções para expressões válidas...\n")

    unittest.main(verbosity=2)
