# ADR-004: Memory Safety Strategy

## Status

Accepted

## Context

E-paper displays have limited memory (typically 32MB for IT8951). Large images can cause:

- Memory allocation failures
- Display corruption
- System crashes
- Poor user experience

We need strategies to handle large images safely.

## Decision

We will implement multiple memory safety strategies:

1. **Validation**: Check image dimensions and memory usage before operations
2. **Progressive Loading**: Process large images in chunks
3. **Buffer Pooling**: Reuse memory allocations in hot paths
4. **Clear Warnings**: Warn users about large memory usage

## Consequences

### Positive

- Prevents crashes from memory exhaustion
- Better user experience with clear error messages
- Supports very large images through progressive loading
- Improved performance through buffer pooling
- Memory usage is predictable

### Negative

- Additional complexity in image handling
- Slight performance overhead for validation
- Progressive loading is slower than direct loading

### Neutral

- Follows defensive programming principles
- Similar to approaches in embedded systems

## Implementation

```python
# Memory validation
def _check_memory_usage(self, width: int, height: int, pixel_format: PixelFormat) -> None:
    memory_usage = self._estimate_memory_usage(width, height, pixel_format)

    if memory_usage > MemoryConstants.SAFE_IMAGE_MEMORY_BYTES:
        raise IT8951MemoryError(
            f"Image memory usage ({memory_usage:,} bytes) exceeds safe limit"
        )

# Progressive loading for large images
def display_image_progressive(
    self,
    image: Image.Image,
    chunk_height: int = 256
) -> None:
    # Process image in horizontal strips

# Buffer pooling
with ManagedBuffer.bytes(buffer_size, fill_value=color) as data:
    # Use buffer
    # Automatically returned to pool
```

## Thresholds

- Warning threshold: 8MB
- Error threshold: 16MB
- Chunk size: 256 pixels height
- Buffer pool size: 5 buffers per size
