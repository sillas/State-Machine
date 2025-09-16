from typing import Any, Optional
import time as t
import logging
import uuid
import concurrent.futures

from core.exceptions import StateMachineExecutionError, StateNotFoundError
from core.lambda_handler import Lambda


class StateMachine:
    """
    StateMachine manages the execution of a state-driven workflow using a tree of Lambda states.

    Args:
        machine_name (str): The unique name of the state machine.
        machine_tree (list[Lambda]): A list of Lambda state objects representing the workflow.
        timeout (int, optional): Maximum allowed execution time for the entire state machine in seconds. Defaults to 30.

    Raises:
        ValueError: If the machine_tree is empty.
        TimeoutError: If the execution exceeds the specified timeout.
        StateNotFoundError: If a state is not found in the machine tree.
        StateMachineExecutionError: If an error occurs during state execution.

    Methods:
        run(entry_point_event: Any) -> Any:
            Executes the state machine starting from the entry point event.
            Each state is executed in sequence, passing the output of one state as the input to the next.
            Handles per-state and global timeouts, logging, and error propagation.
            Returns the final output when the workflow completes successfully.
    """

    def __init__(self, machine_name: str, machine_tree: list[Lambda], timeout: Optional[int] = None):

        self.namespace = uuid.NAMESPACE_URL
        self.machine_name = machine_name
        self.machine_id = str(uuid.uuid5(self.namespace, self.machine_name))

        if len(machine_tree) == 0:
            raise ValueError("machine_tree must contains lambdas!")

        self.head_lambda = machine_tree[0]
        self.machine_tree = {}

        states_timeout_sum = 0
        for l in machine_tree:
            self.machine_tree[l.name] = l
            states_timeout_sum += l.timeout

        if timeout is None:
            self.timeout = states_timeout_sum
        else:
            self.timeout = timeout

        if states_timeout_sum > self.timeout:
            logging.warning(
                f"Sum of all states timeouts ({states_timeout_sum}s) exceeds machine timeout ({self.timeout}s). Changing machine timeout to {states_timeout_sum + 1}s."
            )
            self.timeout = states_timeout_sum + 1

    def run(self, entry_point_event: Any) -> Any:
        start_time = t.time()
        execution_id = str(uuid.uuid4())  # Unique ID for this execution
        timeout = self.timeout
        machine_tree = self.machine_tree
        event = entry_point_event or None
        step_lambda: Lambda | None = self.head_lambda
        next_state: str | None = step_lambda.name
        context = {
            "machine_name": self.machine_name,
            "machine_id": self.machine_id,
            "execution_id": execution_id,
            "state_name": next_state,
            "start_time": start_time,
        }

        while True:
            if t.time() - start_time > timeout:
                logging.error(
                    f"Execution {execution_id} timed out after {timeout} seconds. Returning None."
                )
                raise TimeoutError(
                    f"Execution {execution_id} timed out after {timeout} seconds.")

            if not step_lambda:
                logging.error(
                    f"Execution {execution_id} encountered an invalid state: {next_state}."
                )
                raise StateNotFoundError(f"State {next_state} does not exist!")

            logging.info(
                {
                    **context,
                    "input": event,
                    "message": f"Entering state {next_state}"
                }
            )

            try:

                step_start_time = t.time()

                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    # ----------------------------------------------ACT
                    state_timeout = step_lambda.timeout
                    future = executor.submit(
                        step_lambda.handler, event, context)
                    try:
                        event = future.result(
                            timeout=state_timeout)
                    except concurrent.futures.TimeoutError:
                        future.cancel()
                        logging.error(
                            {
                                "execution_id": execution_id,
                                "state_name": context["state_name"],
                                "message": f"State {context['state_name']} timed out."
                            }
                        )
                        raise TimeoutError(
                            f"State {context['state_name']} timed out after {state_timeout} seconds."
                        )
                next_state = step_lambda.next_state
                # ----------------------------------------------
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
                raise StateMachineExecutionError(
                    f"Error in state {next_state}: {str(e)}") from e
