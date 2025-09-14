import sys
import os

# Adiciona o diretório raiz ao path para importar o módulo utils
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.statement_evaluator import StatementEvaluator
from utils.statement_models import StatementBuilder, Operator, CommonStatements

def test_statement_evaluator():
    # Example statements definition using the old dictionary format
    statements = [
        {
            "sttm": ["$.user.age gt 18", "$.user.verified eq true"],
            "then": "adult_verified_state",
            "bool_ops": None
        },
        {
            "sttm": ["$.user.role eq admin"],
            "then": "admin_state",
            "bool_ops": None
        },
        {
            "sttm": ["$.user.purchases gt 5"],
            "then": "premium_state",
            "bool_ops": "AND"  # Both conditions must be true
        },
        {
            "sttm": ["$.user.totalSpent gt 100"],
            "then": "premium_state",  # This is the state we return if the AND condition is true
            "bool_ops": None
        },
        {
            "sttm": ["$.user.lastLogin gt 30"],
            "then": "inactive_state",
            "bool_ops": None
        },
        {
            "sttm": None,  # Default case
            "then": "default_state",
            "bool_ops": None
        }
    ]

    # Create the evaluator
    evaluator = StatementEvaluator(statements)

    # Test case 1: Adult and verified user
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
    print(f"Test case 1 result: {result1}")  # Should return "adult_verified_state"

    # Test case 2: Admin user
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
    print(f"Test case 2 result: {result2}")  # Should return "admin_state"

    # Test case 3: Premium user (both conditions true)
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
    print(f"Test case 3 result: {result3}")  # Should return "premium_state"

    # Test case 4: Inactive user
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
    print(f"Test case 4 result: {result4}")  # Should return "inactive_state"

    # Test case 5: Default case
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
    print(f"Test case 5 result: {result5}")  # Should return "default_state"

if __name__ == "__main__":
    test_statement_evaluator()
    
    # Mostrar como usar a nova forma com classes
    print("\n--- Testando com as classes de modelo ---")
    
    # Criando statements usando as classes
    model_statements = [
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
    statement_dicts = [s.to_dict() for s in model_statements]
    
    # Criar o avaliador
    model_evaluator = StatementEvaluator(statement_dicts)
    
    # Executar os mesmos testes com o novo avaliador
    data1 = {"user": {"age": 25, "verified": True, "role": "user", "purchases": 3, "totalSpent": 50, "lastLogin": 10}}
    print(f"Test case 1 result: {model_evaluator.evaluate(data1)}")
    
    data2 = {"user": {"age": 30, "verified": False, "role": "admin", "purchases": 2, "totalSpent": 40, "lastLogin": 5}}
    print(f"Test case 2 result: {model_evaluator.evaluate(data2)}")
    
    data3 = {"user": {"age": 35, "verified": False, "role": "user", "purchases": 10, "totalSpent": 200, "lastLogin": 15}}
    print(f"Test case 3 result: {model_evaluator.evaluate(data3)}")
    
    data4 = {"user": {"age": 28, "verified": False, "role": "user", "purchases": 1, "totalSpent": 20, "lastLogin": 45}}
    print(f"Test case 4 result: {model_evaluator.evaluate(data4)}")
    
    data5 = {"user": {"age": 15, "verified": False, "role": "user", "purchases": 0, "totalSpent": 0, "lastLogin": 2}}
    print(f"Test case 5 result: {model_evaluator.evaluate(data5)}")
