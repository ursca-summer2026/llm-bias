"""
Statistical analysis module for bias metrics.

This module provides statistical tests and analysis tools for quantifying
bias patterns in LLM responses.
"""

import numpy as np
import pandas as pd
from scipy import stats
from typing import Any, Dict, Optional, Tuple

from llm_bias_research.bias_detector import detect_pronoun, PronounGroup


class BiasAnalyzer:
    """Performs statistical analysis on bias research data.

    Provides methods for:
    - Chi-square tests for independence
    - T-tests for comparing groups
    - Effect size calculations
    - Confidence intervals
    """

    def __init__(self, data: pd.DataFrame) -> None:
        """Initialize analyzer with response data.

        Args:
            data: DataFrame with columns: model, keyword, prompt, output
                 Can also include pre-computed 'pronoun_group' column.
        """
        self.data = data.copy()
        
        # Add pronoun group classification if not present
        if "pronoun_group" not in self.data.columns:
            self.data["pronoun_group"] = self.data["output"].apply(detect_pronoun)

    def get_pronoun_distribution(
        self,
        groupby: Optional[str] = None,
    ) -> pd.DataFrame:
        """Get pronoun distribution, optionally grouped.

        Args:
            groupby: Column to group by (e.g., 'model', 'keyword').

        Returns:
            DataFrame with pronoun counts or proportions.
        """
        if groupby:
            counts = (
                self.data.groupby([groupby, "pronoun_group"])
                .size()
                .unstack(fill_value=0)
            )
        else:
            counts = self.data["pronoun_group"].value_counts()

        return counts

    def chi_square_test(
        self,
        var1: str,
        var2: str = "pronoun_group",
    ) -> Dict[str, Any]:
        """Perform chi-square test of independence.

        Tests whether two categorical variables are independent.

        Args:
            var1: First variable (e.g., 'keyword', 'model').
            var2: Second variable (default: 'pronoun_group').

        Returns:
            Dictionary with test results: chi2, p_value, dof, cramers_v.
        """
        # Create contingency table
        contingency = pd.crosstab(self.data[var1], self.data[var2])
        
        # Perform chi-square test
        chi2, p_value, dof, expected = stats.chi2_contingency(contingency)
        
        # Calculate Cramér's V (effect size)
        n = contingency.sum().sum()
        min_dim = min(contingency.shape) - 1
        cramers_v = np.sqrt(chi2 / (n * min_dim)) if min_dim > 0 else 0
        
        return {
            "chi2": chi2,
            "p_value": p_value,
            "dof": dof,
            "cramers_v": cramers_v,
            "significant": p_value < 0.05,
            "interpretation": self._interpret_cramers_v(cramers_v),
        }

    def _interpret_cramers_v(self, v: float) -> str:
        """Interpret Cramér's V effect size.

        Args:
            v: Cramér's V value.

        Returns:
            Interpretation string.
        """
        if v < 0.1:
            return "negligible"
        elif v < 0.3:
            return "small"
        elif v < 0.5:
            return "medium"
        else:
            return "large"

    def t_test_pronouns(
        self,
        group1_filter: Dict[str, str],
        group2_filter: Dict[str, str],
        pronoun: PronounGroup = "he/him",
    ) -> Dict[str, Any]:
        """Perform t-test comparing pronoun usage between two groups.

        Args:
            group1_filter: Filter for group 1 (e.g., {'model': 'phi3'}).
            group2_filter: Filter for group 2 (e.g., {'model': 'llama3.2'}).
            pronoun: Which pronoun group to compare.

        Returns:
            Dictionary with test results: t_statistic, p_value, cohens_d, etc.
        """
        # Filter data for each group
        group1 = self._filter_data(group1_filter)
        group2 = self._filter_data(group2_filter)

        # Calculate proportions for each group
        prop1 = (group1["pronoun_group"] == pronoun).mean()
        prop2 = (group2["pronoun_group"] == pronoun).mean()

        # Perform independent samples t-test
        # Using pronoun indicator (0/1) as continuous variable
        g1_values = (group1["pronoun_group"] == pronoun).astype(int)
        g2_values = (group2["pronoun_group"] == pronoun).astype(int)

        t_stat, p_value = stats.ttest_ind(g1_values, g2_values)

        # Calculate Cohen's d (effect size)
        cohens_d = self._cohens_d(g1_values, g2_values)

        return {
            "pronoun": pronoun,
            "group1_proportion": prop1,
            "group2_proportion": prop2,
            "difference": prop1 - prop2,
            "t_statistic": t_stat,
            "p_value": p_value,
            "cohens_d": cohens_d,
            "significant": p_value < 0.05,
            "interpretation": self._interpret_cohens_d(cohens_d),
        }

    def _filter_data(self, filters: Dict[str, str]) -> pd.DataFrame:
        """Apply filters to data.

        Args:
            filters: Dictionary of column:value filters.

        Returns:
            Filtered DataFrame.
        """
        filtered = self.data
        for col, val in filters.items():
            filtered = filtered[filtered[col] == val]
        return filtered

    def _cohens_d(self, group1: pd.Series, group2: pd.Series) -> float:
        """Calculate Cohen's d effect size.

        Args:
            group1: First group values.
            group2: Second group values.

        Returns:
            Cohen's d value.
        """
        n1, n2 = len(group1), len(group2)
        var1, var2 = group1.var(), group2.var()
        
        # Pooled standard deviation
        pooled_std = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
        
        if pooled_std == 0:
            return 0.0
        
        return (group1.mean() - group2.mean()) / pooled_std

    def _interpret_cohens_d(self, d: float) -> str:
        """Interpret Cohen's d effect size.

        Args:
            d: Cohen's d value.

        Returns:
            Interpretation string.
        """
        d_abs = abs(d)
        if d_abs < 0.2:
            return "negligible"
        elif d_abs < 0.5:
            return "small"
        elif d_abs < 0.8:
            return "medium"
        else:
            return "large"

    def confidence_interval(
        self,
        group_filter: dict[str, str],
        pronoun: PronounGroup,
        confidence: float = 0.95,
    ) -> tuple[float, float, float]:
        """Calculate confidence interval for pronoun proportion.

        Args:
            group_filter: Filter for group (e.g., {'keyword': 'Nurse'}).
            pronoun: Which pronoun group.
            confidence: Confidence level (default: 0.95).

        Returns:
            Tuple of (proportion, lower_bound, upper_bound).
        """
        data = self._filter_data(group_filter)
        
        # Calculate proportion
        successes = (data["pronoun_group"] == pronoun).sum()
        n = len(data)
        
        if n == 0:
            return 0.0, 0.0, 0.0
        
        proportion = successes / n
        
        # Wilson score interval (better for proportions than normal approximation)
        z = stats.norm.ppf((1 + confidence) / 2)
        denominator = 1 + z**2 / n
        center = (proportion + z**2 / (2 * n)) / denominator
        margin = z * np.sqrt((proportion * (1 - proportion) / n + z**2 / (4 * n**2))) / denominator
        
        return proportion, max(0, center - margin), min(1, center + margin)

    def summary_statistics(self) -> Dict[str, Any]:
        """Generate summary statistics for the dataset.

        Returns:
            Dictionary with various summary metrics.
        """
        summary = {
            "total_responses": len(self.data),
            "models": self.data["model"].nunique() if "model" in self.data.columns else 0,
            "keywords": self.data["keyword"].nunique() if "keyword" in self.data.columns else 0,
            "pronoun_distribution": self.data["pronoun_group"].value_counts().to_dict(),
        }

        # Overall bias metrics
        pronoun_props = self.data["pronoun_group"].value_counts(normalize=True)
        summary["bias_score"] = abs(
            pronoun_props.get("he/him", 0) - pronoun_props.get("she/her", 0)
        )

        return summary
