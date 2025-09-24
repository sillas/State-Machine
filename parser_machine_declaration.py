from typing import Any, Optional
from pathlib import Path
import yaml

from core.blocks.choice_handler import Choice
from core.blocks.lambda_handler import Lambda
from core.blocks.parallel_handler import ParallelHandler
from core.state_machine import StateMachine
from core.utils.state_base import State


def extract_hash_words(text: str) -> list[str]:
    """
    Extrai todas as palavras que começam com '#' de uma string.

    Args:
        text (str): A string de entrada

    Returns:
        list[str]: Lista com todas as palavras que começam com '#'
    """
    import re

    # Padrão regex para capturar palavras que começam com '#'
    # \# - corresponde ao caractere '#' literal
    # \w+ - corresponde a uma ou mais letras, dígitos ou underscore
    # \b - boundary word (garante que pegue palavras completas)
    pattern = r'#\w+(?:-\w+)*'

    matches = re.findall(pattern, text)
    return matches


def lambda_config(this_state: dict[str, Any], next_state: dict[str, Any] | None, lambda_dir: str, machine_tree: list[State]) -> None:

    name = this_state['name']
    lambda_full_path = f"{lambda_dir}/{name}/main.py"
    lambda_file_path = Path(lambda_full_path)

    if not lambda_file_path.exists():
        raise ModuleNotFoundError(f"Lambda {lambda_full_path} não encontrado.")

    cofig: dict[str, Any] = {
        "name": name,
        "next_state": next_state['name'] if next_state else None,
        "lambda_path": lambda_dir,
    }

    timeout = this_state.get('timeout')

    if timeout:
        cofig['timeout'] = int(timeout)

    machine_tree.append(Lambda(**cofig))


def choice_config(this_state: dict[str, Any], next_state: str, vars: dict[str, Any], states: dict[str, Any], machine_tree: list[State]) -> None:

    choice_name = this_state['name']
    statements = vars.get(next_state)

    if statements is None:
        raise ValueError(
            f"statements for choice {choice_name} does not exist!")

    print('---')
    for i in range(len(statements)):
        words = extract_hash_words(statements[i])
        for w in words:
            statements[i] = statements[i].replace(
                w, f"'{states[w[1:]]['name']}'")

    machine_tree.append(Choice(choice_name, statements))


def parallel_config(this_state: dict[str, Any], next_state: dict[str, Any] | None, definition: dict[str, Any] | None, machine_tree: list[State]) -> None:

    if definition is None:
        raise

    workflows = [
        parse_machine(definition[w])
        for w in this_state['workflows']
    ]
    machine_tree.append(ParallelHandler(
        name=this_state['name'],
        next_state=next_state['name'] if next_state else None,
        workflows=workflows
    ))


def parse_machine(machine: dict[str, Any], definition: Optional[dict[str, Any]] = None) -> StateMachine:

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
                states[next_state] if next_state else None,
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
                states,
                machine_tree
            )
            continue

        if state_type == 'parallel':
            parallel_config(
                this_state,
                states[next_state] if next_state else None,
                definition,
                machine_tree
            )
            continue

    return StateMachine(name, machine_tree)


def parser(machines_definitions: str) -> StateMachine | None:

    try:
        with open(machines_definitions, 'r') as file:
            data = yaml.safe_load(file)
            machine = data[data['entry']]
            return parse_machine(machine, data)

    except FileNotFoundError:
        print(f"Error: {machines_definitions} not found.")

    except yaml.YAMLError as e:
        print(f"Error parsing YAML: {e}")

    except KeyError as e:
        print(f"Key error! {str(e)}")

    except Exception as e:
        print(f"Error: {str(e)}")

    return None


def use_example_parallel():

    machine = parser('sm_p_description.yml')
    if not machine:
        return

    event: dict[str, int] = {"value": 50}
    result = machine.run(event)
    print(result)


def use_example():

    machine = parser('sm_description.yml')
    if not machine:
        return

    event: dict[str, int] = {"value": 50}
    result = machine.run(event)
    print(result)


if __name__ == "__main__":
    use_example()
    use_example_parallel()
