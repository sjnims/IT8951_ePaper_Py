# ADR-001: Use Google Style Docstrings

## Status

Accepted

## Context

The project needs a consistent docstring format for documentation. Python supports multiple docstring styles including:

- reStructuredText (Sphinx default)
- Google style
- NumPy style
- Epytext

## Decision

We will use Google style docstrings throughout the codebase.

## Consequences

### Positive

- More readable than reStructuredText for humans
- Well-supported by modern documentation tools
- Clear sections for Args, Returns, Raises, etc.
- Good IDE support for auto-completion
- Consistent with many modern Python projects

### Negative

- Requires configuration for Sphinx documentation generation
- Team members may need to learn the format

### Neutral

- Different from NumPy style used by scientific Python community

## Example

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
    if width < 0 or height < 0:
        raise ValueError("Dimensions must be non-negative")
    return width * height
```
