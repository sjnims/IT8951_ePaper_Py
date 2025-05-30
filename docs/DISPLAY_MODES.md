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

## Extended Display Modes

These modes are defined in the IT8951 specification but are scheduled for testing in Phase 6 of the roadmap.

### GLR16 (Grayscale Light Reduction 16, Mode 5)

- **Purpose**: Ghost reduction variant of GL16
- **Expected Update Time**: ~450-500ms
- **Use Cases**: When GL16 leaves too much ghosting
- **Characteristics**: Enhanced ghost clearing algorithm
- **Status**: Defined but not yet tested/documented

### GLD16 (Grayscale Light Delta 16, Mode 6)

- **Purpose**: Optimized for partial updates
- **Expected Update Time**: ~400-450ms
- **Use Cases**: Updating regions with minimal change
- **Characteristics**: Delta-based update algorithm
- **Status**: Defined but not yet tested/documented

### DU4 (Direct Update 4-level, Mode 7)

- **Purpose**: Fast 4-level grayscale updates
- **Expected Update Time**: ~300ms
- **Use Cases**: Simple graphics with limited gray levels
- **Characteristics**: Faster than full grayscale, more levels than DU
- **Status**: Defined but not yet tested/documented

## Mode Selection Guide

### Decision Tree

```text
Is this the first display after power on?
└─ Yes → Use INIT

Is the content binary (pure black/white)?
├─ Yes → Need speed?
│        ├─ Yes → Use A2 (with auto-clear)
│        └─ No → Use DU
└─ No → Continue...

Is this a photo or detailed image?
├─ Yes → Use GC16
└─ No → Use GL16 (general purpose)
```

### Code Examples

```python
from IT8951_ePaper_Py import EPaperDisplay, DisplayMode

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
```

## Performance Characteristics

| Mode | Speed | Quality | Ghosting | Power |
|------|-------|---------|----------|--------|
| INIT | Slowest | N/A | None | Highest |
| DU | Fast | Binary | Low | Low |
| GC16 | Medium | Best | None | Medium |
| GL16 | Medium | Good | Low | Medium |
| A2 | Fastest | Binary | High* | Lowest |

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

## Future Enhancements

The extended modes (GLR16, GLD16, DU4) are scheduled for:

- Testing and validation (Phase 6.1)
- Performance benchmarking
- Use case documentation
- Example code creation

## Best Practices

1. **Always start with INIT** after power on
2. **Use appropriate mode** for content type
3. **Monitor ghosting** and clear when needed
4. **Consider temperature** effects on performance
5. **Test modes** with your specific content

## Mode Constants

```python
from IT8951_ePaper_Py.constants import DisplayMode

# Available modes
DisplayMode.INIT   # 0
DisplayMode.DU     # 1
DisplayMode.GC16   # 2
DisplayMode.GL16   # 3
DisplayMode.A2     # 4
DisplayMode.GLR16  # 5 (future)
DisplayMode.GLD16  # 6 (future)
DisplayMode.DU4    # 7 (future)
```

## References

- [IT8951 Datasheet and Technical Documentation](https://www.waveshare.com/wiki/6inch_HD_e-Paper_HAT) - See "Resources" section
- [Waveshare E-Paper Wiki](https://www.waveshare.com/wiki/Main_Page#Display.2FE-Paper) - General e-paper documentation
- [Waveshare 10.3inch E-Paper HAT Documentation](https://www.waveshare.com/wiki/10.3inch_e-Paper_HAT) - Specific to this display
- [E Ink Technology Overview](https://www.eink.com/technology.html) - Understanding e-paper technology
- [Original Waveshare IT8951 Driver](https://github.com/waveshareteam/IT8951-ePaper) - C implementation reference
