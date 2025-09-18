from typing import Any, Optional
import concurrent.futures

from core.state_base import State, StateType
from core.state_machine import StateMachine


class ParallelHandler(State):
    """
    ParallelHandler executes multiple StateMachine workflows in parallel, managing their timeouts and aggregating results.

    Args:
        name (str): The name of the parallel handler.
        next_state (Optional[str]): The next state to transition to after execution.
        workflows (list[StateMachine]): List of StateMachine instances to run in parallel.

    Attributes:
        workflows (list[StateMachine]): The workflows to execute in parallel.
        timeout (int): The effective timeout for the parallel execution.

    Methods:
        handler(event: Any, context: dict[str, Any]) -> Any:
            Runs all workflows in parallel, waits for completion or timeout, and returns a dictionary mapping workflow names to their results.
    """

    def __init__(self, name: str, next_state: Optional[str], workflows: list[StateMachine]):

        self.workflows = workflows

        timeout: int = 0
        for w in workflows:
            timeout += w.timeout

        super().__init__(
            name=name,
            next_state=next_state,
            type=StateType.PARALLEL,
            timeout=timeout + 1
        )

    def handler(self, event: Any, context: dict[str, Any]) -> Any:
        """
        Executes multiple workflows in parallel using threads, passing the given event and context to each workflow's `run` method.

        Args:
            event (Any): The event data to be processed by each workflow.
            context (dict[str, Any]): A dictionary containing contextual information for the workflows.

        Returns:
            dict[str, Any]: A dictionary mapping each workflow's machine name to its result. If a workflow raises an exception, the result will contain an "error" key with the exception message.

        Raises:
            concurrent.futures.TimeoutError: If the execution of all workflows does not complete within the specified timeout.
        """

        results = {}

        with concurrent.futures.ThreadPoolExecutor(max_workers=len(self.workflows)) as executor:
            future_map = {
                executor.submit(w.run, event, context): w.machine_name
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
