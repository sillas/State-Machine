import sys
import os

# Adiciona o diretório raiz ao path para importar o módulo utils
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.statement_evaluator import StatementEvaluator
from utils.statement_models import Statement, StatementBuilder, Operator, BooleanOperator, CommonStatements

def test_statement_models():
    # Criando statements usando as classes
    statements = [
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
    
    # Converter para o formato de dicionário que o StatementEvaluator espera
    statement_dicts = [s.to_dict() for s in statements]
    
    # Criar o avaliador
    evaluator = StatementEvaluator(statement_dicts)
    
    # Teste 1: Usuário adulto verificado
    data1 = {
        "user": {
            "age": 25,
            "verified": True,
            "role": "user",
            "purchases": 3,
            "totalSpent": 50,
            "lastLogin": 10
        }
    }
    result1 = evaluator.evaluate(data1)
    print(f"Test case 1 result: {result1}")  # Deve retornar "adult_verified_state"
    
    # Teste 2: Usuário admin
    data2 = {
        "user": {
            "age": 30,
            "verified": False,
            "role": "admin",
            "purchases": 2,
            "totalSpent": 40,
            "lastLogin": 5
        }
    }
    result2 = evaluator.evaluate(data2)
    print(f"Test case 2 result: {result2}")  # Deve retornar "admin_state"
    
    # Teste 3: Usuário premium (ambas condições verdadeiras)
    data3 = {
        "user": {
            "age": 35,
            "verified": False,
            "role": "user",
            "purchases": 10,
            "totalSpent": 200,
            "lastLogin": 15
        }
    }
    result3 = evaluator.evaluate(data3)
    print(f"Test case 3 result: {result3}")  # Deve retornar "premium_state"
    
    # Teste 4: Usuário inativo
    data4 = {
        "user": {
            "age": 28,
            "verified": False,
            "role": "user",
            "purchases": 1,
            "totalSpent": 20,
            "lastLogin": 45
        }
    }
    result4 = evaluator.evaluate(data4)
    print(f"Test case 4 result: {result4}")  # Deve retornar "inactive_state"
    
    # Teste 5: Caso default
    data5 = {
        "user": {
            "age": 15,
            "verified": False,
            "role": "user",
            "purchases": 0,
            "totalSpent": 0,
            "lastLogin": 2
        }
    }
    result5 = evaluator.evaluate(data5)
    print(f"Test case 5 result: {result5}")  # Deve retornar "default_state"

if __name__ == "__main__":
    test_statement_models()
