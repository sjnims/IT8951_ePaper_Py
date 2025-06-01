<!-- markdownlint-disable MD024 -->
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.9.0] - 2025-02-01

### Added

- Automated Test Selection (ATS) with Codecov for intelligent test filtering
- GitHub Actions workflow configuration for Codecov ATS (ci-ats.yml)
- Test markers for better organization (@pytest.mark.slow, serial, performance, etc.)
- Parallel test execution with pytest-xdist (~2 second test runs)
- Shared test fixtures for reduced setup overhead (conftest.py)
- Helper methods extracted from complex functions for maintainability
- Code quality improvements through cyclomatic complexity reduction

### Changed

- Test isolation fixed for reliable parallel execution
- Hardware timing delays mocked more aggressively in tests
- Test data sizes optimized for faster execution
- Restored pytest settings with coverage after fixing test isolation
- Coverage configuration enhanced for parallel test support
- Refactored high complexity methods:
  - EPaperDisplay._validate_mode_pixel_format split into helper methods
  - display_image_progressive broken down into focused methods
  - IT8951.pack_pixels simplified with helper methods
  - validate_alignment refactored for better maintainability

### Fixed

- Test isolation issues causing hangs in parallel execution
- Flaky timing assertion in test_partial_update_mode_performance
- Coverage collection issues with pytest-xdist workers

### Developer Experience

- Tests run in ~2 seconds with full parallelization
- 98.35% test coverage maintained
- 0 pyright errors (100% type safety)
- All ruff linting and formatting checks pass
- Cyclomatic complexity reduced across codebase

## [0.7.0] - 2025-02-01

### Added

- Extended display mode support (GLR16, GLD16, DU4) for specialized use cases
- Hardware compatibility warnings for extended modes
- Comprehensive mode characteristics metadata for all display modes
- Mode comparison and benchmarking example (extended_modes_demo.py)
- Full test coverage for extended display modes
- Pixel format compatibility validation with warnings
- Mode selection decision tree in documentation

### Changed

- Enhanced display mode documentation with extended mode details
- Updated ROADMAP.md to mark Phase 7 as complete

### Fixed

- Test assertion for pixel format warning messages

## [0.6.0] - 2025-01-31

### Added

- Buffer pool implementation for memory allocation optimization
- Numpy-optimized pixel packing for significant performance gains (20-50x faster)
- Thread safety documentation (docs/THREAD_SAFETY.md)
- Command utilities module for shared validation logic
- Alignment utilities module for pixel alignment operations
- VCOM calibration utilities extracted to separate module
- Pixel packing benchmarks example
- Comprehensive test suite for new modules
- CONTRIBUTING.md with contribution guidelines
- CHANGELOG.md for version history
- Architecture Decision Records (ADRs) in docs/adr/
- Enhanced docstrings throughout codebase

### Changed

- Improved type annotations throughout codebase (replaced Any with np.generic)
- Refactored duplicated alignment logic into dedicated module (~5% reduction in duplication)
- Extracted VCOM calibration logic from display module
- Updated pre-commit hook versions to match poetry.lock
- Enhanced memory efficiency with buffer pooling in clear() method
- All docstrings now follow Google style format consistently

### Fixed

- Configuration inconsistencies between pre-commit and pyproject.toml
- Remaining magic numbers extracted to constants

## [0.5.0] - 2025-01-29

### Added

- Comprehensive power management features (Phase 5 completion)
- Power state tracking (ACTIVE, STANDBY, SLEEP)
- Auto-sleep timeout with configurable duration
- Context manager support for automatic power management
- `get_device_status()` method for comprehensive device information
- Power management demo example
- POWER_MANAGEMENT.md documentation

### Changed

- Context manager now supports auto-sleep on exit
- Enhanced device status reporting

## [0.4.0] - 2025-01-27

### Added

- Complete 1bpp (binary) display support with optimizations
- 2bpp (4-level grayscale) display support
- Enhanced driving capability for long cables/blurry displays
- Progressive image loading for memory-constrained operations
- Bit depth comparison examples
- Binary and grayscale demo examples
- BIT_DEPTH_SUPPORT.md documentation
- Comprehensive test coverage for all bit depths

### Changed

- Improved alignment handling for different pixel formats
- Enhanced memory usage validation

## [0.3.1] - 2025-01-25

### Added

- Python 3.12 support
- Performance timing decorators for critical operations
- `wake()` method to complement standby/sleep
- Comprehensive performance guide (PERFORMANCE_GUIDE.md)
- Extended display modes documentation (DISPLAY_MODES.md)
- SECURITY.md with vulnerability reporting policy
- Pre-commit configuration for code quality

### Changed

- Extracted magic numbers (LUT_BUSY_BIT constant)
- Refactored repeated command patterns
- Completed 1bpp pixel packing implementation
- Updated documentation from 8bpp to 4bpp default references

### Fixed

- Version synchronization between pyproject.toml and __init__.py

## [0.3.0] - 2025-01-24

### Added

- Memory-safe image operations with automatic validation
- SPI speed optimization with Pi version detection
- VCOM value validation and mismatch warnings
- Pixel alignment utilities
- Enhanced error messages with context
- A2 mode refresh tracking and auto-clear feature
- Memory usage warnings for large images
- Comprehensive troubleshooting guide in README

### Changed

- Improved error handling with specific exception types
- Enhanced VCOM handling with validation
- Better memory management for large images

## [0.2.0] - 2025-01-23

### Added

- Basic power management (standby/sleep methods)
- VCOM calibration helper with interactive mode
- `dump_registers()` method for debugging
- Register write capabilities
- Enhanced examples with error handling
- Proper GPIO cleanup in examples

### Changed

- Improved initialization sequence
- Better error messages
- Enhanced documentation

## [0.1.0] - 2025-01-22

### Added

- Initial release of IT8951 e-Paper Python driver
- Core display functionality (init, clear, display_image)
- Support for all standard display modes (INIT, DU, GC16, GL16, A2)
- 8bpp grayscale support
- Rotation support (0°, 90°, 180°, 270°)
- Hardware abstraction with MockSPI for testing
- Comprehensive test suite with >95% coverage
- Basic examples (display image, partial update)
- Type hints throughout codebase
- Modern Python 3.11+ support

[Unreleased]: https://github.com/sjnims/IT8951_ePaper_Py/compare/v0.9.0...HEAD
[0.9.0]: https://github.com/sjnims/IT8951_ePaper_Py/compare/v0.7.0...v0.9.0
[0.7.0]: https://github.com/sjnims/IT8951_ePaper_Py/compare/v0.6.0...v0.7.0
[0.6.0]: https://github.com/sjnims/IT8951_ePaper_Py/compare/v0.5.0...v0.6.0
[0.5.0]: https://github.com/sjnims/IT8951_ePaper_Py/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/sjnims/IT8951_ePaper_Py/compare/v0.3.1...v0.4.0
[0.3.1]: https://github.com/sjnims/IT8951_ePaper_Py/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/sjnims/IT8951_ePaper_Py/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/sjnims/IT8951_ePaper_Py/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/sjnims/IT8951_ePaper_Py/releases/tag/v0.1.0
