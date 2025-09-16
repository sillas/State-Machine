import time
import uuid
from typing import Any
from utils.constants import Lambda, LambdaTypes

class StateMachine:
    def __init__(self, machine_name: str, machine_tree: list[Lambda], timeout: int = 30):

        self.namespace = uuid.NAMESPACE_URL
        self.machine_name = machine_name
        self.timeout = timeout
        self.transition_count = {}
        self.current_state = 0

        if len(machine_tree) == 0:
            raise ValueError("machine_tree must contains lambdas!")

        self.head_lambda = machine_tree[0]
        self.machine_tree = {}
        for l in machine_tree:
            self.machine_tree[l.name] = l
    
    def run(self, entry_point_event: Any) -> Any:

        start_time = time.time()
        timeout = self.timeout
        machine_tree = self.machine_tree
        event = entry_point_event or None
        next_state: str|None = "START"
        context = {
            "start_time": start_time,
            "machine_name": self.machine_name,
            "machine_id": str(uuid.uuid5(self.namespace, self.machine_name)),
            "step_name": next_state
        }

        step_lambda: Lambda | None = self.head_lambda

        while 1:

            if time.time() - start_time > timeout:
                raise Exception("Timeout atingido! Retornando None")

            if not step_lambda:
                raise Exception(f"State {next_state} does not exist!")

            print("\nInput: ", event)
            print(f'-- -- -- -- -- -- -- STATE {next_state}')
            event = step_lambda.handler(event, context) # Act
            next_state = step_lambda.next_state
            print('-- -- -- -- -- -- --')
            print("Output: ", event)
            print("Context: ", context)
            print(f'{context["timestamp"] - start_time} s---------------------------------------\n')

            if next_state == None:
                return event
         
            step_lambda = machine_tree.get(next_state) # Next