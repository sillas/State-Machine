import yaml

from parser import parse_cond
from logger import _e


def load_yml(machine_definitions_file: str):
    """Load and return data from the given machine definitions YAML file."""
    try:
        with open(machine_definitions_file, 'r') as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        _e(f"Error: {machine_definitions_file} not found.")
        raise
    except yaml.YAMLError as e:
        _e(f"Error parsing YAML: {e}")
        raise
    except KeyError as e:
        _e(f"Key error! {str(e)}")
        raise
    except Exception as e:
        _e(f"Error: {str(e)}")
        raise


def main():
    definition = load_yml("test-cache/example.yml")
    machine_def = definition[definition["entry"]]
    parse_cond(
        "premium-decision",
        machine_def['vars']['$premium-conditions'],
        machine_def['states']
    )


if __name__ == "__main__":
    main()
