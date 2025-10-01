"""
Testes para o parser de condições focados em expressões VÁLIDAS.
Baseado na definição fornecida, testa se todas as expressões válidas são interpretadas corretamente.

Definição testada:
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

import unittest
import sys
from pathlib import Path

from core.handlers.choice_handler import Choice

# Adicionar o diretório test-cache ao path
test_cache_dir = Path(__file__).parent.parent.parent / "test-cache"
sys.path.insert(0, str(test_cache_dir))


class TestValidConditions(unittest.TestCase):
    """Testa parsing correto das condições."""

    def setUp(self):
        self.states = {
            "match": {"name": "string_match"},
            "no-match": {"name": "no_match"},
            "default": {"name": "default_state"}
        }

    def act_and_assert(self, choice_name, conditions, test_list):

        choice = Choice(choice_name, conditions, self.states)

        for test in test_list:
            input_data = test['input']
            output_data = choice.handler(input_data, {})

            self.assertTrue(choice.next_state == self.states[test['state']]['name'])  # nopep8
            self.assertDictEqual(input_data, output_data)

            choice.cache_handler.clear_all_cache()

    def test_cache_substitution(self):
        """Testa se ao mudar as condições, o cache é atualizado"""

        conditions_1 = [
            "when $.name eq 'João Silva' then #match else #no-match"
        ]

        choice_name = "test_cache_substitution"

        choice_1 = Choice(choice_name, conditions_1, self.states)
        file_path_1 = choice_1.cache_handler.get_path_from_cache()

        conditions_2 = [
            "when $.name neq 'João Silva' then #no-match else #match"
        ]

        choice_2 = Choice(choice_name, conditions_2, self.states)
        file_path_2 = choice_2.cache_handler.get_path_from_cache()

        self.assertNotEqual(file_path_1, file_path_2)
        choice_2.cache_handler.clear_all_cache()

    def test_simple_string_literals(self):
        """Testa strings literais simples com aspas simples."""

        conditions = [
            "when $.name eq 'João Silva' then #match",
            "when 'João Silva Machado' contains $.name then #match",
            "when $.title eq 'Machine Learning Engineer' then #match",
            "#default"
        ]

        test_list = [
            {'input': {'name': 'João Silva'}, 'state': 'match'},
            {'input': {'name': 'Silva'}, 'state': 'match'},
            {'input': {'title': 'Machine Learning Engineer'}, 'state': 'match'},
            {'input': {'other': 'no match'}, 'state': 'default'}
        ]

        self.act_and_assert("test_simple_string", conditions, test_list)

    def test_simple_number_literals(self):
        """Testa números literais simples com aspas simples."""

        conditions = [
            "when $.age eq 10 then #match",
            "when $.age eq 100 then #no-match",
            "#default"
        ]

        test_list = [
            {'input': {'age': 10}, 'state': 'match'},
            {'input': {'age': 100}, 'state': 'no-match'},
            {'input': {'age': 1000.0}, 'state': 'default'}
        ]

        self.act_and_assert("test_simple_number", conditions, test_list)

    def test_simple_list_literals(self):
        """Testa listas literais simples com aspas simples."""

        conditions = [
            "when [5, 10, 20] contains $.age then #match",
            "when $.toos eq [] then #no-match",
            "#default"
        ]

        test_list = [
            {'input': {'age': 10}, 'state': 'match'},
            {'input': {'toos': []}, 'state': 'no-match'},
            {'input': {'age': 1000.0}, 'state': 'default'}
        ]

        self.act_and_assert(
            "test_simple_list",
            conditions,
            test_list
        )

    def test_simple_dict_literals(self):
        """Testa listas literais simples com aspas simples."""

        conditions = [
            "when {\"name\": \"pedro\"} contains $.name then #match",
            "when $.full_name contains 'Machado' then #match",
            "when $.toos eq {} then #no-match",
            "#default"
        ]

        test_list = [
            {'input': {'name': "name"}, 'state': 'match'},
            {'input': {'full_name': "Pedro Silva Machado"}, 'state': 'match'},
            {'input': {'toos': {}}, 'state': 'no-match'},
            {'input': {'age': 1000.0}, 'state': 'default'}
        ]

        self.act_and_assert(
            "test_simple_dict",
            conditions,
            test_list
        )


if __name__ == "__main__":
    # Configuração para mostrar mais detalhes nos testes
    unittest.main(verbosity=2, buffer=True)
