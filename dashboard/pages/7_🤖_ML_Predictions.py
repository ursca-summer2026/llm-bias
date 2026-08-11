"""
ML Predictions page - Use machine learning to predict and analyze bias patterns.
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

from components.charts import PRONOUN_COLORS
from components.help import show_help_sidebar, show_metric_explanation

st.set_page_config(page_title="ML Predictions", page_icon="🤖", layout="wide")

st.title("🤖 Machine Learning Predictions")
st.markdown("Use ML to predict bias patterns and identify key factors.")

# Load data
if "data" not in st.session_state or st.session_state.data is None:
    st.warning("⚠️ No data loaded. Please upload a database on the main page.")
    st.stop()

data = st.session_state.data.copy()

# Sidebar
show_help_sidebar()

st.sidebar.markdown("---")
st.sidebar.markdown("### ML Options")

# Import ML analyzer
try:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
    from llm_bias_research.ml_analyzer import MLBiasAnalyzer
    has_ml = True
except ImportError:
    has_ml = False
    st.error("""
    ⚠️ **ML Analyzer not available**
    
    Could not import the ML analysis module.
    """)
    st.stop()

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

filtered_data = data[
    (data["model"].isin(selected_models)) &
    (data["keyword"].isin(selected_keywords)) &
    (data["prompt"].isin(selected_prompts))
]

if len(filtered_data) == 0:
    st.error("No data matches the selected filters.")
    st.stop()

# Initialize ML analyzer
analyzer = MLBiasAnalyzer(filtered_data)

# Overview
st.markdown("## 🎯 ML Analysis Overview")

with st.expander("ℹ️ About ML Predictions", expanded=False):
    st.markdown("""
    **Machine Learning Analysis** uses algorithms to:
    
    1. **Predict** which pronoun group a response belongs to based on profession and prompt
    2. **Identify** which factors (keywords, models) most strongly predict bias
    3. **Measure** feature importance to understand what drives bias patterns
    
    **Random Forest Classifier** is used because it:
    - Handles categorical data well
    - Provides feature importance scores
    - Resists overfitting
    - Works with non-linear relationships
    """)

# Bias Prediction Model
st.markdown("## 🧠 Bias Prediction Model")

with st.spinner("Training Random Forest classifier..."):
    try:
        # Train model
        results = analyzer.train_bias_predictor()
        
        # Display results
        col1, col2, col3, col4 = st.columns(4)
        train_accuracy = results.get("train_accuracy", 0.0)
        test_accuracy = results.get("test_accuracy", 0.0)
        cv_scores = results.get("cv_scores", [])
        if not cv_scores:
            cv_scores = [results.get("cv_mean_accuracy", 0.0)]
        
        with col1:
            st.metric(
                "Training Accuracy",
                f"{train_accuracy:.1%}",
                help="How well the model fits training data"
            )
        
        with col2:
            st.metric(
                "Test Accuracy",
                f"{test_accuracy:.1%}",
                help="How well the model predicts unseen data"
            )
        
        with col3:
            cv_mean = np.mean(cv_scores)
            cv_std = np.std(cv_scores)
            st.metric(
                "Cross-Val Accuracy",
                f"{cv_mean:.1%}",
                help=f"Mean ± Std: {cv_mean:.1%} ± {cv_std:.1%}"
            )
        
        with col4:
            # Calculate baseline (most frequent class)
            baseline = filtered_data["pronoun_group"].value_counts().max() / len(filtered_data)
            improvement = test_accuracy - baseline
            st.metric(
                "vs Baseline",
                f"+{improvement:.1%}",
                help=f"Baseline: {baseline:.1%} (always predict most common)"
            )
        
        # Model interpretation
        if test_accuracy > 0.5:
            if test_accuracy > 0.7:
                interpretation = "🟢 **Strong predictive power** - Bias patterns are highly systematic"
            elif test_accuracy > 0.6:
                interpretation = "🟡 **Moderate predictive power** - Some bias patterns are learnable"
            else:
                interpretation = "🟠 **Weak predictive power** - Bias patterns exist but are complex"
        else:
            interpretation = "🔴 **No predictive power** - Bias appears random or model needs improvement"
        
        st.markdown(interpretation)
        
        # Feature Importance
        st.markdown("## 🔑 Feature Importance")
        
        st.markdown("""
        **Feature importance** shows which factors most strongly predict bias.  
        Higher values = more influential in determining pronoun usage.
        """)
        
        feature_names = results.get("feature_names", [])
        feature_importance_values = results.get("feature_importance", [])
        if len(feature_names) != len(feature_importance_values):
            feature_importance_values = [0.0] * len(feature_names)

        feature_importance = pd.DataFrame({
            "Feature": feature_names,
            "Importance": feature_importance_values
        }).sort_values("Importance", ascending=False)
        
        # Only show top features
        top_features = feature_importance.head(20)
        
        fig = px.bar(
            top_features,
            x="Importance",
            y="Feature",
            orientation="h",
            title="Top 20 Most Important Features",
            color="Importance",
            color_continuous_scale="Viridis"
        )
        fig.update_layout(
            yaxis={'categoryorder': 'total ascending'},
            height=max(400, len(top_features) * 25)
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Top professions driving bias
        st.markdown("### 🏆 Professions Most Predictive of Bias")
        
        keyword_features = feature_importance[
            feature_importance["Feature"].str.startswith("keyword_")
        ].head(10)
        
        keyword_features["Profession"] = keyword_features["Feature"].str.replace("keyword_", "")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.dataframe(
                keyword_features[["Profession", "Importance"]].style.background_gradient(
                    subset=["Importance"],
                    cmap="YlOrRd"
                ),
                use_container_width=True,
                hide_index=True
            )
        
        with col2:
            # Show actual distribution for top profession
            top_prof = keyword_features.iloc[0]["Profession"]
            prof_data = filtered_data[filtered_data["keyword"] == top_prof]
            
            pronoun_dist = prof_data["pronoun_group"].value_counts()
            
            fig = px.pie(
                values=pronoun_dist.values,
                names=pronoun_dist.index,
                title=f"Pronoun Distribution: {top_prof}",
                color=pronoun_dist.index,
                color_discrete_map=PRONOUN_COLORS
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Confusion Matrix
        st.markdown("## 🎯 Prediction Accuracy Matrix")
        
        with st.expander("ℹ️ How to Read the Confusion Matrix", expanded=False):
            st.markdown("""
            The confusion matrix shows:
            - **Rows**: Actual pronoun groups
            - **Columns**: Predicted pronoun groups
            - **Diagonal values** (top-left to bottom-right): Correct predictions
            - **Off-diagonal values**: Misclassifications
            
            Higher numbers on the diagonal = better predictions.
            """)
        
        confusion_matrix = pd.DataFrame(
            results['confusion_matrix'],
            index=results['class_labels'],
            columns=results['class_labels']
        )
        
        fig = px.imshow(
            confusion_matrix,
            labels=dict(x="Predicted", y="Actual", color="Count"),
            x=results['class_labels'],
            y=results['class_labels'],
            title="Confusion Matrix",
            color_continuous_scale="Blues",
            text_auto=True
        )
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"Could not train model: {e}")
        st.info("This may happen if there's insufficient data variety or if required features are missing.")

# Bias Likelihood Prediction
st.markdown("## 🔮 Predict Bias for New Professions")

with st.expander("ℹ️ About Bias Prediction", expanded=False):
    st.markdown("""
    Enter a profession to predict how likely it is to be associated with each pronoun group.
    
    This uses the trained model to estimate bias based on patterns learned from existing data.
    
    **Note:** Predictions are based on learned patterns and may reflect existing biases in the training data.
    """)

with st.form("prediction_form"):
    col1, col2 = st.columns(2)
    
    with col1:
        new_keyword = st.text_input(
            "Profession/Keyword",
            value="Scientist",
            help="Enter any profession"
        )
    
    with col2:
        # Get available prompts from data
        available_prompts = filtered_data["prompt"].unique()
        if len(available_prompts) > 0:
            selected_prompt = st.selectbox(
                "Prompt Template",
                options=list(available_prompts)[:5],  # Show first 5
                help="Choose a prompt template"
            )
        else:
            selected_prompt = "Describe a {keyword}."
    
    submitted = st.form_submit_button("Predict Bias")
    
    if submitted:
        try:
            # Make prediction
            prediction = analyzer.predict_bias_likelihood(
                new_keyword,
                selected_prompt,
                predictor_results=results,
            )
            
            st.markdown("### Prediction Results")
            
            # Show probabilities
            probabilities = prediction.get("probabilities", {}) or {}
            if not isinstance(probabilities, dict):
                probabilities = {}

            col1, col2, col3, col4 = st.columns(4)
            
            cols = [col1, col2, col3, col4]
            pronouns = ["he/him", "she/her", "they/them", "none"]
            
            for col, pronoun in zip(cols, pronouns):
                if pronoun in probabilities:
                    prob = probabilities[pronoun]
                    col.metric(
                        pronoun.title(),
                        f"{prob:.1%}",
                        delta=f"{prob - 0.25:.1%}" if prob > 0.25 else None
                    )
            
            # Visualization
            prob_df = pd.DataFrame({
                "Pronoun": list(probabilities.keys()),
                "Probability": list(probabilities.values())
            })
            
            fig = px.bar(
                prob_df,
                x="Pronoun",
                y="Probability",
                title=f"Predicted Pronoun Distribution: {new_keyword}",
                color="Pronoun",
                color_discrete_map=PRONOUN_COLORS
            )
            fig.update_layout(
                yaxis_title="Probability",
                showlegend=False,
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Interpretation
            predicted_class = prediction.get("predicted_class")
            confidence = prediction.get("confidence", 0.0)
            
            if probabilities:
                if confidence > 0.6:
                    strength = "strongly"
                elif confidence > 0.4:
                    strength = "moderately"
                else:
                    strength = "weakly"
                
                st.info(f"""
                📊 **Interpretation:**  
                The model predicts "{new_keyword}" is **{strength} associated** with **{predicted_class}** 
                (confidence: {confidence:.1%}).
                
                This is based on patterns learned from similar professions in the training data.
                """)
            else:
                st.warning("The model could not produce probability values for this input.")
            
        except Exception as e:
            st.error(f"Prediction failed: {e}")

# Batch Prediction
st.markdown("## 📊 Batch Prediction Analysis")

st.markdown("Analyze bias predictions for multiple professions at once.")

# Let user enter multiple professions
professions_text = st.text_area(
    "Enter professions (one per line)",
    value="Engineer\nNurse\nTeacher\nCEO\nSecretary\nPilot\nChef\nAccountant",
    height=150
)

if st.button("Analyze Batch"):
    professions = [p.strip() for p in professions_text.split("\n") if p.strip()]
    
    if professions:
        with st.spinner("Making predictions..."):
            try:
                # Use first available prompt
                prompt = filtered_data["prompt"].iloc[0]
                
                batch_results = []
                for prof in professions:
                    pred = analyzer.predict_bias_likelihood(
                        prof,
                        prompt,
                        predictor_results=results,
                    )
                    probabilities = pred.get("probabilities", {}) or {}
                    batch_results.append({
                        "Profession": prof,
                        "Predicted": pred.get("predicted_class", "unknown"),
                        "Confidence": pred.get("confidence", 0.0),
                        **probabilities
                    })
                
                batch_df = pd.DataFrame(batch_results)
                
                # Display table
                st.dataframe(
                    batch_df.style.background_gradient(
                        subset=["he/him", "she/her", "they/them"],
                        cmap="RdYlGn"
                    ).format({
                        "Confidence": "{:.1%}",
                        "he/him": "{:.1%}",
                        "she/her": "{:.1%}",
                        "they/them": "{:.1%}",
                        "none": "{:.1%}"
                    }),
                    use_container_width=True
                )
                
                # Visualize
                fig = px.bar(
                    batch_df,
                    x="Profession",
                    y=["he/him", "she/her", "they/them", "none"],
                    title="Predicted Pronoun Distribution by Profession",
                    color_discrete_map=PRONOUN_COLORS,
                    barmode="stack"
                )
                fig.update_layout(
                    yaxis_title="Probability",
                    height=500
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Download option
                csv = batch_df.to_csv(index=False)
                st.download_button(
                    "⬇️ Download Predictions",
                    csv,
                    "batch_predictions.csv",
                    "text/csv"
                )
                
            except Exception as e:
                st.error(f"Batch prediction failed: {e}")
    else:
        st.warning("Please enter at least one profession.")

# Model Performance by Category
st.markdown("## 📈 Model Performance Analysis")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### Accuracy by Pronoun Group")
    
    # Calculate per-class accuracy if possible
    st.info("Per-class accuracy would show which pronoun groups are easier/harder to predict.")
    
    # Show class distribution
    class_dist = filtered_data["pronoun_group"].value_counts()
    
    fig = px.bar(
        x=class_dist.index,
        y=class_dist.values,
        labels={"x": "Pronoun Group", "y": "Count"},
        title="Class Distribution in Training Data",
        color=class_dist.index,
        color_discrete_map=PRONOUN_COLORS
    )
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown("### Cross-Validation Scores")
    
    if 'results' in locals() and 'cv_scores' in results:
        cv_df = pd.DataFrame({
            "Fold": range(1, len(results['cv_scores']) + 1),
            "Accuracy": results['cv_scores']
        })
        
        fig = px.line(
            cv_df,
            x="Fold",
            y="Accuracy",
            title="Cross-Validation Accuracy by Fold",
            markers=True
        )
        fig.add_hline(
            y=cv_df["Accuracy"].mean(),
            line_dash="dash",
            annotation_text=f"Mean: {cv_df['Accuracy'].mean():.1%}"
        )
        fig.update_layout(yaxis_tickformat=".0%")
        st.plotly_chart(fig, use_container_width=True)

# Footer
st.markdown("---")
st.markdown("""
💡 **Key Insights:**
- High accuracy suggests bias patterns are systematic and predictable
- Feature importance reveals which professions drive bias most strongly
- Predictions can identify potential biases before collecting new data
- Use this analysis to guide further research questions

⚠️ **Important:** ML models learn from existing data. If the training data contains biases, 
predictions will reflect those biases. Always interpret results critically.

📖 Click **?** in sidebar for detailed explanations of ML concepts.
""")
