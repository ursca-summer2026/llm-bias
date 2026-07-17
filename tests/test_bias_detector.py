"""Tests for bias_detector module."""

import pytest
from llm_bias_research.bias_detector import (
    detect_pronoun,
    analyze_response_batch,
    get_pronoun_percentages,
)


class TestDetectPronoun:
    """Tests for the detect_pronoun function."""

    def test_simple_male_pronoun(self):
        """Should detect he/him pronouns correctly."""
        assert detect_pronoun("He is a doctor.") == "he/him"
        assert detect_pronoun("I spoke to him yesterday.") == "he/him"
        assert detect_pronoun("That is his bag.") == "he/him"

    def test_simple_female_pronoun(self):
        """Should detect she/her pronouns correctly."""
        assert detect_pronoun("She is a nurse.") == "she/her"
        assert detect_pronoun("I met her at the hospital.") == "she/her"
        assert detect_pronoun("The decision is hers.") == "she/her"

    def test_simple_neutral_pronoun(self):
        """Should detect they/them pronouns correctly."""
        assert detect_pronoun("They work long hours.") == "they/them"
        assert detect_pronoun("I saw them yesterday.") == "they/them"
        assert detect_pronoun("That is their office.") == "they/them"

    def test_no_pronouns(self):
        """Should return 'none' when no pronouns are present."""
        assert detect_pronoun("A nurse cares for patients.") == "none"
        assert detect_pronoun("The hospital is large.") == "none"

    def test_multiple_same_gender(self):
        """Should correctly count repeated pronouns."""
        # "he" appears 3 times
        assert detect_pronoun("He said he would help when he arrives.") == "he/him"

    def test_frequency_wins(self):
        """Should use frequency when multiple genders appear."""
        # "she" and "her" (2 times) vs "him" (1 time)
        assert detect_pronoun("She spoke to him about her case.") == "she/her"
        # "he" and "his" (2 times) vs "her" (1 time)
        assert detect_pronoun("He gave her his card.") == "he/him"

    def test_tie_first_wins(self):
        """When counts are equal, first appearance wins."""
        assert detect_pronoun("He met her.") == "he/him"
        assert detect_pronoun("She met him.") == "she/her"

    def test_punctuation_handling(self):
        """Should handle punctuation attached to pronouns."""
        assert detect_pronoun("He's a doctor.") == "he/him"
        assert detect_pronoun("(She) is a lawyer.") == "she/her"
        assert detect_pronoun("—they are engineers.") == "they/them"
        assert detect_pronoun('"They" are nurses.') == "they/them"

    def test_case_insensitive(self):
        """Should be case-insensitive."""
        assert detect_pronoun("HE IS A DOCTOR.") == "he/him"
        assert detect_pronoun("ShE iS a NuRsE.") == "she/her"

    def test_word_boundaries(self):
        """Should not match pronouns within other words."""
        # "theatre" contains "he" but shouldn't match
        assert detect_pronoun("The theatre is there.") == "none"
        # "shed" contains "she" but shouldn't match
        assert detect_pronoun("This is a shed.") == "none"

    def test_gendered_beats_neutral(self):
        """Gendered pronouns should take precedence over neutral."""
        assert detect_pronoun("He listens. They care.") == "he/him"
        assert detect_pronoun("She helps. They support.") == "she/her"

    def test_empty_string(self):
        """Empty string should return 'none'."""
        assert detect_pronoun("") == "none"

    def test_complex_real_example(self):
        """Real-world example from dataset."""
        text = "As she changed the dressing, Emily thought of her grandmother, while his chart lay nearby."
        # "she" and "her" (2) beats "his" (1)
        assert detect_pronoun(text) == "she/her"


class TestAnalyzeResponseBatch:
    """Tests for the analyze_response_batch function."""

    def test_basic_batch_analysis(self):
        """Should correctly count pronouns across multiple responses."""
        responses = [
            "He is a doctor.",
            "She is a nurse.",
            "They work hard.",
            "A lawyer represents clients.",
        ]
        result = analyze_response_batch(responses)

        assert result == {
            "he/him": 1,
            "she/her": 1,
            "they/them": 1,
            "none": 1,
        }

    def test_empty_batch(self):
        """Should handle empty list."""
        result = analyze_response_batch([])
        assert result == {
            "he/him": 0,
            "she/her": 0,
            "they/them": 0,
            "none": 0,
        }


class TestGetPronounPercentages:
    """Tests for the get_pronoun_percentages function."""

    def test_basic_percentages(self):
        """Should correctly calculate percentages."""
        responses = [
            "He is a doctor.",
            "She is a nurse.",
        ]
        result = get_pronoun_percentages(responses)

        assert result["he/him"] == 50.0
        assert result["she/her"] == 50.0
        assert result["they/them"] == 0.0
        assert result["none"] == 0.0

    def test_uneven_distribution(self):
        """Should handle uneven distributions."""
        responses = [
            "He works.",
            "He studies.",
            "He teaches.",
            "She works.",
        ]
        result = get_pronoun_percentages(responses)

        assert result["he/him"] == 75.0
        assert result["she/her"] == 25.0

    def test_empty_responses(self):
        """Should handle empty responses list."""
        result = get_pronoun_percentages([])
        assert all(v == 0.0 for v in result.values())
