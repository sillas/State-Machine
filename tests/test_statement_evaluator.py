import sys
import os

# Adiciona o diretório raiz ao path para importar o módulo utils
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tests.common_statements import CommonStatements
from utils.statement_evaluator import StatementEvaluator
from utils.statement_models import StatementBuilder, Operator

def test_statement_evaluator():
    
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
    
    # Criar o avaliador
    model_evaluator = StatementEvaluator(model_statements)
    
    # Executar os mesmos testes com o avaliador
    data1 = {"user": {"age": 25, "verified": True, "role": "user", "purchases": 3, "totalSpent": 50, "lastLogin": 10}}
    print(f"Test case 1 result: {model_evaluator.evaluate(data1)}") # "adult_verified_state"
    
    data2 = {"user": {"age": 30, "verified": False, "role": "admin", "purchases": 2, "totalSpent": 40, "lastLogin": 5}}
    print(f"Test case 2 result: {model_evaluator.evaluate(data2)}") # "admin_state"
    
    data3 = {"user": {"age": 35, "verified": False, "role": "user", "purchases": 10, "totalSpent": 200, "lastLogin": 15}}
    print(f"Test case 3 result: {model_evaluator.evaluate(data3)}") # premium_state
    
    data4 = {"user": {"age": 28, "verified": False, "role": "user", "purchases": 1, "totalSpent": 20, "lastLogin": 45}}
    print(f"Test case 4 result: {model_evaluator.evaluate(data4)}") # inactive_state
    
    data5 = {"user": {"age": 15, "verified": False, "role": "user", "purchases": 0, "totalSpent": 0, "lastLogin": 2}}
    print(f"Test case 5 result: {model_evaluator.evaluate(data5)}") # default_state

if __name__ == "__main__":
    test_statement_evaluator()
