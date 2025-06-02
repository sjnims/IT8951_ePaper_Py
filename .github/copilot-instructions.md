# copilot-instructions.md

This file provides guidance to Copilot when working with this IT8951 e-paper Python driver project.

## Quick Reference

**Current Version**: 0.9.0
**Test Coverage**: 98.35%
**Python Support**: 3.11+
**Default Pixel Format**: 4bpp (PixelFormat.BPP_4)

## Project Overview

A Python driver for the IT8951 e-paper controller, designed for use with Waveshare's 10.3-inch e-paper HAT. The driver communicates via SPI and is optimized for low power consumption with comprehensive power management features:

- **Hardware**: 10.3-inch e-paper HAT from Waveshare with IT8951 controller, and Raspberry Pi (any variant)
- **Goal**: Provide a simple, efficient interface for rendering images to e-paper displays
- **Dev Machine**: macOS M2 MAX (all dependencies must be macOS-compatible)
- **Build System**: Poetry-based with pyproject.toml configuration
- **Python Version**: 3.11+ (uses modern syntax like `X | Y` unions)

## Architecture Overview

### Core Modules

- **display.py**: High-level user API (EPaperDisplay class) with power management - start here for usage
- **it8951.py**: Low-level IT8951 controller communication protocol with power state tracking
- **spi_interface.py**: Hardware abstraction layer (SPIInterface, RaspberryPiSPI, MockSPI)
- **models.py**: Pydantic v2 models for type-safe data structures
- **constants.py**: Hardware constants, commands, display modes, and PowerState enum
- **exceptions.py**: Custom exception hierarchy (all inherit from IT8951Error)

### Utility Modules (added in v0.6.0)

- **alignment.py**: Pixel alignment operations (extracted from display.py)
- **buffer_pool.py**: Thread-safe memory buffer management
- **command_utils.py**: Command validation and utility functions
- **pixel_packing.py**: Numpy-optimized pixel packing (20-50x faster)
- **vcom_calibration.py**: VCOM calibration logic (extracted from display.py)

## Quick Start

```bash
# Install dependencies (macOS development)
poetry install

# Run tests (now ~2 seconds with parallel execution)
poetry run pytest

# Run tests with coverage
poetry run pytest --cov

# Type checking
poetry run pyright

# Linting and formatting
poetry run ruff check .
poetry run ruff format .

# Check cyclomatic complexity
poetry run radon cc src/ -a
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
- **Don't** add type ignores without explanatory comments
- **Don't** create new test files without checking if existing ones fit
- **Don't** forget to update version in BOTH `__init__.py` AND `pyproject.toml`
- **Don't** use list append in loops - use list comprehensions for performance

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
- **Coverage**: Target 100% (currently 98.35%)
- **Hardware Mocking**: Use MockSPI for hardware-independent testing
- **Test Structure**: Mirror source structure with `test_<module>.py`
- **Fixtures**: Use MockerFixture for complex mocking scenarios
- **Shared Fixtures**: Use conftest.py for common test fixtures
- **Test Markers**: Use @pytest.mark.slow, @pytest.mark.serial, etc.
- **Parallel Execution**: Tests run in parallel with pytest-xdist
- **Think** before creating a new test file - is there an existing one that fits?
- **Think deeply** before changing implementation code to match a test's expectation:
  - Did we just change the implementation of a feature that might also require us to change its tests?
  - Just because we have an existing test, doesn't mean it's still the right test for the job.

## Modern Python (3.11+)

- Use `str | None` instead of `Union[str, None]`
- Avoid `Any` - use specific types (e.g., `np.generic` for numpy)
- Use pathlib, f-strings, type annotations everywhere
- Pydantic V2 for data models
- Prefer TypedDict for complex return types
- Use dataclasses where Pydantic is overkill

## Error Reporting

- Custom exception hierarchy in `exceptions.py`

## Hardware Abstraction

- Mock all hardware dependencies for macOS development

## Key Implementation Details

- **Display Modes**: INIT, DU, GC16, GL16, A2, GLR16, GLD16, DU4 (see constants.py)
- **Power States**: ACTIVE, STANDBY, SLEEP (see PowerState enum)
- **Image Rotations**: 0°, 90°, 180°, 270° supported
- **Default VCOM**: Required parameter (no default)
- **Max Display Size**: 2048x2048 pixels (validated in models)
- **Endianness**: Little-endian by default
- **Pixel Format**: 4bpp grayscale default (PixelFormat.BPP_4)
- **Memory**: Images loaded to controller's internal memory before display
- **Auto-sleep**: Configurable timeout for battery optimization
- **Context Manager**: Automatic power management with `with` statement
- **Progressive Loading**: Available for images >16MB
- **Buffer Pool**: Thread-safe memory allocation optimization

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
3. Update version in `pyproject.toml` if using dynamic versioning
4. Update CHANGELOG.md with release notes
5. Update README.md with new version and features
6. Commit version bump to `main`
7. Create annotated tag: `git tag -a v0.x.0 -m "Release notes"`
8. Push tag: `git push origin v0.x.0`
9. Create GitHub release from tag if desired

## Common Tasks

### When Adding New Modules

1. Add module to appropriate section in README.md architecture
2. Update CLAUDE.md architecture overview
3. Create corresponding test file `test_<module>.py`
4. Add docstring with module purpose
5. Consider if it should be re-exported in `__init__.py`

### When Updating Documentation

1. Check if README.md needs updates (version, features, etc.)
2. Update CHANGELOG.md for any changes
3. Update relevant docs/*.md files
4. Keep ROADMAP.md current with completed phases

### Performance Optimization Patterns

1. Use numpy for array operations (20-50x faster)
2. Prefer list comprehensions over append loops
3. Extract magic numbers to constants
4. Reduce cyclomatic complexity by extracting helper methods
5. Use buffer pooling for repeated allocations

## CI/CD Specifics

- Tests run in parallel with pytest-xdist (~2 second runs)
- Codecov ATS enabled for intelligent test selection
- Pre-commit hooks run ruff and pyright
- GitHub Actions runs on Ubuntu only (for now)
- CodeQL security scanning enabled

## Known Issues to Watch For

1. **Type ignores**: Always add explanatory comments
2. **Test coverage**: Some edge cases in SPI interface are hard to test
3. **Thread safety**: Only buffer_pool.py is thread-safe currently
4. **Platform testing**: Only Ubuntu in CI, but dev on macOS
