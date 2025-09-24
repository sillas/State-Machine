from pathlib import Path
from typing import Any, Callable

import yaml

from core.blocks.choice_handler import Choice
from core.blocks.lambda_handler import Lambda
from core.blocks.parallel_handler import Parallel
from core.state_machine import StateMachine


class ConfigHandlers:

    machine_tree = []

    def __init__(self, states: dict[str, Any], vars: dict[str, Any] | None, lambda_dir: str) -> None:
        self.vars = vars if vars else {}
        self.states = states
        self.lambda_dir = lambda_dir

    def set_state(self, this_state: str, next_state: str | None) -> None:
        self.this_state = self.states[this_state]
        self.next_state = self.states.get(next_state or '')

    def _lambda(self) -> None:

        name = self.this_state['name']
        lambda_full_path = f"{self.lambda_dir}/{name}/main.py"
        lambda_file_path = Path(lambda_full_path)

        if not lambda_file_path.exists():
            raise ModuleNotFoundError(
                f"Lambda {lambda_full_path} não encontrado.")

        config: dict[str, Any] = {
            "name": name,
            "next_state": self.next_state['name'] if self.next_state else None,
            "lambda_path": self.lambda_dir,
        }

        timeout = self.this_state.get('timeout')

        if timeout:
            config['timeout'] = int(timeout)

        self.machine_tree.append(Lambda(**config))

    def _choice(self, conditions: str) -> None:

        choice_name = self.this_state['name']
        conditions_list = self.vars.get(conditions)

        if conditions_list is None:
            raise ValueError(
                f"conditions for choice {choice_name} does not exist!")

        for i in range(len(conditions_list)):
            words = self._extract_hash_words(conditions_list[i])
            for w in words:
                nn = self.states[w[1:]]['name']
                conditions_list[i] = conditions_list[i].replace(w, f"'{nn}'")

        self.machine_tree.append(Choice(choice_name, conditions_list))

    def _parallel(self, parse_machine: Callable, machines_def: dict[str, Any] | None) -> None:

        if machines_def is None:
            raise

        workflows = [
            parse_machine(machines_def[w])
            for w in self.this_state['workflows']
        ]
        self.machine_tree.append(Parallel(
            name=self.this_state['name'],
            next_state=self.next_state['name'] if self.next_state else None,
            workflows=workflows
        ))

    def _extract_hash_words(self, text: str) -> list[str]:
        import re
        pattern = r'#\w+(?:-\w+)*'
        matches = re.findall(pattern, text)
        return matches


class MachineParser:

    data: dict[str, Any]
    machine: dict[str, Any]

    def __init__(self, machines_definitions: str) -> None:

        data = self._load_data(machines_definitions)
        self.machine = data[data['entry']]
        self.data = data

    def parser(self) -> StateMachine:
        return self.parse_machine(self.machine)

    def parse_machine(self, machine) -> StateMachine:

        name = machine['name']
        tree = machine['tree']

        configs = ConfigHandlers(
            states=machine['states'],
            vars=machine.get('vars'),
            lambda_dir=machine['lambda_dir']
        )

        for this_state, next_state in tree.items():
            configs.set_state(this_state, next_state)

            state_type = configs.this_state['type']

            method = getattr(configs, f"_{state_type}")

            if state_type == 'lambda':
                method()

            elif state_type == 'choice':
                method(next_state)

            elif state_type == 'parallel':
                method(self.parse_machine, self.data)

        return StateMachine(name, configs.machine_tree)

    def _load_data(self, machines_definitions: str):
        try:
            with open(machines_definitions, 'r') as file:
                return yaml.safe_load(file)

        except FileNotFoundError:
            print(f"Error: {machines_definitions} not found.")

        except yaml.YAMLError as e:
            print(f"Error parsing YAML: {e}")

        except KeyError as e:
            print(f"Key error! {str(e)}")

        except Exception as e:
            print(f"Error: {str(e)}")

        raise


def use_example_parallel():

    parser_handler = MachineParser('sm_p_description.yml')
    machine = parser_handler.parser()

    if not machine:
        return

    event: dict[str, int] = {"value": 50}
    result = machine.run(event)
    print(result)


def use_example():

    parser_handler = MachineParser('sm_description.yml')
    machine = parser_handler.parser()

    if not machine:
        return

    event: dict[str, int] = {"value": 50}
    result = machine.run(event)
    print(result)


if __name__ == "__main__":
    print("Serial...")
    use_example()
    print("\nParallel...")
    use_example_parallel()
