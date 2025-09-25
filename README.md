# State Machine for AI Agent Workflows

A flexible state machine implementation similar to AWS Step Functions, designed to orchestrate and coordinate AI agent workflows.

**⚠️ DEVELOPMENT STATUS**: This project is currently in active development and may not function correctly or functionality may be incomplete. APIs, interfaces, and functionality are subject to change without notice. Please do not use in production environments.

## Overview

This project provides a state machine framework that allows you to define, execute, and manage complex workflows involving AI agents. The state machine supports both programmatic definition (Python code) and declarative configuration (YAML files).

## Key Features

- **Lambda-based Architecture**: Execute custom functions at each state
- **Conditional Logic**: Natural language-like conditional statements with JSONPath support
- **Parallel Execution**: Run multiple workflows concurrently
- **YAML Configuration**: Define workflows declaratively
- **Timeout Handling**: Built-in protection for long-running operations

## Quick Start

1. Install [uv](https://docs.astral.sh/uv/getting-started/installation/)
2. Run: `$ uv run main.py`

## Simple Example

```python
from core.state_machine import StateMachine
from core.handlers.lambda_handler import Lambda
from core.handlers.choice_handler import Choice

# Define a simple workflow
machine_tree = [
    Lambda("process_data", "make_decision", "lambdas/example"),
    Choice("make_decision", [
        "when $.value gt 50 then 'high_value' else 'low_value'"
    ]),
    Lambda("high_value", None, "lambdas/example"),
    Lambda("low_value", None, "lambdas/example")
]

# Create and run the state machine
machine = StateMachine("simple_workflow", machine_tree)
result = machine.run({"value": 75})
```

### Using YAML Configuration

You can also define workflows using YAML files:

```yaml
entry: my-workflow

my-workflow:
  name: 'Simple Workflow'
  lambda_dir: lambdas/example
  tree:
    process-data: make-decision
    make-decision: $conditions
    high-value: null
    low-value: null
  states:
    process-data:
      name: process_data
      type: lambda
    make-decision:
      name: make_decision  
      type: choice
    high-value:
      name: high_value
      type: lambda
    low-value:
      name: low_value
      type: lambda
  vars:
    $conditions:
      - "when $.value gt 50 then #high-value else #low-value"
```

Load and execute:

```python
from core.parser_machine import StateMachineParser

parser = StateMachineParser('workflow.yml')
machine = parser.parse()
result = machine.run({"value": 75})
```

## Lambda Functions

Each lambda state corresponds to a function in the `lambdas/{name}/main.py` file:

```python
# lambdas/example/process_data/main.py
def lambda_handler(event, context):
    # Process the input event
    event["processed"] = True
    return event
```

## Documentation

For detailed documentation, examples, and advanced usage:

- **[📚 Complete Documentation](docs/)** - Comprehensive guides and references
- **[⚙️ YAML Configuration](docs/yaml-configuration.md)** - How to define workflows in YAML
- **[📝 Examples](docs/yaml-examples.md)** - Practical examples and use cases  
- **[🔧 API Reference](docs/api-reference.md)** - Technical API documentation

## Architecture

```
core/           # Core state machine implementation
lambdas/        # Lambda function implementations  
machines/       # Example configurations (Python & YAML)
docs/           # Complete documentation
tests/          # Test cases and validation
```

## Use Cases

- **Multi-agent Coordination**: Orchestrate communication between AI agents
- **Sequential Task Processing**: Define step-by-step workflows
- **Decision Trees**: Implement complex decision-making logic
- **Parallel Processing**: Execute multiple workflows simultaneously
- **Error Handling**: Implement retry mechanisms and graceful failures

## Contributing

This project is in active development. See the [documentation](docs/) for detailed information about the architecture and advanced features.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
