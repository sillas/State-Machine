# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0-alpha] - 2025-09-23

### Added
- **Add Choice Block with Advanced Conditional Logic**
  - Natural language-like conditional statements with comprehensive operator support
  - New comparison operators: `gt`, `lt`, `eq`, `neq`, `gte`, `lte`, `contains`, `starts_with`, `ends_with`
  - Boolean logic operators: `and`, `or`, `not` with proper precedence handling
  - Support for parentheses grouping in complex conditions
  - When-then-else and if-elif-else like statement syntax for conditional branching
  - Nested conditional evaluations with fallback logic

- **Advanced Data Type Support in Choice Conditions**
  - JSONPath expressions for dynamic data extraction (`$.user.name`, `$.items[0]`)
  - Literal string parsing with proper quote handling
  - Numeric value support (integers and floats)
  - Empty list detection and comparison (`[]`)
  - List parsing and evaluation capabilities
  - Custom condition parsers architecture for extensibility

- **Robust Condition Evaluation Engine**
  - Multi-statement evaluation with first-match priority
  - Exception handling for malformed conditions with graceful degradation
  - Support for complex nested expressions
  - Whitespace and formatting tolerance in condition strings
  - Comprehensive error reporting for debugging

### Enhanced
- **Choice Handler Architecture**
  - Modular parser system in `core/utils/parsers.py` for different data types
  - Improved condition parsing with recursive evaluation support
  - Better separation of concerns between parsing and evaluation logic
  - Enhanced performance through parser caching and optimization

### Examples
- Updated `machines/example_machine.py` with advanced Choice usage demonstrations
- Comprehensive test coverage in `tests/core/block/test_choice_handler.py` showing all new features
- Real-world examples of complex conditional logic patterns

## [1.1.0-alpha] - 2025-09-18

### Added
- New parallel execution block feature through `Parallel` class
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