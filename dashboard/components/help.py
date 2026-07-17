"""
Help system for non-technical users.

Provides contextual explanations and guidance throughout the dashboard.
"""

import streamlit as st


def show_help_sidebar() -> None:
    """Display help information in the sidebar."""
    with st.sidebar.expander("❓ Help & Glossary"):
        st.markdown(
            """
            ### Understanding the Dashboard
            
            **Pronoun Groups:**
            - **he/him**: Masculine pronouns (he, him, his)
            - **she/her**: Feminine pronouns (she, her, hers)
            - **they/them**: Neutral pronouns (they, them, their)
            - **none**: No pronouns detected
            
            **Bias Score:**
            The difference between he/him and she/her percentages.
            Higher scores indicate stronger gender associations.
            
            **Statistical Significance:**
            - **p-value < 0.05**: Result is statistically significant
            - **p-value ≥ 0.05**: Result could be due to chance
            
            **Effect Sizes:**
            - **Cramér's V** (chi-square): 0.1=small, 0.3=medium, 0.5=large
            - **Cohen's d** (t-test): 0.2=small, 0.5=medium, 0.8=large
            
            **Cosine Similarity:**
            Measures how similar two models' responses are.
            - 1.0 = identical
            - 0.0 = completely different
            """
        )


def show_metric_explanation(metric_name: str) -> None:
    """Show explanation for a specific metric.

    Args:
        metric_name: Name of the metric to explain.
    """
    explanations = {
        "chi_square": """
            **Chi-Square Test**
            
            Tests whether gender bias and profession are independent.
            
            - **Null hypothesis**: No relationship between profession and gender
            - **p < 0.05**: We reject null hypothesis (bias exists)
            - **Cramér's V**: Effect size (strength of relationship)
            
            Use this to determine if observed patterns are statistically significant
            or could have occurred by chance.
        """,
        "t_test": """
            **T-Test**
            
            Compares pronoun usage between two groups (models, keywords, etc.).
            
            - **Null hypothesis**: No difference between groups
            - **p < 0.05**: Significant difference exists
            - **Cohen's d**: Effect size (magnitude of difference)
            
            Use this to compare two specific models or professions.
        """,
        "cosine_similarity": """
            **Cosine Similarity**
            
            Measures textual similarity between model responses.
            
            - **1.0**: Responses are identical in content
            - **0.8-0.9**: Very similar responses
            - **0.5-0.7**: Moderately similar
            - **< 0.5**: Different response patterns
            
            Use this to identify which models produce similar outputs,
            which may indicate similar training data or architectures.
        """,
        "confidence_interval": """
            **Confidence Interval**
            
            Range where the true proportion likely falls.
            
            - **95% CI**: We're 95% confident the true value is in this range
            - **Narrow CI**: More precise estimate (larger sample)
            - **Wide CI**: Less precise (smaller sample or more variance)
            
            Use this to understand the uncertainty in your measurements.
        """,
    }

    if metric_name in explanations:
        st.info(explanations[metric_name])


def show_interpretation_guide(section: str) -> None:
    """Show interpretation guide for a dashboard section.

    Args:
        section: Section name (e.g., 'heatmap', 'wordcloud').
    """
    guides = {
        "heatmap": """
            ### How to Read the Heatmap
            
            - **Rows**: Professions or models
            - **Columns**: Pronoun groups (he/him, she/her, they/them, none)
            - **Colors**: Darker = more responses in that category
            
            **What to look for:**
            - Rows that are mostly dark blue in "he/him" or "she/her" show strong bias
            - Even distribution across columns suggests less bias
            - Compare different professions to identify patterns
        """,
        "wordcloud": """
            ### Understanding Word Clouds
            
            - **Size**: Larger words appear more frequently
            - **Color**: Grouped by pronoun category
            - **Position**: Random (doesn't carry meaning)
            
            **What to look for:**
            - Different vocabulary associated with different genders
            - Stereotypical terms (e.g., "caring" with she, "strong" with he)
            - Profession-specific terms that may correlate with bias
        """,
        "time_series": """
            ### Time Series Analysis
            
            Track how bias changes across model versions or time periods.
            
            **What to look for:**
            - Upward/downward trends in specific pronoun usage
            - Sudden changes that might indicate training data shifts
            - Whether newer models show less bias than older ones
        """,
    }

    if section in guides:
        with st.expander("📖 How to Interpret This Analysis"):
            st.markdown(guides[section])


def show_quick_tips() -> None:
    """Display quick tips for using the dashboard."""
    st.sidebar.markdown(
        """
        ### 💡 Quick Tips
        
        - **Filter data** using dropdowns to focus on specific models/keywords
        - **Export visualizations** by right-clicking charts
        - **Statistical significance** is marked with asterisks (*)
        - **Hover over charts** for detailed information
        - **Use the tabs** to switch between different views
        """
    )


def show_methodology_link() -> None:
    """Show link to methodology documentation."""
    st.sidebar.markdown(
        """
        ### 📚 Learn More
        
        - [Methodology Documentation](../docs/methodology.md)
        - [API Reference](../docs/api_reference.md)
        - [GitHub Repository](https://github.com/yourusername/llm-bias-research)
        """
    )
