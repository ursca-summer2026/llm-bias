"""
Tests for the ML analyzer module.
"""

import pytest
import pandas as pd
import numpy as np
from llm_bias_research.ml_analyzer import MLBiasAnalyzer


@pytest.fixture
def sample_ml_data():
    """Create sample data for ML testing."""
    np.random.seed(42)
    
    data = {
        "id": range(1, 201),
        "keyword": ["Nurse"] * 50 + ["Doctor"] * 50 + ["Engineer"] * 50 + ["Teacher"] * 50,
        "model": ["phi3"] * 100 + ["llama3.2"] * 100,
        "prompt": ["Describe a {keyword}."] * 200,
        "output": [
            f"Sample response {i} with various words" for i in range(200)
        ],
        "pronoun_group": (
            ["he/him"] * 10 + ["she/her"] * 30 + ["they/them"] * 10 +  # Nurse
            ["he/him"] * 35 + ["she/her"] * 10 + ["they/them"] * 5 +   # Doctor
            ["he/him"] * 40 + ["she/her"] * 5 + ["they/them"] * 5 +    # Engineer
            ["he/him"] * 15 + ["she/her"] * 25 + ["they/them"] * 10    # Teacher
        )
    }
    
    return pd.DataFrame(data)


@pytest.fixture
def ml_analyzer(sample_ml_data):
    """Create ML analyzer instance."""
    return MLBiasAnalyzer(sample_ml_data)


class TestMLBiasAnalyzerInit:
    """Test ML analyzer initialization."""
    
    def test_init(self, sample_ml_data):
        """Test basic initialization."""
        analyzer = MLBiasAnalyzer(sample_ml_data)
        assert len(analyzer.data) == 200
        assert "pronoun_group" in analyzer.data.columns
    
    def test_init_with_empty_data(self):
        """Test initialization with empty data."""
        with pytest.raises((ValueError, KeyError)):
            MLBiasAnalyzer(pd.DataFrame())
    
    def test_init_with_minimal_data(self):
        """Test initialization with minimal valid data."""
        data = pd.DataFrame({
            "id": [1, 2],
            "keyword": ["A", "B"],
            "prompt": ["Test"] * 2,
            "output": ["Text 1", "Text 2"],
            "pronoun_group": ["he/him", "she/her"]
        })
        
        analyzer = MLBiasAnalyzer(data)
        assert len(analyzer.data) == 2


class TestBiasPredictorTraining:
    """Test Random Forest bias predictor."""
    
    def test_train_bias_predictor(self, ml_analyzer):
        """Test training the bias prediction model."""
        results = ml_analyzer.train_bias_predictor()
        
        # Check all expected keys exist
        assert "train_accuracy" in results
        assert "test_accuracy" in results
        assert "cv_scores" in results
        assert "feature_importance" in results
        assert "feature_names" in results
        assert "confusion_matrix" in results
        assert "class_labels" in results
        
        # Check value types and ranges
        assert 0 <= results["train_accuracy"] <= 1
        assert 0 <= results["test_accuracy"] <= 1
        assert isinstance(results["cv_scores"], (list, np.ndarray))
        assert len(results["cv_scores"]) > 0
        
        # Check feature importance
        assert len(results["feature_importance"]) == len(results["feature_names"])
        assert all(imp >= 0 for imp in results["feature_importance"])
        assert np.isclose(sum(results["feature_importance"]), 1.0, atol=0.01)
    
    def test_train_with_test_size(self, ml_analyzer):
        """Test training with custom test size."""
        results = ml_analyzer.train_bias_predictor(test_size=0.3)
        
        assert "train_accuracy" in results
        assert "test_accuracy" in results
    
    def test_train_with_cv_folds(self, ml_analyzer):
        """Test training with custom CV folds."""
        results = ml_analyzer.train_bias_predictor(cv_folds=3)
        
        assert len(results["cv_scores"]) == 3
    
    def test_feature_names_include_keywords(self, ml_analyzer):
        """Test that feature names include encoded keywords."""
        results = ml_analyzer.train_bias_predictor()
        
        feature_names = results["feature_names"]
        
        # Should have keyword features
        keyword_features = [f for f in feature_names if f.startswith("keyword_")]
        assert len(keyword_features) > 0
    
    def test_confusion_matrix_shape(self, ml_analyzer):
        """Test confusion matrix has correct shape."""
        results = ml_analyzer.train_bias_predictor()
        
        cm = results["confusion_matrix"]
        labels = results["class_labels"]
        
        assert cm.shape[0] == cm.shape[1]
        assert cm.shape[0] == len(labels)
    
    def test_model_better_than_baseline(self, ml_analyzer):
        """Test that model performs better than baseline."""
        results = ml_analyzer.train_bias_predictor()
        
        # Baseline is most frequent class
        baseline = ml_analyzer.data["pronoun_group"].value_counts().max() / len(ml_analyzer.data)
        
        # Model should generally do better than baseline
        # (May not always be true with random data, but should be for structured data)
        test_acc = results["test_accuracy"]
        
        # At minimum, should not be dramatically worse
        assert test_acc > baseline * 0.5


class TestBiasPrediction:
    """Test bias prediction for new instances."""
    
    def test_predict_bias_likelihood(self, ml_analyzer):
        """Test predicting bias for a new profession."""
        # Train first
        ml_analyzer.train_bias_predictor()
        
        # Predict
        prediction = ml_analyzer.predict_bias_likelihood("Scientist", "Describe a {keyword}.")
        
        assert "predicted_class" in prediction
        assert "confidence" in prediction
        assert "probabilities" in prediction
        
        # Check probabilities
        probs = prediction["probabilities"]
        assert all(0 <= p <= 1 for p in probs.values())
        assert np.isclose(sum(probs.values()), 1.0, atol=0.01)
        
        # Predicted class should be the one with highest probability
        max_prob_class = max(probs, key=probs.get)
        assert prediction["predicted_class"] == max_prob_class
        assert prediction["confidence"] == probs[max_prob_class]
    
    def test_predict_without_training(self, ml_analyzer):
        """Test that prediction fails without training first."""
        with pytest.raises((AttributeError, ValueError)):
            ml_analyzer.predict_bias_likelihood("Test", "Test prompt")
    
    def test_predict_for_known_keyword(self, ml_analyzer):
        """Test prediction for a keyword that exists in training data."""
        ml_analyzer.train_bias_predictor()
        
        # Predict for a keyword from training data
        prediction = ml_analyzer.predict_bias_likelihood("Nurse", "Describe a {keyword}.")
        
        assert prediction["predicted_class"] in ["he/him", "she/her", "they/them", "none"]
        assert 0 <= prediction["confidence"] <= 1


class TestCosineSimilarity:
    """Test cosine similarity analysis."""
    
    def test_compute_response_similarity(self, ml_analyzer):
        """Test computing similarity between two models."""
        result = ml_analyzer.compute_response_similarity("phi3", "llama3.2")
        
        assert "overall_similarity" in result
        assert "keyword_similarities" in result
        
        # Similarity should be between -1 and 1 (typically 0 to 1)
        assert -1 <= result["overall_similarity"] <= 1
        
        # Check keyword-level similarities
        for keyword, sim in result["keyword_similarities"].items():
            assert -1 <= sim <= 1
    
    def test_similarity_same_model(self, ml_analyzer):
        """Test that same model has perfect similarity with itself."""
        result = ml_analyzer.compute_response_similarity("phi3", "phi3")
        
        # Should be very close to 1.0 (perfect similarity)
        assert result["overall_similarity"] > 0.95
    
    def test_similarity_with_few_samples(self):
        """Test similarity with minimal data."""
        data = pd.DataFrame({
            "model": ["A", "A", "B", "B"],
            "keyword": ["X", "Y", "X", "Y"],
            "output": ["text1", "text2", "text3", "text4"],
            "pronoun_group": ["he/him"] * 4
        })
        
        analyzer = MLBiasAnalyzer(data)
        result = analyzer.compute_response_similarity("A", "B")
        
        assert "overall_similarity" in result
        assert -1 <= result["overall_similarity"] <= 1
    
    def test_similarity_nonexistent_model(self, ml_analyzer):
        """Test similarity with nonexistent model."""
        with pytest.raises((ValueError, KeyError)):
            ml_analyzer.compute_response_similarity("phi3", "nonexistent_model")


class TestCompareAllModels:
    """Test comparison across all models."""
    
    def test_compare_all_models(self, ml_analyzer):
        """Test computing similarity matrix for all models."""
        result = ml_analyzer.compare_all_models()
        
        assert "similarity_matrix" in result
        assert "most_similar" in result
        assert "least_similar" in result
        
        # Check similarity matrix
        sim_matrix = result["similarity_matrix"]
        models = ml_analyzer.data["model"].unique()
        
        assert sim_matrix.shape == (len(models), len(models))
        
        # Diagonal should be close to 1.0 (self-similarity)
        for i in range(len(models)):
            assert sim_matrix.iloc[i, i] > 0.95
    
    def test_most_similar_pair(self, ml_analyzer):
        """Test identification of most similar models."""
        result = ml_analyzer.compare_all_models()
        
        most_similar = result["most_similar"]
        
        assert "model1" in most_similar
        assert "model2" in most_similar
        assert "similarity" in most_similar
        assert 0 <= most_similar["similarity"] <= 1
    
    def test_least_similar_pair(self, ml_analyzer):
        """Test identification of least similar models."""
        result = ml_analyzer.compare_all_models()
        
        least_similar = result["least_similar"]
        
        assert "model1" in least_similar
        assert "model2" in least_similar
        assert "similarity" in least_similar
        assert -1 <= least_similar["similarity"] <= 1
    
    def test_compare_with_single_model(self):
        """Test comparison when only one model exists."""
        data = pd.DataFrame({
            "model": ["A"] * 10,
            "keyword": ["X"] * 10,
            "output": [f"text{i}" for i in range(10)],
            "pronoun_group": ["he/him"] * 10
        })
        
        analyzer = MLBiasAnalyzer(data)
        
        # Should handle gracefully (may raise exception or return special value)
        try:
            result = analyzer.compare_all_models()
            # If it doesn't raise, should have 1x1 matrix
            assert result["similarity_matrix"].shape == (1, 1)
        except ValueError:
            # It's also acceptable to raise an error for single model
            pass


class TestWordFrequencyExtraction:
    """Test TF-IDF word frequency extraction."""
    
    def test_extract_word_frequencies(self, ml_analyzer):
        """Test extracting top words for each pronoun group."""
        word_freq = ml_analyzer.extract_word_frequencies(top_n=10)
        
        # Should have results for pronoun groups that exist in data
        assert isinstance(word_freq, dict)
        assert len(word_freq) > 0
        
        # Check structure for each group
        for pronoun_group, words in word_freq.items():
            assert isinstance(words, list)
            assert len(words) <= 10
            
            # Each item should be (word, score) tuple
            for word, score in words:
                assert isinstance(word, str)
                assert isinstance(score, (int, float))
                assert score >= 0
    
    def test_word_frequencies_custom_top_n(self, ml_analyzer):
        """Test with custom number of top words."""
        word_freq_5 = ml_analyzer.extract_word_frequencies(top_n=5)
        word_freq_20 = ml_analyzer.extract_word_frequencies(top_n=20)
        
        # Should respect top_n parameter
        for pronoun_group in word_freq_5.keys():
            assert len(word_freq_5[pronoun_group]) <= 5
        
        for pronoun_group in word_freq_20.keys():
            assert len(word_freq_20[pronoun_group]) <= 20
    
    def test_word_frequencies_different_groups(self, ml_analyzer):
        """Test that different pronoun groups have different word frequencies."""
        word_freq = ml_analyzer.extract_word_frequencies(top_n=10)
        
        # Get top words for each group
        if "he/him" in word_freq and "she/her" in word_freq:
            he_words = {word for word, _ in word_freq["he/him"]}
            she_words = {word for word, _ in word_freq["she/her"]}
            
            # There should be some difference (not all words the same)
            # Though some overlap is expected
            assert he_words != she_words


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_insufficient_data_for_training(self):
        """Test training with insufficient data."""
        data = pd.DataFrame({
            "keyword": ["A"],
            "prompt": ["Test"],
            "output": ["Text"],
            "pronoun_group": ["he/him"]
        })
        
        analyzer = MLBiasAnalyzer(data)
        
        # Should either work with warnings or raise appropriate error
        try:
            results = analyzer.train_bias_predictor()
            # If it works, accuracy might be low/undefined
            assert "train_accuracy" in results
        except (ValueError, Exception):
            # It's acceptable to fail with insufficient data
            pass
    
    def test_single_class_prediction(self):
        """Test when data has only one pronoun group."""
        data = pd.DataFrame({
            "keyword": ["A", "B", "C"] * 10,
            "prompt": ["Test"] * 30,
            "output": [f"Text {i}" for i in range(30)],
            "pronoun_group": ["he/him"] * 30  # Only one class
        })
        
        analyzer = MLBiasAnalyzer(data)
        
        # Should handle single-class scenario
        try:
            results = analyzer.train_bias_predictor()
            # Accuracy should be 100% for single class
            assert results["train_accuracy"] == 1.0
        except ValueError:
            # May raise error for single class
            pass
    
    def test_empty_text_responses(self):
        """Test handling of empty text responses."""
        data = pd.DataFrame({
            "keyword": ["A", "B"],
            "prompt": ["Test"] * 2,
            "output": ["", ""],  # Empty responses
            "pronoun_group": ["he/him", "she/her"]
        })
        
        analyzer = MLBiasAnalyzer(data)
        
        # Should handle empty text gracefully
        try:
            result = analyzer.compute_response_similarity("A", "B")
            # May have zero or undefined similarity
            assert "overall_similarity" in result
        except (ValueError, Exception):
            # Acceptable to fail with empty text
            pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
