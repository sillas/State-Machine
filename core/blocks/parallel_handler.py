from typing import Any, Optional
import logging
import concurrent.futures

from core.blocks.lambda_handler import Lambda, LambdaTypes
from core.state_machine import StateMachine


class ParallelHandler(Lambda):
    """
    ParallelHandler executes multiple StateMachine workflows in parallel, managing their timeouts and aggregating results.

    Args:
        name (str): The name of the parallel handler.
        workflows (list[StateMachine]): List of StateMachine instances to run in parallel.
        next_state (Optional[str]): The next state to transition to after execution.
        timeout (Optional[int], optional): Maximum allowed time (in seconds) for all workflows to complete. Defaults to 60 seconds.

    Attributes:
        workflows (list[StateMachine]): The workflows to execute in parallel.
        next_state (Optional[str]): The next state after execution.
        timeout (int): The effective timeout for the parallel execution.

    Methods:
        handler(event: Any, context: dict[str, Any]) -> Any:
            Runs all workflows in parallel, waits for completion or timeout, and returns a dictionary mapping workflow names to their results.
    """

    def __init__(self, name: str, workflows: list[StateMachine], next_state: Optional[str], timeout: Optional[int] = 60):
        self.workflows = workflows
        self.next_state = next_state

        state_machine_timeout_sum = 0
        for w in workflows:
            state_machine_timeout_sum += w.timeout

        if timeout is None:
            _timeout = state_machine_timeout_sum

        else:
            _timeout = timeout

            if _timeout < state_machine_timeout_sum:
                logging.warning(
                    f"Sum of all workflows timeouts ({state_machine_timeout_sum}s) exceeds parallel handler timeout ({_timeout}s). Changing machine timeout to {state_machine_timeout_sum + 1}s."
                )
                _timeout = state_machine_timeout_sum + 1

        super().__init__(name, None, LambdaTypes.PARALLEL, timeout=_timeout)

    def handler(self, event: Any, context: dict[str, Any]) -> Any:

        results = {}

        with concurrent.futures.ThreadPoolExecutor(max_workers=len(self.workflows)) as executor:
            future_map = {
                executor.submit(w.run, event): w.machine_name
                for w in self.workflows
            }

            for future in concurrent.futures.as_completed(future_map, timeout=self.timeout):

                workflow_name = future_map[future]

                try:
                    result = future.result()
                except Exception as e:
                    result = {"error": str(e)}

                results[workflow_name] = result

        return results
