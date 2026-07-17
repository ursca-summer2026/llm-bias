"""
Database management module for SQLite operations.

This module handles:
- Creating and managing SQLite schemas
- Inserting and querying bias research data
- Supporting multi-model comparisons
"""

import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

from llm_bias_research.bias_detector import detect_pronoun


class BiasDatabase:
    """Manages SQLite database for bias research data.

    The database has three main tables:
    - models: Stores model metadata
    - keywords: Stores profession/keyword data
    - responses: Stores individual LLM responses with foreign keys
    """

    def __init__(self, db_path: str) -> None:
        """Initialize database connection.

        Args:
            db_path: Path to the SQLite database file.
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def create_schema(self) -> None:
        """Create the database schema if it doesn't exist.

        Creates three normalized tables:
        - models: id, name, created_at
        - keywords: id, keyword, created_at
        - responses: id, num, prompt, output, model_id, keyword_id, created_at
        """
        schema = """
        -- The AI models we tested (e.g., phi3, llama3.2)
        CREATE TABLE IF NOT EXISTS models (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- The professions/keywords we prompted about
        CREATE TABLE IF NOT EXISTS keywords (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            keyword TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Individual responses from models
        CREATE TABLE IF NOT EXISTS responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            num INTEGER NOT NULL,
            prompt TEXT NOT NULL,
            output TEXT NOT NULL,
            model_id INTEGER NOT NULL,
            keyword_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (model_id) REFERENCES models(id),
            FOREIGN KEY (keyword_id) REFERENCES keywords(id)
        );

        -- Indexes for faster queries
        CREATE INDEX IF NOT EXISTS idx_responses_model ON responses(model_id);
        CREATE INDEX IF NOT EXISTS idx_responses_keyword ON responses(keyword_id);
        """

        with sqlite3.connect(self.db_path) as conn:
            conn.executescript(schema)

    def insert_model_data(
        self,
        model_name: str,
        rows: List[Dict[str, Any]],
    ) -> int:
        """Insert data for a model from collected rows.

        Args:
            model_name: Name of the model.
            rows: List of dictionaries with keys: rowIndex, keyword, prompt, response.

        Returns:
            Number of rows inserted.

        Raises:
            ValueError: If rows are invalid.
        """
        if not rows:
            raise ValueError("No data to insert")

        with sqlite3.connect(self.db_path) as conn:
            # Insert model
            conn.execute(
                "INSERT OR IGNORE INTO models (name) VALUES (?)",
                (model_name,),
            )
            model_id = conn.execute(
                "SELECT id FROM models WHERE name = ?",
                (model_name,),
            ).fetchone()[0]

            # Insert each response
            for row in rows:
                keyword = row["keyword"]
                
                # Insert keyword
                conn.execute(
                    "INSERT OR IGNORE INTO keywords (keyword) VALUES (?)",
                    (keyword,),
                )
                keyword_id = conn.execute(
                    "SELECT id FROM keywords WHERE keyword = ?",
                    (keyword,),
                ).fetchone()[0]

                # Insert response
                conn.execute(
                    """
                    INSERT INTO responses (num, prompt, output, model_id, keyword_id)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        row["rowIndex"],
                        row["prompt"],
                        row["response"],
                        model_id,
                        keyword_id,
                    ),
                )

            conn.commit()

        return len(rows)

    def get_all_models(self) -> List[str]:
        """Get list of all model names in the database.

        Returns:
            List of model names.
        """
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute("SELECT name FROM models ORDER BY name").fetchall()
        return [row[0] for row in rows]

    def get_all_keywords(self) -> List[str]:
        """Get list of all keywords in the database.

        Returns:
            List of keywords.
        """
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute("SELECT keyword FROM keywords ORDER BY keyword").fetchall()
        return [row[0] for row in rows]

    def get_responses(
        self,
        model: Optional[str] = None,
        keyword: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get responses with optional filtering.

        Args:
            model: Filter by model name (optional).
            keyword: Filter by keyword (optional).

        Returns:
            List of response dictionaries with keys: num, model, keyword, prompt, output.
        """
        query = """
            SELECT 
                responses.num,
                models.name as model,
                keywords.keyword,
                responses.prompt,
                responses.output
            FROM responses
            JOIN models ON responses.model_id = models.id
            JOIN keywords ON responses.keyword_id = keywords.id
            WHERE 1=1
        """
        params = []

        if model:
            query += " AND models.name = ?"
            params.append(model)

        if keyword:
            query += " AND keywords.keyword = ?"
            params.append(keyword)

        query += " ORDER BY models.name, responses.num"

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(query, params).fetchall()

        return [dict(row) for row in rows]

    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics.

        Returns:
            Dictionary with counts and breakdowns.
        """
        with sqlite3.connect(self.db_path) as conn:
            stats = {}

            # Record counts
            stats["total_models"] = conn.execute("SELECT COUNT(*) FROM models").fetchone()[0]
            stats["total_keywords"] = conn.execute("SELECT COUNT(*) FROM keywords").fetchone()[0]
            stats["total_responses"] = conn.execute("SELECT COUNT(*) FROM responses").fetchone()[0]

            # Models
            stats["models"] = [
                row[0] for row in conn.execute("SELECT name FROM models ORDER BY name").fetchall()
            ]

            # Keywords
            stats["keywords"] = [
                row[0] for row in conn.execute("SELECT keyword FROM keywords ORDER BY keyword").fetchall()
            ]

            # Responses per model
            rows = conn.execute("""
                SELECT models.name, COUNT(responses.id)
                FROM models
                LEFT JOIN responses ON models.id = responses.model_id
                GROUP BY models.id
                ORDER BY models.name
            """).fetchall()
            stats["responses_per_model"] = {row[0]: row[1] for row in rows}

            # Responses per keyword
            rows = conn.execute("""
                SELECT keywords.keyword, COUNT(responses.id)
                FROM keywords
                LEFT JOIN responses ON keywords.id = responses.keyword_id
                GROUP BY keywords.id
                ORDER BY keywords.keyword
            """).fetchall()
            stats["responses_per_keyword"] = {row[0]: row[1] for row in rows}

        return stats

    def close(self) -> None:
        """Close any open connections (placeholder for future connection pooling)."""
        pass
