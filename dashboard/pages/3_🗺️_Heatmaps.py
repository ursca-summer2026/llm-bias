"""
Heatmaps Page

Visualizes bias patterns using heatmaps:
- Profession × Pronoun Group
- Model × Pronoun Group
- Interactive filtering and exploration
"""

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dashboard.components.charts import create_heatmap
from dashboard.components.help import show_interpretation_guide

st.set_page_config(page_title="Heatmaps", page_icon="🗺️", layout="wide")

st.title("🗺️ Bias Heatmaps")

st.markdown(
    """
    Heatmaps provide a visual representation of bias patterns, making it easy to identify
    which professions or models show the strongest gender associations.
    """
)

show_interpretation_guide("heatmap")

# Check if data is loaded
if "data" not in st.session_state:
    st.warning("⚠️ Please load data from the main page first.")
    st.stop()

data = st.session_state["data"]

st.markdown("---")

# Section 1: Profession × Pronoun Heatmap
st.header("1️⃣ Bias by Profession")

st.markdown(
    """
    This heatmap shows how each profession/keyword associates with different pronoun groups.
    Rows with strong bias will show concentrated color in one column.
    """
)

# Filters
col1, col2, col3 = st.columns(3)

with col1:
    model_filter = st.selectbox(
        "Filter by Model",
        ["All models"] + list(data["model"].unique()),
        key="prof_model_filter",
    )

with col2:
    prompt_filter = st.selectbox(
        "Filter by Prompt",
        ["All prompts"] + list(data["prompt"].unique()),
        key="prof_prompt_filter",
    )

with col3:
    show_percentages = st.checkbox("Show as percentages", value=False, key="prof_pct")

# Filter data
filtered_data = data.copy()
if model_filter != "All models":
    filtered_data = filtered_data[filtered_data["model"] == model_filter]
if prompt_filter != "All prompts":
    filtered_data = filtered_data[filtered_data["prompt"] == prompt_filter]

# Create contingency table
if show_percentages:
    contingency = pd.crosstab(
        filtered_data["keyword"],
        filtered_data["pronoun_group"],
        normalize="index",
    ) * 100
    value_format = ".1f"
    title_suffix = " (%)"
else:
    contingency = pd.crosstab(
        filtered_data["keyword"],
        filtered_data["pronoun_group"],
    )
    value_format = ".0f"
    title_suffix = ""

# Reorder columns
col_order = [c for c in ["he/him", "she/her", "they/them", "none"] if c in contingency.columns]
contingency = contingency[col_order]

# Create heatmap
import plotly.graph_objects as go

fig = go.Figure(
    data=go.Heatmap(
        z=contingency.values,
        x=contingency.columns,
        y=contingency.index,
        colorscale="Blues",
        text=contingency.values,
        texttemplate=f"%{{text:{value_format}}}",
        textfont={"size": 12},
        hovertemplate="<b>%{y}</b><br>%{x}: %{z" + (":." + value_format + "}" if show_percentages else ":.0f}") + "<extra></extra>",
        colorbar=dict(title="Count" if not show_percentages else "Percent"),
    )
)

fig.update_layout(
    title=f"Profession × Pronoun Group{title_suffix}",
    xaxis_title="Pronoun Group",
    yaxis_title="Profession",
    height=max(400, len(contingency.index) * 50),
)

st.plotly_chart(fig, use_container_width=True)

# Analysis
st.subheader("📊 Analysis")

# Find most biased professions
if not contingency.empty:
    # Calculate bias scores for each profession
    bias_scores = {}
    for keyword in contingency.index:
        he_pct = contingency.loc[keyword, "he/him"] if "he/him" in contingency.columns else 0
        she_pct = contingency.loc[keyword, "she/her"] if "she/her" in contingency.columns else 0

        if not show_percentages:
            total = contingency.loc[keyword].sum()
            if total > 0:
                he_pct = (he_pct / total) * 100
                she_pct = (she_pct / total) * 100

        bias_scores[keyword] = {
            "bias_score": abs(he_pct - she_pct),
            "dominant": "he/him" if he_pct > she_pct else "she/her" if she_pct > he_pct else "balanced",
            "he_pct": he_pct,
            "she_pct": she_pct,
        }

    bias_df = pd.DataFrame.from_dict(bias_scores, orient="index")
    bias_df = bias_df.sort_values("bias_score", ascending=False)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**🔴 Most Biased Professions**")
        top_biased = bias_df.head(5)
        for keyword, row in top_biased.iterrows():
            dominant_icon = "👨" if row["dominant"] == "he/him" else "👩" if row["dominant"] == "she/her" else "⚖️"
            st.write(f"{dominant_icon} **{keyword}**: {row['bias_score']:.1f}% bias toward {row['dominant']}")

    with col2:
        st.markdown("**🟢 Most Balanced Professions**")
        least_biased = bias_df.tail(5).sort_values("bias_score")
        for keyword, row in least_biased.iterrows():
            st.write(f"⚖️ **{keyword}**: {row['bias_score']:.1f}% bias")

st.markdown("---")

# Section 2: Model × Pronoun Heatmap
st.header("2️⃣ Bias by Model")

st.markdown(
    """
    Compare bias patterns across different models. This shows whether some models
    exhibit stronger gender bias than others.
    """
)

# Filters
col1, col2, col3 = st.columns(3)

with col1:
    keyword_filter = st.selectbox(
        "Filter by Keyword",
        ["All keywords"] + list(data["keyword"].unique()),
        key="model_keyword_filter",
    )

with col2:
    prompt_filter_model = st.selectbox(
        "Filter by Prompt",
        ["All prompts"] + list(data["prompt"].unique()),
        key="model_prompt_filter",
    )

with col3:
    show_percentages_model = st.checkbox("Show as percentages", value=False, key="model_pct")

# Filter data
filtered_data_model = data.copy()
if keyword_filter != "All keywords":
    filtered_data_model = filtered_data_model[filtered_data_model["keyword"] == keyword_filter]
if prompt_filter_model != "All prompts":
    filtered_data_model = filtered_data_model[filtered_data_model["prompt"] == prompt_filter_model]

# Create contingency table
if show_percentages_model:
    contingency_model = pd.crosstab(
        filtered_data_model["model"],
        filtered_data_model["pronoun_group"],
        normalize="index",
    ) * 100
    value_format_model = ".1f"
    title_suffix_model = " (%)"
else:
    contingency_model = pd.crosstab(
        filtered_data_model["model"],
        filtered_data_model["pronoun_group"],
    )
    value_format_model = ".0f"
    title_suffix_model = ""

# Reorder columns
col_order_model = [c for c in ["he/him", "she/her", "they/them", "none"] if c in contingency_model.columns]
contingency_model = contingency_model[col_order_model]

# Create heatmap
fig_model = go.Figure(
    data=go.Heatmap(
        z=contingency_model.values,
        x=contingency_model.columns,
        y=contingency_model.index,
        colorscale="Blues",
        text=contingency_model.values,
        texttemplate=f"%{{text:{value_format_model}}}",
        textfont={"size": 12},
        hovertemplate="<b>%{y}</b><br>%{x}: %{z" + (":." + value_format_model + "}" if show_percentages_model else ":.0f}") + "<extra></extra>",
        colorbar=dict(title="Count" if not show_percentages_model else "Percent"),
    )
)

fig_model.update_layout(
    title=f"Model × Pronoun Group{title_suffix_model}",
    xaxis_title="Pronoun Group",
    yaxis_title="Model",
    height=max(300, len(contingency_model.index) * 60),
)

st.plotly_chart(fig_model, use_container_width=True)

# Model comparison
st.subheader("📊 Model Comparison")

if not contingency_model.empty:
    model_bias_scores = {}
    for model in contingency_model.index:
        he_pct_m = contingency_model.loc[model, "he/him"] if "he/him" in contingency_model.columns else 0
        she_pct_m = contingency_model.loc[model, "she/her"] if "she/her" in contingency_model.columns else 0

        if not show_percentages_model:
            total_m = contingency_model.loc[model].sum()
            if total_m > 0:
                he_pct_m = (he_pct_m / total_m) * 100
                she_pct_m = (she_pct_m / total_m) * 100

        model_bias_scores[model] = abs(he_pct_m - she_pct_m)

    model_bias_df = pd.DataFrame.from_dict(
        model_bias_scores, orient="index", columns=["Bias Score"]
    ).sort_values("Bias Score", ascending=False)

    import plotly.express as px

    fig_bar = px.bar(
        model_bias_df.reset_index(),
        x="index",
        y="Bias Score",
        labels={"index": "Model", "Bias Score": "Bias Score (%)"},
        title="Model Bias Scores (Lower is Better)",
        color="Bias Score",
        color_continuous_scale="RdYlGn_r",
    )

    fig_bar.update_layout(height=300)
    st.plotly_chart(fig_bar, use_container_width=True)

    # Best and worst
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**🏆 Least Biased Model**")
        best_model = model_bias_df.idxmin()[0]
        st.success(f"{best_model}: {model_bias_df.loc[best_model, 'Bias Score']:.2f}% bias")

    with col2:
        st.markdown("**⚠️ Most Biased Model**")
        worst_model = model_bias_df.idxmax()[0]
        st.warning(f"{worst_model}: {model_bias_df.loc[worst_model, 'Bias Score']:.2f}% bias")

st.markdown("---")

# Tips
st.info(
    """
    💡 **Tips for Interpretation:**
    
    - **Dark cells** indicate high frequency/percentage
    - **Light cells** indicate low frequency/percentage
    - Look for **rows with concentrated color** in one pronoun column
    - Compare **patterns across rows** to identify consistency
    - Use **percentage view** for fair comparison across different sample sizes
    """
)
