# Memory Safety Guide

This guide explains the memory safety features in IT8951 e-Paper Python driver and how to use them effectively.

## Overview

The IT8951 controller has 64MB of SDRAM, but not all of it is available for image data. The driver implements several memory safety features to prevent out-of-memory errors and improve reliability.

## Memory Limits

- **Total Memory**: 64MB (IT8951 SDRAM)
- **Safe Image Memory**: 32MB (leaves room for waveforms and system use)
- **Warning Threshold**: 16MB (triggers warnings for large operations)

## Memory Usage by Pixel Format

Different pixel formats use different amounts of memory:

| Format | Bits/Pixel | Memory Usage | Example (1024x768) |
|--------|------------|--------------|-------------------|
| 8bpp   | 8          | 1 byte/pixel | 786 KB           |
| 4bpp   | 4          | 0.5 byte/pixel | 393 KB         |
| 2bpp   | 2          | 0.25 byte/pixel | 197 KB        |
| 1bpp   | 1          | 0.125 byte/pixel | 98 KB         |

## Safety Features

### 1. VCOM Required Parameter (v0.4.0+)

VCOM is now a required parameter to prevent hardware damage from incorrect voltage:

```python
# Old (v0.3.x and below)
display = EPaperDisplay()  # Used default -2.0V

# New (v0.4.0+)
display = EPaperDisplay(vcom=-2.0)  # Must specify VCOM
```

**Important**: Check your display's FPC cable sticker for the correct VCOM value!

### 2. Memory Usage Estimation

The driver estimates memory usage before operations:

```python
# Automatic memory check in display_image()
display.display_image(large_image)  # Raises IT8951MemoryError if too large
```

Memory is checked for:

- Image dimensions exceeding 2048x2048
- Operations exceeding safe memory limit (32MB)
- Operations exceeding warning threshold (16MB)

### 3. Memory Usage Warnings

When an operation uses significant memory, you'll see warnings:

```text
UserWarning: Large image memory usage: 16,777,216 bytes (16.0 MB).
Consider using a more efficient pixel format (4bpp, 2bpp, or 1bpp)
to improve performance and reduce memory usage.
```

### 4. Progressive Image Loading

For very large images, use progressive loading to process in chunks:

```python
# Regular method (loads entire image)
display.display_image(large_image)  # May fail with IT8951MemoryError

# Progressive method (loads in chunks)
display.display_image_progressive(
    large_image,
    chunk_height=256,  # Process 256 pixels at a time
    pixel_format=PixelFormat.BPP_4
)
```

Benefits:

- Reduces peak memory usage
- Allows display of images larger than available memory
- Automatically handles alignment requirements

## Memory Optimization Strategies

### 1. Choose Appropriate Pixel Format

```python
# For photos with gradients
display.display_image(photo, pixel_format=PixelFormat.BPP_4)  # 50% memory

# For simple graphics
display.display_image(diagram, pixel_format=PixelFormat.BPP_2)  # 25% memory

# For text and line art
display.display_image(text, pixel_format=PixelFormat.BPP_1)  # 12.5% memory
```

### 2. Use Partial Updates

For dynamic content, update only changed regions:

```python
# Update just a small area
display.display_partial(
    small_image,
    x=100, y=100,
    mode=DisplayMode.DU  # Fast mode for partial updates
)
```

### 3. Progressive Loading Parameters

Adjust chunk size based on your needs:

```python
# Smaller chunks = less memory, more operations
display.display_image_progressive(img, chunk_height=128)

# Larger chunks = more memory, fewer operations
display.display_image_progressive(img, chunk_height=512)
```

### 4. Clear Display Periodically

Free up memory by clearing the display:

```python
# Full clear resets memory
display.clear()

# A2 mode auto-clear prevents ghosting and memory issues
display = EPaperDisplay(vcom=-2.0, a2_refresh_limit=10)
```

## Error Handling

### IT8951MemoryError

Raised when memory operations fail:

```python
try:
    display.display_image(huge_image)
except IT8951MemoryError as e:
    print(f"Memory error: {e}")
    # Try with lower bit depth or progressive loading
    display.display_image_progressive(huge_image, pixel_format=PixelFormat.BPP_2)
```

### Common Causes

1. **Image too large**: Dimensions exceed 2048x2048
2. **Insufficient memory**: Image requires more than 32MB
3. **Buffer allocation failed**: System out of memory

## Best Practices

1. **Always specify VCOM**: Check your display's sticker
2. **Use 4bpp by default**: Best balance of quality and memory
3. **Monitor warnings**: Address memory warnings early
4. **Use progressive loading**: For images over 16MB
5. **Test memory limits**: Know your application's requirements

## Example: Memory-Safe Image Display

```python
from IT8951_ePaper_Py import EPaperDisplay
from IT8951_ePaper_Py.constants import PixelFormat, DisplayMode
from IT8951_ePaper_Py.exceptions import IT8951MemoryError
from PIL import Image

# Initialize with correct VCOM
display = EPaperDisplay(vcom=-2.0)
width, height = display.init()

# Load image
img = Image.open("large_photo.jpg").convert("L")

# Calculate memory usage
pixels = img.width * img.height
memory_8bpp = pixels
memory_4bpp = (pixels + 1) // 2

print(f"Image size: {img.width}x{img.height}")
print(f"Memory at 8bpp: {memory_8bpp:,} bytes ({memory_8bpp/1024/1024:.1f} MB)")
print(f"Memory at 4bpp: {memory_4bpp:,} bytes ({memory_4bpp/1024/1024:.1f} MB)")

try:
    # Try normal display
    if memory_4bpp < 16 * 1024 * 1024:  # Under 16MB
        display.display_image(img, pixel_format=PixelFormat.BPP_4)
    else:
        # Use progressive loading for large images
        print("Using progressive loading...")
        display.display_image_progressive(
            img,
            pixel_format=PixelFormat.BPP_4,
            chunk_height=256
        )
except IT8951MemoryError as e:
    print(f"Memory error: {e}")
    # Fall back to lower bit depth
    display.display_image_progressive(
        img,
        pixel_format=PixelFormat.BPP_2,
        chunk_height=128
    )
```

## Debugging Memory Issues

Enable debug logging to see memory calculations:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Now you'll see memory information in logs
display.display_image(img)
# DEBUG: Estimated memory usage: 1,048,576 bytes
```

## Future Improvements

- Dynamic chunk size calculation based on available memory
- Memory usage statistics and reporting
- Automatic bit depth selection based on content
- Compressed image format support
