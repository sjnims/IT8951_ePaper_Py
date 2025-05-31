# CLAUDE.md

This file provides guidance to Claude Code when working with this IT8951 e-paper Python driver project.

## Project Overview

A Python driver for the IT8951 e-paper controller, designed for use with Waveshare's 10.3-inch e-paper HAT. The driver communicates via SPI and is optimized for low power consumption with comprehensive power management features:

- **Hardware**: 10.3-inch e-paper HAT from Waveshare with IT8951 controller, and Raspberry Pi (any variant)
- **Goal**: Provide a simple, efficient interface for rendering images to e-paper displays
- **Dev Machine**: macOS M2 MAX (all dependencies must be macOS-compatible)
- **Build System**: Poetry-based with pyproject.toml configuration
- **Python Version**: 3.11+ (uses modern syntax like `X | Y` unions)

## Architecture Overview

- **display.py**: High-level user API (EPaperDisplay class) with power management - start here for usage
- **it8951.py**: Low-level IT8951 controller communication protocol with power state tracking
- **spi_interface.py**: Hardware abstraction layer (SPIInterface, RaspberryPiSPI, MockSPI)
- **models.py**: Pydantic v2 models for type-safe data structures
- **constants.py**: Hardware constants, commands, display modes, and PowerState enum
- **exceptions.py**: Custom exception hierarchy (all inherit from IT8951Error)

## Quick Start

```bash
# Install dependencies (macOS development)
poetry install

# Run tests
poetry run pytest

# Type checking
poetry run pyright

# Linting and formatting
poetry run ruff check .
poetry run ruff format .

```

## Usage Example

```python
# Context manager for automatic power management
with EPaperDisplay(vcom=-2.0) as display:
    display.set_auto_sleep_timeout(30.0)  # Sleep after 30s inactivity
    width, height = display.init()
    
    # Display operations
    display.display_image(img)
    
    # Check device status
    status = display.get_device_status()
    print(f"Power state: {status['power_state']}")
    
# Display automatically enters sleep mode on exit
```

## Common Pitfalls to Avoid

- **Don't** use `typing.Any` - be specific with types
- **Don't** use `Union[X, Y]` - use `X | Y` syntax (Python 3.11+)
- **Don't** forget to mock hardware for tests on macOS

## Original Source Code

- The original source code is based on the Waveshare IT8951 e-paper driver, which can be found here: [Waveshare IT8951 e-Paper Driver](https://github.com/waveshareteam/IT8951-ePaper/tree/master/Raspberry)

## Type Stubs

When pyright complains about external libraries:

1. Create stubs in `stubs/<library>/`
2. Include `__init__.pyi` and `py.typed`
3. Match external API exactly (even non-PEP8 names)
4. Configure in pyproject.toml: `stubPath = "stubs"`

## Testing Guidelines

- **Framework**: pytest with pytest-mock for all tests
- **Coverage**: Target 100% (configured in pyproject.toml)
- **Hardware Mocking**: Use MockSPI for hardware-independent testing
- **Test Structure**: Mirror source structure with `test_<module>.py`
- **Fixtures**: Use MockerFixture for complex mocking scenarios
- **Think** before creating a new test file - is there an existing one that fits?
- **Think deeply** before changing implementation code to match a test's expectation:
  - Did we just change the implementation of a feature that might also require us to change its tests?
  - Just because we have an existing test, doesn't mean it's still the right test for the job.

## Modern Python (3.11.12)

- Use `str | None` instead of `Union[str, None]`
- Avoid `Any` - use specific types
- Use pathlib, f-strings, async/await
- Pydantic V2 for data models

## Error Reporting

- Custom exception hierarchy in `exceptions.py`

## Hardware Abstraction

- Mock all hardware dependencies for macOS development

## Key Implementation Details

- **Display Modes**: INIT, DU, GC16, GL16, A2 (see constants.py)
- **Power States**: ACTIVE, STANDBY, SLEEP (see PowerState enum)
- **Image Rotations**: 0°, 90°, 180°, 270° supported
- **Default VCOM**: -2.0V (configurable per device)
- **Max Display Size**: 2048x2048 pixels (validated in models)
- **Endianness**: Little-endian by default
- **Pixel Format**: 4bpp grayscale default
- **Memory**: Images loaded to controller's internal memory before display
- **Auto-sleep**: Configurable timeout for battery optimization
- **Context Manager**: Automatic power management with `with` statement

## Code Style Enforcement

- **Formatter**: ruff format (line length: 100)
- **Linter**: ruff with extensive rule sets
- **Import Sorting**: ruff with isort profile
- **Type Checking**: pyright in strict mode
- **Pre-commit**: Hooks configured for automated checks

## Exception Best Practices

- Always raise from IT8951Error hierarchy
- Use specific exceptions (DisplayError, MemoryError, etc.)
- Include descriptive error messages with context
- Never catch generic Exception

## Chat Preferences

- Explain context for changes
- Use friendly tone
- Reference specific files and line numbers when discussing code

## Release Process

- Development happens on `main` branch
- Releases are marked with annotated tags (e.g., `v0.2.0`)
- No separate release branches - tags provide release points
- Version bumps committed directly to `main`
- For patches, create temporary branch from tag if needed

### Release Workflow

1. Complete all features for the release
2. Update version in `src/IT8951_ePaper_Py/__init__.py`
3. Commit version bump to `main`
4. Create annotated tag: `git tag -a v0.x.0 -m "Release notes"`
5. Push tag: `git push origin v0.x.0`
6. Create GitHub release from tag if desired
