# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.2] - 2026-07-16

### Added
- Multi-database file upload support in dashboard for model comparison
- `load_multiple_databases()` function to merge data from multiple database files
- Expandable sidebar section showing details of loaded databases and models
- Enhanced instructions and help text for multi-model comparison workflow

### Changed
- Dashboard file uploader now accepts multiple files (`accept_multiple_files=True`)
- Database loading workflow optimized for separate model databases
- Model Comparison page updated with clearer usage instructions

### Improved
- Memory efficiency by loading separate databases per model instead of combining during collection
- User experience with detailed database and model information in sidebar
- Documentation with multi-model comparison examples in README and dashboard README

## [0.2.1] - 2026-07-16

### Changed
- Dashboard welcome text color changed to dark green (#0d6f0d) for improved readability and contrast
- All custom info boxes and metric cards now use dark text colors for better legibility

### Fixed
- Low contrast issue in info boxes making text difficult to read
- Breakdown section metric cards now have dark text (#1a1a1a) for better readability
- Insight boxes in Overview page now have dark text for improved contrast

## [0.2.0] - 2026-07-16

### Added
- Nested progress bars showing overall progress and current prompt context
- Enhanced screen indications with detailed processing information
- Default output directory (0_out/) with automatic creation
- Filename serialization to prevent overwriting (file.csv → file_01.csv → file_02.csv)
- Max tokens option (--max-tokens) to control response size and prevent hallucination overflow
- Improved user experience with richer console output
- UV package manager support with 135x faster installation

### Changed
- Default output path changed from "results/output" to "0_out/output"
- Progress bars now show two levels: overall job and current prompt
- Each query run displays abbreviated prompt text for context

### Fixed
- File overwrite protection through automatic filename serialization
- Runaway responses controlled by max_tokens parameter

## [0.1.0] - 2026-07-16

### Added
- Initial project structure and core functionality
- CLI tool for querying Ollama models
- Simultaneous CSV and SQLite database output
- Interactive Streamlit dashboard with multiple analysis pages
- Statistical significance testing (chi-square, t-tests)
- Multi-database comparison tools
- Time-series analysis for tracking bias over model versions
- Sentiment analysis correlation features
- Word cloud visualizations by gender group
- Machine learning bias prediction
- Cosine similarity for model comparison
- PDF export functionality for reports
- Comprehensive test suite with pytest
- Full documentation and examples

## [0.1.0] - 2026-07-16

### Added
- Initial release
- Core bias detection algorithm
- Ollama integration for local LLM querying
- Database schema for storing responses
- Basic Streamlit visualization dashboard

[Unreleased]: https://github.com/yourusername/llm-bias-research/compare/v0.2.2...HEAD
[0.2.2]: https://github.com/yourusername/llm-bias-research/compare/v0.2.1...v0.2.2
[0.2.1]: https://github.com/yourusername/llm-bias-research/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/yourusername/llm-bias-research/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/yourusername/llm-bias-research/releases/tag/v0.1.0
