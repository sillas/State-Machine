import unittest
from unittest.mock import patch, MagicMock

from core.lambda_handler import Lambda, IF, LambdaTypes
from core.statement_models import StatementBuilder, Operator


class TestLambda(unittest.TestCase):
    """Test cases for the Lambda class."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Criar uma instância de Lambda para testes
        self.lambda_instance = Lambda(
            name="test_lambda",
            next_state="next_state",
            type=LambdaTypes.LAMBDA,
            timeout=10
        )

    def test_initialization(self):
        """Test Lambda initialization and parameter validation."""
        # Verificar atributos inicializados corretamente
        self.assertEqual(self.lambda_instance.name, "test_lambda")
        self.assertEqual(self.lambda_instance.type, "lambda")
        self.assertEqual(self.lambda_instance.next_state, "next_state")
        self.assertEqual(self.lambda_instance.timeout, 10)
        self.assertIsNone(self.lambda_instance.statements)
        self.assertIsNone(self.lambda_instance._handler)

        # Testar inicialização com tipo IF
        lambda_if = Lambda(
            name="if_lambda",
            next_state="next_state",
            type=LambdaTypes.IF,
            statements=[]
        )
        self.assertEqual(lambda_if.type, "if_statement")

        # Testar inicialização com timeout padrão
        lambda_default_timeout = Lambda(
            name="default_timeout",
            next_state="next_state"
        )
        self.assertEqual(lambda_default_timeout.timeout, 60)  # valor padrão

    @patch('importlib.util.spec_from_file_location')
    @patch('pathlib.Path.exists')
    def test_handler_module_not_found(self, mock_exists, mock_spec_from_file_location):
        """Test handler behavior when module is not found."""
        # Simular que o módulo não existe
        mock_exists.return_value = False

        with self.assertRaises(ModuleNotFoundError) as context:
            self.lambda_instance.handler({}, {})

        self.assertIn("não encontrado", str(context.exception))
        mock_exists.assert_called_once()
        mock_spec_from_file_location.assert_not_called()

    @patch('importlib.util.spec_from_file_location')
    @patch('pathlib.Path.exists')
    def test_handler_import_error(self, mock_exists, mock_spec_from_file_location):
        """Test handler behavior when module import fails."""
        # Simular que o módulo existe mas não pode ser carregado
        mock_exists.return_value = True
        mock_spec_from_file_location.return_value = None

        with self.assertRaises(ImportError) as context:
            self.lambda_instance.handler({}, {})

        self.assertIn("Não foi possível carregar o módulo",
                      str(context.exception))
        mock_exists.assert_called_once()
        mock_spec_from_file_location.assert_called_once()

    @patch('importlib.util.module_from_spec')
    @patch('importlib.util.spec_from_file_location')
    @patch('pathlib.Path.exists')
    def test_handler_execution(self, mock_exists, mock_spec_from_file_location, mock_module_from_spec):
        """Test successful handler execution."""
        # Preparar mocks para simular carregamento bem-sucedido do módulo
        mock_exists.return_value = True

        # Criar um mock para spec e loader
        mock_spec = MagicMock()
        mock_loader = MagicMock()
        mock_spec.loader = mock_loader
        mock_spec_from_file_location.return_value = mock_spec

        # Criar um mock para o módulo e a função lambda_handler
        mock_module = MagicMock()
        mock_lambda_handler = MagicMock(return_value={"result": "success"})
        mock_module.lambda_handler = mock_lambda_handler
        mock_module_from_spec.return_value = mock_module

        # Chamar o handler
        event_data = {"input": "test"}
        context_data = {"context": "test"}
        result = self.lambda_instance.handler(event_data, context_data)

        # Verificar que o mock lambda_handler foi chamado corretamente
        mock_lambda_handler.assert_called_once()
        # Verificar que o resultado é o esperado
        self.assertEqual(result, {"result": "success"})
        # Verificar que o contexto foi atualizado com timestamp
        self.assertIn("timestamp", context_data)

        # Verificar que o handler foi cacheado
        self.assertEqual(self.lambda_instance._handler, mock_lambda_handler)

        # Chamar novamente para verificar que usa o handler cacheado
        context_data = {"context": "test2"}
        self.lambda_instance.handler(event_data, context_data)
        # Verifica que o lambda_handler foi chamado duas vezes (com parâmetros diferentes)
        self.assertEqual(mock_lambda_handler.call_count, 2)
        # Verificar que o spec_from_file_location foi chamado apenas uma vez (não recarrega o módulo)
        mock_spec_from_file_location.assert_called_once()


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
        self.assertEqual(self.if_instance.type, "lambda")
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
