import multiprocessing
import os
import sys
import logging
from typing import Any, Optional
import traceback
import json

from core.blocks.lambda_handler import Lambda
from core.state_base import StateType

# Configure logging for the detached process
logging.basicConfig(
    filename='detached_processes.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('FireAndForget')


def _isolated_worker(lambda_name, lambda_path, event_data, context_data):
    """
    Runs in a completely separate process with its own Python interpreter.
    This function handles all exceptions internally and logs them appropriately.

    Args:
        lambda_name: Name of the lambda function to execute
        lambda_path: Path to the lambda module
        event_data: Serialized event data
        context_data: Serialized context data
    """

    # Set up logging for this process
    process_logger = logging.getLogger(
        f'FireAndForget-{lambda_name}-{os.getpid()}')

    try:
        process_logger.info(f"Starting detached process for {lambda_name}")

        # Import the module directly
        import importlib.util
        from pathlib import Path

        lambda_path = Path(lambda_path)
        if not lambda_path.exists():
            process_logger.error(f"Lambda module not found at {lambda_path}")
            return

        spec = importlib.util.spec_from_file_location(lambda_name, lambda_path)
        if spec is None or spec.loader is None:
            process_logger.error(f"Could not load module for {lambda_name}")
            return

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Deserialize the event and context
        event = json.loads(event_data)
        context = json.loads(context_data)

        # Add process-specific info to context
        context['detached_process'] = True
        context['process_id'] = os.getpid()

        # Execute the handler
        process_logger.info(f"Executing lambda_handler for {lambda_name}")
        result = module.lambda_handler(event, context)

        # Log the completion
        process_logger.info(f"Successfully completed {lambda_name}")
        process_logger.debug(f"Result: {result}")

    except Exception as e:
        # Log any exceptions but don't propagate them
        process_logger.error(
            f"Error in detached process {lambda_name}: {str(e)}")
        process_logger.error(traceback.format_exc())


class FireAndForget(Lambda):
    """
    Executes a Lambda function in a completely separate process that continues running
    even if the main application or state machine terminates.

    This is ideal for operations that should happen regardless of the main workflow's status,
    such as sending notifications, emails, or persisting data.

    The process handles all its own errors and will not affect the main application if it fails.
    All output is directed to a log file rather than standard output.

    Args:
        name (str): The name of the Lambda function.
        next_state (str | None): The next state to transition to after launching the process.
        timeout (Optional[int], optional): Not used, as the process runs independently.
    """

    def __init__(self, name: str, next_state: str | None, timeout: Optional[int] = None) -> None:
        super().__init__(
            name=name,
            next_state=next_state,
            timeout=timeout
        )
        self.type = StateType.FIRE_AND_FORGET.value

    def handler(self, event: Any, context: dict[str, Any]) -> Any:
        """
        Launches the lambda handler in a completely separate process and returns immediately.

        Args:
            event (Any): The event data passed to the handler.
            context (dict[str, Any]): The context dictionary containing metadata.

        Returns:
            dict: Status information about the launched process.
        """
        # Get the lambda path
        lambda_name = self.name
        lambda_path = f"lambdas/{lambda_name}/main.py"

        try:
            # Serialize the event and context for passing to the new process
            # We need to serialize these to avoid any shared memory issues
            event_data = json.dumps(event)
            context_data = json.dumps(context)

            # Create and start a completely separate process
            # We use multiprocessing.Process with daemon=False to ensure it continues
            # running even if the parent process exits
            process = multiprocessing.Process(
                target=_isolated_worker,
                args=(lambda_name, lambda_path, event_data, context_data),
                daemon=False  # This ensures the process continues even if parent exits
            )
            process.start()

            logger.info(
                f"Launched detached process {process.pid} for {lambda_name}")

            # Return status information
            return {
                "status": "launched",
                "detached_execution": True,
                "process_id": process.pid,
                "lambda_name": lambda_name
            }

        except Exception as e:
            # If there's an error launching the process, log it but don't interrupt the state machine
            logger.error(
                f"Error launching detached process for {lambda_name}: {str(e)}")
            logger.error(traceback.format_exc())

            # Return error information
            return {
                "status": "error",
                "detached_execution": False,
                "error": str(e),
                "lambda_name": lambda_name
            }
