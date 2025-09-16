from typing import Any
import time as t
import logging
import uuid
from core.lambda_handler import Lambda


class StateMachine:
    def __init__(self, machine_name: str, machine_tree: list[Lambda], timeout: int = 30):

        self.namespace = uuid.NAMESPACE_URL
        self.machine_name = machine_name
        self.machine_id = str(uuid.uuid5(self.namespace, self.machine_name))
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
        start_time = t.time()
        execution_id = str(uuid.uuid4())  # Unique ID for this execution
        timeout = self.timeout
        machine_tree = self.machine_tree
        event = entry_point_event or None
        next_state: str | None = "START"
        context = {
            "machine_name": self.machine_name,
            "machine_id": self.machine_id,
            "execution_id": execution_id,
            "state_name": next_state,
            "start_time": start_time,
        }

        step_lambda: Lambda | None = self.head_lambda

        while 1:
            if t.time() - start_time > timeout:
                logging.error(
                    f"Execution {execution_id} timed out after {timeout} seconds. Returning None."
                )
                raise Exception("Timeout atingido! Retornando None")

            if not step_lambda:
                logging.error(
                    f"Execution {execution_id} encountered an invalid state: {next_state}."
                )
                raise Exception(f"State {next_state} does not exist!")

            logging.info(
                {
                    **context,
                    "input": event,
                    "message": f"Entering state {next_state}"
                }
            )

            try:
                step_start_time = t.time()
                event = step_lambda.handler(event, context)  # Act
                next_state = step_lambda.next_state
                step_duration = t.time() - step_start_time

                logging.info(
                    {
                        "execution_id": execution_id,
                        "state_name": context["state_name"],
                        "output": event,
                        "duration": step_duration,
                        "message": f"Exiting state {context['state_name']}"
                    }
                )

                if next_state is None:
                    logging.info(
                        {
                            "execution_id": execution_id,
                            "message": "Execution completed successfully.",
                            "final_output": event
                        }
                    )
                    return event

                context["state_name"] = next_state
                step_lambda = machine_tree.get(next_state)  # Next

            except Exception as e:
                logging.error(
                    {
                        "execution_id": execution_id,
                        "state_name": next_state,
                        "error": str(e),
                        "message": f"Error occurred in state {next_state}"
                    }
                )
                raise
