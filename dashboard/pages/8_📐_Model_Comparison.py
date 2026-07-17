"""
Model Comparison Page

Provides tools for comparing multiple models using:
- Cosine similarity analysis
- Response pattern comparison
- Side-by-side bias metrics
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from llm_bias_research.ml_analyzer import MLBiasAnalyzer
from dashboard.components.help import show_metric_explanation
from dashboard.components.charts import create_scatter_matrix, create_grouped_bar

st.set_page_config(page_title="Model Comparison", page_icon="📐", layout="wide")

st.title("📐 Model Comparison")

st.markdown(
    """
    Compare multiple models using cosine similarity and bias metrics.
    Identify which models produce similar outputs and which show different bias patterns.
    
    💡 **Tip:** Upload multiple database files (one per model) in the main page sidebar to enable comparison.
    """
)

# Check if data is loaded
if "data" not in st.session_state:
    st.warning("⚠️ Please load data from the main page first.")
    st.stop()

data = st.session_state["data"]

# Check if we have multiple models
if data["model"].nunique() < 2:
    st.warning("⚠️ At least 2 models are required for comparison. Current dataset has only 1 model.")
    st.info(
        """
        💡 **To add more models:**
        
        **Option 1 (Recommended):** Upload multiple database files in the main page sidebar
        - Each database file contains data for one model
        - Upload 2+ files to enable multi-model comparison
        
        **Option 2:** Run the query command with different models to separate databases:
        ```bash
        llm-bias query --model phi3 --keywords "Nurse,Doctor" \\
          --prompt-file prompts/default_prompts.txt --output results/phi3_study
        
        llm-bias query --model llama3.2 --keywords "Nurse,Doctor" \\
          --prompt-file prompts/default_prompts.txt --output results/llama_study
        ```
        Then upload both `phi3_study.db` and `llama_study.db` files.
        """
    )
    st.stop()

ml_analyzer = MLBiasAnalyzer(data)

st.markdown("---")

# Section 1: Cosine Similarity Matrix
st.header("1️⃣ Model Similarity Matrix")

st.markdown(
    """
    Cosine similarity measures how similar the textual content of responses is between models.
    High similarity (close to 1.0) suggests similar training data or model architectures.
    """
)

show_metric_explanation("cosine_similarity")

col1, col2 = st.columns(2)

with col1:
    keyword_filter = st.selectbox(
        "Filter by keyword (optional)",
        ["All keywords"] + list(data["keyword"].unique()),
        help="Narrow comparison to a specific profession",
    )

with col2:
    prompt_filter = st.selectbox(
        "Filter by prompt (optional)",
        ["All prompts"] + list(data["prompt"].unique()),
        help="Narrow comparison to a specific prompt",
    )

keyword_param = None if keyword_filter == "All keywords" else keyword_filter
prompt_param = None if prompt_filter == "All prompts" else prompt_filter

if st.button("Compute Similarity Matrix", type="primary"):
    with st.spinner("Computing pairwise similarities (this may take a moment)..."):
        # Filter data if prompt is selected
        filtered_data = data.copy()
        if prompt_param:
            filtered_data = filtered_data[filtered_data["prompt"] == prompt_param]
            ml_analyzer_filtered = MLBiasAnalyzer(filtered_data)
            similarity_matrix = ml_analyzer_filtered.compare_all_models(keyword=keyword_param)
        else:
            similarity_matrix = ml_analyzer.compare_all_models(keyword=keyword_param)

        st.subheader("Similarity Heatmap")
        fig = create_scatter_matrix(
            similarity_matrix,
            title="Model Similarity Matrix (Cosine Similarity)"
        )
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Similarity Table")
        st.dataframe(
            similarity_matrix.style.format("{:.3f}").background_gradient(
                cmap="RdYlGn", vmin=0, vmax=1
            ),
            use_container_width=True,
        )

        # Find most and least similar pairs
        models = similarity_matrix.index.tolist()
        similarities = []

        for i, model1 in enumerate(models):
            for j, model2 in enumerate(models):
                if i < j:
                    similarities.append(
                        (model1, model2, similarity_matrix.loc[model1, model2])
                    )

        similarities_df = pd.DataFrame(
            similarities, columns=["Model 1", "Model 2", "Similarity"]
        )
        similarities_df = similarities_df.sort_values("Similarity", ascending=False)

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("🔗 Most Similar Models")
            top_similar = similarities_df.head(3)
            for _, row in top_similar.iterrows():
                st.metric(
                    f"{row['Model 1']} ↔ {row['Model 2']}",
                    f"{row['Similarity']:.3f}",
                )

        with col2:
            st.subheader("🔀 Most Different Models")
            top_different = similarities_df.tail(3)
            for _, row in top_different.iterrows():
                st.metric(
                    f"{row['Model 1']} ↔ {row['Model 2']}",
                    f"{row['Similarity']:.3f}",
                )

st.markdown("---")

# Section 2: Pairwise Detailed Comparison
st.header("2️⃣ Detailed Pairwise Comparison")

st.markdown(
    """
    Compare two specific models in detail, including similarity metrics
    and bias pattern differences.
    """
)

col1, col2 = st.columns(2)

models = data["model"].unique().tolist()

with col1:
    model1 = st.selectbox("Select Model 1", models, key="m1")

with col2:
    model2 = st.selectbox(
        "Select Model 2",
        [m for m in models if m != model1],
        key="m2",
    )

col1, col2 = st.columns(2)

with col1:
    compare_keyword = st.selectbox(
        "Keyword to compare (optional)",
        ["All keywords"] + list(data["keyword"].unique()),
        key="comp_keyword",
    )

with col2:
    compare_prompt = st.selectbox(
        "Prompt to compare (optional)",
        ["All prompts"] + list(data["prompt"].unique()),
        key="comp_prompt",
    )

compare_keyword_param = None if compare_keyword == "All keywords" else compare_keyword
compare_prompt_param = None if compare_prompt == "All prompts" else compare_prompt

if st.button("Compare Models", type="primary"):
    with st.spinner("Analyzing models..."):
        # Filter data if prompt is selected
        filtered_data = data.copy()
        if compare_prompt_param:
            filtered_data = filtered_data[filtered_data["prompt"] == compare_prompt_param]
            ml_analyzer_filtered = MLBiasAnalyzer(filtered_data)
            similarity_result = ml_analyzer_filtered.compute_response_similarity(
                model1, model2, keyword=compare_keyword_param
            )
        else:
            similarity_result = ml_analyzer.compute_response_similarity(
                model1, model2, keyword=compare_keyword_param
            )

        st.subheader(f"📊 {model1} vs {model2}")
        
        # Check for errors
        if "error" in similarity_result:
            st.error(f"❌ {similarity_result['error']}")
            st.info(
                "This usually happens when there's insufficient data for the selected filters. "
                "Try broadening your selection (e.g., removing keyword or prompt filters)."
            )
            st.stop()

        # Display metrics
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Overall Similarity", f"{similarity_result['overall_similarity']:.3f}")

        with col2:
            st.metric("Pairwise Mean", f"{similarity_result['pairwise_mean']:.3f}")

        with col3:
            st.metric("Pairwise Std Dev", f"{similarity_result['pairwise_std']:.3f}")

        # Interpretation
        sim_score = similarity_result["overall_similarity"]
        if sim_score > 0.8:
            interpretation = "Very similar - models produce highly comparable outputs"
            color = "green"
        elif sim_score > 0.6:
            interpretation = "Moderately similar - some commonality in responses"
            color = "blue"
        elif sim_score > 0.4:
            interpretation = "Somewhat different - distinct response patterns"
            color = "orange"
        else:
            interpretation = "Very different - models show divergent outputs"
            color = "red"

        st.markdown(f":{color}[**{interpretation}**]")

        # Compare pronoun distributions
        st.subheader("Pronoun Distribution Comparison")

        filter_data = data.copy()
        if compare_keyword_param:
            filter_data = filter_data[filter_data["keyword"] == compare_keyword_param]
        if compare_prompt_param:
            filter_data = filter_data[filter_data["prompt"] == compare_prompt_param]

        model1_data = filter_data[filter_data["model"] == model1]
        model2_data = filter_data[filter_data["model"] == model2]
        
        # Check if we have data for both models
        if len(model1_data) == 0 or len(model2_data) == 0:
            st.warning("⚠️ Insufficient data for pronoun distribution comparison with selected filters.")
        else:
            pronoun_comp = pd.DataFrame(
                {
                    model1: model1_data["pronoun_group"].value_counts(normalize=True) * 100,
                    model2: model2_data["pronoun_group"].value_counts(normalize=True) * 100,
                }
            ).fillna(0)

            import plotly.graph_objects as go

            fig = go.Figure()

            fig.add_trace(
                go.Bar(
                    name=model1,
                    x=pronoun_comp.index,
                    y=pronoun_comp[model1],
                    marker_color="#2a78d6",
                )
            )

            fig.add_trace(
                go.Bar(
                    name=model2,
                    x=pronoun_comp.index,
                    y=pronoun_comp[model2],
                    marker_color="#1baf7a",
                )
            )

            fig.update_layout(
                barmode="group",
                title="Pronoun Usage Comparison (%)",
                xaxis_title="Pronoun Group",
                yaxis_title="Percentage",
                height=400,
            )

            st.plotly_chart(fig, use_container_width=True)

            # Bias scores - with safety checks for missing pronoun groups
            he_him_model1 = pronoun_comp.loc["he/him", model1] if "he/him" in pronoun_comp.index else 0
            she_her_model1 = pronoun_comp.loc["she/her", model1] if "she/her" in pronoun_comp.index else 0
            he_him_model2 = pronoun_comp.loc["he/him", model2] if "he/him" in pronoun_comp.index else 0
            she_her_model2 = pronoun_comp.loc["she/her", model2] if "she/her" in pronoun_comp.index else 0
            
            model1_bias = abs(he_him_model1 - she_her_model1)
            model2_bias = abs(he_him_model2 - she_her_model2)

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric(f"{model1} Bias Score", f"{model1_bias:.3f}")

            with col2:
                st.metric(f"{model2} Bias Score", f"{model2_bias:.3f}")

            with col3:
                bias_diff = model1_bias - model2_bias
                st.metric(
                    "Bias Difference",
                    f"{bias_diff:.3f}",
                    delta=f"{bias_diff:.3f}",
                    delta_color="inverse",
                )

st.markdown("---")

# Section 3: Multi-Model Overview
st.header("3️⃣ All Models Overview")

st.markdown(
    """
    Compare bias metrics across all available models simultaneously.
    """
)

# Calculate metrics for each model
model_metrics = []

for model in data["model"].unique():
    model_data = data[data["model"] == model]
    pronoun_dist = model_data["pronoun_group"].value_counts(normalize=True)

    bias_score = abs(
        pronoun_dist.get("he/him", 0) - pronoun_dist.get("she/her", 0)
    )

    model_metrics.append(
        {
            "Model": model,
            "Total Responses": len(model_data),
            "he/him %": pronoun_dist.get("he/him", 0) * 100,
            "she/her %": pronoun_dist.get("she/her", 0) * 100,
            "they/them %": pronoun_dist.get("they/them", 0) * 100,
            "none %": pronoun_dist.get("none", 0) * 100,
            "Bias Score": bias_score,
        }
    )

metrics_df = pd.DataFrame(model_metrics)

st.dataframe(
    metrics_df.style.format(
        {
            "he/him %": "{:.1f}",
            "she/her %": "{:.1f}",
            "they/them %": "{:.1f}",
            "none %": "{:.1f}",
            "Bias Score": "{:.3f}",
        }
    ).background_gradient(subset=["Bias Score"], cmap="RdYlGn_r"),
    use_container_width=True,
)

# Bias score ranking
st.subheader("Model Ranking by Bias Score")

sorted_metrics = metrics_df.sort_values("Bias Score")

import plotly.express as px

fig = px.bar(
    sorted_metrics,
    x="Model",
    y="Bias Score",
    title="Bias Score by Model (Lower is Better)",
    color="Bias Score",
    color_continuous_scale="RdYlGn_r",
)

fig.update_layout(height=400)
st.plotly_chart(fig, use_container_width=True)

st.info(
    """
    💡 **Understanding Bias Scores:**
    - **Lower score** = more balanced between he/him and she/her
    - **Higher score** = stronger preference for one gender
    - Scores close to 0 indicate gender-neutral responses
    - Scores close to 1 indicate complete gender bias
    """
)
