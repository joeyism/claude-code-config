# Contributing to Claude Config Manager

Thank you for considering contributing to Claude Config Manager! This document provides guidelines and instructions for contributing.

## Development Setup

1. **Fork and clone the repository**

```bash
git clone https://github.com/joeyism/claude-code-config.git
cd claude-code-config
```

2. **Create a virtual environment**

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**

```bash
pip install -e ".[dev]"
```

## Running Tests

We use pytest for testing:

```bash
pytest tests/
```

Run with coverage:

```bash
pytest --cov=claude_config_manager tests/
```

## Code Style

We use black for code formatting and ruff for linting:

```bash
# Format code
black claude_config_manager/ tests/

# Lint code
ruff check claude_config_manager/ tests/
```

## Making Changes

1. **Create a new branch**

```bash
git checkout -b feature/your-feature-name
```

2. **Make your changes**
   - Write clear, concise commit messages
   - Add tests for new features
   - Update documentation as needed

3. **Run tests and formatting**

```bash
black claude_config_manager/ tests/
ruff check claude_config_manager/ tests/
pytest tests/
```

4. **Commit and push**

```bash
git add .
git commit -m "Add your descriptive commit message"
git push origin feature/your-feature-name
```

5. **Create a Pull Request**
   - Go to GitHub and create a PR from your branch
   - Describe your changes clearly
   - Reference any related issues

## Reporting Bugs

When reporting bugs, please include:

- Your operating system and version
- Python version
- Steps to reproduce the issue
- Expected behavior
- Actual behavior
- Any error messages or logs

## Feature Requests

We welcome feature requests! Please:

- Check if the feature has already been requested
- Clearly describe the feature and its use case
- Explain why it would be useful to other users

## Code Review Process

All submissions require review. We review PRs for:

- Code quality and style
- Test coverage
- Documentation
- Backwards compatibility
- Performance implications

## Release Process

Releases are managed by maintainers:

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Create a git tag
4. Build and publish to PyPI

## Questions?

Feel free to open an issue for any questions or concerns!
