# API Reference - YAML Parser

This document describes the YAML parser API for loading and executing state machines defined in YAML files.

## StateMachineParser

Main class for loading and converting YAML definitions into executable `StateMachine` objects.

### Constructor

```python
from core.parser_machine import StateMachineParser

parser = StateMachineParser(machine_definitions_file: str)
```

**Parameters:**
- `machine_definitions_file`: Path to the YAML file with the definitions

**Example:**
```python
parser = StateMachineParser('machines/sm_description.yml')
```

### Methods

#### `parse() -> StateMachine`

Converts the loaded YAML definitions into an executable `StateMachine` object.

**Return:** `StateMachine` instance ready for execution

**Example:**
```python
parser = StateMachineParser('machines/sm_description.yml')
machine = parser.parse()

if machine:
    result = machine.run({"value": 50})
    print(result)
```

#### `parse_machine(machine_config: dict) -> StateMachine`

Converts a specific machine configuration into a `StateMachine` object. Used internally and for parsing sub-machines in parallel states.

For direct usage, analyze the example in `machines/example_machine.py`

**Parameters:**
- `machine_config`: Dictionary with machine configuration

**Return:** `StateMachine` instance

## StateConfigurationProcessor

Internal class that processes state configurations and builds execution blocks.

### Supported State Types

#### 1. Lambda State

Executes an external lambda function:

```yaml
states:
  my-state:
    name: function_name
    type: lambda
    timeout: 30  # optional
```

**Processing:**
- Checks if lambda file exists at `{lambda_dir}/{name}/main.py`
- Creates `Lambda` instance with appropriate configurations
- Applies timeout if specified

#### 2. Choice State

Executes conditional logic:

```yaml
states:
  decision:
    name: decision_name
    type: choice
```

**Processing:**
- Resolves condition variables
- Substitutes hash references (`#state`) with real names
- Creates `Choice` instance with processed conditions

#### 3. Parallel State

Executes multiple workflows simultaneously:

```yaml
states:
  parallel:
    name: parallel_execution
    type: parallel
    workflows:
      - workflow-1
      - workflow-2
```

**Processing:**
- Creates `StateMachine` for each listed workflow
- Configures parallel execution via `Parallel`

## Complete Usage Example

```python
from core.parser_machine import StateMachineParser
import logging

# Configure logging to see progress
logging.basicConfig(level=logging.INFO)

def execute_yaml_workflow():
    try:
        # Load definitions from YAML file
        parser = StateMachineParser('machines/sm_description.yml')
        
        # Convert to executable StateMachine
        machine = parser.parse()
        
        if not machine:
            print("Error: could not load the machine")
            return
        
        # Prepare input data
        event = {
            "value": 25,
            "user": {"name": "John", "age": 30}
        }
        
        # Execute the workflow
        result = machine.run(event)
        
        print(f"Final result: {result}")
        
    except FileNotFoundError:
        print("YAML file not found")
    except Exception as e:
        print(f"Error during execution: {e}")

# Execute
execute_yaml_workflow()
```

## Validation and Error Handling

The parser includes robust validation:

### Common Errors

1. **File not found:**
```python
FileNotFoundError: Error: machines/file.yml not found.
```

2. **Invalid YAML:**
```python
yaml.YAMLError: Error parsing YAML: ...
```

3. **State not found:**
```python
KeyError: State key not found: state-name
```

4. **Lambda not found:**
```python
ModuleNotFoundError: Lambda lambdas/example/function/main.py not found.
```

5. **Condition variable not found:**
```python
ValueError: Conditions for choice choice_name do not exist!
```

### Debug Strategies

```python
import logging

# Enable detailed logs
logging.basicConfig(level=logging.DEBUG)

# Create parser with logs
parser = StateMachineParser('machines/problem.yml')

try:
    machine = parser.parse()
    result = machine.run({"test": True})
except Exception as e:
    logging.error(f"Detailed error: {e}")
    # Analyze logs to identify the problem
```

## Integration with Python Code

### Using with programmatic definition:

```python
from core.parser_machine import StateMachineParser
from core.state_machine import StateMachine
from core.handlers.lambda_handler import Lambda

def hybrid_workflow():
    # Load part of the workflow from YAML
    parser = StateMachineParser('machines/part1.yml')
    part1 = parser.parse()
    
    # Create additional part programmatically  
    part2 = StateMachine("part2", [
        Lambda("process_result", None, "lambdas/custom")
    ])
    
    # Combine or execute sequentially
    result1 = part1.run({"input": "data"})
    final_result = part2.run(result1)
    
    return final_result
```

### Creating Custom Parser:

```python
from core.parser_machine import StateMachineParser

class MyParser(StateMachineParser):
    def __init__(self, yaml_file, extra_configurations=None):
        super().__init__(yaml_file)
        self.extra_configurations = extra_configurations or {}
    
    def parse(self):
        machine = super().parse()
        # Apply extra configurations
        if self.extra_configurations.get('global_timeout'):
            # Apply global timeout
            pass
        return machine
```

## Performance and Optimization

### Parsing Cache

```python
import functools
from core.parser_machine import StateMachineParser

@functools.lru_cache(maxsize=10)
def get_cached_machine(yaml_file):
    parser = StateMachineParser(yaml_file)
    return parser.parse()

# Usage with cache
machine = get_cached_machine('machines/frequent.yml')
```

### Prior Validation

```python
def validate_yaml_before_execution(yaml_file):
    try:
        parser = StateMachineParser(yaml_file)
        machine = parser.parse()
        return True, "Valid YAML"
    except Exception as e:
        return False, f"Validation error: {e}"

# Validate before using in production
valid, message = validate_yaml_before_execution('machines/production.yml')
if valid:
    # Proceed with execution
    pass
```

## Known Limitations

1. **Circular references**: The parser does not yet detect infinite loops in workflows
2. **Schema validation**: There is no formal YAML schema validation yet
3. **Variable substitution**: Limited to `$variable` (choice) and `#state` (states) patterns
4. **Nesting**: Does not support nested (sequential) machine definitions in the same yml file

## Next Steps

- Consult [YAML Configuration](yaml-configuration.md) for detailed syntax
- See [YAML Examples](yaml-examples.md) for practical use cases
- Examine the example files in `machines/` for reference