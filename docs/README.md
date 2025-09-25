# State Machine Documentation

This folder contains detailed documentation for the State Machine project.

## Contents

- [YAML Definition](yaml-configuration.md) - How to define state machines using YAML files
- [YAML Examples](yaml-examples.md) - Practical examples and use cases
- [API Reference](api-reference.md) - Technical API documentation

## Overview

The State Machine supports two forms of definition:

1. **Programmatic** - Defining machines directly in Python
2. **Declarative** - Using YAML files for configuration

The documentation in this folder focuses on the declarative approach using YAML, which offers:

- Clear separation between logic and configuration
- Component reusability
- Ease of maintenance
- Workflow versioning

## How to Use

1. Define your state machine in a YAML file
2. Use the `StateMachineParser` to load it
3. Implement the necessary lambda functions
4. Execute using [your_machine].run(input_data)

Consult the specific documents for complete details.