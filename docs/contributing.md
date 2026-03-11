# Contributing to sniff

Thank you for your interest in contributing to sniff!

## Development Setup

1. Clone the repository:
```bash
git clone https://github.com/randreshg/sniff.git
cd sniff
```

2. Create a virtual environment:
```bash
python3.11 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install in development mode:
```bash
pip install -e ".[dev]"
```

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=sniff --cov-report=html

# Run specific test file
pytest tests/test_detect.py
```

## Code Quality

We use ruff for linting and formatting, and mypy for type checking:

```bash
# Format code
ruff format .

# Lint
ruff check .

# Type check
mypy src/sniff
```

## Pull Request Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Run code quality checks
7. Commit your changes (`git commit -m 'Add amazing feature'`)
8. Push to your fork (`git push origin feature/amazing-feature`)
9. Open a Pull Request

## Code Style

- Follow PEP 8
- Use type hints for all functions
- Write docstrings for public APIs
- Keep functions focused and small
- Prefer dataclasses for data structures

## Questions?

Open an issue or start a discussion on GitHub!
