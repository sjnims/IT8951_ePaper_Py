# Display Modes Guide

This guide explains all display modes supported by the IT8951 controller, including the extended modes.

## Standard Display Modes

### INIT (Mode 0)

- **Purpose**: Full display initialization and clearing
- **Update Time**: ~2000ms
- **Use Cases**: First display after power on, clearing ghosting
- **Characteristics**: Complete pixel refresh with multiple passes

### DU (Direct Update, Mode 1)

- **Purpose**: Fast monochrome updates
- **Update Time**: ~260ms
- **Use Cases**: Text updates, simple graphics
- **Characteristics**: Binary black/white only, minimal ghosting

### GC16 (Grayscale Clear 16, Mode 2)

- **Purpose**: High-quality 16-level grayscale
- **Update Time**: ~450ms
- **Use Cases**: Photos, detailed images
- **Characteristics**: Best image quality, full ghost clearing

### GL16 (Grayscale Light 16, Mode 3)

- **Purpose**: Standard 16-level grayscale
- **Update Time**: ~450ms
- **Use Cases**: General purpose grayscale content
- **Characteristics**: Good balance of quality and ghost reduction

### A2 (Mode 4)

- **Purpose**: Ultra-fast binary updates
- **Update Time**: ~120ms
- **Use Cases**: Animations, real-time updates
- **Characteristics**: Fastest mode but accumulates ghosting
- **Important**: Use with auto-clear feature to prevent ghost buildup

## Extended Display Modes (v0.7.0)

These extended modes are now implemented and available for use. Hardware support may vary by display model.

### GLR16 (Ghost Reduction 16-level, Mode 5)

- **Purpose**: Enhanced ghost reduction for 16-level grayscale
- **Update Time**: ~500-600ms (slightly slower than GL16)
- **Use Cases**:
  - When standard GL16 leaves visible ghosting
  - High-contrast images that cause ghosting
  - Periodic refresh to clean up accumulated artifacts
- **Characteristics**:
  - Uses additional voltage passes to reduce ghosting
  - 16 grayscale levels maintained
  - Better transition between high-contrast areas
- **Recommended Pixel Format**: 4bpp or 8bpp
- **Note**: May not be supported on all IT8951 variants

### GLD16 (Ghost Level Detection 16, Mode 6)

- **Purpose**: Adaptive ghost compensation with analysis
- **Update Time**: ~500-700ms (varies based on content)
- **Use Cases**:
  - Complex images with mixed content
  - When ghosting patterns are unpredictable
  - Fine art or detailed grayscale images
- **Characteristics**:
  - Analyzes display state before updating
  - Applies adaptive compensation based on detected ghosting
  - May perform pre-compensation passes
- **Recommended Pixel Format**: 4bpp or 8bpp
- **Note**: Most advanced mode, hardware support varies

### DU4 (Direct Update 4-level, Mode 7)

- **Purpose**: Fast updates with 4 grayscale levels
- **Update Time**: ~180-250ms
- **Use Cases**:
  - Simple graphics with limited shading
  - UI elements with 2-4 gray levels
  - Faster alternative to full 16-level modes
- **Characteristics**:
  - Only 4 distinct gray levels (0, 85, 170, 255)
  - Faster than GC16/GL16 but more levels than DU/A2
  - Some ghosting possible with repeated use
- **Recommended Pixel Format**: 2bpp or 4bpp
- **Note**: Good balance between speed and grayscale capability

## Mode Selection Guide

### Decision Tree

```text
Is this the first display after power on?
└─ Yes → Use INIT

Is the content binary (pure black/white)?
├─ Yes → Need ultra-fast speed?
│        ├─ Yes → Use A2 (with auto-clear)
│        └─ No → Use DU
└─ No → Continue...

How many grayscale levels needed?
├─ 4 levels → Use DU4 (fast with basic shading)
└─ 16 levels → Continue...

Is ghosting a major concern?
├─ Yes → Need adaptive compensation?
│        ├─ Yes → Use GLD16
│        └─ No → Use GLR16
└─ No → Continue...

Is this a photo or detailed image?
├─ Yes → Use GC16 (highest quality)
└─ No → Use GL16 (general purpose)
```

### Code Examples

```python
from IT8951_ePaper_Py import EPaperDisplay, DisplayMode, PixelFormat

# Initialize and clear
display = EPaperDisplay(vcom=-2.0)
display.init()
display.clear()  # Uses INIT mode

# Text update
display.display_image(text_img, mode=DisplayMode.DU)

# Photo display
display.display_image(photo, mode=DisplayMode.GC16)

# Animation with auto-clear
display = EPaperDisplay(vcom=-2.0, a2_refresh_limit=10)
for frame in animation_frames:
    display.display_image(frame, mode=DisplayMode.A2)

# Extended modes examples

# Ghost reduction for high-contrast content
display.display_image(high_contrast_img, mode=DisplayMode.GLR16)

# Adaptive ghost compensation for complex images
display.display_image(complex_artwork, mode=DisplayMode.GLD16)

# Fast 4-level grayscale for UI elements
display.display_image(ui_element, mode=DisplayMode.DU4,
                     pixel_format=PixelFormat.BPP_2)
```

## Performance Characteristics

| Mode | Speed | Quality | Ghosting | Power | Gray Levels |
|------|-------|---------|----------|--------|-------------|
| INIT | Slowest | N/A | None | Highest | 1 |
| DU | Fast | Binary | Low | Low | 2 |
| GC16 | Medium | Best | Minimal | Medium | 16 |
| GL16 | Medium | Good | Low | Medium | 16 |
| A2 | Fastest | Binary | High* | Lowest | 2 |
| GLR16 | Slow | Good | Very Low | Medium-High | 16 |
| GLD16 | Slow | Good | Adaptive | Medium-High | 16 |
| DU4 | Fast | Limited | Medium | Low-Medium | 4 |

*Without auto-clear

## Technical Details

### Waveform Lookup Tables (LUT)

Each display mode uses different waveform LUTs that control:

- Number of frame passes
- Voltage sequences applied
- Temperature compensation
- Ghost reduction algorithms

### Temperature Compensation

The IT8951 automatically adjusts waveforms based on temperature sensor readings. This affects:

- Update speed (slower when cold)
- Ghost reduction effectiveness
- Image quality

### Mode Availability

Not all modes may be available on all displays. The availability depends on:

- Display panel type
- Firmware version
- Loaded waveform data

## Hardware Compatibility

### Extended Mode Support

The extended modes (GLR16, GLD16, DU4) availability depends on:

- IT8951 firmware version
- E-paper panel model and manufacturer
- Loaded waveform data

To check if your hardware supports these modes:

```python
# The driver will warn if a mode is not supported
# when you try to use it
try:
    display.display_image(img, mode=DisplayMode.GLR16)
except Exception as e:
    print(f"GLR16 not supported: {e}")
```

## Best Practices

1. **Always start with INIT** after power on
2. **Use appropriate mode** for content type
3. **Monitor ghosting** and clear when needed
4. **Consider temperature** effects on performance
5. **Test modes** with your specific content

## Mode Constants

```python
from IT8951_ePaper_Py.constants import DisplayMode

# Standard modes (always available)
DisplayMode.INIT   # 0 - Full refresh/clear
DisplayMode.DU     # 1 - Direct Update (2-level)
DisplayMode.GC16   # 2 - Grayscale Clear 16
DisplayMode.GL16   # 3 - Grayscale Light 16
DisplayMode.A2     # 4 - Animation (2-level, fastest)

# Extended modes (v0.7.0, hardware support varies)
DisplayMode.GLR16  # 5 - Ghost Reduction 16-level
DisplayMode.GLD16  # 6 - Ghost Level Detection 16
DisplayMode.DU4    # 7 - Direct Update 4-level
```

## References

- [IT8951 Datasheet and Technical Documentation](https://www.waveshare.com/wiki/6inch_HD_e-Paper_HAT) - See "Resources" section
- [Waveshare E-Paper Wiki](https://www.waveshare.com/wiki/Main_Page#Display.2FE-Paper) - General e-paper documentation
- [Waveshare 10.3inch E-Paper HAT Documentation](https://www.waveshare.com/wiki/10.3inch_e-Paper_HAT) - Specific to this display
- [E Ink Technology Overview](https://www.eink.com/technology.html) - Understanding e-paper technology
- [Original Waveshare IT8951 Driver](https://github.com/waveshareteam/IT8951-ePaper) - C implementation reference
