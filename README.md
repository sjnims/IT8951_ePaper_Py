# IT8951 e-Paper Python Driver

[![CI/CD](https://github.com/sjnims/IT8951_ePaper_Py/actions/workflows/ci.yml/badge.svg)](https://github.com/sjnims/IT8951_ePaper_Py/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/sjnims/IT8951_ePaper_Py/graph/badge.svg?token=BB2VKPF6YL)](https://codecov.io/gh/sjnims/IT8951_ePaper_Py)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/release/python-3112/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![CodeQL](https://img.shields.io/badge/CodeQL-enabled-green.svg)](https://github.com/sjnims/IT8951_ePaper_Py/security/code-scanning)

A pure Python implementation of the Waveshare IT8951 e-paper controller driver for Raspberry Pi. This driver provides a clean, modern Python interface for controlling e-paper displays using the IT8951 controller chip.

## Features

- ✨ Pure Python implementation (no C dependencies)
- 🚀 Hardware abstraction layer for easy testing and development
- 📦 Type-safe with full type hints and Pydantic models
- 🧪 Comprehensive test coverage with pytest
- 🔧 Mock SPI interface for development on non-Pi systems
- 🖼️ Support for multiple display modes (INIT, DU, GC16, GL16, A2)
- 🔄 Image rotation support (0°, 90°, 180°, 270°)
- ⚡ Partial display updates for fast refresh
- 🎨 Automatic image conversion and alignment
- 🔒 Security scanning with GitHub CodeQL
- 📊 Code quality metrics with radon
- 🚦 Comprehensive CI/CD pipeline

## Requirements

- Python 3.11.12 (strictly)
- Raspberry Pi with SPI enabled (for hardware usage)
- Waveshare 10.3" e-paper HAT with IT8951 controller

### Python Dependencies

- `pydantic` >= 2.5 - Data validation and models
- `pillow` >= 11.2 - Image processing
- `numpy` >= 2.2 - Numerical operations
- `spidev` >= 3.6 - SPI communication (Raspberry Pi only)
- `RPi.GPIO` >= 0.7.1 - GPIO control (optional, Raspberry Pi only)

## Installation

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
```

## Quick Start

```python
from IT8951_ePaper_Py import EPaperDisplay
from IT8951_ePaper_Py.constants import DisplayMode

# Initialize display with VCOM voltage
display = EPaperDisplay(vcom=-2.0)

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

### Pixel Format

The driver defaults to 4bpp (4 bits per pixel) format as recommended by Waveshare for optimal performance. This provides 16 grayscale levels while reducing data transfer by 50% compared to 8bpp:

```python
# Uses default 4bpp format (recommended)
display.display_image(img)

# Explicitly use 8bpp for full 256 grayscale levels
from IT8951_ePaper_Py.constants import PixelFormat
display.display_image(img, pixel_format=PixelFormat.BPP_8)

# Use 2bpp for even faster updates (4 grayscale levels)
display.display_image(img, pixel_format=PixelFormat.BPP_2)
```

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
5. **Exception Hierarchy** ([`exceptions.py`](src/IT8951_ePaper_Py/exceptions.py))
   - `IT8951Error` - Base exception
   - `CommunicationError` - SPI communication failures
   - `DeviceError` - Device-reported errors
   - `InitializationError` - Initialization failures
   - `DisplayError` - Display operation errors
   - `IT8951MemoryError` - Memory operation failures
   - `IT8951TimeoutError` - Operation timeouts
   - `InvalidParameterError` - Invalid parameters

## Display Modes

- `INIT` (0) - Full initialization mode
- `DU` (1) - Direct update (fast, monochrome)
- `GC16` (2) - 16-level grayscale (high quality)
- `GL16` (3) - 16-level grayscale with flashing
- `A2` (4) - 2-level fast update

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

```

### Project Structure

```text
IT8951_ePaper_Py/
├── src/
│   └── IT8951_ePaper_Py/
│       ├── __init__.py          # Package initialization
│       ├── constants.py         # Hardware constants
│       ├── exceptions.py        # Custom exceptions
│       ├── models.py           # Pydantic data models
│       ├── spi_interface.py    # SPI abstraction layer
│       ├── it8951.py          # Core driver
│       └── display.py         # High-level interface
├── tests/                     # Test suite
├── examples/                  # Example scripts
├── stubs/                     # Type stubs for external libs
├── docs/                      # Documentation
├── ROADMAP.md                # Development roadmap
├── CLAUDE.md                 # AI assistant instructions
└── pyproject.toml            # Project configuration
```

## Roadmap

See our [Development Roadmap](ROADMAP.md) for planned features and improvements, including:

- 4bpp support for better performance
- Lower bit depth support (1bpp, 2bpp)
- Power management features
- Enhanced display modes
- And more!

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
- **Testing**: pytest with coverage on Ubuntu and macOS
- **Security**: CodeQL for comprehensive security analysis
- **Complexity**: radon for maintainability metrics
- **Python Version**: Strictly Python 3.11.12

PRs must pass all checks before merging.

## Troubleshooting

### SPI Not Working

```bash
# Enable SPI on Raspberry Pi
sudo raspi-config
# Navigate to Interface Options > SPI > Enable
```

### Permission Errors

```bash
# Add user to spi and gpio groups
sudo usermod -a -G spi,gpio $USER
# Logout and login again
```

## Acknowledgements

- Based on [Waveshare IT8951 C driver](https://github.com/waveshareteam/IT8951-ePaper)
- Inspired by other e-paper Python libraries
- Thanks to the Raspberry Pi and Python communities

## License

MIT License - see [LICENSE](LICENSE) file for details
