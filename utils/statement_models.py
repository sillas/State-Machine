from enum import Enum
from typing import Any, Dict, List, Optional, Union, Callable


class Operator(Enum):
    """Operadores de comparação suportados."""
    GT = "gt"   # greater than
    LT = "lt"   # less than
    EQ = "eq"   # equal
    NEQ = "neq" # not equal
    GTE = "gte" # greater than or equal
    LTE = "lte" # less than or equal
    CONTAINS = "contains" # for strings/lists
    STARTS_WITH = "starts_with" # for strings
    ENDS_WITH = "ends_with" # for strings


class BooleanOperator(Enum):
    """Operadores booleanos suportados."""
    AND = "AND"
    OR = "OR"


class Condition:
    """
    Representa uma condição individual no formato "left op right".
    
    Exemplo:
        condition = Condition("$.user.age", Operator.GT, 18)
    """
    
    def __init__(self, left: str, operator: Union[Operator, str], right: Any):
        """
        Inicializa uma condição.
        
        Args:
            left: Lado esquerdo da condição, geralmente um JSONPath
            operator: Operador de comparação
            right: Lado direito da condição, pode ser um valor literal ou JSONPath
        """
        self.left = left
        
        # Converter string para Operator se necessário
        if isinstance(operator, str):
            try:
                self.operator = Operator(operator)
            except ValueError:
                raise ValueError(f"Operador inválido: {operator}")
        else:
            self.operator = operator
            
        self.right = right
    
    def to_string(self) -> str:
        """Converte a condição para formato string."""
        return f"{self.left} {self.operator.value} {self.right}"
    
    @classmethod
    def from_string(cls, condition_str: str) -> 'Condition':
        """
        Cria uma condição a partir de uma string.
        
        Args:
            condition_str: String no formato "left op right"
            
        Returns:
            Objeto Condition
        """
        parts = condition_str.split()
        if len(parts) != 3:
            raise ValueError(f"Formato de condição inválido: {condition_str}. Esperado 'left op right'")
        
        left, op, right = parts
        
        # Tenta converter o right para número ou booleano se não for um path
        if not right.startswith("$."):
            try:
                # Tenta converter para int
                if right.isdigit() or (right[0] == '-' and right[1:].isdigit()):
                    right = int(right)
                # Tenta converter para float
                elif '.' in right and right.replace('.', '', 1).replace('-', '', 1).isdigit():
                    right = float(right)
                # Trata valores booleanos
                elif right.lower() == 'true':
                    right = True
                elif right.lower() == 'false':
                    right = False
            except ValueError:
                # Mantém como string se a conversão falhar
                pass
        
        return cls(left, op, right)


class Statement:
    """
    Representa um statement completo com condições e próximo estado.
    
    Exemplo:
        statement = Statement(
            conditions=[Condition("$.user.age", Operator.GT, 18)],
            next_state="adult_state",
            bool_op=None
        )
    """
    
    def __init__(
        self, 
        conditions: Optional[List[Union[Condition, str]]] = None, 
        next_state: Optional[str] = None,
        bool_op: Optional[Union[BooleanOperator, str]] = None
    ):
        """
        Inicializa um statement.
        
        Args:
            conditions: Lista de condições ou None para caso default
            next_state: Próximo estado se as condições forem verdadeiras
            bool_op: Operador booleano para encadear com o próximo statement
        """
        # Processa as condições
        self.conditions = None
        if conditions:
            self.conditions = []
            for cond in conditions:
                if isinstance(cond, str):
                    self.conditions.append(Condition.from_string(cond))
                else:
                    self.conditions.append(cond)
        
        self.next_state = next_state
        
        # Processa o operador booleano
        if bool_op is None:
            self.bool_op = None
        elif isinstance(bool_op, str):
            try:
                self.bool_op = BooleanOperator(bool_op)
            except ValueError:
                raise ValueError(f"Operador booleano inválido: {bool_op}")
        else:
            self.bool_op = bool_op
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte o statement para formato dicionário."""
        result = {
            "sttm": None if self.conditions is None else [c.to_string() for c in self.conditions],
            "then": self.next_state,
            "bool_ops": None if self.bool_op is None else self.bool_op.value
        }
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Statement':
        """
        Cria um statement a partir de um dicionário.
        
        Args:
            data: Dicionário com as chaves 'sttm', 'then' e 'bool_ops'
            
        Returns:
            Objeto Statement
        """
        conditions = data.get("sttm")
        next_state = data.get("then")
        bool_op = data.get("bool_ops")
        
        return cls(conditions, next_state, bool_op)


class StatementBuilder:
    """
    Construtor fluente para criar statements de forma mais legível.
    
    Exemplo:
        statement = (
            StatementBuilder()
            .when("$.user.age", Operator.GT, 18)
            .and_when("$.user.verified", Operator.EQ, True)
            .then("adult_verified_state")
            .build()
        )
    """
    
    def __init__(self):
        """Inicializa o construtor."""
        self.conditions = []
        self.next_state = None
        self.bool_op = None
    
    def when(self, left: str, operator: Union[Operator, str], right: Any) -> 'StatementBuilder':
        """Adiciona uma condição ao statement."""
        if self.conditions is None:
            self.conditions = []
        self.conditions.append(Condition(left, operator, right))
        return self
    
    def and_when(self, left: str, operator: Union[Operator, str], right: Any) -> 'StatementBuilder':
        """Adiciona uma condição com AND implícito."""
        return self.when(left, operator, right)
    
    def or_when(self, left: str, operator: Union[Operator, str], right: Any) -> 'StatementBuilder':
        """
        Define que o próximo statement deve ser combinado com OR.
        Nota: Isso define o bool_op deste statement, não adiciona uma condição OR.
        """
        self.bool_op = BooleanOperator.OR
        return self
    
    def and_next(self) -> 'StatementBuilder':
        """Define que o próximo statement deve ser combinado com AND."""
        self.bool_op = BooleanOperator.AND
        return self
    
    def then(self, next_state: str) -> 'StatementBuilder':
        """Define o próximo estado."""
        self.next_state = next_state
        return self
    
    def default(self, next_state: str) -> 'StatementBuilder':
        """Define um statement default."""
        self.conditions = None
        self.next_state = next_state
        self.bool_op = None
        return self
    
    def build(self) -> Statement:
        """Constrói e retorna o objeto Statement."""
        return Statement(self.conditions, self.next_state, self.bool_op)


# Classes predefinidas para condições comuns
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
            .and_next()
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
