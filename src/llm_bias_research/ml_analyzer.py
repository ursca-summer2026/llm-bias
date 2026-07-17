"""
Machine learning analysis module.

Provides advanced ML-based analysis including:
- Bias prediction using classification models
- Cosine similarity for model comparison
- Feature extraction from text responses
"""

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import LabelEncoder
from typing import Any, Dict, Optional

from llm_bias_research.bias_detector import detect_pronoun


class MLBiasAnalyzer:
    """Machine learning tools for bias analysis."""

    def __init__(self, data: pd.DataFrame) -> None:
        """Initialize ML analyzer.

        Args:
            data: DataFrame with columns: model, keyword, prompt, output
        """
        self.data = data.copy()
        
        if "pronoun_group" not in self.data.columns:
            self.data["pronoun_group"] = self.data["output"].apply(detect_pronoun)

    def train_bias_predictor(
        self,
        test_size: float = 0.2,
        random_state: int = 42,
    ) -> Dict[str, Any]:
        """Train a model to predict pronoun group from prompt and keyword.

        This can help identify which prompt/keyword combinations are most
        predictive of gender bias.

        Args:
            test_size: Proportion of data for testing.
            random_state: Random seed for reproducibility.

        Returns:
            Dictionary with model, scores, and feature importance.
        """
        # Prepare features
        X = self.data[["keyword", "prompt"]].copy()
        
        # Encode categorical features
        keyword_encoder = LabelEncoder()
        X["keyword_encoded"] = keyword_encoder.fit_transform(X["keyword"])
        
        # For prompts, we'll use the prompt type length as a simple feature
        # In a more sophisticated version, we'd use TF-IDF or embeddings
        X["prompt_length"] = X["prompt"].str.len()
        X["prompt_word_count"] = X["prompt"].str.split().str.len()
        
        # Target variable
        y = self.data["pronoun_group"]
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X[["keyword_encoded", "prompt_length", "prompt_word_count"]],
            y,
            test_size=test_size,
            random_state=random_state,
            stratify=y,
        )
        
        # Train Random Forest
        clf = RandomForestClassifier(n_estimators=100, random_state=random_state)
        clf.fit(X_train, y_train)
        
        # Evaluate
        train_score = clf.score(X_train, y_train)
        test_score = clf.score(X_test, y_test)
        cv_scores = cross_val_score(clf, X_train, y_train, cv=5)
        
        # Feature importance
        feature_names = ["keyword", "prompt_length", "prompt_word_count"]
        feature_importance = dict(zip(feature_names, clf.feature_importances_))
        
        return {
            "model": clf,
            "keyword_encoder": keyword_encoder,
            "train_accuracy": train_score,
            "test_accuracy": test_score,
            "cv_mean_accuracy": cv_scores.mean(),
            "cv_std_accuracy": cv_scores.std(),
            "feature_importance": feature_importance,
        }

    def compute_response_similarity(
        self,
        model1: str,
        model2: str,
        keyword: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Compute cosine similarity between two models' responses.

        Uses TF-IDF vectorization to compare the textual content of responses.

        Args:
            model1: First model name.
            model2: Second model name.
            keyword: Optionally filter by specific keyword.

        Returns:
            Dictionary with similarity score and details.
        """
        # Filter data for each model
        data1 = self.data[self.data["model"] == model1]
        data2 = self.data[self.data["model"] == model2]
        
        if keyword:
            data1 = data1[data1["keyword"] == keyword]
            data2 = data2[data2["keyword"] == keyword]
        
        if len(data1) == 0 or len(data2) == 0:
            return {
                "similarity": 0.0,
                "error": "Insufficient data for comparison",
            }
        
        # Get responses
        responses1 = data1["output"].tolist()
        responses2 = data2["output"].tolist()
        
        # Compute TF-IDF
        vectorizer = TfidfVectorizer(max_features=100, stop_words="english")
        
        try:
            # Fit on combined corpus
            all_responses = responses1 + responses2
            vectorizer.fit(all_responses)
            
            # Transform each set
            vectors1 = vectorizer.transform(responses1)
            vectors2 = vectorizer.transform(responses2)
            
            # Compute average vectors
            avg_vec1 = vectors1.mean(axis=0)
            avg_vec2 = vectors2.mean(axis=0)
            
            # Cosine similarity
            similarity = cosine_similarity(avg_vec1, avg_vec2)[0][0]
            
            # Also compute pairwise similarities for distribution
            pairwise_sims = []
            for v1 in vectors1[:min(50, len(vectors1))]:  # Limit for performance
                for v2 in vectors2[:min(50, len(vectors2))]:
                    pairwise_sims.append(cosine_similarity(v1, v2)[0][0])
            
            return {
                "model1": model1,
                "model2": model2,
                "keyword": keyword,
                "overall_similarity": similarity,
                "pairwise_mean": np.mean(pairwise_sims),
                "pairwise_std": np.std(pairwise_sims),
                "pairwise_min": np.min(pairwise_sims),
                "pairwise_max": np.max(pairwise_sims),
                "n_responses_model1": len(responses1),
                "n_responses_model2": len(responses2),
            }
        except Exception as e:
            return {
                "similarity": 0.0,
                "error": f"Failed to compute similarity: {e}",
            }

    def compare_all_models(
        self,
        keyword: Optional[str] = None,
    ) -> pd.DataFrame:
        """Compute pairwise similarity matrix for all models.

        Args:
            keyword: Optionally filter by specific keyword.

        Returns:
            DataFrame with models as rows/columns and similarity as values.
        """
        models = self.data["model"].unique()
        n_models = len(models)
        
        # Initialize similarity matrix
        sim_matrix = np.zeros((n_models, n_models))
        
        for i, model1 in enumerate(models):
            for j, model2 in enumerate(models):
                if i == j:
                    sim_matrix[i, j] = 1.0
                elif i < j:
                    result = self.compute_response_similarity(model1, model2, keyword)
                    sim = result.get("overall_similarity", 0.0)
                    sim_matrix[i, j] = sim
                    sim_matrix[j, i] = sim  # Symmetric
        
        return pd.DataFrame(sim_matrix, index=models, columns=models)

    def extract_word_frequencies(
        self,
        pronoun_group: str,
        top_n: int = 50,
    ) -> Dict[str, int]:
        """Extract most common words for a specific pronoun group.

        Useful for word cloud generation.

        Args:
            pronoun_group: Which pronoun group to analyze.
            top_n: Number of top words to return.

        Returns:
            Dictionary mapping words to frequencies.
        """
        # Filter responses by pronoun group
        filtered = self.data[self.data["pronoun_group"] == pronoun_group]
        
        if len(filtered) == 0:
            return {}
        
        # Combine all responses
        text = " ".join(filtered["output"].tolist())
        
        # Use TF-IDF to get important words
        vectorizer = TfidfVectorizer(
            max_features=top_n,
            stop_words="english",
            ngram_range=(1, 2),  # Include bigrams
        )
        
        try:
            vectorizer.fit([text])
            feature_names = vectorizer.get_feature_names_out()
            
            # Get word counts (not TF-IDF scores)
            word_freq = {}
            words = text.lower().split()
            for word in feature_names:
                word_freq[word] = text.lower().count(word)
            
            # Sort by frequency
            sorted_freq = dict(
                sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:top_n]
            )
            
            return sorted_freq
        except Exception:
            return {}

    def predict_bias_likelihood(
        self,
        keyword: str,
        prompt: str,
        predictor_results: Dict[str, Any],
    ) -> Dict[str, float]:
        """Predict pronoun group probabilities for a new keyword/prompt.

        Args:
            keyword: The keyword/profession.
            prompt: The prompt text.
            predictor_results: Results from train_bias_predictor().

        Returns:
            Dictionary mapping pronoun groups to probabilities.
        """
        model = predictor_results["model"]
        keyword_encoder = predictor_results["keyword_encoder"]
        
        try:
            # Encode keyword
            keyword_encoded = keyword_encoder.transform([keyword])[0]
            
            # Extract features
            prompt_length = len(prompt)
            prompt_word_count = len(prompt.split())
            
            # Create feature vector
            X = np.array([[keyword_encoded, prompt_length, prompt_word_count]])
            
            # Get probability predictions
            proba = model.predict_proba(X)[0]
            classes = model.classes_
            
            return dict(zip(classes, proba))
        except Exception as e:
            return {
                "error": f"Prediction failed: {e}",
            }
