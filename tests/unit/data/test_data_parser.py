"""
Unit tests for data_parser module.
"""

import pytest
from pdf_merger.data_parser import (
    split_serial_numbers,
    normalize_serial_number,
    deduplicate_serial_numbers
)


class TestSplitSerialNumbers:
    """Test cases for split_serial_numbers function."""
    
    def test_parse_single_serial_number(self):
        """Test parsing a single serial number."""
        result = split_serial_numbers("GRNW_000103851")
        assert result == ["GRNW_000103851"]
    
    def test_parse_multiple_serial_numbers(self):
        """Test parsing multiple comma-separated serial numbers."""
        result = split_serial_numbers("GRNW_000103851,GRNW_000103852,GRNW_000103853")
        assert result == ["GRNW_000103851", "GRNW_000103852", "GRNW_000103853"]
    
    def test_parse_with_whitespace(self):
        """Test parsing serial numbers with whitespace."""
        result = split_serial_numbers("GRNW_000103851 , GRNW_000103852 , GRNW_000103853")
        assert result == ["GRNW_000103851", "GRNW_000103852", "GRNW_000103853"]
    
    def test_parse_empty_string(self):
        """Test parsing an empty string."""
        result = split_serial_numbers("")
        assert result == []
    
    def test_parse_whitespace_only(self):
        """Test parsing a string with only whitespace."""
        result = split_serial_numbers("   ")
        assert result == []
    
    def test_parse_with_empty_elements(self):
        """Test parsing with empty elements between commas."""
        result = split_serial_numbers("GRNW_000103851,,GRNW_000103852, ,GRNW_000103853")
        assert result == ["GRNW_000103851", "GRNW_000103852", "GRNW_000103853"]
    
    def test_parse_none_input(self):
        """Test parsing None input (should return empty list)."""
        result = split_serial_numbers(None)
        assert result == []
    
    def test_parse_lowercase_serial_numbers(self):
        """Test parsing lowercase serial numbers."""
        result = split_serial_numbers("grnw_000103851,grnw_000103852")
        assert result == ["grnw_000103851", "grnw_000103852"]
    
    def test_parse_mixed_case_serial_numbers(self):
        """Test parsing mixed case serial numbers."""
        result = split_serial_numbers("GRNW_000103851,grnw_000103852")
        assert result == ["GRNW_000103851", "grnw_000103852"]


class TestNormalizeSerialNumber:
    """Test cases for normalize_serial_number function."""
    
    def test_normalize_lowercase_to_uppercase(self):
        """Test normalizing lowercase prefix to uppercase."""
        result = normalize_serial_number("grnw_000103851", to_uppercase=True)
        assert result == "GRNW_000103851"
    
    def test_normalize_uppercase_stays_uppercase(self):
        """Test that uppercase prefix remains uppercase."""
        result = normalize_serial_number("GRNW_000103851", to_uppercase=True)
        assert result == "GRNW_000103851"
    
    def test_normalize_uppercase_to_lowercase(self):
        """Test normalizing uppercase prefix to lowercase."""
        result = normalize_serial_number("GRNW_000103851", to_uppercase=False)
        assert result == "grnw_000103851"
    
    def test_normalize_lowercase_stays_lowercase(self):
        """Test that lowercase prefix remains lowercase."""
        result = normalize_serial_number("grnw_000103851", to_uppercase=False)
        assert result == "grnw_000103851"
    
    def test_normalize_preserves_suffix(self):
        """Test that numeric suffix is preserved unchanged."""
        result = normalize_serial_number("grnw_000103851", to_uppercase=True)
        assert result == "GRNW_000103851"
        assert result.endswith("000103851")
    
    def test_normalize_with_whitespace(self):
        """Test normalizing serial number with whitespace."""
        result = normalize_serial_number("  grnw_000103851  ", to_uppercase=True)
        assert result == "GRNW_000103851"
    
    def test_normalize_empty_string(self):
        """Test normalizing empty string."""
        result = normalize_serial_number("", to_uppercase=True)
        assert result == ""
    
    def test_normalize_none(self):
        """Test normalizing None input."""
        result = normalize_serial_number(None, to_uppercase=True)
        assert result is None


class TestDeduplicateSerialNumbers:
    """Test cases for deduplicate_serial_numbers function."""
    
    def test_deduplicate_preserve_order(self):
        """Test deduplication preserving order."""
        result = deduplicate_serial_numbers(
            ["GRNW_000103851", "GRNW_000103852", "GRNW_000103851", "GRNW_000103853"],
            preserve_order=True
        )
        assert result == ["GRNW_000103851", "GRNW_000103852", "GRNW_000103853"]
    
    def test_deduplicate_no_preserve_order(self):
        """Test deduplication without preserving order."""
        result = deduplicate_serial_numbers(
            ["GRNW_000103851", "GRNW_000103852", "GRNW_000103851"],
            preserve_order=False
        )
        assert len(result) == 2
        assert "GRNW_000103851" in result
        assert "GRNW_000103852" in result
    
    def test_deduplicate_no_duplicates(self):
        """Test deduplication with no duplicates."""
        result = deduplicate_serial_numbers(
            ["GRNW_000103851", "GRNW_000103852", "GRNW_000103853"],
            preserve_order=True
        )
        assert result == ["GRNW_000103851", "GRNW_000103852", "GRNW_000103853"]
    
    def test_deduplicate_empty_list(self):
        """Test deduplication of empty list."""
        result = deduplicate_serial_numbers([], preserve_order=True)
        assert result == []
    
    def test_deduplicate_filters_none(self):
        """Test that None values are filtered out."""
        result = deduplicate_serial_numbers(
            ["GRNW_000103851", None, "GRNW_000103852", None],
            preserve_order=True
        )
        assert result == ["GRNW_000103851", "GRNW_000103852"]
