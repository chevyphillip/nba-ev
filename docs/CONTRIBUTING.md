# Contributing Guide

Thank you for your interest in contributing to the NBA Stats and Betting Analysis Tool! This document provides guidelines and instructions for contributing to the project.

## Development Setup

### Environment Setup

1. **Python Version**
   - Use Python 3.11 or higher
   - We recommend using `pyenv` for Python version management

2. **Dependencies**
   - We use `uv` for dependency management
   - Install dependencies: `uv sync`
   - Add new dependencies to `pyproject.toml`

3. **Environment Variables**
   - Copy `.env.example` to `.env`
   - Add required API keys
   - Never commit actual API keys to the repository

### Code Style

We follow strict PEP 8 guidelines with some additional requirements:

1. **Type Hints**
   - Use type hints for all function parameters and return values
   - Use `Optional` for parameters that can be None
   - Use `Any` sparingly and only when necessary

2. **Docstrings**
   - Use Google-style docstrings
   - Include type information, parameters, and return values
   - Add examples for complex functions

Example:

```python
def calculate_efficiency(
    stats: pd.DataFrame,
    weights: Optional[Dict[str, float]] = None
) -> pd.DataFrame:
    """
    Calculate efficiency metrics for players or teams.

    Args:
        stats: DataFrame containing raw statistics
        weights: Optional dictionary of metric weights

    Returns:
        DataFrame with calculated efficiency metrics

    Example:
        >>> weights = {"points": 1.0, "assists": 0.7}
        >>> calculate_efficiency(player_stats, weights)
    """
```

3. **Code Formatting**
   - Use `black` for code formatting
   - Maximum line length: 88 characters
   - Use trailing commas in multi-line collections

### Project Structure

```
nba-ev/
├── docs/
│   ├── API.md
│   └── CONTRIBUTING.md
├── nba_ev/
│   ├── __init__.py
│   ├── collectors/
│   │   ├── __init__.py
│   │   ├── basketball_reference.py
│   │   ├── nba_api.py
│   │   └── odds_api.py
│   ├── analyzers/
│   │   ├── __init__.py
│   │   ├── efficiency.py
│   │   └── simulation.py
│   └── utils/
│       ├── __init__.py
│       └── data_processing.py
├── tests/
│   ├── __init__.py
│   ├── test_collectors.py
│   └── test_analyzers.py
├── .env
├── .gitignore
├── LICENSE
├── README.md
└── pyproject.toml
```

### Testing

1. **Test Coverage**
   - Write tests for all new features
   - Maintain minimum 80% test coverage
   - Use pytest for testing

2. **Test Structure**
   - Place tests in the `tests/` directory
   - Mirror the main package structure
   - Use meaningful test names and descriptions

Example test:

```python
def test_efficiency_calculation():
    """Test that efficiency metrics are calculated correctly."""
    test_data = pd.DataFrame({
        "points": [10, 20],
        "assists": [5, 8]
    })
    result = calculate_efficiency(test_data)
    assert "efficiency" in result.columns
    assert result["efficiency"].dtype == float
```

3. **Running Tests**

   ```bash
   pytest
   pytest --cov=nba_ev  # with coverage
   ```

### Git Workflow

1. **Branches**
   - `main`: stable release branch
   - `develop`: development branch
   - Feature branches: `feature/description`
   - Bug fixes: `fix/description`

2. **Commits**
   - Use clear, descriptive commit messages
   - Follow conventional commits format
   - Reference issues when applicable

Example commits:

```
feat(simulation): add Monte Carlo game simulation
fix(api): handle rate limiting in odds API
docs(readme): update installation instructions
```

3. **Pull Requests**
   - Create PRs against the `develop` branch
   - Include tests for new features
   - Update documentation as needed
   - Add to CHANGELOG.md

### Documentation

1. **Code Documentation**
   - Document all public functions and classes
   - Include examples in docstrings
   - Update API.md for new features

2. **README Updates**
   - Keep installation instructions current
   - Document new features
   - Update requirements

3. **Changelog**
   - Add significant changes to CHANGELOG.md
   - Follow semantic versioning
   - Include migration instructions

## Performance Guidelines

1. **Data Processing**
   - Use vectorized operations with pandas
   - Avoid loops when possible
   - Profile code for bottlenecks

2. **API Usage**
   - Implement rate limiting
   - Use async/await for I/O operations
   - Cache responses when appropriate

3. **Memory Management**
   - Monitor memory usage
   - Clean up large objects
   - Use generators for large datasets

## Release Process

1. **Version Bumping**
   - Update version in pyproject.toml
   - Update CHANGELOG.md
   - Create release notes

2. **Testing**
   - Run full test suite
   - Check documentation
   - Verify examples

3. **Release**
   - Tag release in git
   - Create GitHub release
   - Update documentation

## Questions and Support

- Open an issue for bugs or features
- Use discussions for questions
- Tag issues appropriately

## Code of Conduct

Please note that this project is released with a Contributor Code of Conduct. By participating in this project you agree to abide by its terms.

## License

By contributing, you agree that your contributions will be licensed under the project's MIT License.
