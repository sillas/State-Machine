
from pathlib import Path
from typing import Any, Callable
import yaml
from core.handlers.choice_handler import Choice
from core.handlers.lambda_handler import Lambda
from core.handlers.parallel_handler import Parallel
from core.state_machine import StateMachine
from logging_config import error, info


class StateConfigurationProcessor:
    """
    Processes state configurations and builds execution blocks for a state machine.
    Handles lambda, choice, and parallel states, managing variables and state transitions.
    """

    def __init__(self, state_definitions: dict[str, Any], variables: dict[str, Any] | None, lambda_directory: str) -> None:
        """Initialize the processor with state definitions, variables, and lambda directory."""
        self.execution_blocks = []
        self.variables = variables if variables else {}
        self.state_definitions = state_definitions
        self.lambda_directory = lambda_directory

    def set_state(self, current_state_key: str, next_state_key: str | None) -> None:
        """Set the current and next state based on provided keys."""
        try:
            self.this_state = self.state_definitions[current_state_key]
            self.next_state = self.state_definitions.get(next_state_key or '')
        except KeyError as e:
            error(f"State key not found: {e}")
            raise

    def _process_lambda_state(self) -> None:
        """Process a lambda state and append it to execution blocks."""
        try:
            state_name = self.this_state['name']
            lambda_full_path = Path(self.lambda_directory) / state_name / "main.py"  # nopep8
            lambda_file_path = Path(lambda_full_path)

            if not lambda_file_path.exists():
                error(f"Lambda {lambda_full_path} not found.")
                raise ModuleNotFoundError(
                    f"Lambda {lambda_full_path} not found.")

            lambda_config: dict[str, Any] = {
                "name": state_name,
                "next_state": self.next_state['name'] if self.next_state else None,
                "lambda_path": self.lambda_directory,
            }

            timeout_value = self.this_state.get('timeout')
            if timeout_value:
                lambda_config['timeout'] = int(timeout_value)

            self.execution_blocks.append(Lambda(**lambda_config))
            info(f"Lambda state processed: {state_name}")
        except Exception as e:
            error(f"Error processing lambda state: {e}")
            raise

    def _process_choice_state(self, conditions: str) -> None:
        """Process a choice state and append it to execution blocks."""
        try:
            choice_name = self.this_state['name']
            conditions_list = self.variables.get(conditions)

            if conditions_list is None:
                error(
                    f"Conditions for choice {choice_name} do not exist!")
                raise ValueError(
                    f"Conditions for choice {choice_name} do not exist!")

            for i in range(len(conditions_list)):
                hash_words = self._extract_hash_words(conditions_list[i])
                for word in hash_words:
                    state_name = self.state_definitions[word[1:]]['name']
                    conditions_list[i] = conditions_list[i].replace(
                        word, f"'{state_name}'")

            self.execution_blocks.append(
                Choice(choice_name, conditions_list, self.state_definitions))
            info(f"Choice state processed: {choice_name}")
        except Exception as e:
            error(f"Error processing choice state: {e}")
            raise

    def _process_parallel_state(self, parse_machine: Callable, machine_definitions: dict[str, Any] | None) -> None:
        """Process a parallel state and append it to execution blocks."""
        try:
            if machine_definitions is None:
                error("machine_definitions is None in parallel state.")
                raise ValueError(
                    "machine_definitions is None in parallel state.")

            workflows = [
                parse_machine(machine_definitions[workflow])
                for workflow in self.this_state['workflows']
            ]

            parallel_conf = {
                "name": self.this_state['name'],
                "next_state": self.next_state['name'] if self.next_state else None,
                "workflows": workflows
            }

            self.execution_blocks.append(Parallel(**parallel_conf))
            info(f"Parallel state processed: {self.this_state['name']}")
        except Exception as e:
            error(f"Error processing parallel state: {e}")
            raise

    def _extract_hash_words(self, text: str) -> list[str]:
        """Extract hash words (e.g., #state) from a string."""
        import re
        pattern = r'#\w+(?:-\w+)*'
        matches = re.findall(pattern, text)
        return matches


class StateMachineParser:
    """
    Parses a state machine definition from a YAML file and constructs a StateMachine object.
    Handles loading, parsing, and building the execution tree for the state machine.
    """

    data: dict[str, Any]
    machine: dict[str, Any]

    def __init__(self, machine_definitions_file: str) -> None:
        """Initialize the parser with the path to the machine definitions YAML file."""
        try:
            data = self._load_data(machine_definitions_file)
            self.machine = data[data['entry']]
            self.data = data
            info(
                f"StateMachineParser - __init__ - Loaded machine definitions from {machine_definitions_file}")
        except Exception as e:
            error(
                f"StateMachineParser - __init__ - Error initializing StateMachineParser: {e}")
            raise

    def parse(self) -> StateMachine:
        """Parse the loaded machine definition and return a StateMachine object."""
        try:
            return self.parse_machine(self.machine)
        except Exception as e:
            error(f"StateMachineParser - parse - Error parsing machine: {e}")
            raise

    def parse_machine(self, machine_config: dict[str, Any]) -> StateMachine:
        """Parse a machine configuration and return a StateMachine object."""
        try:
            name = machine_config['name']
            execution_tree = machine_config['tree']

            state_processor = StateConfigurationProcessor(
                state_definitions=machine_config['states'],
                variables=machine_config.get('vars'),
                lambda_directory=machine_config['lambda_dir']
            )

            for current_state, next_state in execution_tree.items():
                try:
                    state_processor.set_state(current_state, next_state)
                    state_type = state_processor.this_state['type']
                    method = getattr(
                        state_processor, f"_process_{state_type}_state")
                    if state_type == 'lambda':
                        method()
                    elif state_type == 'choice':
                        method(next_state)
                    elif state_type == 'parallel':
                        method(self.parse_machine, self.data)
                except Exception as e:
                    error(
                        f"StateMachineParser - parse_machine - Error processing state '{current_state}': {e}")
                    raise

            info(f"State machine '{name}' parsed successfully.")
            return StateMachine(name, state_processor.execution_blocks)
        except Exception as e:
            error(
                f"StateMachineParser - parse_machine - Error parsing machine config: {e}")
            raise

    def _load_data(self, machine_definitions_file: str):
        """Load and return data from the given machine definitions YAML file."""
        err_msg = "StateMachineParser - _load_data - "
        try:
            with open(machine_definitions_file, 'r') as file:
                return yaml.safe_load(file)
        except FileNotFoundError:
            error(f"{err_msg}Error: {machine_definitions_file} not found.")
            raise
        except yaml.YAMLError as e:
            error(f"{err_msg}Error parsing YAML: {e}")
            raise
        except KeyError as e:
            error(f"{err_msg}Key error! {str(e)}")
            raise
        except Exception as e:
            error(f"{err_msg}Error: {str(e)}")
            raise
