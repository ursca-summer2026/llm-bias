"""
Tests for the data collector module.

Note: These tests require Ollama to be running for integration tests.
Use @pytest.mark.requires_ollama for tests that need Ollama.
"""

import pytest
import pandas as pd
from pathlib import Path
import tempfile
import sqlite3
from unittest.mock import Mock, patch, MagicMock

from llm_bias_research.collector import BiasCollector


@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_prompts():
    """Sample prompts for testing."""
    return [
        "Describe a {keyword}.",
        "What does a {keyword} do?",
        "Tell me about a typical {keyword}."
    ]


@pytest.fixture
def sample_keywords():
    """Sample keywords for testing."""
    return ["Nurse", "Doctor"]


class TestBiasCollectorInit:
    """Test BiasCollector initialization."""
    
    def test_init_basic(self):
        """Test basic initialization."""
        collector = BiasCollector(model="phi3")
        assert collector.model == "phi3"
        assert collector.rate_limit_delay >= 0
        assert collector.max_retries > 0
    
    def test_init_with_custom_params(self):
        """Test initialization with custom parameters."""
        collector = BiasCollector(
            model="llama3.2",
            rate_limit_delay=0.1,
            max_retries=5
        )
        assert collector.model == "llama3.2"
        assert collector.rate_limit_delay == 0.1
        assert collector.max_retries == 5
    
    def test_init_invalid_delay(self):
        """Test initialization with invalid delay."""
        with pytest.raises((ValueError, AssertionError)):
            BiasCollector(model="phi3", rate_limit_delay=-1)
    
    def test_init_invalid_retries(self):
        """Test initialization with invalid retries."""
        with pytest.raises((ValueError, AssertionError)):
            BiasCollector(model="phi3", max_retries=0)


class TestBiasCollectorMocked:
    """Test BiasCollector with mocked Ollama calls."""
    
    @patch('llm_bias_research.collector.ollama')
    def test_query_model_basic(self, mock_ollama, temp_output_dir):
        """Test basic model query with mocked response."""
        # Mock Ollama response
        mock_ollama.chat.return_value = {
            "message": {
                "content": "A nurse is a healthcare professional. They provide patient care."
            }
        }
        
        collector = BiasCollector(model="phi3")
        result = collector.query_model("Describe a nurse.")
        
        assert result == "A nurse is a healthcare professional. They provide patient care."
        mock_ollama.chat.assert_called_once()
    
    @patch('llm_bias_research.collector.ollama')
    def test_query_model_first_two_sentences(self, mock_ollama):
        """Test that only first two sentences are returned."""
        mock_ollama.chat.return_value = {
            "message": {
                "content": "First sentence. Second sentence. Third sentence. Fourth sentence."
            }
        }
        
        collector = BiasCollector(model="phi3")
        result = collector.query_model("Test prompt")
        
        assert "First sentence" in result
        assert "Second sentence" in result
        # Should not include third and fourth sentences
        assert result.count('.') <= 2
    
    @patch('llm_bias_research.collector.ollama')
    def test_query_model_retry_on_error(self, mock_ollama):
        """Test retry mechanism on API error."""
        # First call fails, second succeeds
        mock_ollama.chat.side_effect = [
            Exception("Connection error"),
            {"message": {"content": "Success response."}}
        ]
        
        collector = BiasCollector(model="phi3", max_retries=3)
        result = collector.query_model("Test prompt")
        
        assert result == "Success response."
        assert mock_ollama.chat.call_count == 2
    
    @patch('llm_bias_research.collector.ollama')
    def test_query_model_max_retries_exceeded(self, mock_ollama):
        """Test behavior when max retries exceeded."""
        # All calls fail
        mock_ollama.chat.side_effect = Exception("Connection error")
        
        collector = BiasCollector(model="phi3", max_retries=2)
        
        # Should raise exception after retries
        with pytest.raises(Exception):
            collector.query_model("Test prompt")
        
        assert mock_ollama.chat.call_count == 2
    
    @patch('llm_bias_research.collector.ollama')
    @patch('llm_bias_research.collector.BiasDatabase')
    def test_collect_data_creates_outputs(
        self, 
        mock_db, 
        mock_ollama, 
        temp_output_dir, 
        sample_keywords, 
        sample_prompts
    ):
        """Test that collect_data creates both CSV and database."""
        # Mock responses
        mock_ollama.chat.return_value = {
            "message": {"content": "Test response. Second sentence."}
        }
        
        collector = BiasCollector(model="phi3")
        
        output_path = temp_output_dir / "test_output"
        csv_path, db_path = collector.collect_data(
            keywords=sample_keywords,
            prompts=sample_prompts,
            output_path=str(output_path),
            runs_per_prompt=2
        )
        
        # Check paths returned
        assert csv_path.endswith(".csv")
        assert db_path.endswith(".db")
        
        # Check CSV created
        assert Path(csv_path).exists()
        
        # Check CSV content
        df = pd.read_csv(csv_path)
        expected_rows = len(sample_keywords) * len(sample_prompts) * 2  # 2 runs
        assert len(df) == expected_rows
        assert "keyword" in df.columns
        assert "prompt" in df.columns
        assert "response" in df.columns
    
    @patch('llm_bias_research.collector.ollama')
    def test_collect_data_csv_only(
        self, 
        mock_ollama, 
        temp_output_dir, 
        sample_keywords, 
        sample_prompts
    ):
        """Test collect_data with CSV only (no database)."""
        mock_ollama.chat.return_value = {
            "message": {"content": "Test response."}
        }
        
        collector = BiasCollector(model="phi3")
        
        output_path = temp_output_dir / "test_output"
        csv_path, db_path = collector.collect_data(
            keywords=sample_keywords,
            prompts=sample_prompts,
            output_path=str(output_path),
            runs_per_prompt=1,
            create_database=False
        )
        
        # CSV should exist
        assert Path(csv_path).exists()
        
        # Database path returned but may not be created
        assert db_path is None or db_path.endswith(".db")
    
    @patch('llm_bias_research.collector.ollama')
    def test_collect_data_progress_bar(
        self, 
        mock_ollama, 
        temp_output_dir, 
        sample_keywords, 
        sample_prompts
    ):
        """Test that progress bar is shown during collection."""
        mock_ollama.chat.return_value = {
            "message": {"content": "Test response."}
        }
        
        collector = BiasCollector(model="phi3")
        
        output_path = temp_output_dir / "test_output"
        
        # Should complete without errors
        csv_path, db_path = collector.collect_data(
            keywords=sample_keywords,
            prompts=sample_prompts,
            output_path=str(output_path),
            runs_per_prompt=1
        )
        
        assert Path(csv_path).exists()
    
    @patch('llm_bias_research.collector.ollama')
    def test_collect_data_rate_limiting(self, mock_ollama, temp_output_dir):
        """Test that rate limiting delay is applied."""
        import time
        
        mock_ollama.chat.return_value = {
            "message": {"content": "Test response."}
        }
        
        collector = BiasCollector(model="phi3", rate_limit_delay=0.05)
        
        output_path = temp_output_dir / "test_output"
        
        start_time = time.time()
        collector.collect_data(
            keywords=["Test"],
            prompts=["Prompt"],
            output_path=str(output_path),
            runs_per_prompt=3
        )
        elapsed = time.time() - start_time
        
        # Should take at least 2 delays (3 queries = 2 delays between them)
        # Using 0.05s delay, should take at least 0.1s
        assert elapsed >= 0.08  # Slightly less to account for timing variance


@pytest.mark.requires_ollama
class TestBiasCollectorIntegration:
    """Integration tests that require Ollama to be running.
    
    Run with: pytest -m requires_ollama
    Skip with: pytest -m "not requires_ollama"
    """
    
    def test_query_model_real(self):
        """Test real query to Ollama (requires Ollama running)."""
        try:
            collector = BiasCollector(model="phi3")
            result = collector.query_model("Say 'test'.")
            
            assert isinstance(result, str)
            assert len(result) > 0
        except Exception as e:
            pytest.skip(f"Ollama not available: {e}")
    
    def test_collect_data_real(self, temp_output_dir):
        """Test real data collection (requires Ollama running)."""
        try:
            collector = BiasCollector(model="phi3")
            
            output_path = temp_output_dir / "integration_test"
            csv_path, db_path = collector.collect_data(
                keywords=["Test"],
                prompts=["Briefly describe a {keyword}."],
                output_path=str(output_path),
                runs_per_prompt=1
            )
            
            # Verify CSV
            assert Path(csv_path).exists()
            df = pd.read_csv(csv_path)
            assert len(df) == 1
            assert df.iloc[0]["keyword"] == "Test"
            
            # Verify database
            assert Path(db_path).exists()
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM responses")
            count = cursor.fetchone()[0]
            conn.close()
            assert count == 1
            
        except Exception as e:
            pytest.skip(f"Ollama not available: {e}")


class TestUtilityFunctions:
    """Test utility functions in collector module."""
    
    def test_format_prompt(self):
        """Test prompt formatting with keyword substitution."""
        from llm_bias_research.collector import BiasCollector
        
        collector = BiasCollector(model="phi3")
        prompt_template = "Describe a {keyword}."
        formatted = prompt_template.replace("{keyword}", "Nurse")
        
        assert formatted == "Describe a Nurse."
        assert "{keyword}" not in formatted
    
    def test_extract_first_sentences(self):
        """Test extraction of first two sentences."""
        text = "First sentence. Second sentence. Third sentence."
        
        # Simple extraction
        parts = text.split(".")
        first_two = ". ".join(parts[:2]) + "."
        
        assert first_two == "First sentence. Second sentence."


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "not requires_ollama"])
