"""Tests for database module."""

import sqlite3
import tempfile
from pathlib import Path

import pytest

from llm_bias_research.database import BiasDatabase


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    yield db_path

    # Cleanup
    Path(db_path).unlink(missing_ok=True)


@pytest.fixture
def sample_rows():
    """Sample data rows for testing."""
    return [
        {
            "rowIndex": 1,
            "keyword": "Nurse",
            "prompt": "Describe a Nurse.",
            "response": "A nurse helps patients.",
        },
        {
            "rowIndex": 2,
            "keyword": "Doctor",
            "prompt": "Describe a Doctor.",
            "response": "A doctor treats illnesses.",
        },
        {
            "rowIndex": 3,
            "keyword": "Nurse",
            "prompt": "What does a Nurse do?",
            "response": "Nurses provide care.",
        },
    ]


class TestBiasDatabase:
    """Tests for BiasDatabase class."""

    def test_create_schema(self, temp_db):
        """Should create database schema successfully."""
        db = BiasDatabase(temp_db)
        db.create_schema()

        # Verify tables exist
        with sqlite3.connect(temp_db) as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            )
            tables = [row[0] for row in cursor.fetchall()]

        assert "models" in tables
        assert "keywords" in tables
        assert "responses" in tables

    def test_insert_model_data(self, temp_db, sample_rows):
        """Should insert model data correctly."""
        db = BiasDatabase(temp_db)
        db.create_schema()

        count = db.insert_model_data("test_model", sample_rows)

        assert count == 3

        # Verify data was inserted
        with sqlite3.connect(temp_db) as conn:
            model_count = conn.execute("SELECT COUNT(*) FROM models").fetchone()[0]
            keyword_count = conn.execute("SELECT COUNT(*) FROM keywords").fetchone()[0]
            response_count = conn.execute("SELECT COUNT(*) FROM responses").fetchone()[0]

        assert model_count == 1
        assert keyword_count == 2  # Nurse and Doctor
        assert response_count == 3

    def test_get_all_models(self, temp_db, sample_rows):
        """Should retrieve all model names."""
        db = BiasDatabase(temp_db)
        db.create_schema()
        db.insert_model_data("model1", sample_rows)
        db.insert_model_data("model2", sample_rows)

        models = db.get_all_models()

        assert len(models) == 2
        assert "model1" in models
        assert "model2" in models

    def test_get_all_keywords(self, temp_db, sample_rows):
        """Should retrieve all keywords."""
        db = BiasDatabase(temp_db)
        db.create_schema()
        db.insert_model_data("test_model", sample_rows)

        keywords = db.get_all_keywords()

        assert len(keywords) == 2
        assert "Nurse" in keywords
        assert "Doctor" in keywords

    def test_get_responses_no_filter(self, temp_db, sample_rows):
        """Should retrieve all responses without filtering."""
        db = BiasDatabase(temp_db)
        db.create_schema()
        db.insert_model_data("test_model", sample_rows)

        responses = db.get_responses()

        assert len(responses) == 3

    def test_get_responses_with_model_filter(self, temp_db, sample_rows):
        """Should filter responses by model."""
        db = BiasDatabase(temp_db)
        db.create_schema()
        db.insert_model_data("model1", sample_rows)
        db.insert_model_data("model2", sample_rows)

        responses = db.get_responses(model="model1")

        assert len(responses) == 3
        assert all(r["model"] == "model1" for r in responses)

    def test_get_responses_with_keyword_filter(self, temp_db, sample_rows):
        """Should filter responses by keyword."""
        db = BiasDatabase(temp_db)
        db.create_schema()
        db.insert_model_data("test_model", sample_rows)

        responses = db.get_responses(keyword="Nurse")

        assert len(responses) == 2
        assert all(r["keyword"] == "Nurse" for r in responses)

    def test_get_statistics(self, temp_db, sample_rows):
        """Should return correct statistics."""
        db = BiasDatabase(temp_db)
        db.create_schema()
        db.insert_model_data("test_model", sample_rows)

        stats = db.get_statistics()

        assert stats["total_models"] == 1
        assert stats["total_keywords"] == 2
        assert stats["total_responses"] == 3
        assert "test_model" in stats["models"]
        assert "Nurse" in stats["keywords"]
        assert "Doctor" in stats["keywords"]

    def test_insert_empty_rows_raises_error(self, temp_db):
        """Should raise ValueError for empty rows."""
        db = BiasDatabase(temp_db)
        db.create_schema()

        with pytest.raises(ValueError, match="No data to insert"):
            db.insert_model_data("test_model", [])
