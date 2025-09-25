import unittest
from unittest.mock import patch, MagicMock

from core.handlers.choice_handler import Choice, OPERATORS
from core.utils.state_base import StateType


class TestChoice(unittest.TestCase):
    """Test cases for the Choice class."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create test statements for various scenarios
        self.test_statements = [
            "when $.user.age gt 18 then 'adult'",
            "when $.price gte 100 then 'expensive' else 'cheap'",
            "when $.empty_list eq [] then 'empty'",
            "'default_value'"
        ]

        # Create a Choice instance for testing
        self.choice = Choice(
            name="test_choice",
            statements=self.test_statements
        )

        # Test data for evaluations
        self.test_data = {
            "user": {
                "name": "João Silva",
                "age": 25,
                "items": ["apple", "banana"]
            },
            "price": 150,
            "empty_list": []
        }

    def test_initialization(self):
        """Test Choice initialization and parameter validation."""
        # Verify attributes are correctly initialized
        self.assertEqual(self.choice.name, "test_choice")
        self.assertEqual(self.choice.type, StateType.CHOICE.value)
        self.assertEqual(self.choice.next_state, None)
        self.assertEqual(self.choice.timeout, 1)
        self.assertEqual(self.choice._operations, self.test_statements)

    def test_operators_dictionary(self):
        """Test that all operators work correctly."""
        # Test greater than
        self.assertTrue(OPERATORS[' gt '](10, 5))
        self.assertFalse(OPERATORS[' gt '](5, 10))

        # Test less than
        self.assertTrue(OPERATORS[' lt '](5, 10))
        self.assertFalse(OPERATORS[' lt '](10, 5))

        # Test equal
        self.assertTrue(OPERATORS[' eq '](5, 5))
        self.assertFalse(OPERATORS[' eq '](5, 10))

        # Test not equal
        self.assertTrue(OPERATORS[' neq '](5, 10))
        self.assertFalse(OPERATORS[' neq '](5, 5))

        # Test greater than or equal
        self.assertTrue(OPERATORS[' gte '](10, 10))
        self.assertTrue(OPERATORS[' gte '](10, 5))
        self.assertFalse(OPERATORS[' gte '](5, 10))

        # Test less than or equal
        self.assertTrue(OPERATORS[' lte '](5, 5))
        self.assertTrue(OPERATORS[' lte '](5, 10))
        self.assertFalse(OPERATORS[' lte '](10, 5))

        # Test contains
        self.assertTrue(OPERATORS[' contains ']("hello world", "world"))
        self.assertFalse(OPERATORS[' contains ']("hello", "world"))

        # Test starts_with
        self.assertTrue(OPERATORS[' starts_with ']("hello world", "hello"))
        self.assertFalse(OPERATORS[' starts_with ']("hello world", "world"))

        # Test ends_with
        self.assertTrue(OPERATORS[' ends_with ']("hello world", "world"))
        self.assertFalse(OPERATORS[' ends_with ']("hello world", "hello"))

    @patch('core.utils.parsers.PARSERS')
    def test_handler_execution(self, mock_parsers):
        """Test successful handler execution with mocked parsers."""
        # Mock parser to simulate JSONPath evaluation
        mock_parser_instance = MagicMock()
        mock_parser_instance.can_parse.return_value = True
        mock_parser_instance.parse.return_value = 25  # Age value

        mock_parser_class = MagicMock(return_value=mock_parser_instance)
        mock_parsers.__iter__.return_value = [mock_parser_class]

        # Create context
        context = {}

        # Execute handler
        result = self.choice.handler(self.test_data, context)

        # Verify results
        # Handler returns original event
        self.assertEqual(result, self.test_data)
        self.assertIn("timestamp", context)
        self.assertIsInstance(context["timestamp"], float)
        self.assertIsNotNone(self.choice.next_state)

    def test_evaluate_simple_condition(self):
        """Test evaluation of simple conditions."""
        # Mock the data
        self.choice._data = self.test_data

        # Test direct value evaluation
        with patch.object(self.choice, '_parse_condition', return_value=True):
            result = self.choice._evaluate(["simple_condition"])
            self.assertTrue(result)

    def test_evaluate_when_then_else(self):
        """Test evaluation of when-then-else statements."""
        self.choice._data = self.test_data

        # Test when condition is true
        with patch.object(self.choice, '_parse_condition') as mock_parse:
            # condition=True, then='adult'
            mock_parse.side_effect = [True, 'adult']
            result = self.choice._evaluate(
                ["when condition then 'adult' else 'minor'"])
            self.assertEqual(result, 'adult')

        # Test when condition is false with else clause
        with patch.object(self.choice, '_parse_condition') as mock_parse:
            # condition=False, else='minor'
            mock_parse.side_effect = [False, 'minor']
            result = self.choice._evaluate(
                ["when condition then 'adult' else 'minor'"])
            self.assertEqual(result, 'minor')

    def test_evaluate_multiple_operations(self):
        """Test evaluation with multiple operations."""
        self.choice._data = self.test_data

        # Test first condition matches
        with patch.object(self.choice, '_parse_condition') as mock_parse:
            mock_parse.side_effect = [True, 'first_match']
            operations = ["when condition1 then 'first_match'",
                          "when condition2 then 'second_match'"]
            result = self.choice._evaluate(operations)
            self.assertEqual(result, 'first_match')

    def test_parse_condition_with_parentheses(self):
        """Test parsing conditions with parentheses."""
        # Test basic parentheses removal
        condition = "($.user.age gt 18)"
        extracted = self.choice._extract_parentheses_content(condition)
        self.assertEqual(extracted, "$.user.age gt 18")

        # Test condition with logical operators (should not remove parentheses)
        condition_with_logic = "($.user.age gt 18 and $.user.name eq 'João')"
        extracted_logic = self.choice._extract_parentheses_content(
            condition_with_logic)
        self.assertEqual(extracted_logic, condition_with_logic)

    def test_parse_condition_not_operator(self):
        """Test parsing conditions with NOT operator."""
        # Test with actual NOT logic without mocking the method itself
        with patch('core.handlers.choice_handler.PARSERS') as mock_parsers:
            mock_parser_instance = MagicMock()
            mock_parser_instance.can_parse.return_value = True
            mock_parser_instance.parse.return_value = False  # Condition evaluates to False

            mock_parser_class = MagicMock(return_value=mock_parser_instance)
            mock_parsers.__iter__.return_value = [mock_parser_class]

            result = self.choice._parse_condition("not condition")
            self.assertTrue(result)  # NOT False = True

    def test_parse_condition_logical_operators(self):
        """Test parsing conditions with AND/OR operators."""
        # Test AND operator
        with patch('core.handlers.choice_handler.PARSERS') as mock_parsers:
            mock_parser_instance = MagicMock()
            mock_parser_instance.can_parse.return_value = True
            mock_parser_instance.parse.side_effect = [
                True, True]  # Both conditions true

            mock_parser_class = MagicMock(return_value=mock_parser_instance)
            mock_parsers.__iter__.return_value = [mock_parser_class]

            result = self.choice._parse_condition("condition1 and condition2")
            self.assertTrue(result)

        # Test OR operator
        with patch('core.handlers.choice_handler.PARSERS') as mock_parsers:
            mock_parser_instance = MagicMock()
            mock_parser_instance.can_parse.return_value = True
            mock_parser_instance.parse.side_effect = [
                False, True]  # First false, second true

            mock_parser_class = MagicMock(return_value=mock_parser_instance)
            mock_parsers.__iter__.return_value = [mock_parser_class]

            result = self.choice._parse_condition("condition1 or condition2")
            self.assertTrue(result)

    def test_parse_condition_comparison_operators(self):
        """Test parsing conditions with comparison operators."""
        with patch.object(self.choice, '_parse_condition') as mock_parse:
            # Mock the recursive calls for left and right operands
            mock_parse.side_effect = [25, 18]  # left=25, right=18

            # Test with gt operator
            result = self.choice._parse_condition("left gt right")
            self.assertTrue(result)

    def test_parse_condition_with_parsers(self):
        """Test parsing conditions using external parsers."""
        # Create a simple condition that will trigger parser usage
        condition = "test_condition"

        # Mock the PARSERS list directly in the choice_handler module
        with patch('core.handlers.choice_handler.PARSERS') as mock_parsers:
            mock_parser_instance = MagicMock()
            mock_parser_instance.can_parse.return_value = True
            mock_parser_instance.parse.return_value = "parsed_value"

            mock_parser_class = MagicMock(return_value=mock_parser_instance)
            mock_parsers.__iter__.return_value = [mock_parser_class]

            result = self.choice._parse_condition(condition)
            self.assertEqual(result, "parsed_value")

            # Verify parser was called correctly
            mock_parser_class.assert_called_with(condition)
            mock_parser_instance.can_parse.assert_called_once()
            mock_parser_instance.parse.assert_called_once_with(self.choice)

    def test_parse_condition_empty_or_none(self):
        """Test parsing with empty or None conditions."""
        # Test None condition
        with self.assertRaises(ValueError):
            self.choice._parse_condition(None)

        # Test empty condition
        with self.assertRaises(ValueError):
            self.choice._parse_condition("")

    def test_parse_condition_invalid_not(self):
        """Test parsing with invalid NOT condition."""
        with self.assertRaises(ValueError):
            self.choice._parse_condition("not ")

    def test_evaluate_with_exceptions(self):
        """Test evaluation handling exceptions gracefully."""
        self.choice._data = self.test_data

        # Test that exceptions are caught and operation continues
        with patch.object(self.choice, '_parse_condition', side_effect=Exception("Test error")):
            operations = ["invalid_operation", "'fallback_value'"]
            # Should skip the invalid operation and return None since no valid operations found
            result = self.choice._evaluate(operations)
            self.assertIsNone(result)

    def test_evaluate_empty_operations(self):
        """Test evaluation with empty or whitespace operations."""
        self.choice._data = self.test_data

        # Test with empty strings and whitespace
        operations = ["", "   ", "when condition then 'result'"]
        with patch.object(self.choice, '_parse_condition') as mock_parse:
            mock_parse.side_effect = [True, 'result']
            result = self.choice._evaluate(operations)
            self.assertEqual(result, 'result')

    def test_evaluate_no_matching_conditions(self):
        """Test evaluation when no conditions match."""
        self.choice._data = self.test_data

        with patch.object(self.choice, '_parse_condition', return_value=False):
            operations = ["when condition1 then 'result1'",
                          "when condition2 then 'result2'"]
            result = self.choice._evaluate(operations)
            self.assertIsNone(result)

    def test_choice_with_real_data_scenario(self):
        """Test Choice with a realistic data scenario."""
        # Test data similar to the example in the original code
        test_data = {
            "user": {
                "name": "Jonas Silva",
                "age": 37,
                "items": ["apple", "banana"]
            },
            "price": 170,
            "empty_list": []
        }

        # Create choice with realistic operations
        operations = [
            "when price gte 100 then 'expensive'",
            "when empty_list eq [] then 'list is empty'",
            "'default value'"
        ]

        choice = Choice(name="real_test", statements=operations)
        choice._data = test_data

        # Mock parser behavior for price comparison
        with patch('core.handlers.choice_handler.PARSERS') as mock_parsers:
            mock_parser_instance = MagicMock()
            mock_parser_instance.can_parse.return_value = True

            # Setup mock to return values for price and the literal '100'
            mock_parser_instance.parse.side_effect = [
                170, 100, 'expensive']  # price, 100, then result

            mock_parser_class = MagicMock(return_value=mock_parser_instance)
            mock_parsers.__iter__.return_value = [mock_parser_class]

            result = choice._evaluate(operations[:1])  # Test first operation
            self.assertEqual(result, 'expensive')


if __name__ == '__main__':
    unittest.main()
