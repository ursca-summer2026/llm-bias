"""
Word Cloud page - Visualize most common words associated with different gender groups.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
import sys
import numpy as np
from collections import Counter
import re

# Add parent directory to path for imports
dashboard_dir = Path(__file__).parent.parent
if str(dashboard_dir) not in sys.path:
    sys.path.insert(0, str(dashboard_dir))

from components.charts import PRONOUN_COLORS
from components.help import show_help_sidebar

st.set_page_config(page_title="Word Clouds", page_icon="☁️", layout="wide")

st.title("☁️ Word Clouds")
st.markdown("Explore the most common words associated with different pronoun groups.")

# Load data
if "data" not in st.session_state or st.session_state.data is None:
    st.warning("⚠️ No data loaded. Please upload a database on the main page.")
    st.stop()

data = st.session_state.data

# Sidebar
show_help_sidebar()

st.sidebar.markdown("---")
st.sidebar.markdown("### Display Options")

# Try to import wordcloud
try:
    from wordcloud import WordCloud
    import matplotlib.pyplot as plt
    has_wordcloud = True
except ImportError:
    has_wordcloud = False
    st.error("""
    ⚠️ **WordCloud library not installed**
    
    This page requires the wordcloud library.
    
    Install it with:
    ```bash
    pip install wordcloud matplotlib
    ```
    """)
    st.stop()

# Import ML analyzer for word frequency extraction
try:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
    from llm_bias_research.ml_analyzer import MLBiasAnalyzer
    has_ml = True
except ImportError:
    has_ml = False

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

# Word cloud settings
max_words = st.sidebar.slider("Max Words", 20, 200, 100, step=10)
min_word_length = st.sidebar.slider("Min Word Length", 2, 6, 3)

# Remove common words
st.sidebar.markdown("### Common Words to Remove")
remove_stopwords = st.sidebar.checkbox("Remove English stopwords", value=True)
custom_stopwords = st.sidebar.text_area(
    "Additional words to exclude (one per line)",
    value="the\na\nan\nand\nor\nbut\nin\non\nat\nto\nfor\nof\nis\nare\nwas\nwere\nthat\nthis\nthese\nthose",
    height=100
)

# Parse custom stopwords
custom_stop_list = [w.strip().lower() for w in custom_stopwords.split("\n") if w.strip()]

# Function to generate word cloud
def generate_wordcloud(text_data, color="blue", title="Word Cloud"):
    """Generate a word cloud from text data."""
    if len(text_data) == 0:
        return None
    
    # Combine all text
    combined_text = " ".join(text_data)
    
    # Create word cloud
    wordcloud = WordCloud(
        width=800,
        height=400,
        background_color="white",
        max_words=max_words,
        stopwords=set(custom_stop_list) if not remove_stopwords else None,
        colormap="Blues" if color == "blue" else ("Greens" if color == "green" else "Oranges"),
        min_word_length=min_word_length,
        relative_scaling=0.5,
        collocations=False
    ).generate(combined_text)
    
    # Create matplotlib figure
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.imshow(wordcloud, interpolation="bilinear")
    ax.set_title(title, fontsize=16, fontweight="bold")
    ax.axis("off")
    
    return fig

# Function to extract top words
def get_top_words(text_data, n=20):
    """Extract top N words from text data."""
    if len(text_data) == 0:
        return pd.DataFrame()
    
    # Combine and tokenize
    combined_text = " ".join(text_data).lower()
    
    # Remove punctuation and split
    words = re.findall(r'\b[a-z]+\b', combined_text)
    
    # Filter by length and stopwords
    words = [
        w for w in words 
        if len(w) >= min_word_length and w not in custom_stop_list
    ]
    
    # Count frequencies
    word_counts = Counter(words)
    
    # Convert to DataFrame
    top_words = pd.DataFrame(
        word_counts.most_common(n),
        columns=["Word", "Frequency"]
    )
    
    return top_words

# Main content
st.markdown("## ☁️ Word Clouds by Pronoun Group")

with st.expander("ℹ️ How to Interpret Word Clouds", expanded=False):
    st.markdown("""
    **Word clouds** visualize word frequency - larger words appear more often.
    
    **What to look for:**
    - **Vocabulary differences**: Do models use different words when describing different genders?
    - **Stereotypes**: Are certain professions or traits more associated with specific pronouns?
    - **Neutral language**: How often are gender-neutral terms used?
    
    **Interpretation tips:**
    - Larger words = higher frequency
    - Color intensity = relative importance
    - Similar words across groups suggest less bias
    - Distinct vocabularies may indicate stereotyping
    """)

# Generate word clouds for each pronoun group
pronoun_groups = ["he/him", "she/her", "they/them", "none"]

for pronoun in pronoun_groups:
    pronoun_data = filtered_data[filtered_data["pronoun_group"] == pronoun]
    
    if len(pronoun_data) == 0:
        continue
    
    st.markdown(f"### {pronoun.title()} ({len(pronoun_data)} responses)")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Generate word cloud
        text_list = pronoun_data["output"].tolist()
        
        # Choose color based on pronoun
        if pronoun == "he/him":
            color = "blue"
        elif pronoun == "she/her":
            color = "green"
        else:
            color = "orange"
        
        fig = generate_wordcloud(
            text_list,
            color=color,
            title=f"Most Common Words in {pronoun.title()} Responses"
        )
        
        if fig:
            st.pyplot(fig)
            plt.close()
    
    with col2:
        # Show top words table
        top_words = get_top_words(text_list, n=15)
        
        if not top_words.empty:
            st.markdown("**Top Words:**")
            st.dataframe(
                top_words.style.background_gradient(subset=["Frequency"], cmap="Blues"),
                use_container_width=True,
                height=400
            )

# Comparative Analysis
st.markdown("## 🔍 Comparative Word Analysis")

col1, col2 = st.columns(2)

with col1:
    group1 = st.selectbox("Compare Group 1", pronoun_groups, index=0)

with col2:
    group2 = st.selectbox("Compare Group 2", pronoun_groups, index=1)

if group1 != group2:
    data1 = filtered_data[filtered_data["pronoun_group"] == group1]
    data2 = filtered_data[filtered_data["pronoun_group"] == group2]
    
    words1 = get_top_words(data1["output"].tolist(), n=30)
    words2 = get_top_words(data2["output"].tolist(), n=30)
    
    # Find unique words
    if not words1.empty and not words2.empty:
        words1_set = set(words1["Word"].tolist())
        words2_set = set(words2["Word"].tolist())
        
        unique_to_1 = words1_set - words2_set
        unique_to_2 = words2_set - words1_set
        common = words1_set & words2_set
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(f"Unique to {group1}", len(unique_to_1))
            if unique_to_1:
                st.write(", ".join(list(unique_to_1)[:10]))
        
        with col2:
            st.metric("Common Words", len(common))
            if common:
                st.write(", ".join(list(common)[:10]))
        
        with col3:
            st.metric(f"Unique to {group2}", len(unique_to_2))
            if unique_to_2:
                st.write(", ".join(list(unique_to_2)[:10]))
        
        # Side-by-side comparison
        st.markdown("### Side-by-Side Frequency Comparison")
        
        # Merge dataframes
        comparison = words1.merge(
            words2,
            on="Word",
            how="outer",
            suffixes=(f"_{group1}", f"_{group2}")
        ).fillna(0)
        
        comparison = comparison.head(20)
        
        fig = px.bar(
            comparison.melt(id_vars="Word", var_name="Group", value_name="Frequency"),
            x="Word",
            y="Frequency",
            color="Group",
            title="Word Frequency Comparison (Top 20 Words)",
            barmode="group",
            color_discrete_map={
                f"Frequency_{group1}": PRONOUN_COLORS.get(group1, "#666666"),
                f"Frequency_{group2}": PRONOUN_COLORS.get(group2, "#999999")
            }
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

# By Profession
st.markdown("## 👔 Word Clouds by Profession")

selected_profession = st.selectbox(
    "Select Profession",
    options=sorted(filtered_data["keyword"].unique())
)

profession_data = filtered_data[filtered_data["keyword"] == selected_profession]

col1, col2 = st.columns(2)

with col1:
    st.markdown(f"### All Responses for {selected_profession}")
    
    text_list = profession_data["output"].tolist()
    fig = generate_wordcloud(
        text_list,
        color="blue",
        title=f"Word Cloud: {selected_profession}"
    )
    
    if fig:
        st.pyplot(fig)
        plt.close()

with col2:
    st.markdown(f"### Breakdown by Gender")
    
    for pronoun in ["he/him", "she/her", "they/them"]:
        pronoun_prof_data = profession_data[profession_data["pronoun_group"] == pronoun]
        
        if len(pronoun_prof_data) > 0:
            pct = len(pronoun_prof_data) / len(profession_data) * 100
            st.markdown(f"**{pronoun}**: {pct:.1f}% ({len(pronoun_prof_data)} responses)")

# TF-IDF Analysis (if ML analyzer available)
if has_ml:
    st.markdown("## 🔬 TF-IDF Analysis")
    
    with st.expander("ℹ️ About TF-IDF", expanded=False):
        st.markdown("""
        **TF-IDF** (Term Frequency-Inverse Document Frequency) identifies words that are:
        - Common in one group
        - Rare in other groups
        
        These are the most **distinctive** words for each pronoun group.
        """)
    
    try:
        analyzer = MLBiasAnalyzer(filtered_data)
        word_freq = analyzer.extract_word_frequencies(top_n=15)
        
        # Display TF-IDF results
        cols = st.columns(len(pronoun_groups))
        
        for idx, pronoun in enumerate(pronoun_groups):
            if pronoun in word_freq:
                with cols[idx]:
                    st.markdown(f"### {pronoun.title()}")
                    st.markdown("**Most Distinctive Words:**")
                    
                    for word, score in word_freq[pronoun]:
                        st.write(f"- {word} ({score:.3f})")
    
    except Exception as e:
        st.warning(f"Could not perform TF-IDF analysis: {e}")

# Download options
st.markdown("---")
st.markdown("## 📥 Export Word Frequencies")

export_pronoun = st.selectbox(
    "Select pronoun group to export",
    pronoun_groups
)

export_data = filtered_data[filtered_data["pronoun_group"] == export_pronoun]
top_words_export = get_top_words(export_data["output"].tolist(), n=100)

if not top_words_export.empty:
    csv = top_words_export.to_csv(index=False)
    st.download_button(
        f"⬇️ Download {export_pronoun} Word Frequencies",
        csv,
        f"word_frequencies_{export_pronoun.replace('/', '_')}.csv",
        "text/csv"
    )

# Footer
st.markdown("---")
st.markdown("""
💡 **Tips:**
- Look for stereotypical words (e.g., "nurturing" vs "assertive")
- Compare word clouds across pronoun groups for differences
- Consider context - some word differences may be legitimate
- Use TF-IDF to find the most distinctive vocabulary for each group

📖 Click **?** in sidebar for help interpreting word clouds.
""")
