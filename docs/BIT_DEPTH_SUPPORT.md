# Bit Depth Support Documentation

This document describes the bit depth support in the IT8951 e-paper driver, including implementation details and usage examples.

## Overview

The driver supports four pixel formats:

| Format | Bits/Pixel | Colors | Data Size | Use Cases |
|--------|------------|---------|-----------|-----------|
| 1bpp | 1 | 2 (B/W) | 12.5% | Text, QR codes, line art |
| 2bpp | 2 | 4 | 25% | Simple graphics, icons |
| 4bpp | 4 | 16 | 50% | General purpose (default) |
| 8bpp | 8 | 256 | 100% | High-quality photos |

## 1bpp (Binary) Support

### 1bpp Features

- **Pixel Packing**: 8 pixels per byte, MSB-first bit ordering
- **32-bit Alignment**: Special alignment for 1bpp mode as per IT8951 requirements
- **Endian Conversion**: Support for bit order reversal when needed
- **Optimized for A2 Mode**: Perfect match for binary display mode

### 1bpp Usage Examples

```python
from IT8951_ePaper_Py import EPaperDisplay
from IT8951_ePaper_Py.constants import DisplayMode, PixelFormat

# Basic 1bpp display
display = EPaperDisplay(vcom=-2.0)
display.init()

# Display binary image (text, QR code, etc.)
display.display_image(
    binary_image,
    mode=DisplayMode.A2,  # A2 mode is ideal for 1bpp
    pixel_format=PixelFormat.BPP_1
)
```

### Endian Conversion

For devices that require different bit ordering:

```python
from IT8951_ePaper_Py.it8951 import IT8951

# Pack pixels to 1bpp
packed_data = IT8951.pack_pixels(grayscale_pixels, PixelFormat.BPP_1)

# Convert bit order if needed (MSB-first to LSB-first)
converted_data = IT8951.convert_endian_1bpp(packed_data, reverse_bits=True)
```

### Performance Benefits

- **Data Transfer**: Only 12.5% of 8bpp data size
- **A2 Mode Synergy**: Both are binary, no grayscale processing overhead
- **Fastest Updates**: Ideal for real-time displays (clocks, counters)

## 2bpp Support

### 2bpp Features

- **Pixel Packing**: 4 pixels per byte
- **4 Grayscale Levels**: 0x00, 0x55, 0xAA, 0xFF
- **Simple Graphics**: Good for icons and basic UI elements

### 2bpp Usage Example

```python
# Display 4-level grayscale image
display.display_image(
    simple_graphic,
    pixel_format=PixelFormat.BPP_2
)
```

## Implementation Details

### Pixel Packing Algorithm

The `pack_pixels()` method in `it8951.py` handles all formats:

1. **1bpp**: Threshold at 128, pack 8 pixels/byte, MSB first
2. **2bpp**: Shift right 6 bits, pack 4 pixels/byte
3. **4bpp**: Shift right 4 bits, pack 2 pixels/byte
4. **8bpp**: No packing needed

### Alignment Requirements

- **1bpp**: 32-pixel alignment (4-byte boundaries)
- **Other formats**: 4-pixel alignment

The alignment is handled automatically in `display.py`:

```python
def _align_coordinate(self, coord: int, pixel_format: PixelFormat) -> int:
    if pixel_format == PixelFormat.BPP_1:
        return (coord // ProtocolConstants.PIXEL_ALIGNMENT_1BPP) * ProtocolConstants.PIXEL_ALIGNMENT_1BPP
    return (coord // ProtocolConstants.PIXEL_ALIGNMENT_DEFAULT) * ProtocolConstants.PIXEL_ALIGNMENT_DEFAULT
```

## Examples

### Text Display with 1bpp

See `examples/binary_1bpp_demo.py` for a complete demonstration of:

- Text rendering
- QR code patterns
- Line art and diagrams

### Real-time Clock with 1bpp + A2

See `examples/a2_1bpp_optimization.py` for:

- Ultra-fast clock updates
- Status displays
- Performance benchmarking

## Best Practices

1. **Choose the Right Format**:
   - Use 1bpp for binary content (text, QR codes)
   - Use 2bpp for simple graphics with limited shading
   - Use 4bpp as default for balanced quality/speed
   - Use 8bpp only when maximum quality is needed

2. **Combine with Appropriate Display Mode**:
   - 1bpp + A2: Fastest binary updates
   - 2bpp/4bpp + DU: Fast grayscale updates
   - 8bpp + GC16: Highest quality

3. **Consider Alignment**:
   - 1bpp requires 32-pixel alignment
   - Plan your layout accordingly
   - Use alignment warnings during development

## Testing Coverage

The implementation is thoroughly tested in `tests/test_pixel_packing.py`:

- Pixel packing for all formats
- Endian conversion for 1bpp
- Edge cases and empty data handling
- Alignment validation

## Future Enhancements

While the core bit depth support is complete, potential improvements include:

- Dithering algorithms for better quality at lower bit depths
- Optimized grayscale conversion for 2bpp
- Hardware-accelerated packing for Raspberry Pi
