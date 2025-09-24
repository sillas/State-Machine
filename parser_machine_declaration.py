from typing import Any
from pathlib import Path
import yaml

from core.blocks.choice_handler import Choice
from core.blocks.lambda_handler import Lambda
from core.state_machine import StateMachine


def lambda_config(this_state, next_state, lambda_dir, machine_tree) -> None:

    name = this_state['name']
    lambda_path = f"/{lambda_dir}/{name}"
    lambda_file_path = Path(f"{lambda_path}/main.py")

    if not lambda_file_path.exists():
        raise ModuleNotFoundError(f"Lambda {lambda_path} não encontrado.")

    cofig: dict[str, Any] = {
        "name": name,
        "next_state": next_state['name'],
        "lambda_path": lambda_path,
    }

    timeout = this_state.get('timeout')

    if timeout:
        cofig['timeout'] = int(timeout)

    machine_tree.append(Lambda(**cofig))


def choice_config(this_state, next_state, vars, machine_tree):

    choice_name = this_state['name']
    statements = vars.get(next_state)

    if statements is None:
        raise ValueError(
            f"statements for choice {choice_name} does not exist!")

    machine_tree.append(Choice(choice_name, statements))


def parse_machine(machine: dict) -> StateMachine:

    name = machine['name']
    lambda_dir = machine['lambda_dir']
    tree = machine['tree']
    states = machine['states']
    vars = machine.get('vars')

    machine_tree = []

    for state, next_state in tree.items():

        this_state = states[state]
        state_type = this_state['type']

        if state_type == 'lambda':
            lambda_config(
                this_state,
                states[next_state],
                lambda_dir,
                machine_tree
            )
            continue

        if state_type == 'choice':

            if vars is None:
                raise ValueError(f"'vars' does not exist for machine {name}")

            choice_config(
                this_state,
                next_state,
                vars,
                machine_tree
            )
            continue

    return StateMachine(name, machine_tree)


def parser(machines_definitions: str):

    try:
        with open(machines_definitions, 'r') as file:
            data = yaml.safe_load(file)

            for key in data.keys():
                return parse_machine(data[key])

    except FileNotFoundError:
        print(f"Error: {machines_definitions} not found.")

    except yaml.YAMLError as e:
        print(f"Error parsing YAML: {e}")


if __name__ == "__main__":
    parser('sm_description.yml')
