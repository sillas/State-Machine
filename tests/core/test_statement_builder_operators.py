import unittest
from core.statement_models import StatementBuilder, Operator, BooleanOperator


class TestStatementBuilderOperators(unittest.TestCase):
    """Testes específicos para os operadores and_when e or_when na classe StatementBuilder."""

    def test_and_when_functionality(self):
        """Testa se and_when adiciona uma condição corretamente."""
        # Cria um statement com and_when
        statement = (
            StatementBuilder()
            .when("$.user.age", Operator.GT, 18)
            .and_when("$.user.verified", Operator.EQ, True)
            .then("adult_verified_state")
            .build()
        )

        # Verifica se duas condições foram adicionadas
        self.assertIsNotNone(statement.conditions)
        if statement.conditions:
            self.assertEqual(len(statement.conditions), 2)

            # Verifica se as condições estão corretas
            self.assertEqual(statement.conditions[0].left, "$.user.age")
            self.assertEqual(
                statement.conditions[0].operator.value, Operator.GT.value)
            self.assertEqual(statement.conditions[0].right, 18)

            self.assertEqual(statement.conditions[1].left, "$.user.verified")
            self.assertEqual(
                statement.conditions[1].operator.value, Operator.EQ.value)
            self.assertEqual(statement.conditions[1].right, True)

        # Verifica o estado de destino
        self.assertEqual(statement.next_state, "adult_verified_state")

        # Verifica se não há operador booleano entre statements
        self.assertIsNone(statement.bool_op)

    def test_or_when_parameters(self):
        """Testa se or_when está utilizando os parâmetros corretamente."""
        # Cria um statement com or_when
        statement = (
            StatementBuilder()
            .when("$.user.age", Operator.GT, 18)
            .or_when("$.user.role", Operator.EQ, "admin")
            .then("special_access_state")
            .build()
        )

        # Verifica se or_when agora adiciona uma condição
        self.assertIsNotNone(statement.conditions)
        if statement.conditions:
            self.assertEqual(len(statement.conditions), 2)

            # Verifica se as condições estão corretas
            self.assertEqual(statement.conditions[0].left, "$.user.age")
            self.assertEqual(
                statement.conditions[0].operator.value, Operator.GT.value)
            self.assertEqual(statement.conditions[0].right, 18)

            self.assertEqual(statement.conditions[1].left, "$.user.role")
            self.assertEqual(
                statement.conditions[1].operator.value, Operator.EQ.value)
            self.assertEqual(statement.conditions[1].right, "admin")

        # Verifica se o bool_op foi definido como OR
        self.assertEqual(statement.bool_op, BooleanOperator.OR)

    def test_expected_or_when_behavior(self):
        """Testa o comportamento esperado de or_when agora que foi implementado corretamente."""
        statement = (
            StatementBuilder()
            .when("$.user.age", Operator.GT, 18)
            .or_when("$.user.role", Operator.EQ, "admin")
            .then("special_access_state")
            .build()
        )

        # Verifica se duas condições foram adicionadas
        self.assertIsNotNone(statement.conditions)
        if statement.conditions:
            self.assertEqual(len(statement.conditions), 2)

            # Verifica as condições
            self.assertEqual(statement.conditions[0].left, "$.user.age")
            self.assertEqual(
                statement.conditions[0].operator.value, Operator.GT.value)
            self.assertEqual(statement.conditions[0].right, 18)

            self.assertEqual(statement.conditions[1].left, "$.user.role")
            self.assertEqual(
                statement.conditions[1].operator.value, Operator.EQ.value)
            self.assertEqual(statement.conditions[1].right, "admin")

        # Verifica bool_op
        self.assertEqual(statement.bool_op, BooleanOperator.OR)

    def test_chaining_with_or_next(self):
        """Testa o encadeamento de statements com or_next"""
        # Verificamos apenas a definição do bool_op sem executar o avaliador
        statement = (
            StatementBuilder()
            .when("$.user.role", Operator.EQ, "admin")
            .or_next()
            .build()
        )

        # Verifica se o bool_op de statement é OR
        self.assertEqual(statement.bool_op, BooleanOperator.OR)

    def test_and_next_functionality(self):
        """Testa o encadeamento de statements com and_next"""
        # Verificamos apenas a definição do bool_op sem executar o avaliador
        statement = (
            StatementBuilder()
            .when("$.user.purchases", Operator.GT, 5)
            .and_next()
            .build()
        )

        # Verifica se o bool_op de statement é AND
        self.assertEqual(statement.bool_op, BooleanOperator.AND)


if __name__ == "__main__":
    unittest.main()
