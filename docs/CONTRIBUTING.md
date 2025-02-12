# Contributing to NBA Data Analytics Platform

Thank you for your interest in contributing to the NBA Data Analytics Platform! This document provides guidelines and instructions for contributing.

## Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct:

- Be respectful and inclusive
- Focus on constructive feedback
- Maintain professional discourse
- Follow project standards and guidelines

## Getting Started

1. **Fork the Repository**

   ```bash
   git clone https://github.com/yourusername/nba-ev.git
   cd nba-ev
   ```

2. **Set Up Development Environment**

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Create a Feature Branch**

   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Workflow

### 1. Code Style

We follow strict Python coding standards:

- **PEP 8** style guide
- **Type hints** for all functions
- **Docstrings** for all modules, classes, and functions
- **Black** for code formatting
- **isort** for import sorting

```bash
# Format code
black src/ tests/
isort src/ tests/

# Type checking
mypy src/

# Linting
pylint src/
```

### 2. Testing

All new features must include tests:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src tests/

# Run specific test file
pytest tests/test_your_feature.py
```

### 3. Documentation

Update documentation for any changes:

1. **Code Documentation**
   - Clear docstrings
   - Type hints
   - Inline comments for complex logic

2. **Project Documentation**
   - Update relevant .md files in docs/
   - Add new guides if needed
   - Update README.md if necessary

### 4. Commit Guidelines

Follow conventional commits:

```
type(scope): description

[optional body]

[optional footer]
```

Types:

- feat: New feature
- fix: Bug fix
- docs: Documentation changes
- style: Code style changes
- refactor: Code refactoring
- test: Adding tests
- chore: Maintenance

Example:

```
feat(collectors): add rate limiting to NBA API requests

- Added rate limiting decorator
- Updated configuration settings
- Added tests for rate limiting
```

## Pull Request Process

1. **Update Documentation**
   - Add/update docstrings
   - Update relevant documentation files
   - Add comments for complex logic

2. **Run Tests**

   ```bash
   # Ensure all tests pass
   pytest
   
   # Check coverage
   pytest --cov=src tests/
   ```

3. **Code Quality**

   ```bash
   # Format code
   black src/ tests/
   isort src/ tests/
   
   # Run type checking
   mypy src/
   
   # Run linting
   pylint src/
   ```

4. **Create Pull Request**
   - Clear title following commit conventions
   - Detailed description of changes
   - Link to related issues
   - List of testing steps

5. **Review Process**
   - Address reviewer comments
   - Update tests if needed
   - Maintain clean commit history

## Project Structure

```
nba-ev/
├── data/                  # Data storage
├── docs/                 # Documentation
├── monitoring/          # Monitoring config
├── notebooks/          # Jupyter notebooks
├── scripts/            # Utility scripts
├── src/                # Source code
├── tests/             # Test suite
└── visualizations/    # Output graphics
```

## Development Guidelines

### 1. Code Organization

- Keep modules focused and single-purpose
- Use clear, descriptive names
- Follow project structure
- Maintain separation of concerns

### 2. Error Handling

- Use appropriate exception types
- Add error logging
- Provide helpful error messages
- Handle edge cases

### 3. Performance

- Use vectorized operations
- Implement caching where appropriate
- Monitor memory usage
- Profile code when needed

### 4. Security

- Never commit sensitive data
- Use environment variables
- Validate inputs
- Follow security best practices

## Release Process

1. **Version Bump**
   - Update version in pyproject.toml
   - Update CHANGELOG.md
   - Create release notes

2. **Testing**
   - Run full test suite
   - Verify documentation
   - Check dependencies

3. **Release**
   - Create release branch
   - Tag release
   - Update main branch

## Getting Help

- Check existing documentation
- Search closed issues
- Join discussions
- Ask questions in issues

## Recognition

Contributors will be:

- Listed in CONTRIBUTORS.md
- Mentioned in release notes
- Credited in documentation

Thank you for contributing to the NBA Data Analytics Platform!
