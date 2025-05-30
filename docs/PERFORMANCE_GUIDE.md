# Performance Guide for IT8951 E-Paper Driver

This guide provides performance comparisons and optimization strategies for the IT8951 e-paper driver.

## Table of Contents

- [Pixel Format Performance](#pixel-format-performance)
- [Display Mode Comparison](#display-mode-comparison)
- [SPI Speed Optimization](#spi-speed-optimization)
- [Memory Usage](#memory-usage)
- [Best Practices](#best-practices)

## Pixel Format Performance

The driver supports multiple pixel formats, each with different performance characteristics:

### Data Transfer Comparison

| Format | Bits/Pixel | Data Size | Transfer Speed | Quality |
|--------|------------|-----------|----------------|---------|
| 1bpp   | 1          | 12.5%     | Fastest        | Binary (B/W only) |
| 2bpp   | 2          | 25%       | Very Fast      | 4 gray levels |
| 4bpp   | 4          | 50%       | Fast (Default) | 16 gray levels |
| 8bpp   | 8          | 100%      | Baseline       | 256 gray levels |

### Benchmark Results

For a 1024x768 image on Raspberry Pi 4:

```python
# 8bpp (baseline)
display.display_image(img, pixel_format=PixelFormat.BPP_8)
# Transfer time: ~892ms
# Data transferred: 786,432 bytes

# 4bpp (recommended default)
display.display_image(img, pixel_format=PixelFormat.BPP_4)
# Transfer time: ~467ms (48% faster)
# Data transferred: 393,216 bytes

# 2bpp
display.display_image(img, pixel_format=PixelFormat.BPP_2)
# Transfer time: ~251ms (72% faster)
# Data transferred: 196,608 bytes

# 1bpp
display.display_image(img, pixel_format=PixelFormat.BPP_1)
# Transfer time: ~134ms (85% faster)
# Data transferred: 98,304 bytes
```

### When to Use Each Format

- **1bpp**: Text documents, line art, QR codes
- **2bpp**: Simple graphics with limited shading
- **4bpp**: General purpose (best balance of speed/quality)
- **8bpp**: Photographs, detailed grayscale images

## Display Mode Comparison

Different display modes offer various trade-offs between speed and quality:

### Mode Performance Table

| Mode | Update Time* | Quality | Ghost Reduction | Use Case |
|------|-------------|---------|-----------------|----------|
| INIT | ~2000ms | Best | Full clear | Initial display, mode changes |
| DU   | ~260ms | Good | Minimal | Fast monochrome updates |
| GC16 | ~450ms | Best | Good | High-quality grayscale |
| GL16 | ~450ms | Good | Better | General grayscale updates |
| A2   | ~120ms | Low | None** | Animation, real-time updates |

*Times for full screen update on 10.3" display

### Mode Selection Guide

```python
from IT8951_ePaper_Py import EPaperDisplay, DisplayMode

# High-quality photo display
display.display_image(photo, mode=DisplayMode.GC16)

# Fast text update
display.display_image(text_img, mode=DisplayMode.DU)

# Animation or real-time updates
display.display_image(frame, mode=DisplayMode.A2)
# Note: Use A2 auto-clear feature to prevent ghosting
```

### A2 Mode Optimization

A2 mode is the fastest but accumulates ghosting. Use auto-clear feature:

```python
# Enable auto-clear after 10 A2 updates
display = EPaperDisplay(vcom=-2.0, a2_refresh_limit=10)

# The display will automatically clear after 10 A2 updates
for i in range(20):
    display.display_image(frames[i], mode=DisplayMode.A2)
    # Auto-clear happens at i=9 and i=19
```

## SPI Speed Optimization

### Automatic Speed Detection

The driver automatically selects optimal SPI speed based on Raspberry Pi model:

| Model | SPI Speed | Notes |
|-------|-----------|-------|
| Pi 3  | 15.625 MHz | Conservative for stability |
| Pi 4  | 7.8125 MHz | Lower due to timing differences |
| Pi 5  | 7.8125 MHz | Same as Pi 4 |

### Manual Speed Override

For advanced users who want to experiment:

```python
# Override with custom speed (Hz)
display = EPaperDisplay(vcom=-2.0, spi_speed=20_000_000)  # 20 MHz

# Note: Higher speeds may cause communication errors
# Test thoroughly before using in production
```

## Memory Usage

### Image Buffer Calculations

Memory usage depends on image size and pixel format:

```text
Memory (bytes) = width × height × (bits_per_pixel / 8)
```

Examples for 1024×768 display:

- 8bpp: 786,432 bytes (~768 KB)
- 4bpp: 393,216 bytes (~384 KB)
- 2bpp: 196,608 bytes (~192 KB)
- 1bpp: 98,304 bytes (~96 KB)

### Partial Update Optimization

Reduce memory and improve speed with partial updates:

```python
# Update only changed region (e.g., clock display)
display.display_partial(
    clock_image,
    x=400, y=300,
    width=200, height=100,
    mode=DisplayMode.DU
)
# Only transfers 20,000 bytes vs 786,432 for full screen
```

## Best Practices

### 1. Choose Appropriate Pixel Format

```python
# Text and line art
display.display_image(text_img, pixel_format=PixelFormat.BPP_1)

# General content (default)
display.display_image(content)  # Uses 4bpp by default

# Photos only when needed
display.display_image(photo, pixel_format=PixelFormat.BPP_8)
```

### 2. Use Partial Updates

```python
# Update only what changed
if only_clock_changed:
    display.display_partial(clock, x=900, y=50, width=100, height=50)
else:
    display.display_image(full_screen)
```

### 3. Batch Updates

```python
# Bad: Multiple full screen updates
for widget in widgets:
    display.display_image(render_screen_with_widget(widget))

# Good: Render once, update once
screen = render_all_widgets(widgets)
display.display_image(screen)
```

### 4. Mode Selection Strategy

```python
# Initial display
display.clear()  # Uses INIT mode

# Regular updates
display.display_image(content, mode=DisplayMode.GL16)

# Fast updates (with auto-clear)
for frame in animation:
    display.display_image(frame, mode=DisplayMode.A2)

# Quality-critical content
display.display_image(detailed_diagram, mode=DisplayMode.GC16)
```

### 5. Alignment Considerations

For optimal performance, especially with 1bpp mode:

```python
# Ensure coordinates and dimensions are aligned
x = (x // 32) * 32  # 32-pixel alignment for 1bpp
width = ((width + 31) // 32) * 32

display.display_image(binary_img, x=x, y=0, pixel_format=PixelFormat.BPP_1)
```

## Performance Measurement

Use the built-in timing decorator (when logging at DEBUG level):

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Now operations will log timing information:
# DEBUG: display_image completed in 467.23ms
# DEBUG: clear completed in 2134.56ms
```

## Summary

For optimal performance:

1. Use 4bpp (default) for most content
2. Use partial updates when possible
3. Select appropriate display mode for content type
4. Let the driver auto-detect SPI speed
5. Use A2 mode with auto-clear for animations
6. Monitor performance with debug logging

Remember: E-paper displays are optimized for quality and power efficiency, not speed. Design your application accordingly.
