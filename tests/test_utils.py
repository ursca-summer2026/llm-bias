"""Tests for utils module."""

import tempfile
from pathlib import Path

import pytest

from llm_bias_research.utils import (
    load_prompts,
    sanitize_filename,
    parse_keywords,
    format_percentage,
    prompt_type,
    validate_model_name,
)


class TestLoadPrompts:
    """Tests for load_prompts function."""

    def test_load_valid_prompts(self):
        """Should load prompts from valid file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Prompt 1\n")
            f.write("Prompt 2\n")
            f.write("\n")  # Empty line should be skipped
            f.write("Prompt 3\n")
            temp_path = f.name

        try:
            prompts = load_prompts(temp_path)
            assert len(prompts) == 3
            assert prompts == ["Prompt 1", "Prompt 2", "Prompt 3"]
        finally:
            Path(temp_path).unlink()

    def test_load_nonexistent_file(self):
        """Should raise FileNotFoundError for nonexistent file."""
        with pytest.raises(FileNotFoundError):
            load_prompts("/nonexistent/file.txt")

    def test_load_empty_file(self):
        """Should raise ValueError for empty file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("\n\n\n")  # Only empty lines
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="No valid prompts"):
                load_prompts(temp_path)
        finally:
            Path(temp_path).unlink()


class TestSanitizeFilename:
    """Tests for sanitize_filename function."""

    def test_remove_problematic_characters(self):
        """Should remove/replace problematic filename characters."""
        assert sanitize_filename("file/name") == "file_name"
        assert sanitize_filename("file:name") == "file_name"
        assert sanitize_filename("file<>name") == "file__name"

    def test_collapse_underscores(self):
        """Should collapse multiple underscores."""
        assert sanitize_filename("file___name") == "file_name"

    def test_strip_dots_spaces(self):
        """Should strip leading/trailing dots and spaces."""
        assert sanitize_filename("  file.txt  ") == "file.txt"
        assert sanitize_filename(".file.txt.") == "file.txt"


class TestParseKeywords:
    """Tests for parse_keywords function."""

    def test_parse_simple_keywords(self):
        """Should parse comma-separated keywords."""
        result = parse_keywords("Nurse,Doctor,Engineer")
        assert result == ["Nurse", "Doctor", "Engineer"]

    def test_parse_keywords_with_spaces(self):
        """Should trim whitespace from keywords."""
        result = parse_keywords("Nurse , Doctor ,  Engineer  ")
        assert result == ["Nurse", "Doctor", "Engineer"]

    def test_parse_empty_string(self):
        """Should return empty list for empty string."""
        assert parse_keywords("") == []

    def test_parse_skip_empty_keywords(self):
        """Should skip empty keywords."""
        result = parse_keywords("Nurse,,Doctor")
        assert result == ["Nurse", "Doctor"]


class TestFormatPercentage:
    """Tests for format_percentage function."""

    def test_format_basic_percentage(self):
        """Should format decimal as percentage."""
        assert format_percentage(0.456, 1) == "45.6%"
        assert format_percentage(0.5, 0) == "50%"
        assert format_percentage(1.0, 2) == "100.00%"


class TestPromptType:
    """Tests for prompt_type function."""

    def test_replace_keyword(self):
        """Should replace keyword with placeholder."""
        result = prompt_type("Briefly describe a Nurse.", "Nurse")
        assert result == "Briefly describe a ___"

    def test_case_insensitive(self):
        """Should be case-insensitive."""
        result = prompt_type("Briefly describe a NURSE.", "nurse")
        assert result == "Briefly describe a ___"

    def test_strip_trailing_punctuation(self):
        """Should strip trailing punctuation."""
        result = prompt_type("Describe a Doctor, please.", "Doctor")
        assert result == "Describe a ___"


class TestValidateModelName:
    """Tests for validate_model_name function."""

    def test_valid_model_names(self):
        """Should accept valid model names."""
        assert validate_model_name("phi3") is True
        assert validate_model_name("llama3.2") is True
        assert validate_model_name("qwen-2.5") is True

    def test_invalid_model_names(self):
        """Should reject invalid model names."""
        assert validate_model_name("") is False
        assert validate_model_name("model with spaces") is False
        assert validate_model_name("model/path") is False
        assert validate_model_name(None) is False
