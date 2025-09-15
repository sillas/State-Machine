# Classes predefinidas para condições comuns
from utils.statement_models import Operator, Statement, StatementBuilder


class CommonStatements:
    """Classe com statements comuns predefinidos."""
    
    @staticmethod
    def adult_user(next_state: str) -> Statement:
        """Statement para usuário adulto (idade > 18)."""
        return (
            StatementBuilder()
            .when("$.user.age", Operator.GT, 18)
            .then(next_state)
            .build()
        )
    
    @staticmethod
    def admin_user(next_state: str) -> Statement:
        """Statement para usuário admin."""
        return (
            StatementBuilder()
            .when("$.user.role", Operator.EQ, "admin")
            .then(next_state)
            .build()
        )
    
    @staticmethod
    def premium_user(next_state: str) -> Statement:
        """Statement para usuário premium (mais de 5 compras e valor total > 100)."""
        return (
            StatementBuilder()
            .when("$.user.purchases", Operator.GT, 5)
            .and_when("$.user.totalSpent", Operator.GT, 100)
            .then(next_state)
            .build()
        )
    
    @staticmethod
    def high_value_user(next_state: str) -> Statement:
        """Statement para usuário de alto valor (gasto total > 100)."""
        return (
            StatementBuilder()
            .when("$.user.totalSpent", Operator.GT, 100)
            .then(next_state)
            .build()
        )
    
    @staticmethod
    def inactive_user(next_state: str) -> Statement:
        """Statement para usuário inativo (último login > 30 dias)."""
        return (
            StatementBuilder()
            .when("$.user.lastLogin", Operator.GT, 30)
            .then(next_state)
            .build()
        )
    
    @staticmethod
    def default(next_state: str) -> Statement:
        """Statement default."""
        return (
            StatementBuilder()
            .default(next_state)
            .build()
        )