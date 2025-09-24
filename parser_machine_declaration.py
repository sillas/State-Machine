from typing import Any
import yaml

from core.blocks.lambda_handler import Lambda


def lambda_config(this_state, next_state, lambda_dir, machine_tree) -> None:

    name = this_state['name']

    cofig: dict[str, Any] = {
        "name": name,
        "next_state": next_state['name'],
        "lambda_path": f"{lambda_dir}/{name}",
    }

    timeout = this_state.get('timeout')

    if timeout:
        cofig['timeout'] = int(timeout)

    machine_tree.append(Lambda(**cofig))


def parse_machine(machine: dict):

    name = machine['name']
    lambda_dir = machine['lambda_dir']
    tree = machine['tree']
    states = machine['states']
    vars = machine.get('vars')

    machine_tree = []

    for state, next_state in tree.items():
        this_state = states[state]

        if this_state['type'] == 'lambda':
            lambda_config(
                this_state,
                states[next_state],
                lambda_dir,
                machine_tree
            )

            # next_state = states[next_state]['name']

            # cofig: dict[str, Any] = {
            #     "name": state_def['name'],
            #     "next_state": next_state,
            #     "lambda_path": f"{lambda_dir}/{name}",
            # }

            # timeout = state_def.get('timeout')

            # if timeout:
            #     cofig['timeout'] = int(timeout)

            # machine_tree.append(Lambda(**cofig))
            continue


def parser(machines_definitions: str):

    try:
        with open(machines_definitions, 'r') as file:
            data = yaml.safe_load(file)

            for key in data.keys():
                machine = parse_machine(data[key])

    except FileNotFoundError:
        print(f"Error: {machines_definitions} not found.")

    except yaml.YAMLError as e:
        print(f"Error parsing YAML: {e}")


if __name__ == "__main__":
    parser('sm_description.yml')
