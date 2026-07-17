"""
Time Series Analysis page - Track bias changes over time or across model versions.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sys
from datetime import datetime

# Add parent directory to path for imports
dashboard_dir = Path(__file__).parent.parent
if str(dashboard_dir) not in sys.path:
    sys.path.insert(0, str(dashboard_dir))

from components.charts import create_line_chart, PRONOUN_COLORS
from components.help import show_help_sidebar, show_metric_explanation

st.set_page_config(page_title="Time Series Analysis", page_icon="📈", layout="wide")

st.title("📈 Time Series Analysis")
st.markdown("Track how bias patterns change over time or across model versions.")

# Load data
if "data" not in st.session_state or st.session_state.data is None:
    st.warning("⚠️ No data loaded. Please upload a database on the main page.")
    st.stop()

data = st.session_state.data

# Sidebar
show_help_sidebar()

st.sidebar.markdown("---")
st.sidebar.markdown("### Analysis Options")

# Check if timestamp exists
has_timestamp = "created_at" in data.columns

if not has_timestamp:
    st.info("""
    ℹ️ **Time Series Analysis Requires Timestamps**
    
    Your current database doesn't have timestamp information. To enable time series analysis:
    
    1. Collect data at different times
    2. Ensure the database includes `created_at` timestamps
    3. Compare multiple database files from different collection periods
    
    **Alternative:** You can still analyze patterns across model versions if your data includes version information.
    """)
    
    # Show model version analysis instead
    st.markdown("## 🔄 Model Version Comparison")
    
    # Extract version numbers if model names contain them
    data["model_base"] = data["model"].str.replace(r'\d+\.\d+', '', regex=True)
    data["model_version"] = data["model"].str.extract(r'(\d+\.\d+)')[0]
    
    if data["model_version"].notna().any():
        st.markdown("### Bias Trends Across Model Versions")
        
        version_trends = data.groupby(["model_base", "model_version", "pronoun_group"]).size().reset_index(name="count")
        
        for model_base in version_trends["model_base"].unique():
            model_data = version_trends[version_trends["model_base"] == model_base]
            
            fig = px.line(
                model_data,
                x="model_version",
                y="count",
                color="pronoun_group",
                title=f"Pronoun Usage Trends: {model_base}",
                markers=True,
                color_discrete_map=PRONOUN_COLORS
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No model version information found in the data.")
    
    st.stop()

# Convert timestamp to datetime
data["timestamp"] = pd.to_datetime(data["created_at"])
data = data.sort_values("timestamp")

# Analysis type
analysis_type = st.sidebar.radio(
    "Analysis Type",
    ["Overall Trends", "By Keyword", "By Model", "Custom Comparison"],
    help="Choose what to track over time"
)

# Date range filter
st.sidebar.markdown("### Date Range")
min_date = data["timestamp"].min().date()
max_date = data["timestamp"].max().date()

date_range = st.sidebar.date_input(
    "Select Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

# Additional filters
st.sidebar.markdown("### Additional Filters")

models = sorted(data["model"].unique())
selected_models = st.sidebar.multiselect(
    "Models",
    options=models,
    default=models
)

keywords = sorted(data["keyword"].unique())
selected_keywords = st.sidebar.multiselect(
    "Keywords/Professions",
    options=keywords,
    default=keywords
)

prompts = sorted(data["prompt"].unique())
selected_prompts = st.sidebar.multiselect(
    "Prompts",
    options=prompts,
    default=prompts
)

if len(date_range) == 2:
    start_date, end_date = date_range
    filtered_data = data[
        (data["timestamp"].dt.date >= start_date) &
        (data["timestamp"].dt.date <= end_date) &
        (data["model"].isin(selected_models)) &
        (data["keyword"].isin(selected_keywords)) &
        (data["prompt"].isin(selected_prompts))
    ]
else:
    filtered_data = data[
        (data["model"].isin(selected_models)) &
        (data["keyword"].isin(selected_keywords)) &
        (data["prompt"].isin(selected_prompts))
    ]

# Time aggregation
time_agg = st.sidebar.selectbox(
    "Time Aggregation",
    ["Day", "Week", "Month"],
    help="How to group data points"
)

# Resample data based on aggregation
if time_agg == "Day":
    freq = "D"
elif time_agg == "Week":
    freq = "W"
else:
    freq = "M"

# Overall Trends
if analysis_type == "Overall Trends":
    st.markdown("## 📊 Overall Pronoun Usage Over Time")
    
    # Calculate proportions over time
    time_groups = filtered_data.groupby([pd.Grouper(key="timestamp", freq=freq), "pronoun_group"]).size()
    time_proportions = time_groups.groupby(level=0).apply(lambda x: x / x.sum() * 100)
    time_proportions = time_proportions.reset_index(name="percentage")
    
    # Line chart
    fig = go.Figure()
    
    for pronoun in ["he/him", "she/her", "they/them", "none"]:
        pronoun_data = time_proportions[time_proportions["pronoun_group"] == pronoun]
        fig.add_trace(go.Scatter(
            x=pronoun_data["timestamp"],
            y=pronoun_data["percentage"],
            name=pronoun,
            mode="lines+markers",
            line=dict(color=PRONOUN_COLORS[pronoun], width=2),
            marker=dict(size=8)
        ))
    
    fig.update_layout(
        title="Pronoun Usage Trends Over Time",
        xaxis_title="Date",
        yaxis_title="Percentage of Responses",
        hovermode="x unified",
        height=500
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Summary statistics
    st.markdown("### 📈 Trend Summary")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # He/Him trend
        he_data = time_proportions[time_proportions["pronoun_group"] == "he/him"]["percentage"]
        he_change = he_data.iloc[-1] - he_data.iloc[0] if len(he_data) > 1 else 0
        st.metric(
            "He/Him Trend",
            f"{he_data.iloc[-1]:.1f}%" if len(he_data) > 0 else "N/A",
            f"{he_change:+.1f}%"
        )
    
    with col2:
        # She/Her trend
        she_data = time_proportions[time_proportions["pronoun_group"] == "she/her"]["percentage"]
        she_change = she_data.iloc[-1] - she_data.iloc[0] if len(she_data) > 1 else 0
        st.metric(
            "She/Her Trend",
            f"{she_data.iloc[-1]:.1f}%" if len(she_data) > 0 else "N/A",
            f"{she_change:+.1f}%"
        )
    
    with col3:
        # They/Them trend
        they_data = time_proportions[time_proportions["pronoun_group"] == "they/them"]["percentage"]
        they_change = they_data.iloc[-1] - they_data.iloc[0] if len(they_data) > 1 else 0
        st.metric(
            "They/Them Trend",
            f"{they_data.iloc[-1]:.1f}%" if len(they_data) > 0 else "N/A",
            f"{they_change:+.1f}%"
        )

# By Keyword
elif analysis_type == "By Keyword":
    st.markdown("## 🔍 Trends by Profession/Keyword")
    
    selected_keywords = st.multiselect(
        "Select Keywords to Track",
        options=sorted(filtered_data["keyword"].unique()),
        default=list(sorted(filtered_data["keyword"].unique()))[:3],
        help="Compare trends for specific professions"
    )
    
    if selected_keywords:
        keyword_data = filtered_data[filtered_data["keyword"].isin(selected_keywords)]
        
        # Gendered pronoun usage over time by keyword
        keyword_time = keyword_data.groupby([
            pd.Grouper(key="timestamp", freq=freq),
            "keyword",
            "pronoun_group"
        ]).size().reset_index(name="count")
        
        keyword_time["total"] = keyword_time.groupby([
            "timestamp", "keyword"
        ])["count"].transform("sum")
        keyword_time["percentage"] = keyword_time["count"] / keyword_time["total"] * 100
        
        # Plot for each pronoun group
        for pronoun in ["he/him", "she/her", "they/them"]:
            st.markdown(f"### {pronoun.title()} Usage")
            
            pronoun_data = keyword_time[keyword_time["pronoun_group"] == pronoun]
            
            fig = px.line(
                pronoun_data,
                x="timestamp",
                y="percentage",
                color="keyword",
                title=f"{pronoun.title()} Trends by Profession",
                markers=True
            )
            fig.update_layout(
                xaxis_title="Date",
                yaxis_title="Percentage",
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Please select at least one keyword to analyze.")

# By Model
elif analysis_type == "By Model":
    st.markdown("## 🤖 Trends by Model")
    
    selected_models = st.multiselect(
        "Select Models to Track",
        options=sorted(filtered_data["model"].unique()),
        default=list(sorted(filtered_data["model"].unique())),
        help="Compare trends across different models"
    )
    
    if selected_models:
        model_data = filtered_data[filtered_data["model"].isin(selected_models)]
        
        # Bias score over time
        model_time = model_data.groupby([
            pd.Grouper(key="timestamp", freq=freq),
            "model"
        ]).apply(
            lambda x: (x["pronoun_group"].isin(["he/him", "she/her"])).sum() / len(x) * 100
        ).reset_index(name="bias_score")
        
        fig = px.line(
            model_time,
            x="timestamp",
            y="bias_score",
            color="model",
            title="Gendered Pronoun Usage by Model Over Time",
            markers=True
        )
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Gendered Pronoun Rate (%)",
            height=500
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Gender balance over time
        st.markdown("### Gender Balance Evolution")
        
        balance_time = model_data.groupby([
            pd.Grouper(key="timestamp", freq=freq),
            "model"
        ]).apply(
            lambda x: abs(
                (x["pronoun_group"] == "he/him").sum() -
                (x["pronoun_group"] == "she/her").sum()
            ) / len(x) * 100
        ).reset_index(name="imbalance")
        
        fig = px.line(
            balance_time,
            x="timestamp",
            y="imbalance",
            color="model",
            title="Gender Imbalance Over Time (Lower is Better)",
            markers=True
        )
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Imbalance Score (%)",
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Please select at least one model to analyze.")

# Custom Comparison
else:
    st.markdown("## 🔬 Custom Time Series Comparison")
    
    col1, col2 = st.columns(2)
    
    with col1:
        comparison_var = st.selectbox(
            "Primary Variable",
            ["keyword", "model", "pronoun_group"],
            help="What to track over time"
        )
        
        values = sorted(filtered_data[comparison_var].unique())
        selected_values = st.multiselect(
            f"Select {comparison_var.title()}s",
            options=values,
            default=values[:min(3, len(values))]
        )
    
    with col2:
        metric_type = st.selectbox(
            "Metric",
            ["Count", "Percentage", "Bias Score"],
            help="What metric to plot"
        )
    
    if selected_values:
        plot_data = filtered_data[filtered_data[comparison_var].isin(selected_values)]
        
        if metric_type == "Count":
            time_series = plot_data.groupby([
                pd.Grouper(key="timestamp", freq=freq),
                comparison_var
            ]).size().reset_index(name="value")
            ylabel = "Count"
            
        elif metric_type == "Percentage":
            time_series = plot_data.groupby([
                pd.Grouper(key="timestamp", freq=freq),
                comparison_var
            ]).size()
            time_series = time_series.groupby(level=0).apply(
                lambda x: x / x.sum() * 100
            ).reset_index(name="value")
            ylabel = "Percentage"
            
        else:  # Bias Score
            time_series = plot_data.groupby([
                pd.Grouper(key="timestamp", freq=freq),
                comparison_var
            ]).apply(
                lambda x: (x["pronoun_group"].isin(["he/him", "she/her"])).sum() / len(x) * 100
            ).reset_index(name="value")
            ylabel = "Gendered Pronoun Rate (%)"
        
        fig = px.line(
            time_series,
            x="timestamp",
            y="value",
            color=comparison_var,
            title=f"{metric_type} Over Time by {comparison_var.title()}",
            markers=True
        )
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title=ylabel,
            height=500
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info(f"Please select at least one {comparison_var} to analyze.")

# Export options
st.markdown("---")
st.markdown("### 📥 Export Time Series Data")

col1, col2 = st.columns([3, 1])

with col1:
    st.markdown("Download the time series data for further analysis in Excel or other tools.")

with col2:
    if st.button("Download CSV"):
        csv = filtered_data.to_csv(index=False)
        st.download_button(
            "⬇️ Download",
            csv,
            "time_series_data.csv",
            "text/csv"
        )

# Footer
st.markdown("---")
st.markdown("""
💡 **Tips:**
- Look for gradual changes that might indicate model learning or drift
- Compare time periods before and after model updates
- Consider external factors that might influence results (data collection changes, prompt modifications)

📖 For help interpreting trends, click the **?** in the sidebar.
""")
