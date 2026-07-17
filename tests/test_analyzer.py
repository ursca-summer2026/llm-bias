"""
Tests for the statistical analyzer module.
"""

import pytest
import pandas as pd
import numpy as np
from llm_bias_research.analyzer import BiasAnalyzer


@pytest.fixture
def sample_data():
    """Create sample data for testing."""
    np.random.seed(42)
    
    data = {
        "id": range(1, 101),
        "keyword": ["Nurse"] * 50 + ["Doctor"] * 50,
        "model": ["phi3"] * 100,
        "prompt": ["Describe a {keyword}."] * 100,
        "output": ["Sample text"] * 100,
        "pronoun_group": (
            ["he/him"] * 10 + ["she/her"] * 30 + ["they/them"] * 5 + ["none"] * 5 +  # Nurse
            ["he/him"] * 35 + ["she/her"] * 10 + ["they/them"] * 3 + ["none"] * 2    # Doctor
        )
    }
    
    return pd.DataFrame(data)


@pytest.fixture
def analyzer(sample_data):
    """Create analyzer instance with sample data."""
    return BiasAnalyzer(sample_data)


class TestBiasAnalyzer:
    """Test cases for BiasAnalyzer class."""
    
    def test_init(self, sample_data):
        """Test analyzer initialization."""
        analyzer = BiasAnalyzer(sample_data)
        assert len(analyzer.data) == 100
        assert "pronoun_group" in analyzer.data.columns
    
    def test_init_with_empty_data(self):
        """Test initialization with empty DataFrame."""
        with pytest.raises((ValueError, KeyError)):
            BiasAnalyzer(pd.DataFrame())
    
    def test_chi_square_test(self, analyzer):
        """Test chi-square test of independence."""
        result = analyzer.chi_square_test("keyword")
        
        assert "chi2" in result
        assert "p_value" in result
        assert "dof" in result
        assert "cramers_v" in result
        assert "interpretation" in result
        
        # Check value types
        assert isinstance(result["chi2"], (int, float))
        assert isinstance(result["p_value"], (int, float))
        assert isinstance(result["dof"], (int, np.integer))
        assert isinstance(result["cramers_v"], (int, float))
        
        # Check value ranges
        assert result["chi2"] >= 0
        assert 0 <= result["p_value"] <= 1
        assert result["dof"] > 0
        assert 0 <= result["cramers_v"] <= 1
    
    def test_chi_square_with_model(self, analyzer):
        """Test chi-square test with model variable."""
        # Add more models to sample data
        analyzer.data.loc[50:, "model"] = "llama3.2"
        
        result = analyzer.chi_square_test("model")
        
        assert result["chi2"] >= 0
        assert 0 <= result["p_value"] <= 1
    
    def test_chi_square_interpretation(self, analyzer):
        """Test interpretation of Cramér's V."""
        result = analyzer.chi_square_test("keyword")
        
        interpretation = result["interpretation"]
        assert any(word in interpretation.lower() for word in ["small", "medium", "large", "negligible"])
    
    def test_t_test_pronouns(self, analyzer):
        """Test independent samples t-test."""
        result = analyzer.t_test_pronouns(
            group1_filter={"keyword": "Nurse"},
            group2_filter={"keyword": "Doctor"},
            pronoun="he/him"
        )
        
        assert "t_statistic" in result
        assert "p_value" in result
        assert "cohens_d" in result
        assert "interpretation" in result
        assert "group1_mean" in result
        assert "group2_mean" in result
        
        # Check types
        assert isinstance(result["t_statistic"], (int, float))
        assert isinstance(result["p_value"], (int, float))
        assert isinstance(result["cohens_d"], (int, float))
        
        # Check p-value range
        assert 0 <= result["p_value"] <= 1
    
    def test_t_test_with_different_pronouns(self, analyzer):
        """Test t-test with different pronoun groups."""
        for pronoun in ["he/him", "she/her", "they/them"]:
            result = analyzer.t_test_pronouns(
                group1_filter={"keyword": "Nurse"},
                group2_filter={"keyword": "Doctor"},
                pronoun=pronoun
            )
            
            assert result["t_statistic"] is not None
            assert result["p_value"] is not None
    
    def test_t_test_cohens_d_interpretation(self, analyzer):
        """Test Cohen's d effect size interpretation."""
        result = analyzer.t_test_pronouns(
            group1_filter={"keyword": "Nurse"},
            group2_filter={"keyword": "Doctor"},
            pronoun="he/him"
        )
        
        interpretation = result["interpretation"]
        assert any(word in interpretation.lower() for word in ["small", "medium", "large", "negligible"])
    
    def test_confidence_interval(self, analyzer):
        """Test confidence interval calculation."""
        result = analyzer.confidence_interval(
            group_filter={"keyword": "Nurse"},
            pronoun="he/him",
            confidence=0.95
        )
        
        assert "lower" in result
        assert "upper" in result
        assert "mean" in result
        assert "n" in result
        
        # Check range
        assert 0 <= result["lower"] <= 1
        assert 0 <= result["upper"] <= 1
        assert result["lower"] <= result["mean"] <= result["upper"]
        
        # Check sample size
        assert result["n"] > 0
    
    def test_confidence_interval_different_levels(self, analyzer):
        """Test confidence intervals at different levels."""
        ci_90 = analyzer.confidence_interval(
            group_filter={"keyword": "Nurse"},
            pronoun="he/him",
            confidence=0.90
        )
        
        ci_95 = analyzer.confidence_interval(
            group_filter={"keyword": "Nurse"},
            pronoun="he/him",
            confidence=0.95
        )
        
        ci_99 = analyzer.confidence_interval(
            group_filter={"keyword": "Nurse"},
            pronoun="he/him",
            confidence=0.99
        )
        
        # Higher confidence = wider interval
        width_90 = ci_90["upper"] - ci_90["lower"]
        width_95 = ci_95["upper"] - ci_95["lower"]
        width_99 = ci_99["upper"] - ci_99["lower"]
        
        assert width_90 < width_95 < width_99
    
    def test_confidence_interval_invalid_confidence(self, analyzer):
        """Test error handling for invalid confidence level."""
        with pytest.raises((ValueError, AssertionError)):
            analyzer.confidence_interval(
                group_filter={"keyword": "Nurse"},
                pronoun="he/him",
                confidence=1.5  # Invalid
            )
    
    def test_filter_group(self, analyzer):
        """Test internal group filtering."""
        # This tests the helper method used by other functions
        nurses = analyzer.data[analyzer.data["keyword"] == "Nurse"]
        assert len(nurses) == 50
        
        doctors = analyzer.data[analyzer.data["keyword"] == "Doctor"]
        assert len(doctors) == 50
    
    def test_with_all_same_values(self):
        """Test analyzer with no variation in data."""
        data = pd.DataFrame({
            "id": range(1, 51),
            "keyword": ["Nurse"] * 50,
            "pronoun_group": ["he/him"] * 50
        })
        
        analyzer = BiasAnalyzer(data)
        
        # Chi-square should handle this (might have warnings)
        result = analyzer.chi_square_test("keyword")
        # Result may be NaN or have special values
        assert "chi2" in result
    
    def test_with_small_sample(self):
        """Test analyzer with very small sample size."""
        data = pd.DataFrame({
            "id": [1, 2, 3],
            "keyword": ["Nurse", "Doctor", "Nurse"],
            "pronoun_group": ["he/him", "she/her", "they/them"]
        })
        
        analyzer = BiasAnalyzer(data)
        
        # Should still run but may have low statistical power
        result = analyzer.chi_square_test("keyword")
        assert result["dof"] >= 0
    
    def test_effect_size_calculation(self, analyzer):
        """Test that effect sizes are calculated correctly."""
        result = analyzer.chi_square_test("keyword")
        
        # Cramér's V should be between 0 and 1
        assert 0 <= result["cramers_v"] <= 1
        
        # For t-test
        t_result = analyzer.t_test_pronouns(
            group1_filter={"keyword": "Nurse"},
            group2_filter={"keyword": "Doctor"},
            pronoun="he/him"
        )
        
        # Cohen's d can be > 1 for very large effects
        assert isinstance(t_result["cohens_d"], (int, float))
    
    def test_multiple_filters(self, analyzer):
        """Test filtering with multiple conditions."""
        # Add another column
        analyzer.data["prompt_type"] = ["short"] * 50 + ["long"] * 50
        
        result = analyzer.t_test_pronouns(
            group1_filter={"keyword": "Nurse", "prompt_type": "short"},
            group2_filter={"keyword": "Doctor", "prompt_type": "long"},
            pronoun="he/him"
        )
        
        assert result["t_statistic"] is not None
        assert result["p_value"] is not None
    
    def test_missing_pronoun_group(self, analyzer):
        """Test behavior when requested pronoun group has no data."""
        # Filter to group with very few samples
        result = analyzer.confidence_interval(
            group_filter={"keyword": "Nurse"},
            pronoun="none",
            confidence=0.95
        )
        
        # Should still return a result (might be 0 or with wide CI)
        assert "mean" in result


class TestStatisticalMethods:
    """Test statistical calculation accuracy."""
    
    def test_cramers_v_calculation(self):
        """Test Cramér's V calculation with known values."""
        # Create data with known association
        data = pd.DataFrame({
            "keyword": ["A"] * 40 + ["B"] * 60,
            "pronoun_group": (
                ["he/him"] * 10 + ["she/her"] * 30 +  # A
                ["he/him"] * 50 + ["she/her"] * 10    # B
            )
        })
        
        analyzer = BiasAnalyzer(data)
        result = analyzer.chi_square_test("keyword")
        
        # Should show strong association
        assert result["cramers_v"] > 0.3  # Medium to large effect
        assert result["p_value"] < 0.05  # Significant
    
    def test_cohens_d_calculation(self):
        """Test Cohen's d calculation with known values."""
        # Create data with known difference
        data = pd.DataFrame({
            "keyword": ["A"] * 50 + ["B"] * 50,
            "pronoun_group": (
                ["he/him"] * 5 + ["she/her"] * 45 +   # A: 10% he/him
                ["he/him"] * 45 + ["she/her"] * 5     # B: 90% he/him
            )
        })
        
        analyzer = BiasAnalyzer(data)
        result = analyzer.t_test_pronouns(
            group1_filter={"keyword": "A"},
            group2_filter={"keyword": "B"},
            pronoun="he/him"
        )
        
        # Should show very large effect
        assert abs(result["cohens_d"]) > 0.8  # Large effect
        assert result["p_value"] < 0.001  # Highly significant


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
