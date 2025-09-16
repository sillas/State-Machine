from typing import Any, Optional
import logging
import concurrent.futures

from core.state_machine import StateMachine


class ParallelHandler:

    def __init__(self, name: str, workflows: list[StateMachine], next_state: str, timeout: Optional[int] = 60):
        self.workflows = workflows
        self.next_state = next_state
        self.name = name
        self.type = "Parallel"

        state_machine_timeout_sum = 0
        for w in workflows:
            state_machine_timeout_sum += w.timeout

        if timeout is None:
            self.timeout = state_machine_timeout_sum

        else:
            self.timeout = timeout

            if self.timeout < state_machine_timeout_sum:
                logging.warning(
                    f"Sum of all workflows timeouts ({state_machine_timeout_sum}s) exceeds parallel handler timeout ({self.timeout}s). Changing machine timeout to {state_machine_timeout_sum + 1}s."
                )
                self.timeout = state_machine_timeout_sum + 1

    def handler(self, event: Any, _: dict) -> dict[str, Any]:

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
