import unittest
from core.blocks.if_handler import IF
from core.statement_models import Operator, StatementBuilder


class TestIF(unittest.TestCase):
    """Test cases for the IF class."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Criar statements para o teste
        self.statements = [
            StatementBuilder()
            .when("$.user.age", Operator.GT, 18)
            .then("adult_state")
            .build(),

            StatementBuilder()
            .default("default_state")
            .build()
        ]

        # Criar uma instância de IF para testes
        self.if_instance = IF(name="test_if", statements=self.statements)

    def test_initialization(self):
        """Test IF initialization and parameter validation."""
        # Verificar atributos inicializados corretamente
        self.assertEqual(self.if_instance.name, "test_if")
        self.assertEqual(self.if_instance.type, "if_statement")
        self.assertIsNone(self.if_instance.next_state)
        self.assertEqual(self.if_instance.timeout, 1)
        self.assertIsNotNone(self.if_instance.evaluator)

    def test_handler_adult_user(self):
        """Test IF handler with adult user data."""
        # Dados de teste que devem direcionar para "adult_state"
        event_data = {"user": {"age": 25}}
        context_data = {}

        # Chamar o handler
        result = self.if_instance.handler(event_data, context_data)

        # Verificar que o evento é passado sem alterações
        self.assertEqual(result, event_data)
        # Verificar que o next_state foi atualizado corretamente
        self.assertEqual(self.if_instance.next_state, "adult_state")
        # Verificar que o contexto foi atualizado com timestamp
        self.assertIn("timestamp", context_data)

    def test_handler_default_case(self):
        """Test IF handler with default case."""
        # Dados de teste que devem direcionar para o caso padrão
        event_data = {"user": {"age": 15}}
        context_data = {}

        # Chamar o handler
        result = self.if_instance.handler(event_data, context_data)

        # Verificar que o evento é passado sem alterações
        self.assertEqual(result, event_data)
        # Verificar que o next_state foi atualizado corretamente
        self.assertEqual(self.if_instance.next_state, "default_state")
        # Verificar que o contexto foi atualizado com timestamp
        self.assertIn("timestamp", context_data)


if __name__ == '__main__':
    unittest.main()
