# ADR-003: Default to 4bpp Pixel Format

## Status

Accepted

## Context

The IT8951 controller supports multiple pixel formats:

- 8bpp: 1 byte per pixel, full quality but highest memory/bandwidth usage
- 4bpp: 2 pixels per byte, 16 grayscale levels, 50% less data
- 2bpp: 4 pixels per byte, 4 grayscale levels
- 1bpp: 8 pixels per byte, binary only

The Waveshare wiki specifically recommends 4bpp for general use.

## Decision

We will default to 4bpp (PixelFormat.BPP_4) for all display operations while allowing users to override.

## Consequences

### Positive

- 50% reduction in data transfer compared to 8bpp
- Still provides 16 grayscale levels (sufficient for most content)
- Faster display updates
- Lower memory usage
- Follows manufacturer recommendation
- Better for battery-powered applications

### Negative

- Not the highest quality option (8bpp)
- May require users to explicitly choose 8bpp for photographs

### Neutral

- Aligns with C driver defaults
- Industry standard for e-paper displays

## Implementation

```python
def display_image(
    self,
    image: Image.Image,
    x: int = 0,
    y: int = 0,
    mode: DisplayMode = DisplayMode.GC16,
    rotation: Rotation = Rotation.ROTATE_0,
    pixel_format: PixelFormat = PixelFormat.BPP_4,  # Default to 4bpp
) -> None:
    """Display an image on the e-paper."""
```

## References

- Waveshare Wiki: "It is recommended to use 4bpp for refreshing"
- Performance tests show 4bpp is 2x faster than 8bpp with minimal quality loss
