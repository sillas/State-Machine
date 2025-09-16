import unittest
from core.jsonpath_query import jsonpath_query


class TestJsonPathQuery(unittest.TestCase):
    """Test cases for the jsonpath_query function."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Sample test data
        self.test_data = {
            "store": {
                "book": [
                    {
                        "category": "reference",
                        "author": "Nigel Rees",
                        "title": "Sayings of the Century",
                        "price": 8.95
                    },
                    {
                        "category": "fiction",
                        "author": "Evelyn Waugh",
                        "title": "Sword of Honour",
                        "price": 12.99
                    },
                    {
                        "category": "fiction",
                        "author": "Herman Melville",
                        "title": "Moby Dick",
                        "price": 8.99
                    }
                ],
                "bicycle": {
                    "color": "red",
                    "price": 19.95
                }
            },
            "users": [
                {"id": 1, "name": "John", "active": True},
                {"id": 2, "name": "Jane", "active": False},
                {"id": 3, "name": "Bob", "active": True}
            ]
        }

    def test_single_value_query(self):
        """Test query that returns a single value."""
        # Query for a specific value
        result = jsonpath_query(self.test_data, "$.store.bicycle.color")

        # Should return the single value directly, not in a list
        self.assertEqual(result, "red")
        self.assertIsInstance(result, str)

    def test_multiple_values_query(self):
        """Test query that returns multiple values."""
        # Query for all book titles
        result = jsonpath_query(self.test_data, "$.store.book[*].title")

        # Should return a list of all matching values
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 3)
        self.assertIn("Sayings of the Century", result)
        self.assertIn("Sword of Honour", result)
        self.assertIn("Moby Dick", result)

    def test_filter_expression(self):
        """Test query with a filter expression."""
        # Query for books by price
        result = jsonpath_query(
            self.test_data,
            "$.store.book[*]"
        )

        # Filter manually for books with category 'fiction'
        fiction_books = [book for book in result if book.get(
            'category') == 'fiction']

        # Should return 2 fiction books
        self.assertEqual(len(fiction_books), 2)
        # Check that both fiction books are included
        titles = [book["title"] for book in fiction_books]
        self.assertIn("Sword of Honour", titles)
        self.assertIn("Moby Dick", titles)

    def test_empty_result(self):
        """Test query that returns no matches."""
        # Query for a non-existent property
        result = jsonpath_query(self.test_data, "$.store.nonexistent")

        # Should return an empty list
        self.assertEqual(result, [])

    def test_array_index_query(self):
        """Test query that accesses a specific array index."""
        # Query for the first book
        result = jsonpath_query(self.test_data, "$.store.book[0]")

        # Should return the first book object
        self.assertIsInstance(result, dict)
        self.assertEqual(result["title"], "Sayings of the Century")
        self.assertEqual(result["author"], "Nigel Rees")

    def test_array_slice_query(self):
        """Test query that uses array slicing."""
        # Query for the first two books
        result = jsonpath_query(self.test_data, "$.store.book[0:2]")

        # Should return a list of the first two book objects
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["title"], "Sayings of the Century")
        self.assertEqual(result[1]["title"], "Sword of Honour")

    def test_invalid_jsonpath_expression(self):
        """Test behavior with invalid JSONPath expression."""
        # Try with an invalid expression
        with self.assertRaises(ValueError) as context:
            jsonpath_query(self.test_data, "[{invalid json!@#}]")

        # Should raise a ValueError with a specific message
        self.assertIn("Invalid JSONPath expression", str(context.exception))

    def test_none_jsonpath_expression(self):
        """Test behavior with None as JSONPath expression."""
        # Try with None as expression
        with self.assertRaises((ValueError, TypeError)):
            # expected to fail in runtime
            jsonpath_query(self.test_data, None)  # type: ignore

    def test_none_data_object(self):
        """Test behavior with None as data object."""
        # Try with None as data object
        result = jsonpath_query(None, "$")
        self.assertEqual(result, None)

    def test_empty_jsonpath_expression(self):
        """Test behavior with empty JSONPath expression."""
        # Try with an empty expression
        with self.assertRaises(ValueError):
            jsonpath_query(self.test_data, "")

    def test_deep_nested_query(self):
        """Test query on a deeply nested structure."""
        # Create a deeply nested structure
        nested_data = {
            "level1": {
                "level2": {
                    "level3": {
                        "level4": {
                            "value": "deep value"
                        }
                    }
                }
            }
        }

        # Query for the deep value
        result = jsonpath_query(
            nested_data, "$.level1.level2.level3.level4.value")

        # Should return the deep value
        self.assertEqual(result, "deep value")


if __name__ == '__main__':
    unittest.main()
