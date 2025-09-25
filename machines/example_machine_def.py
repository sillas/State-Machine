
from time import sleep
from core.parser_machine import StateMachineParser


def use_example_parallel():
    """Run the example parallel state machine with a sample event."""

    parser_handler = StateMachineParser('machines/sm_p_description.yml')
    machine = parser_handler.parse()

    if not machine:
        return

    event: dict[str, int] = {"value": 50}
    result = machine.run(event)
    print(result)


def use_example():
    """Run the example serial state machine with a sample event."""

    parser_handler = StateMachineParser('machines/sm_description.yml')
    machine = parser_handler.parse()

    if not machine:
        return

    event: dict[str, int] = {"value": 50}
    result = machine.run(event)
    print("RESULT: ", result)


def main():
    print("Serial...")
    use_example()

    sleep(3)

    print("\nParallel...")
    use_example_parallel()
