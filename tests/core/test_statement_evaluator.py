import unittest

from core.statement_evaluator import StatementEvaluator
from core.statement_models import StatementBuilder, Operator
from tests.core.common_statements import CommonStatements


class TestStatementEvaluator(unittest.TestCase):
    """Test cases for the StatementEvaluator class."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Criando statements usando as classes
        self.model_statements = [
            # Adult verified user
            StatementBuilder()
            .when("$.user.age", Operator.GT, 18)
            .and_when("$.user.verified", Operator.EQ, True)
            .then("adult_verified_state")
            .build(),

            # Admin user
            CommonStatements.admin_user("admin_state"),

            # Premium user (encadeado com AND)
            StatementBuilder()
            .when("$.user.purchases", Operator.GT, 5)
            .and_next()
            .build(),

            # High value user (segunda parte do AND acima)
            CommonStatements.high_value_user("premium_state"),

            # Inactive user
            CommonStatements.inactive_user("inactive_state"),

            # Default case
            CommonStatements.default("default_state")
        ]

        # Criar o avaliador
        self.evaluator = StatementEvaluator(self.model_statements)

    def test_adult_verified_user(self):
        """Test that adult verified users go to the correct state."""
        data = {"user": {"age": 25, "verified": True, "role": "user",
                         "purchases": 3, "totalSpent": 50, "lastLogin": 10}}
        result = self.evaluator.evaluate(data)
        self.assertEqual(result, "adult_verified_state")

    def test_admin_user(self):
        """Test that admin users go to the correct state."""
        data = {"user": {"age": 30, "verified": False, "role": "admin",
                         "purchases": 2, "totalSpent": 40, "lastLogin": 5}}
        result = self.evaluator.evaluate(data)
        self.assertEqual(result, "admin_state")

    def test_premium_user(self):
        """Test that premium users go to the correct state."""
        data = {"user": {"age": 35, "verified": False, "role": "user",
                         "purchases": 10, "totalSpent": 200, "lastLogin": 15}}
        result = self.evaluator.evaluate(data)
        self.assertEqual(result, "premium_state")

    def test_inactive_user(self):
        """Test that inactive users go to the correct state."""
        data = {"user": {"age": 28, "verified": False, "role": "user",
                         "purchases": 1, "totalSpent": 20, "lastLogin": 45}}
        result = self.evaluator.evaluate(data)
        self.assertEqual(result, "inactive_state")

    def test_default_case(self):
        """Test that users not matching any condition go to the default state."""
        data = {"user": {"age": 15, "verified": False, "role": "user",
                         "purchases": 0, "totalSpent": 0, "lastLogin": 2}}
        result = self.evaluator.evaluate(data)
        self.assertEqual(result, "default_state")


if __name__ == "__main__":
    unittest.main()
