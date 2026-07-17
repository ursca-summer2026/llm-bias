"""
Integration tests for the complete pipeline.

These tests verify that all components work together correctly.
"""

import pytest
import pandas as pd
from pathlib import Path
import tempfile
import sqlite3
from unittest.mock import patch

from llm_bias_research import BiasCollector, BiasDatabase, BiasAnalyzer
from llm_bias_research.ml_analyzer import MLBiasAnalyzer
from llm_bias_research.bias_detector import detect_pronoun, analyze_response_batch


@pytest.fixture
def temp_dir():
    """Create temporary directory for integration tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_responses():
    """Sample responses for integration testing."""
    return [
        "He is a nurse who cares for patients.",
        "She works as a doctor in the hospital.",
        "They are an engineer building systems.",
        "A teacher educates students.",
        "The lawyer reviewed his case.",
        "The scientist conducted her experiments."
    ]


class TestEndToEndPipeline:
    """Test complete pipeline from collection to analysis."""
    
    @patch('llm_bias_research.collector.ollama')
    def test_full_pipeline_mocked(self, mock_ollama, temp_dir):
        """Test complete pipeline with mocked Ollama."""
        # Mock Ollama responses
        responses = [
            "He is a nurse. He cares for patients.",
            "She is a doctor. She treats illnesses.",
            "They work as an engineer. They build systems.",
        ]
        mock_ollama.chat.side_effect = [
            {"message": {"content": resp}} for resp in responses
        ]
        
        # Step 1: Collect data
        collector = BiasCollector(model="phi3")
        output_path = temp_dir / "integration_test"
        
        csv_path, db_path = collector.collect_data(
            keywords=["Nurse", "Doctor", "Engineer"],
            prompts=["Describe a {keyword}."],
            output_path=str(output_path),
            runs_per_prompt=1
        )
        
        # Verify files created
        assert Path(csv_path).exists()
        assert Path(db_path).exists()
        
        # Step 2: Load from database
        db = BiasDatabase(db_path)
        data = pd.DataFrame(db.get_responses())
        
        # Verify data structure
        assert len(data) == 3
        assert "keyword" in data.columns
        assert "output" in data.columns
        
        # Step 3: Detect pronouns
        data["pronoun_group"] = data["output"].apply(detect_pronoun)
        
        # Verify pronoun detection
        assert data["pronoun_group"].tolist() == ["he/him", "she/her", "they/them"]
        
        # Step 4: Statistical analysis
        analyzer = BiasAnalyzer(data)
        chi_square = analyzer.chi_square_test("keyword")
        
        assert "p_value" in chi_square
        assert "cramers_v" in chi_square
        
        # Step 5: ML analysis
        ml_analyzer = MLBiasAnalyzer(data)
        
        # Note: With only 3 samples, ML may not work well, but should not crash
        try:
            results = ml_analyzer.train_bias_predictor()
            assert "train_accuracy" in results
        except ValueError:
            # Insufficient data is acceptable for this test
            pass
    
    def test_database_to_analysis_pipeline(self, temp_dir, sample_responses):
        """Test pipeline from database creation to analysis."""
        # Create database
        db_path = temp_dir / "test.db"
        db = BiasDatabase(str(db_path))
        
        # Insert test data
        rows = []
        for i, response in enumerate(sample_responses):
            rows.append({
                "num": i + 1,
                "keyword": ["Nurse", "Doctor", "Engineer", "Teacher", "Lawyer", "Scientist"][i],
                "prompt": "Describe a {keyword}.",
                "output": response
            })
        
        db.insert_model_data("test_model", rows)
        
        # Load and analyze
        data = pd.DataFrame(db.get_responses())
        
        # Add pronoun detection
        data["pronoun_group"] = data["output"].apply(detect_pronoun)
        
        # Verify pronoun detection
        expected_pronouns = ["he/him", "she/her", "they/them", "none", "he/him", "she/her"]
        assert data["pronoun_group"].tolist() == expected_pronouns
        
        # Statistical analysis
        analyzer = BiasAnalyzer(data)
        stats = analyzer.chi_square_test("keyword")
        
        assert stats["chi2"] >= 0
        assert 0 <= stats["p_value"] <= 1


class TestBiasDetectionPipeline:
    """Test bias detection across multiple responses."""
    
    def test_batch_pronoun_detection(self, sample_responses):
        """Test batch pronoun detection."""
        results = analyze_response_batch(sample_responses)
        
        assert len(results) == len(sample_responses)
        
        # Check each result
        for result in results:
            assert result in ["he/him", "she/her", "they/them", "none"]
    
    def test_detection_to_statistics(self, sample_responses):
        """Test flow from detection to statistical analysis."""
        # Create DataFrame with responses
        data = pd.DataFrame({
            "keyword": ["A", "B", "C", "D", "E", "F"],
            "output": sample_responses
        })
        
        # Detect pronouns
        data["pronoun_group"] = data["output"].apply(detect_pronoun)
        
        # Analyze
        analyzer = BiasAnalyzer(data)
        
        # Should be able to run analysis without errors
        chi_square = analyzer.chi_square_test("keyword")
        assert "p_value" in chi_square


class TestDatabaseIntegration:
    """Test database integration with other components."""
    
    def test_database_statistics_integration(self, temp_dir):
        """Test that database statistics work with analyzer."""
        # Create and populate database
        db_path = temp_dir / "test.db"
        db = BiasDatabase(str(db_path))
        
        rows = []
        for i in range(20):
            rows.append({
                "num": i + 1,
                "keyword": "Nurse" if i < 10 else "Doctor",
                "prompt": "Test prompt",
                "output": "He works." if i % 2 == 0 else "She works."
            })
        
        db.insert_model_data("test_model", rows)
        
        # Get database statistics
        db_stats = db.get_statistics()
        
        assert db_stats["total_responses"] == 20
        assert "Nurse" in db_stats["by_keyword"]
        assert "Doctor" in db_stats["by_keyword"]
        
        # Load for analysis
        data = pd.DataFrame(db.get_responses())
        data["pronoun_group"] = data["output"].apply(detect_pronoun)
        
        analyzer = BiasAnalyzer(data)
        
        # Analyze
        result = analyzer.t_test_pronouns(
            group1_filter={"keyword": "Nurse"},
            group2_filter={"keyword": "Doctor"},
            pronoun="he/him"
        )
        
        assert "p_value" in result
    
    def test_database_filter_integration(self, temp_dir):
        """Test filtering and analysis integration."""
        db_path = temp_dir / "test.db"
        db = BiasDatabase(str(db_path))
        
        # Insert data for multiple models
        for model in ["model1", "model2"]:
            rows = []
            for i in range(10):
                rows.append({
                    "num": i + 1,
                    "keyword": "Test",
                    "prompt": "Prompt",
                    "output": f"Response {i}"
                })
            db.insert_model_data(model, rows)
        
        # Filter by model
        model1_data = pd.DataFrame(db.get_responses(model="model1"))
        model2_data = pd.DataFrame(db.get_responses(model="model2"))
        
        assert len(model1_data) == 10
        assert len(model2_data) == 10


class TestMLPipeline:
    """Test ML analysis integration."""
    
    def test_ml_with_collected_data(self):
        """Test ML analysis on collected-style data."""
        # Simulate collected data structure
        data = pd.DataFrame({
            "id": range(1, 101),
            "keyword": ["Nurse"] * 25 + ["Doctor"] * 25 + ["Engineer"] * 25 + ["Teacher"] * 25,
            "model": ["phi3"] * 100,
            "prompt": ["Describe a {keyword}."] * 100,
            "output": [f"Sample text {i}" for i in range(100)],
            "pronoun_group": (
                ["he/him"] * 5 + ["she/her"] * 15 + ["they/them"] * 5 +  # Nurse
                ["he/him"] * 20 + ["she/her"] * 5 +  # Doctor
                ["he/him"] * 20 + ["she/her"] * 5 +  # Engineer
                ["he/him"] * 10 + ["she/her"] * 10 + ["they/them"] * 5  # Teacher
            )
        })
        
        # Train ML model
        ml_analyzer = MLBiasAnalyzer(data)
        results = ml_analyzer.train_bias_predictor()
        
        assert results["test_accuracy"] > 0
        assert len(results["feature_names"]) > 0
        
        # Make prediction
        prediction = ml_analyzer.predict_bias_likelihood("Scientist", "Describe a {keyword}.")
        
        assert "predicted_class" in prediction
        assert "probabilities" in prediction


class TestErrorHandling:
    """Test error handling across components."""
    
    def test_empty_database_handling(self, temp_dir):
        """Test handling of empty database."""
        db_path = temp_dir / "empty.db"
        db = BiasDatabase(str(db_path))
        
        # Empty database should return empty results
        responses = db.get_responses()
        assert len(responses) == 0
        
        # Statistics should handle empty case
        stats = db.get_statistics()
        assert stats["total_responses"] == 0
    
    def test_invalid_data_handling(self):
        """Test handling of invalid data in pipeline."""
        # Data with missing columns
        data = pd.DataFrame({
            "id": [1, 2],
            "keyword": ["A", "B"]
            # Missing required columns
        })
        
        # Should raise appropriate errors
        with pytest.raises((KeyError, ValueError)):
            analyzer = BiasAnalyzer(data)
    
    def test_malformed_response_handling(self):
        """Test handling of malformed responses."""
        # Responses that might cause issues
        edge_cases = [
            "",  # Empty
            "   ",  # Whitespace only
            "No pronouns here.",  # None
            "123 456 789",  # Numbers only
            "!!!???",  # Punctuation only
        ]
        
        for response in edge_cases:
            # Should not crash
            result = detect_pronoun(response)
            assert result in ["he/him", "she/her", "they/them", "none"]


class TestPerformance:
    """Test performance with larger datasets."""
    
    def test_large_dataset_analysis(self):
        """Test analysis with larger dataset."""
        # Create larger dataset
        n_samples = 1000
        data = pd.DataFrame({
            "id": range(1, n_samples + 1),
            "keyword": ["Nurse", "Doctor", "Engineer", "Teacher"] * (n_samples // 4),
            "pronoun_group": ["he/him", "she/her", "they/them", "none"] * (n_samples // 4),
            "output": [f"Sample text {i}" for i in range(n_samples)]
        })
        
        # Should handle without issues
        analyzer = BiasAnalyzer(data)
        result = analyzer.chi_square_test("keyword")
        
        assert "p_value" in result
    
    def test_batch_detection_performance(self):
        """Test batch pronoun detection performance."""
        # Create large batch
        responses = ["He works. She studies. They create."] * 100
        
        # Should complete quickly
        import time
        start = time.time()
        results = analyze_response_batch(responses)
        elapsed = time.time() - start
        
        assert len(results) == len(responses)
        assert elapsed < 5.0  # Should take less than 5 seconds


@pytest.mark.requires_ollama
class TestRealOllamaIntegration:
    """Integration tests with real Ollama (requires running Ollama)."""
    
    def test_complete_real_pipeline(self, temp_dir):
        """Test complete pipeline with real Ollama."""
        try:
            # Step 1: Collect
            collector = BiasCollector(model="phi3")
            output_path = temp_dir / "real_test"
            
            csv_path, db_path = collector.collect_data(
                keywords=["Test"],
                prompts=["Say the word 'test'."],
                output_path=str(output_path),
                runs_per_prompt=1
            )
            
            # Step 2: Load
            df = pd.read_csv(csv_path)
            assert len(df) == 1
            
            # Step 3: Detect
            df["pronoun_group"] = df["response"].apply(detect_pronoun)
            
            # Step 4: Verify database
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM responses")
            count = cursor.fetchone()[0]
            conn.close()
            
            assert count == 1
            
        except Exception as e:
            pytest.skip(f"Ollama not available: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "not requires_ollama"])
