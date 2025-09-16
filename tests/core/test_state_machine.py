import unittest
import concurrent.futures
from unittest.mock import patch, MagicMock

from core.exceptions import StateMachineExecutionError, StateNotFoundError
from core.lambda_handler import Lambda
from core.state_machine import StateMachine


class TestStateMachine(unittest.TestCase):
    """Test cases for the StateMachine class."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create Lambda objects with mocked handlers
        self.lambda1 = Lambda("lambda1", "lambda2", timeout=5)
        self.lambda1_handler = MagicMock(return_value={"key": "value1"})

        self.lambda2 = Lambda("lambda2", "lambda3", timeout=3)
        self.lambda2_handler = MagicMock(return_value={"key": "value2"})

        self.lambda3 = Lambda("lambda3", None, timeout=2)
        self.lambda3_handler = MagicMock(
            return_value={"key": "value3", "result": "final"})

        # Replace the handler methods with our mocks
        self.lambda1._handler = self.lambda1_handler
        self.lambda2._handler = self.lambda2_handler
        self.lambda3._handler = self.lambda3_handler

        # Default machine tree for testing
        self.machine_tree = [self.lambda1, self.lambda2, self.lambda3]

    def test_initialization(self):
        """Test StateMachine initialization and parameter validation."""
        # Test normal initialization
        machine = StateMachine("test_machine", self.machine_tree)

        # Check machine properties
        self.assertEqual(machine.machine_name, "test_machine")
        self.assertEqual(machine.head_lambda, self.lambda1)
        self.assertEqual(len(machine.machine_tree), 3)
        # Sum of lambdas timeouts (5+3+2)
        self.assertEqual(machine.timeout, 10)

        # Test custom timeout
        custom_timeout = 15
        machine = StateMachine(
            "test_machine", self.machine_tree, timeout=custom_timeout)

        self.assertEqual(machine.timeout, custom_timeout)

        # Test timeout adjustment when sum of lambdas exceeds machine timeout
        machine = StateMachine("test_machine", self.machine_tree, timeout=8)
        self.assertEqual(machine.timeout, 11)  # Should be adjusted to sum+1

        # Test empty machine tree
        with self.assertRaises(ValueError):
            StateMachine("test_machine", [])

    def test_successful_execution(self):
        """Test the successful execution flow of the state machine."""
        machine = StateMachine("test_machine", self.machine_tree)

        # Define input event
        input_event = {"input": "test_data"}

        # Execute the state machine
        result = machine.run(input_event)

        # Verify all lambdas were called with correct parameters
        self.lambda1_handler.assert_called_once()
        args, _ = self.lambda1_handler.call_args

        self.assertEqual(args[0], input_event)  # Check event passed correctly
        self.assertEqual(args[1]["machine_name"],
                         "test_machine")  # Check context

        self.lambda2_handler.assert_called_once()
        args, _ = self.lambda2_handler.call_args

        self.assertEqual(args[0], {"key": "value1"})  # Output from lambda1

        self.lambda3_handler.assert_called_once()
        args, _ = self.lambda3_handler.call_args
        self.assertEqual(args[0], {"key": "value2"})  # Output from lambda2

        # Verify final result
        self.assertEqual(result, {"key": "value3", "result": "final"})

    def test_state_not_found_error(self):
        """Test that StateNotFoundError is raised when a state is not found."""
        # Create a Lambda that transitions to a non-existent state
        bad_lambda = Lambda("bad_lambda", "non_existent_state", timeout=1)
        bad_lambda._handler = MagicMock(return_value={"key": "value"})

        machine = StateMachine("test_machine", [bad_lambda])

        # Execute the state machine and expect StateNotFoundError
        with self.assertRaises(StateNotFoundError):
            machine.run({"input": "test_data"})

    def test_state_execution_error(self):
        """Test that StateMachineExecutionError is raised when a state execution fails."""
        # Create a Lambda with a handler that raises an exception
        error_lambda = Lambda("error_lambda", "next_state", timeout=1)
        error_lambda._handler = MagicMock(side_effect=ValueError("Test error"))

        machine = StateMachine("test_machine", [error_lambda])

        # Execute the state machine and expect StateMachineExecutionError
        with self.assertRaises(StateMachineExecutionError):
            machine.run({"input": "test_data"})

    @patch('time.time')
    def test_machine_timeout(self, mock_time):
        """Test that TimeoutError is raised when the state machine execution exceeds timeout."""
        # Mock time.time to simulate timeout
        # Provide enough values for all time.time() calls
        mock_time.side_effect = [0, 0, 0, 100, 100, 100, 100, 100]

        machine = StateMachine("test_machine", self.machine_tree, timeout=5)

        # Execute the state machine and expect TimeoutError
        with self.assertRaises(TimeoutError):
            machine.run({"input": "test_data"})

    @patch('concurrent.futures.ThreadPoolExecutor')
    def test_state_timeout(self, mock_executor):
        """Test that TimeoutError is raised when a state execution exceeds its timeout."""
        # Setup mock executor to simulate a state timeout
        mock_future = MagicMock()
        mock_future.result.side_effect = concurrent.futures.TimeoutError()
        mock_future.cancel.return_value = None

        mock_executor_instance = MagicMock()
        mock_executor_instance.__enter__.return_value.submit.return_value = mock_future
        mock_executor.return_value = mock_executor_instance

        # Create a simpler test case with just one Lambda
        test_lambda = Lambda("test_lambda", None, timeout=1)
        test_lambda._handler = MagicMock(return_value={"key": "value"})

        machine = StateMachine("test_machine", [test_lambda])

        # Expect StateMachineExecutionError wrapping a TimeoutError
        with self.assertRaises(StateMachineExecutionError) as context:
            machine.run({"input": "test_data"})

        # Verificar que a mensagem de erro contém a informação sobre timeout
        self.assertIn("timed out", str(context.exception))


if __name__ == "__main__":
    unittest.main()
