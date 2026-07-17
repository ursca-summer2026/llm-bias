"""
Main Streamlit application for LLM Bias Research.

This is the entry point for the interactive dashboard.
"""

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent))

from llm_bias_research.database import BiasDatabase
from llm_bias_research.bias_detector import detect_pronoun
from dashboard.components.help import show_help_sidebar

# Page configuration
st.set_page_config(
    page_title="LLM Bias Research Dashboard",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for better styling
st.markdown(
    """
    <style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        padding: 1rem 0;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
        color: #1a1a1a;
    }
    .info-box {
        background-color: #e7f3ff;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #0066cc;
        margin: 1rem 0;
        color: #0d6f0d;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def load_database(db_path: str) -> pd.DataFrame:
    """Load data from database and add pronoun classifications.

    Args:
        db_path: Path to SQLite database.

    Returns:
        DataFrame with all responses and pronoun groups.
    """
    db = BiasDatabase(db_path)
    data = pd.DataFrame(db.get_responses())

    # Add pronoun group classification
    data["pronoun_group"] = data["output"].apply(detect_pronoun)

    # Standardize keyword capitalization
    data["keyword"] = data["keyword"].str.strip().str.title()

    return data


@st.cache_data
def load_multiple_databases(db_paths: list) -> pd.DataFrame:
    """Load and merge data from multiple database files.
    
    Each database typically contains data for a single model, and this function
    combines them for multi-model comparison analysis.

    Args:
        db_paths: List of paths to SQLite databases.

    Returns:
        Combined DataFrame with all responses and pronoun groups.
    """
    all_data = []
    
    for db_path in db_paths:
        try:
            data = load_database(db_path)
            all_data.append(data)
        except Exception as e:
            st.warning(f"⚠️ Could not load {Path(db_path).name}: {e}")
    
    if not all_data:
        raise ValueError("No databases could be loaded successfully")
    
    # Combine all dataframes
    combined_data = pd.concat(all_data, ignore_index=True)
    
    return combined_data


def main() -> None:
    """Main dashboard application."""

    # Title
    st.markdown('<h1 class="main-header">🔍 LLM Bias Research Dashboard</h1>', unsafe_allow_html=True)

    st.markdown(
        """
        <div class="info-box">
        <b>Welcome!</b> This dashboard helps you explore and analyze gender bias in Large Language Models.
        Gender bias manifests when models systematically associate certain professions with specific genders.
        We measure this by analyzing pronoun usage in model responses.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Sidebar - Database selection
    st.sidebar.title("⚙️ Configuration")

    # Initialize database paths list
    db_paths = []

    # Check for database path from command line (backward compatibility)
    if len(sys.argv) > 2 and sys.argv[1] == "--database":
        db_paths.append(sys.argv[2])

    # Multi-file uploader for multiple models
    uploaded_dbs = st.sidebar.file_uploader(
        "Upload database file(s)",
        type=["db", "sqlite", "sqlite3"],
        accept_multiple_files=True,
        help="Upload one or more SQLite database files. Each file typically contains data for one model.",
    )

    if uploaded_dbs:
        # Clear command line databases if user uploads files
        db_paths = []
        
        # Save uploaded files temporarily
        for idx, uploaded_db in enumerate(uploaded_dbs):
            temp_path = Path(f"temp_uploaded_{idx}.db")
            temp_path.write_bytes(uploaded_db.read())
            db_paths.append(str(temp_path))
    elif not db_paths:
        # Look for databases in common locations
        st.sidebar.info("📁 No database selected. Upload files above or use --database flag.")

    # Load data
    if db_paths and all(Path(p).exists() for p in db_paths):
        try:
            # Load single or multiple databases
            if len(db_paths) == 1:
                data = load_database(db_paths[0])
            else:
                data = load_multiple_databases(db_paths)
            
            # Display loaded database info
            st.sidebar.success(f"✓ Loaded {len(data)} responses")
            
            # Show database and model details
            with st.sidebar.expander("📊 Loaded Data Details", expanded=True):
                st.write(f"**Databases:** {len(db_paths)}")
                
                # Show each database and its models
                for db_path in db_paths:
                    db_name = Path(db_path).name
                    try:
                        db_data = load_database(db_path)
                        models = db_data["model"].unique()
                        st.write(f"• `{db_name}`")
                        for model in models:
                            count = len(db_data[db_data["model"] == model])
                            st.write(f"  - {model}: {count} responses")
                    except:
                        st.write(f"• `{db_name}` (error loading)")
                
                st.write(f"**Total Models:** {data['model'].nunique()}")
                st.write(f"**Total Keywords:** {data['keyword'].nunique()}")

            # Store in session state
            st.session_state["data"] = data
            st.session_state["db_paths"] = db_paths

            # Display overview
            show_overview(data)

        except Exception as e:
            st.error(f"❌ Error loading database(s): {e}")
            st.info("💡 Upload database files using the sidebar or check file integrity.")
    else:
        st.warning(
            """
            ⚠️ **No database loaded**
            
            Please either:
            1. **Upload database file(s)** using the sidebar uploader
               - Upload multiple files to compare different models
               - Each file typically contains data for one model
            2. **Run the CLI** to create databases:
               ```bash
               # Create separate database for each model
               llm-bias query --model phi3 --keywords "Nurse,Doctor" \\
                 --prompt-file prompts/default_prompts.txt \\
                 --output results/phi3_study
               
               llm-bias query --model llama3.2 --keywords "Nurse,Doctor" \\
                 --prompt-file prompts/default_prompts.txt \\
                 --output results/llama_study
               ```
            3. **Specify database path** when launching:
               ```bash
               streamlit run app.py -- --database results/phi3_test.db
               ```
            """
        )
        st.stop()

    # Help sidebar
    show_help_sidebar()


def show_overview(data: pd.DataFrame) -> None:
    """Display overview statistics and quick insights.

    Args:
        data: DataFrame with response data.
    """
    st.header("📊 Quick Overview")

    # Metrics row
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Responses", len(data))

    with col2:
        n_models = data["model"].nunique()
        st.metric("Models", n_models)

    with col3:
        n_keywords = data["keyword"].nunique()
        st.metric("Keywords", n_keywords)

    with col4:
        # Calculate bias score (difference between he/him and she/her proportions)
        pronoun_counts = data["pronoun_group"].value_counts(normalize=True)
        bias_score = abs(
            pronoun_counts.get("he/him", 0) - pronoun_counts.get("she/her", 0)
        )
        st.metric("Overall Bias Score", f"{bias_score:.3f}")

    st.markdown("---")

    # Pronoun distribution
    st.subheader("📈 Overall Pronoun Distribution")

    col1, col2 = st.columns([2, 1])

    with col1:
        import plotly.express as px

        pronoun_df = data["pronoun_group"].value_counts().reset_index()
        pronoun_df.columns = ["Pronoun Group", "Count"]

        fig = px.bar(
            pronoun_df,
            x="Pronoun Group",
            y="Count",
            color="Pronoun Group",
            color_discrete_map={
                "he/him": "#2a78d6",
                "she/her": "#1baf7a",
                "they/them": "#eda100",
                "none": "#898781",
            },
            title="Response Distribution by Pronoun Group",
        )
        fig.update_layout(showlegend=False, height=400)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("#### Breakdown")
        for _, row in pronoun_df.iterrows():
            percentage = (row["Count"] / len(data)) * 100
            st.markdown(
                f"""
                <div class="metric-card">
                    <b>{row['Pronoun Group']}</b><br>
                    {row['Count']} responses ({percentage:.1f}%)
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown("")

    st.markdown("---")

    # Models overview
    st.subheader("🤖 Models Overview")

    models_data = data.groupby("model")["pronoun_group"].value_counts(normalize=True).unstack(fill_value=0)

    import plotly.graph_objects as go

    fig = go.Figure()

    colors = {"he/him": "#2a78d6", "she/her": "#1baf7a", "they/them": "#eda100", "none": "#898781"}

    for pronoun in ["he/him", "she/her", "they/them", "none"]:
        if pronoun in models_data.columns:
            fig.add_trace(
                go.Bar(
                    name=pronoun,
                    x=models_data.index,
                    y=models_data[pronoun] * 100,
                    marker_color=colors.get(pronoun, "#cccccc"),
                )
            )

    fig.update_layout(
        barmode="stack",
        title="Pronoun Distribution by Model (%)",
        xaxis_title="Model",
        yaxis_title="Percentage",
        height=400,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Keywords overview
    st.subheader("🔑 Keywords Overview")

    keywords_data = data.groupby("keyword")["pronoun_group"].value_counts(normalize=True).unstack(fill_value=0)

    fig = go.Figure()

    for pronoun in ["he/him", "she/her", "they/them", "none"]:
        if pronoun in keywords_data.columns:
            fig.add_trace(
                go.Bar(
                    name=pronoun,
                    x=keywords_data.index,
                    y=keywords_data[pronoun] * 100,
                    marker_color=colors.get(pronoun, "#cccccc"),
                )
            )

    fig.update_layout(
        barmode="stack",
        title="Pronoun Distribution by Keyword (%)",
        xaxis_title="Keyword/Profession",
        yaxis_title="Percentage",
        height=400,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    st.plotly_chart(fig, use_container_width=True)

    # Navigation hint
    st.info(
        """
        💡 **Explore More:**
        - Use the sidebar to navigate to different analysis pages
        - Statistical Analysis page for significance tests
        - Heatmaps for detailed profession × gender patterns
        - Model Comparison for similarity analysis
        """
    )


if __name__ == "__main__":
    main()
