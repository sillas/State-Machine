import unittest
import concurrent.futures
from unittest.mock import patch, MagicMock

from core.blocks.parallel_handler import ParallelHandler
from core.state_machine import StateMachine
from core.state_base import StateType


class TestParallelHandler(unittest.TestCase):
    """Test cases for the ParallelHandler class."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create mock workflows with proper typing
        self.mock_workflow1 = MagicMock(spec=StateMachine)
        self.mock_workflow1.machine_name = "workflow1"
        self.mock_workflow1.timeout = 5

        self.mock_workflow2 = MagicMock(spec=StateMachine)
        self.mock_workflow2.machine_name = "workflow2"
        self.mock_workflow2.timeout = 3

        # Create a list of mock workflows - cast to proper type for type checker
        self.workflows: list[StateMachine] = [
            self.mock_workflow1,
            self.mock_workflow2
        ]

        # Create an instance of ParallelHandler for tests
        self.parallel_handler = ParallelHandler(
            name="test_parallel",
            next_state="next_state",
            workflows=self.workflows
        )

    def test_initialization(self):
        """Test ParallelHandler initialization and parameter validation."""
        # Verify attributes are correctly initialized
        self.assertEqual(self.parallel_handler.name, "test_parallel")
        self.assertEqual(self.parallel_handler.type, StateType.PARALLEL.value)
        self.assertEqual(self.parallel_handler.next_state, "next_state")

        # Check that timeout is the sum of workflow timeouts plus 1
        expected_timeout = self.mock_workflow1.timeout + self.mock_workflow2.timeout + 1
        self.assertEqual(self.parallel_handler.timeout, expected_timeout)

    @patch('concurrent.futures.ThreadPoolExecutor')
    def test_handler_successful_execution(self, mock_executor_cls):
        """Test successful parallel execution of workflows."""
        # Set up mock results for each workflow
        workflow1_result = {"status": "success", "data": "result1"}
        workflow2_result = {"status": "success", "data": "result2"}

        # Configure mock executor
        mock_executor = MagicMock()
        mock_executor_cls.return_value.__enter__.return_value = mock_executor

        # Configure mock futures
        mock_future1 = MagicMock()
        mock_future1.result.return_value = workflow1_result

        mock_future2 = MagicMock()
        mock_future2.result.return_value = workflow2_result

        # Map futures to workflow names
        mock_executor.submit.side_effect = [mock_future1, mock_future2]

        # Configure as_completed to return futures in order
        with patch('concurrent.futures.as_completed', return_value=[mock_future1, mock_future2]):
            # Prepare test data
            event_data = {"input": "test"}
            context_data = {}

            # Call the handler
            result = self.parallel_handler.handler(event_data, context_data)

            # Verify executor was called with correct parameters
            mock_executor.submit.assert_any_call(
                self.mock_workflow1.run, event_data, context_data)
            mock_executor.submit.assert_any_call(
                self.mock_workflow2.run, event_data, context_data)

            # Verify the expected results
            expected_result = {
                "workflow1": workflow1_result,
                "workflow2": workflow2_result
            }
            self.assertEqual(result, expected_result)

    @patch('concurrent.futures.ThreadPoolExecutor')
    def test_handler_with_workflow_error(self, mock_executor_cls):
        """Test handling of workflow errors during parallel execution."""
        # Set up success result for one workflow and error for another
        workflow1_result = {"status": "success", "data": "result1"}
        workflow2_error = Exception("Workflow 2 failed")

        # Configure mock executor
        mock_executor = MagicMock()
        mock_executor_cls.return_value.__enter__.return_value = mock_executor

        # Configure mock futures
        mock_future1 = MagicMock()
        mock_future1.result.return_value = workflow1_result

        mock_future2 = MagicMock()
        mock_future2.result.side_effect = workflow2_error

        # Map futures to workflow names
        mock_executor.submit.side_effect = [mock_future1, mock_future2]

        # Configure as_completed to return futures in order
        with patch('concurrent.futures.as_completed', return_value=[mock_future1, mock_future2]):
            # Prepare test data
            event_data = {"input": "test"}
            context_data = {}

            # Call the handler
            result = self.parallel_handler.handler(event_data, context_data)

            # Verify executor was called with correct parameters
            mock_executor.submit.assert_any_call(
                self.mock_workflow1.run, event_data, context_data)
            mock_executor.submit.assert_any_call(
                self.mock_workflow2.run, event_data, context_data)

            # Verify the expected results, with error captured in workflow2
            expected_result = {
                "workflow1": workflow1_result,
                "workflow2": {"error": str(workflow2_error)}
            }
            self.assertEqual(result, expected_result)

    @patch('concurrent.futures.ThreadPoolExecutor')
    def test_timeout_propagation(self, mock_executor_cls):
        """Test timeout is correctly propagated to ThreadPoolExecutor."""
        # Configure mock executor
        mock_executor = MagicMock()
        mock_executor_cls.return_value.__enter__.return_value = mock_executor

        # Configure mock futures and as_completed to simulate timeout
        mock_future = MagicMock()
        mock_executor.submit.return_value = mock_future

        # Configure as_completed with timeout error
        with patch('concurrent.futures.as_completed', side_effect=concurrent.futures.TimeoutError()):
            # Prepare test data
            event_data = {"input": "test"}
            context_data = {}

            # Call the handler and expect TimeoutError
            with self.assertRaises(concurrent.futures.TimeoutError):
                self.parallel_handler.handler(event_data, context_data)

            # Verify as_completed was called with the correct timeout
            with patch('concurrent.futures.as_completed') as mock_as_completed:
                try:
                    self.parallel_handler.handler(event_data, context_data)
                except Exception:
                    pass

                # Check that the timeout parameter was passed correctly
                mock_as_completed.assert_called_once()
                _, kwargs = mock_as_completed.call_args
                self.assertEqual(
                    kwargs.get('timeout'),
                    self.parallel_handler.timeout)


if __name__ == '__main__':
    unittest.main()
