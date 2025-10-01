# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.0.0-alpha] - 2025-10-01

### Added
- **Intelligent Function Caching System for Choice Handler**
  - Dynamic code generation with hash-based validation (`CacheHandler` class)
  - Automatic cache invalidation when conditions change
  - Persistent function caching in `conditions_cache/` directory with metadata
  - `clear_all_cache()` method for testing and cache management
  - Cache file cleanup for outdated versions of the same choice

- **Enhanced JSONPath Integration**
  - `create_jsonpath_wrapper()` utility for seamless data extraction
  - Automatic parameter mapping from JSONPath expressions to function parameters
  - `build_jsonpath_params_mapping()` for consistent parameter name generation
  - Improved handling of complex nested JSONPath expressions

- **Advanced Condition Parser Architecture**
  - Modular operator handling with dedicated methods:
    - `_handle_contains_operator()` for membership testing
    - `_handle_string_operators()` for `starts_with` and `ends_with`
    - `_handle_comparison_operators()` for numeric comparisons
  - `add_constants_or_literals()` for literal string and constant detection
  - Better support for literal strings as return values (not just state references)
  - Enhanced parsing of nested when-then-else statements

- **New Exception Handling**
  - `ChoiceInitializationError` exception for better error tracking
  - Improved error messages with context about cache and parsing failures

### Changed
- **Choice Handler Refactoring**
  - Removed deprecated `_data` and `_operations` attributes
  - Moved initialization logic to private `_initialize_handler()` method
  - Simplified constructor with clearer separation of concerns
  - Handler now properly raises exceptions instead of generic errors

- **Parser Module Improvements**
  - Reorganized `core/utils/parser.py` with clearer class structure
  - `ConditionParser` now accepts `CacheHandler` instance for better encapsulation
  - Improved operator substitution with regex-based patterns
  - Better handling of edge cases in JSONPath conversion
  - Enhanced `_op_substitution()` method split into focused helper methods

- **Logging System Overhaul**
  - Renamed logging functions for clarity: `_i` → `info`, `_e` → `error`, `_w` → `warning`
  - Fixed typo: `warnning_message` → `warning_message`
  - Consistent logging across `StateMachine`, `Choice`, and parser modules
  - Improved log messages with execution timing and state transitions

- **State Machine Execution**
  - Enhanced logging format with clear entry/exit markers (`>>>` and `<<<`)
  - Added execution duration tracking for each state
  - Better timeout error messages with execution context
  - Improved final output logging with total duration

### Enhanced
- **Code Organization**
  - Removed deprecated `choice_handler_deprecated.py` file
  - Removed obsolete `parsers.py` parser classes (integrated into main parser)
  - Consolidated all condition parsing logic in `core/utils/parser.py`
  - Improved imports organization across all modules

- **Lambda Handler Improvements**
  - Updated file path construction to use `Path` objects
  - More robust path handling with `pathlib.Path`

- **Parser Machine Updates**
  - Better error context in state processing
  - Improved lambda path construction using `Path` objects
  - Enhanced error messages for debugging

### Fixed
- **Operator Parsing Issues**
  - Fixed `contains` operator to properly swap operands (X contains Y → Y in X)
  - Improved regex patterns for string operators
  - Better handling of whitespace in operator detection

- **Statement Processing**
  - Fixed literal string detection in statement returns
  - Improved nested statement parsing with proper condition extraction
  - Better handling of `else` clauses in complex nested conditions

- **Cache Management**
  - Fixed duplicate parameter handling in JSONPath mapping
  - Improved hash generation for cache validation
  - Better cleanup of old cache files

### Performance
- **Caching Benefits**
  - Reduced parsing overhead through intelligent function caching
  - Faster condition evaluation with pre-compiled cached functions
  - Eliminated redundant parsing for identical choice configurations

### Documentation
- Updated inline documentation for new `CacheHandler` class
- Improved docstrings for parser utility functions
- Enhanced comments explaining cache mechanisms

### Testing
- Updated test suite to work with new caching system
- Added `test_cache_substitution()` to verify cache invalidation
- Enhanced test coverage for literal strings and complex conditions
- All tests passing with new architecture

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