# Contributing to IT8951 e-Paper Python Driver

Thank you for your interest in contributing to the IT8951 e-Paper Python driver! This document provides guidelines and instructions for contributing to this project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Coding Standards](#coding-standards)
- [Documentation](#documentation)
- [Reporting Issues](#reporting-issues)

## Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct:

- **Be respectful and inclusive**: Treat everyone with respect, regardless of their background or experience level
- **Be patient and constructive**: Provide helpful feedback and be open to receiving it
- **Focus on the project**: Keep discussions relevant to improving the codebase
- **No harassment**: Zero tolerance for harassment, discrimination, or inappropriate behavior

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:

   ```bash
   git clone https://github.com/YOUR_USERNAME/IT8951_ePaper_Py.git
   cd IT8951_ePaper_Py
   ```

3. **Add the upstream remote**:

   ```bash
   git remote add upstream https://github.com/sjnims/IT8951_ePaper_Py.git
   ```

## Development Setup

This project uses Poetry for dependency management and requires Python 3.11.12 or later.

### Prerequisites

- Python 3.11.12+ (supports 3.11 and 3.12)
- Poetry (install via `pipx install poetry` or see [Poetry installation](https://python-poetry.org/docs/#installation))
- Git

### Installation

1. **Install dependencies**:

   ```bash
   poetry install
   ```

2. **Activate the virtual environment**:

   ```bash
   poetry shell
   ```

3. **Install pre-commit hooks**:

   ```bash
   poetry run pre-commit install
   ```

### Development on macOS

For macOS development (no hardware access), the MockSPI interface will be used automatically:

```bash
# Run tests
poetry run pytest

# Type checking
poetry run pyright

# Linting and formatting
poetry run ruff check .
poetry run ruff format .
```

### Development on Raspberry Pi

For testing with actual hardware:

1. Connect your e-paper display HAT to the Raspberry Pi
2. Enable SPI interface: `sudo raspi-config` → Interface Options → SPI
3. Run tests with hardware: `poetry run pytest --hardware`

## Making Changes

### Branch Naming

Use descriptive branch names:

- `feature/add-color-support`
- `fix/spi-timeout-issue`
- `docs/update-api-reference`
- `refactor/simplify-alignment-logic`

### Commit Messages

Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```text
<type>(<scope>): <subject>

<body>

<footer>
```

Types:

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Test additions or modifications
- `chore`: Build process or auxiliary tool changes

Examples:

```bash
feat(display): add support for 4bpp pixel format
fix(spi): handle timeout errors gracefully
docs(readme): update installation instructions
```

### Development Workflow

1. **Keep your fork updated**:

   ```bash
   git fetch upstream
   git checkout main
   git merge upstream/main
   ```

2. **Create a feature branch**:

   ```bash
   git checkout -b feature/your-feature
   ```

3. **Make your changes**:
   - Write clean, readable code
   - Add tests for new functionality
   - Update documentation as needed

4. **Run checks before committing**:

   ```bash
   # Format code
   poetry run ruff format .

   # Lint code
   poetry run ruff check . --fix

   # Type checking
   poetry run pyright

   # Run tests
   poetry run pytest
   ```

## Testing

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov

# Run specific test file
poetry run pytest tests/test_display.py

# Run with verbose output
poetry run pytest -v
```

### Writing Tests

- Place tests in the `tests/` directory
- Name test files as `test_<module>.py`
- Use pytest fixtures for common setup
- Mock hardware dependencies (see existing tests for examples)
- Aim for high test coverage (current target: 95%+)

Example test structure:

```python
import pytest
from unittest.mock import MagicMock, patch

from IT8951_ePaper_Py.display import EPaperDisplay

class TestEPaperDisplay:
    @pytest.fixture
    def mock_spi(self, mocker):
        """Create a mock SPI interface."""
        return mocker.MagicMock()

    def test_initialization(self, mock_spi):
        """Test display initialization."""
        display = EPaperDisplay(vcom=-2.0, spi_interface=mock_spi)
        # Add assertions
```

## Submitting Changes

### Pull Request Process

1. **Ensure all tests pass** and code meets quality standards
2. **Update documentation** if you've changed APIs
3. **Add an entry to CHANGELOG.md** (if it exists)
4. **Push to your fork** and create a pull request
5. **Fill out the PR template** completely

### PR Guidelines

- Keep PRs focused on a single feature or fix
- Include tests for new functionality
- Update relevant documentation
- Ensure CI checks pass
- Respond to review feedback promptly

### What to Expect

- PRs are typically reviewed within 3-5 days
- You may be asked to make changes
- Once approved, your PR will be merged
- Your contribution will be included in the next release

## Coding Standards

### Python Style

This project follows:

- PEP 8 (enforced by ruff)
- Modern Python practices (3.11+ features)
- Type hints for all public APIs

### Key Conventions

1. **Use type hints**:

   ```python
   def display_image(self, image: Image.Image, x: int = 0, y: int = 0) -> None:
   ```

2. **Use f-strings** for formatting:

   ```python
   raise ValueError(f"Invalid mode: {mode}")
   ```

3. **Prefer pathlib** over os.path:

   ```python
   from pathlib import Path
   config_file = Path.home() / ".config" / "epaper.conf"
   ```

4. **Use | for union types** (not Union):

   ```python
   def process(data: bytes | str) -> None:
   ```

5. **Document with Google-style docstrings**:

   ```python
   def calculate_area(width: int, height: int) -> int:
       """Calculate the area of a rectangle.

       Args:
           width: The width in pixels.
           height: The height in pixels.

       Returns:
           The area in square pixels.

       Raises:
           ValueError: If width or height is negative.
       """
   ```

### Architecture Guidelines

- Keep the hardware abstraction layer (SPIInterface) separate
- Use Pydantic models for data validation
- Raise specific exceptions (inherit from IT8951Error)
- Follow SOLID principles
- Prefer composition over inheritance

## Documentation

### Docstring Requirements

All public modules, classes, and functions must have docstrings:

```python
"""Module description.

Extended description if needed.
"""

class MyClass:
    """Brief class description.

    Longer description explaining the purpose and usage.

    Attributes:
        attr1: Description of attribute.
        attr2: Description of attribute.
    """

    def method(self, param: int) -> str:
        """Brief method description.

        Args:
            param: Description of parameter.

        Returns:
            Description of return value.

        Raises:
            ValueError: When param is invalid.
        """
```

### Documentation Updates

When adding new features:

1. Update relevant docstrings
2. Add examples to the `examples/` directory
3. Update README.md if needed
4. Create or update documentation in `docs/`

## Reporting Issues

### Before Creating an Issue

1. **Search existing issues** to avoid duplicates
2. **Check the documentation** and examples
3. **Verify your setup** meets the requirements

### Creating a Good Issue

Include:

- **Clear title** describing the problem
- **Environment details**: OS, Python version, hardware
- **Steps to reproduce** the issue
- **Expected vs actual behavior**
- **Error messages** or logs
- **Minimal code example** if applicable

Example:

```markdown
## Environment
- OS: Raspberry Pi OS (64-bit)
- Python: 3.11.12
- IT8951_ePaper_Py version: 0.5.0
- Hardware: Waveshare 10.3" e-Paper HAT

## Description
When displaying images larger than 1024x768, the display shows corrupted data.

## Steps to Reproduce
1. Load a 2048x1536 image
2. Call display_image() with default parameters
3. Observe corrupted output

## Expected Behavior
Image should display correctly.

## Actual Behavior
Bottom half of display shows random pixels.

## Code Example
```python
display = EPaperDisplay(vcom=-2.0)
display.init()
img = Image.open("large_image.png")
display.display_image(img)  # Corrupted output
```

## Questions?

Feel free to:

- Open a discussion on GitHub
- Ask questions in issues (label as "question")
- Reach out to maintainers

Thank you for contributing to make this project better!
