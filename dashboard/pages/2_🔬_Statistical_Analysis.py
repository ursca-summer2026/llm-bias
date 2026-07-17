"""
Statistical Analysis Page

Provides comprehensive statistical testing including:
- Chi-square tests
- T-tests
- Effect sizes
- Confidence intervals
"""

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from llm_bias_research.analyzer import BiasAnalyzer
from dashboard.components.help import show_metric_explanation
from dashboard.components.charts import create_grouped_bar

st.set_page_config(page_title="Statistical Analysis", page_icon="🔬", layout="wide")

st.title("🔬 Statistical Analysis")

st.markdown(
    """
    This page provides rigorous statistical tests to determine if observed bias patterns
    are statistically significant or could have occurred by chance.
    """
)

# Check if data is loaded
if "data" not in st.session_state:
    st.warning("⚠️ Please load data from the main page first.")
    st.stop()

data = st.session_state["data"]

# Add optional filters
st.sidebar.markdown("### Data Filters")
st.sidebar.info("Optional: Filter the dataset before running statistical tests")

# Model filter
models = sorted(data["model"].unique())
selected_models = st.sidebar.multiselect(
    "Models",
    options=models,
    default=models,
    help="Filter by specific models"
)

# Keyword filter
keywords = sorted(data["keyword"].unique())
selected_keywords = st.sidebar.multiselect(
    "Keywords/Professions",
    options=keywords,
    default=keywords,
    help="Filter by specific professions"
)

# Prompt filter
prompts = sorted(data["prompt"].unique())
selected_prompts = st.sidebar.multiselect(
    "Prompts",
    options=prompts,
    default=prompts,
    help="Filter by specific prompts"
)

# Apply filters
data = data[
    (data["model"].isin(selected_models)) &
    (data["keyword"].isin(selected_keywords)) &
    (data["prompt"].isin(selected_prompts))
]

if len(data) == 0:
    st.error("No data matches the selected filters.")
    st.stop()

analyzer = BiasAnalyzer(data)

st.markdown("---")

# Section 1: Chi-Square Test
st.header("1️⃣ Chi-Square Test of Independence")

st.markdown(
    """
    Tests whether gender bias (pronoun usage) is independent from profession/keyword.
    **Null Hypothesis**: Gender and profession are independent (no bias exists).
    """
)

show_metric_explanation("chi_square")

col1, col2 = st.columns([1, 1])

with col1:
    chi_var1 = st.selectbox(
        "Select variable to test",
        ["keyword", "model"],
        help="Test whether this variable is independent from pronoun usage",
    )

with col2:
    chi_alpha = st.slider(
        "Significance level (α)",
        0.01,
        0.10,
        0.05,
        0.01,
        help="Common choices: 0.05 (95% confidence), 0.01 (99% confidence)",
    )

if st.button("Run Chi-Square Test", type="primary"):
    with st.spinner("Running statistical test..."):
        results = analyzer.chi_square_test(chi_var1, "pronoun_group")

        st.subheader("Results")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("χ² Statistic", f"{results['chi2']:.2f}")

        with col2:
            p_display = f"{results['p_value']:.4f}" if results["p_value"] >= 0.0001 else "< 0.0001"
            st.metric("p-value", p_display)

        with col3:
            st.metric("Degrees of Freedom", results["dof"])

        with col4:
            st.metric("Cramér's V", f"{results['cramers_v']:.3f}")

        # Interpretation
        if results["significant"]:
            st.success(
                f"""
                ✅ **Result is statistically significant** (p < {chi_alpha})
                
                We reject the null hypothesis. There is a significant relationship between
                {chi_var1} and pronoun usage. This suggests gender bias is present.
                
                **Effect size ({results['interpretation']})**: The Cramér's V of {results['cramers_v']:.3f}
                indicates the strength of this relationship.
                """
            )
        else:
            st.info(
                f"""
                ℹ️ **Result is not statistically significant** (p ≥ {chi_alpha})
                
                We cannot reject the null hypothesis. The observed patterns could be due to chance.
                This does not prove no bias exists, but we lack statistical evidence for it.
                """
            )

st.markdown("---")

# Section 2: T-Test
st.header("2️⃣ Independent Samples T-Test")

st.markdown(
    """
    Compares pronoun usage between two specific groups (e.g., two models or two professions).
    **Null Hypothesis**: The two groups have equal pronoun usage proportions.
    """
)

show_metric_explanation("t_test")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Group 1")
    group1_var = st.selectbox("Variable", ["model", "keyword"], key="g1_var")
    group1_val = st.selectbox("Value", data[group1_var].unique(), key="g1_val")

with col2:
    st.subheader("Group 2")
    group2_var = st.selectbox("Variable", ["model", "keyword"], key="g2_var")
    group2_val = st.selectbox(
        "Value",
        [v for v in data[group2_var].unique() if v != group1_val],
        key="g2_val",
    )

pronoun_to_test = st.selectbox(
    "Pronoun group to compare",
    ["he/him", "she/her", "they/them", "none"],
    help="Which pronoun group's usage to compare between groups",
)

if st.button("Run T-Test", type="primary"):
    with st.spinner("Running statistical test..."):
        group1_filter = {group1_var: group1_val}
        group2_filter = {group2_var: group2_val}

        results = analyzer.t_test_pronouns(group1_filter, group2_filter, pronoun_to_test)

        st.subheader("Results")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Group 1 Proportion", f"{results['group1_proportion']:.1%}")

        with col2:
            st.metric("Group 2 Proportion", f"{results['group2_proportion']:.1%}")

        with col3:
            st.metric("Difference", f"{results['difference']:.1%}")

        with col4:
            p_display = f"{results['p_value']:.4f}" if results["p_value"] >= 0.0001 else "< 0.0001"
            st.metric("p-value", p_display)

        col1, col2 = st.columns(2)

        with col1:
            st.metric("t-statistic", f"{results['t_statistic']:.3f}")

        with col2:
            st.metric("Cohen's d", f"{results['cohens_d']:.3f}")

        # Interpretation
        if results["significant"]:
            direction = "higher" if results["difference"] > 0 else "lower"
            st.success(
                f"""
                ✅ **Significant difference detected** (p < 0.05)
                
                Group 1 ({group1_val}) has {direction} usage of "{pronoun_to_test}" compared to
                Group 2 ({group2_val}).
                
                **Effect size ({results['interpretation']})**: Cohen's d of {results['cohens_d']:.3f}
                indicates the magnitude of this difference.
                """
            )
        else:
            st.info(
                """
                ℹ️ **No significant difference** (p ≥ 0.05)
                
                The two groups do not show significantly different pronoun usage patterns
                for the selected pronoun group.
                """
            )

st.markdown("---")

# Section 3: Confidence Intervals
st.header("3️⃣ Confidence Intervals")

st.markdown(
    """
    Calculate confidence intervals for pronoun usage proportions.
    This shows the range where the true proportion likely falls.
    """
)

show_metric_explanation("confidence_interval")

col1, col2, col3 = st.columns(3)

with col1:
    ci_var = st.selectbox("Group by", ["model", "keyword"], key="ci_var")

with col2:
    ci_val = st.selectbox("Select value", data[ci_var].unique(), key="ci_val")

with col3:
    ci_level = st.slider("Confidence level", 0.90, 0.99, 0.95, 0.01)

pronoun_for_ci = st.selectbox(
    "Pronoun group",
    ["he/him", "she/her", "they/them", "none"],
    key="ci_pronoun",
)

if st.button("Calculate Confidence Interval", type="primary"):
    group_filter = {ci_var: ci_val}
    proportion, lower, upper = analyzer.confidence_interval(
        group_filter, pronoun_for_ci, confidence=ci_level
    )

    st.subheader("Results")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Observed Proportion", f"{proportion:.1%}")

    with col2:
        st.metric("Lower Bound", f"{lower:.1%}")

    with col3:
        st.metric("Upper Bound", f"{upper:.1%}")

    st.info(
        f"""
        📊 **Interpretation**
        
        We can be {ci_level:.0%} confident that the true proportion of "{pronoun_for_ci}"
        usage for {ci_var} "{ci_val}" falls between {lower:.1%} and {upper:.1%}.
        
        **Margin of error**: ±{(upper - lower) / 2:.1%}
        """
    )

    # Visualization
    import plotly.graph_objects as go

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=[proportion],
            y=[ci_val],
            mode="markers",
            marker=dict(size=12, color="#2a78d6"),
            name="Observed",
            showlegend=True,
        )
    )

    fig.add_trace(
        go.Scatter(
            x=[lower, upper],
            y=[ci_val, ci_val],
            mode="lines",
            line=dict(color="#2a78d6", width=3),
            name=f"{ci_level:.0%} CI",
            showlegend=True,
        )
    )

    fig.update_layout(
        title=f"{ci_level:.0%} Confidence Interval for {pronoun_for_ci} Usage",
        xaxis_title="Proportion",
        yaxis_title=ci_var.capitalize(),
        xaxis=dict(range=[0, 1], tickformat=".0%"),
        height=200,
        showlegend=True,
    )

    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# Section 4: Summary Statistics
st.header("4️⃣ Summary Statistics")

summary = analyzer.summary_statistics()

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Total Responses", summary["total_responses"])

with col2:
    st.metric("Number of Models", summary["models"])

with col3:
    st.metric("Number of Keywords", summary["keywords"])

st.subheader("Pronoun Distribution")

pronoun_df = pd.DataFrame(
    list(summary["pronoun_distribution"].items()),
    columns=["Pronoun Group", "Count"],
)
pronoun_df["Percentage"] = (pronoun_df["Count"] / summary["total_responses"]) * 100

st.dataframe(
    pronoun_df.style.format({"Percentage": "{:.1f}%"}),
    use_container_width=True,
)

st.metric("Overall Bias Score", f"{summary['bias_score']:.3f}")

st.info(
    """
    **Bias Score** = |P(he/him) - P(she/her)|
    
    - 0.0 = perfectly balanced
    - 0.5 = strong bias (one gender used 75%, other 25%)
    - 1.0 = complete bias (only one gender mentioned)
    """
)
