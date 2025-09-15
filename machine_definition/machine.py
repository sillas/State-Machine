from enum import Enum
import time
import uuid
from typing import Any, Optional
from pathlib import Path
import importlib.util

class LambdaTypes(Enum):
    IF = "if_statement"
    END = "end"

class Lambda:
    name: str
    type: str
    next_state: str
    statements: list

class StateMachine:
    def __init__(self, machine_name: str, machine_tree: dict[str, Lambda], timeout: int = 30):

        self.namespace = uuid.NAMESPACE_URL
        self.machine_name = machine_name
        self.machine_tree = machine_tree
        self.timeout = timeout
        self.transition_count = {}
        self.current_state = 0
        self._lambda_cache = {}
    
    def _load_lambda(self, lambda_name: str):
        
        handler_cache = self._lambda_cache.get(lambda_name)
        
        if(handler_cache):
            return handler_cache

        lambda_path = Path(f"lambdas/{self.machine_name}/{lambda_name}/main.py")
        
        if not lambda_path.exists():
            raise ModuleNotFoundError(f"Lambda {lambda_name} não encontrado")

        spec = importlib.util.spec_from_file_location(lambda_name, lambda_path)
        
        if spec is None or spec.loader is None:
            raise ImportError(f"Não foi possível carregar o módulo para {lambda_name}")
        
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        handler = module.lambda_handler
        self._lambda_cache[lambda_name] = handler

        return handler
    
    def machine(self, entry_point_event: Any) -> Any:

        start_time = time.time()
        timeout = self.timeout
        machine_tree = self.machine_tree
        event = entry_point_event or None
        context = {
            "start_time": start_time,
            "machine_name": self.machine_name,
            "machine_id": str(uuid.uuid5(self.namespace, self.machine_name))
        }

        try:
            step_lambda_definition: Lambda = machine_tree["init"]
        except Exception:
            raise Exception("Machine tree does not have a entry point!")
        
        while 1:

            if time.time() - start_time > timeout:
                raise Exception("Timeout atingido! Retornando None")

            step_handler = self._load_lambda(step_lambda_definition.name) # Load
            event = step_handler(event, context) # Act
            next_state = step_lambda_definition.next_state

            if next_state == LambdaTypes.END.value:
                return event
         
            step_lambda_definition = machine_tree[next_state] # Next

            if step_lambda_definition.type == LambdaTypes.IF.value:
                from utils.statement_evaluator import StatementEvaluator
                
                # Create evaluator with the statements from the IF lambda
                evaluator = StatementEvaluator(step_lambda_definition.statements)
                
                # Evaluate statements against the current event
                next_state = evaluator.evaluate(event)
                
                if next_state is None:
                    raise ValueError("Statement evaluation failed: no matching condition and no default provided")
                
                step_lambda_definition = machine_tree[next_state]

