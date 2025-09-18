# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Potential Future Enhancements
- **Map Parallel Block**: Apply the same single Lambda function to items in a collection in parallel mode;
- **State Persistence**: Currently lacks state persistence for resuming workflows after failures;
- **Visualization**: Built-in tools for visualizing the state machine structure;
- **Monitoring**: Add observability features for long-running workflows;
- **Documentation**: Add more comprehensive guides;

## [1.1.0-alpha] - 2025-09-18

### Added
- New parallel execution block feature through `ParallelHandler` class
  - Allows running multiple state machine workflows concurrently
  - Automatically calculates and manages timeouts based on child workflows
  - Collects and aggregates results from all parallel workflows
  - Handles errors gracefully in individual workflows without stopping other executions
  - Available in `core/blocks/parallel_handler.py`

### Examples
- Added demonstration of parallel execution in `machines/example_machine.py`:
  - `example_parallel_machine()` function shows how to create and run parallel workflows
  - Supports running different Lambda functions concurrently

## [1.0.0] - Initial Release

### Features
- Core state machine implementation
- Basic state types and transitions
- Conditional (IF) blocks
- Lambda execution blocks
- JSON path query support
- Statement evaluation and conditional logic