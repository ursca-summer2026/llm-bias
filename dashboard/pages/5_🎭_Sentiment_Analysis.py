"""
Sentiment Analysis page - Explore correlation between sentiment and gender bias.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sys
import numpy as np

# Add parent directory to path for imports
dashboard_dir = Path(__file__).parent.parent
if str(dashboard_dir) not in sys.path:
    sys.path.insert(0, str(dashboard_dir))

from components.charts import create_scatter_matrix, PRONOUN_COLORS
from components.help import show_help_sidebar, show_metric_explanation

st.set_page_config(page_title="Sentiment Analysis", page_icon="🎭", layout="wide")

st.title("🎭 Sentiment Analysis")
st.markdown("Explore correlations between sentiment and gender bias in model responses.")

# Load data
if "data" not in st.session_state or st.session_state.data is None:
    st.warning("⚠️ No data loaded. Please upload a database on the main page.")
    st.stop()

data = st.session_state.data.copy()

# Sidebar
show_help_sidebar()

st.sidebar.markdown("---")
st.sidebar.markdown("### Analysis Options")

# Try to import TextBlob for sentiment analysis
try:
    from textblob import TextBlob
    has_textblob = True
except ImportError:
    has_textblob = False
    st.error("""
    ⚠️ **TextBlob not installed**
    
    This page requires the TextBlob library for sentiment analysis.
    
    Install it with:
    ```bash
    pip install textblob
    python -m textblob.download_corpora
    ```
    """)
    st.stop()

# Calculate sentiment if not already done
if "sentiment_polarity" not in data.columns:
    with st.spinner("Analyzing sentiment... This may take a moment."):
        
        @st.cache_data
        def analyze_sentiment(texts):
            """Calculate sentiment polarity for all texts."""
            polarities = []
            subjectivities = []
            
            for text in texts:
                try:
                    blob = TextBlob(str(text))
                    polarities.append(blob.sentiment.polarity)
                    subjectivities.append(blob.sentiment.subjectivity)
                except:
                    polarities.append(0.0)
                    subjectivities.append(0.0)
            
            return polarities, subjectivities
        
        polarities, subjectivities = analyze_sentiment(data["output"].tolist())
        data["sentiment_polarity"] = polarities
        data["sentiment_subjectivity"] = subjectivities
        
        # Categorize sentiment
        data["sentiment_category"] = pd.cut(
            data["sentiment_polarity"],
            bins=[-1.0, -0.1, 0.1, 1.0],
            labels=["Negative", "Neutral", "Positive"]
        )
        
        # Update session state
        st.session_state.data = data

# Filters
st.sidebar.markdown("### Filters")

models = sorted(data["model"].unique())
selected_models = st.sidebar.multiselect(
    "Models",
    options=models,
    default=models
)

keywords = sorted(data["keyword"].unique())
selected_keywords = st.sidebar.multiselect(
    "Professions",
    options=keywords,
    default=keywords
)

prompts = sorted(data["prompt"].unique())
selected_prompts = st.sidebar.multiselect(
    "Prompts",
    options=prompts,
    default=prompts
)

filtered_data = data[
    (data["model"].isin(selected_models)) &
    (data["keyword"].isin(selected_keywords)) &
    (data["prompt"].isin(selected_prompts))
]

if len(filtered_data) == 0:
    st.error("No data matches the selected filters.")
    st.stop()

# Overview
st.markdown("## 📊 Sentiment Overview")

col1, col2, col3, col4 = st.columns(4)

with col1:
    avg_polarity = filtered_data["sentiment_polarity"].mean()
    st.metric("Avg Sentiment", f"{avg_polarity:.3f}", help="Range: -1 (negative) to +1 (positive)")

with col2:
    avg_subjectivity = filtered_data["sentiment_subjectivity"].mean()
    st.metric("Avg Subjectivity", f"{avg_subjectivity:.3f}", help="Range: 0 (objective) to 1 (subjective)")

with col3:
    positive_pct = (filtered_data["sentiment_polarity"] > 0.1).sum() / len(filtered_data) * 100
    st.metric("Positive Responses", f"{positive_pct:.1f}%")

with col4:
    negative_pct = (filtered_data["sentiment_polarity"] < -0.1).sum() / len(filtered_data) * 100
    st.metric("Negative Responses", f"{negative_pct:.1f}%")

# Sentiment Distribution
st.markdown("## 📈 Sentiment Distribution")

col1, col2 = st.columns(2)

with col1:
    # Histogram of sentiment polarity
    fig = px.histogram(
        filtered_data,
        x="sentiment_polarity",
        color="pronoun_group",
        title="Sentiment Polarity Distribution by Pronoun Group",
        color_discrete_map=PRONOUN_COLORS,
        nbins=30,
        barmode="overlay",
        opacity=0.7
    )
    fig.update_layout(
        xaxis_title="Sentiment Polarity",
        yaxis_title="Count",
        height=400
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    # Box plot
    fig = px.box(
        filtered_data,
        x="pronoun_group",
        y="sentiment_polarity",
        color="pronoun_group",
        title="Sentiment by Pronoun Group",
        color_discrete_map=PRONOUN_COLORS
    )
    fig.update_layout(
        xaxis_title="Pronoun Group",
        yaxis_title="Sentiment Polarity",
        height=400,
        showlegend=False
    )
    st.plotly_chart(fig, use_container_width=True)

# Sentiment-Gender Correlation
st.markdown("## 🔗 Sentiment-Gender Correlation Analysis")

with st.expander("ℹ️ How to Interpret", expanded=False):
    st.markdown("""
    **Sentiment Polarity** measures emotional tone:
    - **Positive values** (> 0): Happy, enthusiastic, optimistic language
    - **Negative values** (< 0): Sad, critical, pessimistic language
    - **Zero**: Neutral tone
    
    **Research Question:** Do models use different emotional tones when describing different genders?
    
    For example, do responses with "she/her" tend to be more positive or negative than those with "he/him"?
    """)

# Calculate correlation statistics
pronoun_sentiment = filtered_data.groupby("pronoun_group").agg({
    "sentiment_polarity": ["mean", "std", "count"],
    "sentiment_subjectivity": ["mean", "std"]
}).round(3)

pronoun_sentiment.columns = ["_".join(col).strip() for col in pronoun_sentiment.columns]
st.dataframe(
    pronoun_sentiment.style.background_gradient(subset=["sentiment_polarity_mean"], cmap="RdYlGn"),
    use_container_width=True
)

# Scatter plot: Polarity vs Subjectivity
st.markdown("### Sentiment Landscape")

fig = px.scatter(
    filtered_data.sample(min(1000, len(filtered_data))),  # Sample for performance
    x="sentiment_subjectivity",
    y="sentiment_polarity",
    color="pronoun_group",
    title="Sentiment Polarity vs Subjectivity (Sample)",
    color_discrete_map=PRONOUN_COLORS,
    hover_data=["keyword", "model"],
    opacity=0.6
)

# Add quadrant lines
fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
fig.add_vline(x=0.5, line_dash="dash", line_color="gray", opacity=0.5)

fig.update_layout(
    xaxis_title="Subjectivity (0=Objective, 1=Subjective)",
    yaxis_title="Polarity (-1=Negative, +1=Positive)",
    height=500
)
st.plotly_chart(fig, use_container_width=True)

# By Profession
st.markdown("## 👔 Sentiment by Profession")

col1, col2 = st.columns(2)

with col1:
    # Sentiment by keyword
    keyword_sentiment = filtered_data.groupby("keyword")["sentiment_polarity"].mean().sort_values()
    
    fig = go.Figure(go.Bar(
        x=keyword_sentiment.values,
        y=keyword_sentiment.index,
        orientation="h",
        marker=dict(
            color=keyword_sentiment.values,
            colorscale="RdYlGn",
            showscale=True,
            colorbar=dict(title="Sentiment")
        )
    ))
    
    fig.update_layout(
        title="Average Sentiment by Profession",
        xaxis_title="Sentiment Polarity",
        yaxis_title="Profession",
        height=max(400, len(keyword_sentiment) * 25)
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    # Pronoun group sentiment by keyword (top 10 keywords)
    top_keywords = filtered_data["keyword"].value_counts().head(10).index
    top_data = filtered_data[filtered_data["keyword"].isin(top_keywords)]
    
    keyword_pronoun_sentiment = top_data.groupby(
        ["keyword", "pronoun_group"]
    )["sentiment_polarity"].mean().reset_index()
    
    fig = px.bar(
        keyword_pronoun_sentiment,
        x="keyword",
        y="sentiment_polarity",
        color="pronoun_group",
        title="Sentiment by Profession and Pronoun (Top 10 Professions)",
        color_discrete_map=PRONOUN_COLORS,
        barmode="group"
    )
    fig.update_layout(
        xaxis_title="Profession",
        yaxis_title="Avg Sentiment",
        height=400
    )
    st.plotly_chart(fig, use_container_width=True)

# By Model
st.markdown("## 🤖 Sentiment by Model")

model_sentiment = filtered_data.groupby("model").agg({
    "sentiment_polarity": "mean",
    "sentiment_subjectivity": "mean"
}).reset_index()

col1, col2 = st.columns(2)

with col1:
    fig = px.bar(
        model_sentiment,
        x="model",
        y="sentiment_polarity",
        title="Average Sentiment by Model",
        color="sentiment_polarity",
        color_continuous_scale="RdYlGn"
    )
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    fig = px.bar(
        model_sentiment,
        x="model",
        y="sentiment_subjectivity",
        title="Average Subjectivity by Model",
        color="sentiment_subjectivity",
        color_continuous_scale="Blues"
    )
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)

# Statistical Test
st.markdown("## 📊 Statistical Significance Test")

with st.form("sentiment_test"):
    st.markdown("Test if sentiment differs significantly between pronoun groups:")
    
    col1, col2 = st.columns(2)
    
    with col1:
        group1 = st.selectbox("Group 1", ["he/him", "she/her", "they/them", "none"])
    
    with col2:
        group2 = st.selectbox("Group 2", ["she/her", "he/him", "they/them", "none"])
    
    submitted = st.form_submit_button("Run Test")
    
    if submitted and group1 != group2:
        from scipy import stats
        
        data1 = filtered_data[filtered_data["pronoun_group"] == group1]["sentiment_polarity"]
        data2 = filtered_data[filtered_data["pronoun_group"] == group2]["sentiment_polarity"]
        
        if len(data1) > 0 and len(data2) > 0:
            t_stat, p_value = stats.ttest_ind(data1, data2)
            
            st.markdown("### Results")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(f"{group1} Mean", f"{data1.mean():.3f}")
            
            with col2:
                st.metric(f"{group2} Mean", f"{data2.mean():.3f}")
            
            with col3:
                st.metric("Difference", f"{abs(data1.mean() - data2.mean()):.3f}")
            
            st.markdown(f"""
            **T-statistic:** {t_stat:.4f}  
            **P-value:** {p_value:.4f}  
            **Interpretation:** {'Significant difference' if p_value < 0.05 else 'No significant difference'} at α=0.05
            """)
            
            if p_value < 0.05:
                st.success(f"✅ Sentiment differs significantly between {group1} and {group2}")
            else:
                st.info(f"ℹ️ No significant sentiment difference between {group1} and {group2}")
        else:
            st.error("Insufficient data for comparison.")

# Sample Responses
st.markdown("## 📝 Example Responses by Sentiment")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### Most Positive Responses")
    top_positive = filtered_data.nlargest(3, "sentiment_polarity")
    
    for idx, row in top_positive.iterrows():
        st.markdown(f"""
        **{row['keyword']}** ({row['pronoun_group']}) - Sentiment: {row['sentiment_polarity']:.3f}  
        _{row['output'][:200]}..._
        """)

with col2:
    st.markdown("### Most Negative Responses")
    top_negative = filtered_data.nsmallest(3, "sentiment_polarity")
    
    for idx, row in top_negative.iterrows():
        st.markdown(f"""
        **{row['keyword']}** ({row['pronoun_group']}) - Sentiment: {row['sentiment_polarity']:.3f}  
        _{row['output'][:200]}..._
        """)

# Footer
st.markdown("---")
st.markdown("""
💡 **Insights:**
- Different sentiment patterns may reveal unconscious biases
- Consistently positive/negative sentiment toward specific groups warrants investigation
- Consider cultural and contextual factors in interpretation

📖 Click **?** in sidebar for detailed explanations of sentiment metrics.
""")
