# IT8951 e-Paper Python Driver

[![CI/CD](https://github.com/sjnims/IT8951_ePaper_Py/actions/workflows/ci.yml/badge.svg)](https://github.com/sjnims/IT8951_ePaper_Py/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/sjnims/IT8951_ePaper_Py/graph/badge.svg?token=BB2VKPF6YL)](https://codecov.io/gh/sjnims/IT8951_ePaper_Py)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/release/python-3112/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![CodeQL](https://img.shields.io/badge/CodeQL-enabled-green.svg)](https://github.com/sjnims/IT8951_ePaper_Py/security/code-scanning)

A pure Python implementation of the Waveshare IT8951 e-paper controller driver for Raspberry Pi. This driver provides a clean, modern Python interface for controlling e-paper displays using the IT8951 controller chip.

**New in v0.14.0:** Performance and memory optimizations! Pre-allocated arrays in hot paths, zero-copy SPI transfers, comprehensive memory monitoring utilities, and performance profiling tools. Test coverage increased to 99%.

**v0.13.0:** Enhanced debug mode with 6 verbosity levels, component-specific debugging, and diagnostic context in error messages.

**v0.12.0:** Comprehensive integration test suite with multi-feature workflows, error recovery, and memory management tests.

## Features

### What Sets This Driver Apart

- **🐍 Pure Python** - No C dependencies, runs on any platform with mock mode
- **🔋 Power Management** - Standby/sleep modes with auto-sleep timeout for battery-powered devices
- **🎯 Smart Defaults** - 4bpp mode by default (50% less data, same quality as 8bpp)
- **🛡️ Memory Safety** - Progressive loading for large images with automatic memory warnings
- **🧪 Development-Friendly** - 99.18% test coverage, type hints, and mock SPI for testing without hardware
- **⚡ Production-Ready** - Auto-alignment, VCOM calibration, A2 ghosting prevention, and comprehensive error handling
- **📊 Performance Testing** - Built-in benchmarks for pixel packing, display operations, and memory usage
- **🔍 Troubleshooting Tools** - Interactive diagnostics, register dumps, and guided problem resolution

## Requirements

- Python 3.11 or later (supports 3.11 and 3.12)
- Raspberry Pi with SPI enabled (for hardware usage)
- Waveshare 10.3" e-paper HAT with IT8951 controller

### Python Dependencies

- `pydantic` >= 2.9 - Data validation and models
- `pillow` >= 10.4 - Image processing
- `numpy` >= 1.26,<2.0 - Numerical operations (stays on 1.x to avoid breaking changes)
- `spidev` >= 3.6 - SPI communication (Raspberry Pi only)
- `RPi.GPIO` >= 0.7.1 - GPIO control (optional, Raspberry Pi only)

## Installation

### Platform Support

This library supports multiple platforms:

- **Raspberry Pi** (ARM/ARM64) - Full hardware support
- **Linux** (x86_64) - Development with MockSPI
- **macOS** (Intel/Apple Silicon) - Development with MockSPI
- **Windows** - Basic compatibility with MockSPI

See [Platform Support Guide](docs/PLATFORM_SUPPORT.md) for detailed platform-specific instructions.

### Using Poetry (recommended)

```bash
git clone https://github.com/sjnims/IT8951_ePaper_Py.git
cd IT8951_ePaper_Py
poetry install

# For Raspberry Pi users, install with GPIO support:
poetry install -E rpi
```

### Using pip

```bash
git clone https://github.com/sjnims/IT8951_ePaper_Py.git
cd IT8951_ePaper_Py
pip install -e .

# For Raspberry Pi with GPIO:
pip install -e ".[rpi]"
```

## Quick Start

```python
from IT8951_ePaper_Py import EPaperDisplay
from IT8951_ePaper_Py.constants import DisplayMode

# Initialize display with VCOM voltage (check your display's FPC cable sticker)
display = EPaperDisplay(vcom=-2.0)  # Replace with your display's VCOM value

try:
    # Initialize and get display dimensions
    width, height = display.init()
    print(f"Display size: {width}x{height}")

    # Clear display to white
    display.clear(color=0xFF)

    # Display an image
    from PIL import Image
    img = Image.open("example.jpg")
    display.display_image(img, x=0, y=0, mode=DisplayMode.GC16)
finally:
    display.close()
```

### Power Management

Use the context manager for automatic power management:

```python
# Auto-sleep after 30 seconds of inactivity
with EPaperDisplay(vcom=-2.0) as display:
    display.set_auto_sleep_timeout(30.0)
    width, height = display.init()

    # Display your content
    display.display_image(img)

    # Get device status including power state
    status = display.get_device_status()
    print(f"Power state: {status['power_state']}")

# Display automatically enters sleep mode on exit
```

### Pixel Format

The driver supports multiple pixel formats for different use cases:

```python
from IT8951_ePaper_Py.constants import PixelFormat

# Default: 4bpp (recommended) - 16 grayscale levels, 50% data reduction
display.display_image(img)

# 8bpp - Full 256 grayscale levels
display.display_image(img, pixel_format=PixelFormat.BPP_8)

# 2bpp - 4 grayscale levels, good for simple graphics
display.display_image(img, pixel_format=PixelFormat.BPP_2)

# 1bpp - Binary (black/white), fastest updates for text/QR codes
display.display_image(img, pixel_format=PixelFormat.BPP_1)
```

**Performance comparison:**

- **1bpp**: 1/8 data of 8bpp - ideal for text, QR codes, line art
- **2bpp**: 1/4 data of 8bpp - good for simple graphics with 4 gray levels
- **4bpp**: 1/2 data of 8bpp - best balance of quality and speed (default)
- **8bpp**: Full quality - use when maximum grayscale fidelity is needed

### SPI Speed Configuration

The driver automatically detects your Raspberry Pi version and selects the optimal SPI speed:

- **Raspberry Pi 3 and below**: 15.625 MHz (faster)
- **Raspberry Pi 4 and above**: 7.8125 MHz (more stable)

You can also manually override the SPI speed:

```python
# Manual speed override (10 MHz)
display = EPaperDisplay(vcom=-2.0, spi_speed_hz=10000000)

# Use default auto-detection
display = EPaperDisplay(vcom=-2.0)
```

**Note**: These speeds are based on Waveshare's recommendations. Pi 4+ requires slower speeds due to hardware differences.

## Examples

### Basic Display

```python
# See examples/basic_display.py
python examples/basic_display.py
```

### Image Display

```python
# Display an image file
python examples/image_display.py path/to/image.jpg -2.0
```

### Partial Updates

```python
# Fast partial updates for dynamic content
python examples/partial_update.py
```

### VCOM Calibration

```python
# Find optimal VCOM voltage for your display
python examples/vcom_calibration.py
```

### Power Management Demo

```python
# Demonstrate power management features
python examples/power_management_demo.py
```

### Performance Optimizations

```python
# 4bpp optimized display (50% data reduction)
python examples/performance_4bpp.py

# 1bpp binary display for text/QR codes
python examples/binary_1bpp_demo.py

# Progressive loading for large images
python examples/progressive_loading_demo.py
```

### Battery-Powered Applications

```python
# Comprehensive battery-powered device example
python examples/battery_powered_demo.py
```

### Troubleshooting

```python
# Interactive troubleshooting guide with diagnostics
python examples/troubleshooting_demo.py
```

See all examples in the [`examples/`](examples/) directory.

## Architecture

The driver follows a layered architecture:

1. **Hardware Abstraction Layer** ([`spi_interface.py`](src/IT8951_ePaper_Py/spi_interface.py))
   - `SPIInterface` - Abstract base class
   - `RaspberryPiSPI` - Hardware implementation
   - `MockSPI` - Mock implementation for testing
2. **Core Driver** ([`it8951.py`](src/IT8951_ePaper_Py/it8951.py))
   - Low-level IT8951 controller communication
   - Register operations and command execution
3. **High-Level Display** ([`display.py`](src/IT8951_ePaper_Py/display.py))
   - User-friendly display interface
   - Image processing and alignment
   - Automatic format conversion
4. **Data Models** ([`models.py`](src/IT8951_ePaper_Py/models.py))
   - Type-safe configuration with Pydantic
   - Validation and data structures
5. **Utilities and Helpers**
   - [`alignment.py`](src/IT8951_ePaper_Py/alignment.py) - Pixel alignment operations
   - [`buffer_pool.py`](src/IT8951_ePaper_Py/buffer_pool.py) - Memory buffer management
   - [`command_utils.py`](src/IT8951_ePaper_Py/command_utils.py) - Command validation
   - [`pixel_packing.py`](src/IT8951_ePaper_Py/pixel_packing.py) - Numpy-optimized pixel packing
   - [`vcom_calibration.py`](src/IT8951_ePaper_Py/vcom_calibration.py) - VCOM calibration logic
6. **Exception Hierarchy** ([`exceptions.py`](src/IT8951_ePaper_Py/exceptions.py))
   - `IT8951Error` - Base exception
   - `CommunicationError` - SPI communication failures
   - `DeviceError` - Device-reported errors
   - `InitializationError` - Initialization failures
   - `DisplayError` - Display operation errors
   - `IT8951MemoryError` - Memory operation failures
   - `IT8951TimeoutError` - Operation timeouts
   - `InvalidParameterError` - Invalid parameters
   - `VCOMError` - VCOM voltage configuration errors

## Thread Safety

**Important:** The base `EPaperDisplay` class is NOT thread-safe. The IT8951 controller and SPI communication protocol do not support concurrent operations.

### Using ThreadSafeEPaperDisplay (Recommended)

For multi-threaded applications, use the provided `ThreadSafeEPaperDisplay` wrapper:

```python
from IT8951_ePaper_Py import ThreadSafeEPaperDisplay
import threading

# Create thread-safe display instance
display = ThreadSafeEPaperDisplay(vcom=-2.0)

# Can be safely used from multiple threads
def worker(thread_id):
    display.display_image(image, x=thread_id * 100, y=0)

threads = [threading.Thread(target=worker, args=(i,)) for i in range(4)]
for t in threads:
    t.start()
for t in threads:
    t.join()
```

The `ThreadSafeEPaperDisplay` class:

- Provides automatic thread synchronization using a reentrant lock
- Has identical API to `EPaperDisplay` - just change the class name
- Allows nested method calls within the same thread
- Protects all public methods and properties

### Manual Synchronization

If you prefer manual control, implement your own synchronization:

```python
import threading
from IT8951_ePaper_Py import EPaperDisplay

display = EPaperDisplay(vcom=-2.0)
display_lock = threading.Lock()

# In each thread:
with display_lock:
    display.display_image(image)
```

Thread safety issues to be aware of:

- SPI transactions must be atomic (chip select, data transfer)
- Command/data sequences can be corrupted by concurrent access
- Power state changes affect all operations
- The busy wait mechanism assumes single-threaded access

See [Thread Safety Guide](docs/THREAD_SAFETY.md) for detailed documentation and patterns.

## Display Modes

- `INIT` (0) - Full initialization mode
- `DU` (1) - Direct update (fast, monochrome)
- `GC16` (2) - 16-level grayscale (high quality)
- `GL16` (3) - 16-level grayscale with flashing
- `A2` (4) - 2-level fast update
- `GLR16` (5) - Ghost reduction 16-level (reduces ghosting artifacts)
- `GLD16` (6) - Ghost level detection 16 (adaptive ghost compensation)
- `DU4` (7) - Direct update 4-level (fast 4-grayscale mode)

## Development

### Mock Interface for Non-Pi Development

The driver includes a mock SPI interface that allows development and testing on non-Raspberry Pi systems:

```python
# The driver automatically uses MockSPI when not on a Raspberry Pi
from IT8951_ePaper_Py import EPaperDisplay

# Works on macOS, Windows, Linux without hardware
display = EPaperDisplay(vcom=-2.0)
```

### Setting up Development Environment

```bash
# Install all development dependencies
poetry install --with dev

# Run tests
poetry run pytest

# Run type checking
poetry run pyright

# Run linting
poetry run ruff check .

# Format code
poetry run ruff format .

# Check code complexity
poetry run radon cc src/ -a
```

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov

# Run specific test file
poetry run pytest tests/test_display.py

# Run performance benchmarks
poetry run pytest tests/test_performance.py -v

# Run numpy pixel packing benchmarks
poetry run pytest tests/test_numpy_pixel_packing.py -v

# Run with detailed timing information
poetry run pytest --durations=10
```

The test suite includes:

- **Unit tests** for all modules with 98.35% coverage
- **Performance benchmarks** for critical operations
- **Pixel packing tests** for all bit depths (1bpp, 2bpp, 4bpp, 8bpp)
- **Power management tests** for battery optimization
- **Alignment tests** for edge cases and hardware requirements
- **Extended display mode tests** for GLR16, GLD16, and DU4 modes

### Project Structure

```text
IT8951_ePaper_Py/
├── src/
│   └── IT8951_ePaper_Py/
│       ├── __init__.py          # Package initialization
│       ├── constants.py         # Hardware constants
│       ├── exceptions.py        # Custom exceptions
│       ├── models.py            # Pydantic data models
│       ├── spi_interface.py     # SPI abstraction layer
│       ├── it8951.py            # Core driver
│       ├── display.py           # High-level interface
│       ├── alignment.py         # Pixel alignment utilities
│       ├── buffer_pool.py       # Memory buffer management
│       ├── command_utils.py     # Command validation helpers
│       ├── pixel_packing.py     # Numpy-optimized pixel packing
│       ├── utils.py             # General utilities
│       └── vcom_calibration.py  # VCOM calibration logic
├── tests/                       # Test suite
├── examples/                    # Example scripts
├── stubs/                       # Type stubs for external libs
├── docs/                        # Documentation
├── ROADMAP.md                   # Development roadmap
├── CLAUDE.md                    # AI assistant instructions
├── CHANGELOG.md                 # Version history
├── CONTRIBUTING.md              # Contribution guidelines
└── pyproject.toml               # Project configuration
```

## Error Recovery and Retry Mechanisms

The driver includes comprehensive error recovery capabilities:

### Configurable Retry Policies

```python
from IT8951_ePaper_Py import RetryPolicy, BackoffStrategy, create_retry_spi_interface

# Exponential backoff (default)
policy = RetryPolicy(
    max_attempts=5,
    delay=0.1,
    backoff_factor=2.0,
    backoff_strategy=BackoffStrategy.EXPONENTIAL
)

# Linear backoff for gradual retry
linear_policy = RetryPolicy(
    backoff_strategy=BackoffStrategy.LINEAR,
    max_delay=5.0  # Cap maximum delay
)

# Fixed delay with jitter to prevent thundering herd
jitter_policy = RetryPolicy(
    backoff_strategy=BackoffStrategy.JITTER,
    jitter_range=0.1  # ±10% randomness
)

# Create display with retry-enabled SPI
spi = create_retry_spi_interface(retry_policy=policy)
display = EPaperDisplay(vcom=-2.0, spi_interface=spi)
```

### Error Recovery Examples

```python
# See comprehensive error recovery demonstration
python examples/error_recovery_demo.py

# Basic retry mechanism demo
python examples/retry_demo.py
```

See [Error Recovery Guide](docs/ERROR_RECOVERY.md) for detailed recovery procedures and best practices.

## Debug Mode

The driver includes comprehensive debug logging for troubleshooting and development:

### Enabling Debug Mode

```python
from IT8951_ePaper_Py import enable_debug, disable_debug, DebugLevel

# Enable debug logging
enable_debug(DebugLevel.DEBUG)

# Use the display - will show debug output
display = EPaperDisplay(vcom=-2.0)
display.init()

# Disable when done
disable_debug()
```

### Component-Specific Debugging

```python
from IT8951_ePaper_Py import set_component_debug, DebugLevel

# Set different levels for different components
set_component_debug("spi", DebugLevel.TRACE)      # Very verbose SPI logging
set_component_debug("display", DebugLevel.INFO)   # General display info
set_component_debug("power", DebugLevel.DEBUG)    # Detailed power management
```

### Environment Variables

Configure debug mode via environment:

```bash
# Global debug level
export IT8951_DEBUG=INFO

# Component-specific levels
export IT8951_DEBUG_SPI=TRACE
export IT8951_DEBUG_DISPLAY=DEBUG

python your_script.py
```

### Debug Levels

- `OFF` - No debug output (default)
- `ERROR` - Only errors
- `WARNING` - Warnings and errors
- `INFO` - General information
- `DEBUG` - Detailed debug info
- `TRACE` - Very detailed trace info

See `examples/debug_mode_demo.py` for comprehensive examples.

## Documentation

- [Platform Support](docs/PLATFORM_SUPPORT.md) - Multi-platform installation and compatibility
- [Performance Guide](docs/PERFORMANCE_GUIDE.md) - Optimization tips and benchmarks
- [Display Modes](docs/DISPLAY_MODES.md) - Detailed explanation of all display modes
- [Power Management](docs/POWER_MANAGEMENT.md) - Battery optimization and power states
- [Memory Safety](docs/MEMORY_SAFETY.md) - Memory management best practices
- [Bit Depth Support](docs/BIT_DEPTH_SUPPORT.md) - Using different pixel formats
- [Thread Safety](docs/THREAD_SAFETY.md) - Multi-threading considerations and solutions
- [Error Recovery](docs/ERROR_RECOVERY.md) - Retry policies and recovery procedures
- [Hardware Setup](docs/HARDWARE_SETUP.md) - Raspberry Pi GPIO connections and troubleshooting
- [Migration Guide](docs/MIGRATION_GUIDE.md) - Migrating from the C driver to Python
- [Best Practices](docs/BEST_PRACTICES.md) - Production deployment and optimization tips
- [ATS Monitoring](docs/ATS_MONITORING.md) - Automated Test Selection CI/CD optimization
- [Docstring Style Guide](docs/DOCSTRING_EXAMPLES.md) - Examples of Google-style docstrings for contributors

## Roadmap

See our [Development Roadmap](ROADMAP.md) for completed and planned features. **Phase 13.2 diagnostic enhancements are now complete**, featuring debug mode with configurable verbosity levels and enhanced error messages with diagnostic context.

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Code Style

- Follow PEP 8
- Use type hints for all functions
- Add docstrings (Google style)
- Run `ruff check` and `ruff format` before committing
- Ensure all tests pass before submitting PR

### CI/CD

This project uses GitHub Actions for continuous integration:

- **Linting**: ruff (linting + formatting), pyright
- **Testing**: pytest with coverage on multiple platforms
  - Ubuntu (x86_64) - Python 3.11, 3.12, 3.13
  - macOS (Intel/ARM) - Python 3.13
  - ARM64 (via QEMU) - Python 3.11
  - Windows - Basic compatibility check
- **Security**: CodeQL for comprehensive security analysis
- **Complexity**: radon for maintainability metrics
- **Performance**: Benchmark tests for critical paths
- **Coverage**: 98.35% code coverage maintained

PRs must pass all checks before merging.

## Troubleshooting Guide

### Common Issues

#### Display Not Initializing

1. **Check VCOM voltage**

   ```python
   # VCOM must match your display's specification (check FPC cable sticker)
   display = EPaperDisplay(vcom=-2.0)  # Replace with your display's value
   ```

2. **Verify SPI is enabled**

   ```bash
   # Enable SPI on Raspberry Pi
   sudo raspi-config
   # Navigate to Interface Options > SPI > Enable

   # Verify SPI devices exist
   ls /dev/spi*
   # Should show: /dev/spidev0.0  /dev/spidev0.1
   ```

3. **Check connections**
   - Ensure HAT is properly seated on GPIO pins
   - Verify FPC cable is fully inserted and locked

#### Blurry or Unclear Display

Enable enhanced driving mode for long cables or display quality issues:

```python
display = EPaperDisplay(vcom=-2.0, enhance_driving=True)
```

#### Ghosting Issues

1. **With A2 mode (fast updates)**

   ```python
   # Enable auto-clear to prevent ghosting
   display = EPaperDisplay(vcom=-2.0, a2_refresh_limit=10)
   ```

2. **General ghosting**

   ```python
   # Perform full clear
   display.clear()
   ```

#### Permission Errors

```bash
# Add user to spi and gpio groups
sudo usermod -a -G spi,gpio $USER
# Logout and login again for changes to take effect

# Alternative: run with sudo (not recommended for production)
sudo python your_script.py
```

#### Image Alignment Warnings

The IT8951 requires specific pixel alignment:

```python
# For 1bpp mode, use 32-pixel alignment
x = (x // 32) * 32
width = ((width + 31) // 32) * 32

# For other modes, use 4-pixel alignment (handled automatically)
```

#### Memory Errors

For large images or limited memory:

```python
# Use lower bit depth
display.display_image(img, pixel_format=PixelFormat.BPP_4)  # Default

# Use partial updates
display.display_partial(img, x=100, y=100, width=200, height=200)

# Use progressive loading for very large images (v0.4.0+)
display.display_image_progressive(
    large_image,
    chunk_height=256,  # Process in 256-pixel chunks
    pixel_format=PixelFormat.BPP_4
)
```

The progressive loading feature processes images in chunks to reduce memory usage:

- Ideal for images larger than 16MB
- Automatically handles alignment requirements
- Configurable chunk size for memory/performance tradeoff

#### Slow Performance

1. **Use appropriate pixel format**

   ```python
   # 4bpp is 2x faster than 8bpp with minimal quality loss
   display.display_image(img)  # Uses 4bpp by default
   ```

2. **Choose the right display mode**

   ```python
   # Fast updates
   display.display_image(img, mode=DisplayMode.DU)    # ~260ms
   display.display_image(img, mode=DisplayMode.A2)    # ~120ms

   # Quality updates
   display.display_image(img, mode=DisplayMode.GC16)  # ~450ms
   ```

#### Mock Mode Issues

When developing on non-Raspberry Pi systems:

```python
# The driver automatically uses MockSPI
display = EPaperDisplay(vcom=-2.0)  # Works on any platform

# To explicitly use mock mode
from IT8951_ePaper_Py.spi_interface import MockSPI
mock_spi = MockSPI()
display = EPaperDisplay(vcom=-2.0, spi_interface=mock_spi)
```

### Debugging Tips

1. **Enable debug logging**

   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)

   # Now you'll see timing information:
   # DEBUG: init completed in 523.45ms
   # DEBUG: display_image completed in 467.23ms
   ```

2. **Check device info**

   ```python
   display = EPaperDisplay(vcom=-2.0)
   width, height = display.init()
   print(f"Display size: {width}x{height}")
   print(f"VCOM: {display.get_vcom()}V")
   ```

3. **Verify register values**

   ```python
   # Dump important registers
   regs = display.dump_registers()
   for name, value in regs.items():
       print(f"{name}: 0x{value:04X}")
   ```

### Getting Help

1. Check the [examples](examples/) directory for working code
2. Read the [performance guide](docs/PERFORMANCE_GUIDE.md)
3. Search [existing issues](https://github.com/sjnims/IT8951_ePaper_Py/issues)
4. Create a new issue with:
   - Python version (`python --version`)
   - Raspberry Pi model (`cat /proc/cpuinfo | grep Model`)
   - Display model and VCOM voltage
   - Minimal code to reproduce
   - Debug log output

## Acknowledgements

- Based on [Waveshare IT8951 C driver](https://github.com/waveshareteam/IT8951-ePaper)
- Inspired by other e-paper Python libraries
- Thanks to the Raspberry Pi and Python communities

## License

MIT License - see [LICENSE](LICENSE) file for details
