"""
Overview page - High-level summary of bias patterns across all data.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sys

# Add parent directory to path for imports
dashboard_dir = Path(__file__).parent.parent
if str(dashboard_dir) not in sys.path:
    sys.path.insert(0, str(dashboard_dir))

from components.charts import create_stacked_bar, create_pie_chart, PRONOUN_COLORS
from components.help import show_help_sidebar

st.set_page_config(page_title="Overview", page_icon="📊", layout="wide")

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
        color: #1a1a1a;
    }
    .insight-box {
        background-color: #e8f4f8;
        padding: 15px;
        border-radius: 5px;
        border-left: 4px solid #2a78d6;
        margin: 10px 0;
        color: #1a1a1a;
    }
</style>
""", unsafe_allow_html=True)

st.title("📊 Overview Dashboard")
st.markdown("High-level summary of bias patterns across all data.")

# Load data
if "data" not in st.session_state or st.session_state.data is None:
    st.warning("⚠️ No data loaded. Please upload a database on the main page.")
    st.stop()

data = st.session_state.data

# Sidebar
show_help_sidebar()

st.sidebar.markdown("---")
st.sidebar.markdown("### Filters")

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
filtered_data = data[
    (data["model"].isin(selected_models)) &
    (data["keyword"].isin(selected_keywords)) &
    (data["prompt"].isin(selected_prompts))
]

if len(filtered_data) == 0:
    st.error("No data matches the selected filters.")
    st.stop()

# Key Metrics Row
st.markdown("## 📈 Key Metrics")

col1, col2, col3, col4 = st.columns(4)

with col1:
    total_responses = len(filtered_data)
    st.metric("Total Responses", f"{total_responses:,}")

with col2:
    n_models = filtered_data["model"].nunique()
    st.metric("Models Analyzed", n_models)

with col3:
    n_keywords = filtered_data["keyword"].nunique()
    st.metric("Professions Tested", n_keywords)

with col4:
    bias_score = (
        (filtered_data["pronoun_group"] == "he/him").sum() +
        (filtered_data["pronoun_group"] == "she/her").sum()
    ) / len(filtered_data) * 100
    st.metric("Gendered Response Rate", f"{bias_score:.1f}%")

# Pronoun Distribution
st.markdown("## 🎯 Overall Pronoun Distribution")

col1, col2 = st.columns([2, 1])

with col1:
    # Bar chart
    pronoun_counts = filtered_data["pronoun_group"].value_counts()
    fig = create_stacked_bar(
        data=filtered_data,
        x_col="pronoun_group",
        title="Response Distribution by Pronoun Group",
        show_percentages=True
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    # Pie chart
    fig_pie = create_pie_chart(
        filtered_data,
        "pronoun_group",
        title="Pronoun Proportions"
    )
    st.plotly_chart(fig_pie, use_container_width=True)

# Gender Balance Analysis
st.markdown("## ⚖️ Gender Balance Analysis")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### By Model")
    
    model_pronoun = pd.crosstab(
        filtered_data["model"],
        filtered_data["pronoun_group"],
        normalize="index"
    ) * 100
    
    fig = go.Figure()
    for pronoun in ["he/him", "she/her", "they/them", "none"]:
        if pronoun in model_pronoun.columns:
            fig.add_trace(go.Bar(
                name=pronoun,
                x=model_pronoun.index,
                y=model_pronoun[pronoun],
                marker_color=PRONOUN_COLORS[pronoun]
            ))
    
    fig.update_layout(
        barmode="stack",
        title="Pronoun Distribution by Model (%)",
        xaxis_title="Model",
        yaxis_title="Percentage",
        height=400
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown("### By Profession")
    
    keyword_pronoun = pd.crosstab(
        filtered_data["keyword"],
        filtered_data["pronoun_group"],
        normalize="index"
    ) * 100
    
    fig = go.Figure()
    for pronoun in ["he/him", "she/her", "they/them", "none"]:
        if pronoun in keyword_pronoun.columns:
            fig.add_trace(go.Bar(
                name=pronoun,
                x=keyword_pronoun.index,
                y=keyword_pronoun[pronoun],
                marker_color=PRONOUN_COLORS[pronoun]
            ))
    
    fig.update_layout(
        barmode="stack",
        title="Pronoun Distribution by Profession (%)",
        xaxis_title="Profession",
        yaxis_title="Percentage",
        height=400
    )
    st.plotly_chart(fig, use_container_width=True)

# Key Insights
st.markdown("## 💡 Key Insights")

# Calculate insights
he_pct = (filtered_data["pronoun_group"] == "he/him").sum() / len(filtered_data) * 100
she_pct = (filtered_data["pronoun_group"] == "she/her").sum() / len(filtered_data) * 100
they_pct = (filtered_data["pronoun_group"] == "they/them").sum() / len(filtered_data) * 100
none_pct = (filtered_data["pronoun_group"] == "none").sum() / len(filtered_data) * 100

# Most biased profession
keyword_bias = filtered_data.groupby("keyword").apply(
    lambda x: abs(
        (x["pronoun_group"] == "he/him").sum() - 
        (x["pronoun_group"] == "she/her").sum()
    ) / len(x) * 100
)
most_biased = keyword_bias.idxmax()
bias_value = keyword_bias.max()

# Most balanced profession
most_balanced = keyword_bias.idxmin()
balance_value = keyword_bias.min()

# Display insights
col1, col2 = st.columns(2)

with col1:
    st.markdown(f"""
    <div class="insight-box">
    <h4>🔵 Gender Representation</h4>
    <ul>
        <li><strong>He/Him:</strong> {he_pct:.1f}% of responses</li>
        <li><strong>She/Her:</strong> {she_pct:.1f}% of responses</li>
        <li><strong>They/Them:</strong> {they_pct:.1f}% of responses</li>
        <li><strong>No Pronouns:</strong> {none_pct:.1f}% of responses</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="insight-box">
    <h4>⚖️ Bias Patterns</h4>
    <ul>
        <li><strong>Most Biased:</strong> {most_biased} ({bias_value:.1f}% difference)</li>
        <li><strong>Most Balanced:</strong> {most_balanced} ({balance_value:.1f}% difference)</li>
        <li><strong>Gendered Rate:</strong> {he_pct + she_pct:.1f}% use gendered pronouns</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)

# Model Comparison Summary
st.markdown("## 🔬 Model Comparison Summary")

model_summary = filtered_data.groupby("model").agg({
    "id": "count",
    "pronoun_group": lambda x: (x.isin(["he/him", "she/her"])).sum() / len(x) * 100
}).rename(columns={"id": "Total Responses", "pronoun_group": "Gendered %"})

model_summary = model_summary.sort_values("Gendered %", ascending=False)

st.dataframe(
    model_summary.style.format({
        "Total Responses": "{:,.0f}",
        "Gendered %": "{:.1f}%"
    }).background_gradient(subset=["Gendered %"], cmap="RdYlGn_r"),
    use_container_width=True
)

# Profession Ranking
st.markdown("## 🏆 Profession Rankings")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### Most Male-Associated")
    male_prof = filtered_data.groupby("keyword").apply(
        lambda x: (x["pronoun_group"] == "he/him").sum() / len(x) * 100
    ).sort_values(ascending=False).head(10)
    
    for i, (prof, pct) in enumerate(male_prof.items(), 1):
        st.write(f"{i}. **{prof}**: {pct:.1f}%")

with col2:
    st.markdown("### Most Female-Associated")
    female_prof = filtered_data.groupby("keyword").apply(
        lambda x: (x["pronoun_group"] == "she/her").sum() / len(x) * 100
    ).sort_values(ascending=False).head(10)
    
    for i, (prof, pct) in enumerate(female_prof.items(), 1):
        st.write(f"{i}. **{prof}**: {pct:.1f}%")

# Footer
st.markdown("---")
st.markdown("""
💡 **Tip:** Use the filters in the sidebar to focus on specific models or professions.  
📖 Click the **?** in the sidebar for help understanding these metrics.
""")
