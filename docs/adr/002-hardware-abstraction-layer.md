# ADR-002: Hardware Abstraction Layer Design

## Status

Accepted

## Context

The IT8951 driver needs to communicate with hardware (SPI, GPIO) but also needs to:

- Be testable without hardware
- Support different hardware platforms potentially
- Allow for easy mocking in tests
- Maintain clean separation of concerns

## Decision

We will use an abstract `SPIInterface` base class with concrete implementations:

- `RaspberryPiSPI` for actual hardware
- `MockSPI` for testing

The display classes will depend on the interface, not concrete implementations.

## Consequences

### Positive

- Hardware can be fully mocked for testing
- Easy to add support for other platforms
- Clean dependency injection pattern
- Over 98% test coverage possible without hardware
- Development possible on non-Pi machines (macOS, Windows)

### Negative

- Slight additional complexity
- Extra abstraction layer

### Neutral

- Follows SOLID principles (Dependency Inversion)

## Implementation

```python
# Abstract interface
class SPIInterface(ABC):
    @abstractmethod
    def write_command(self, command: int) -> None:
        pass

    @abstractmethod
    def write_data(self, data: int | bytes) -> None:
        pass

# Concrete implementations
class RaspberryPiSPI(SPIInterface):
    # Real hardware implementation

class MockSPI(SPIInterface):
    # Test implementation

# Usage
display = EPaperDisplay(spi_interface=MockSPI())  # For testing
display = EPaperDisplay()  # Auto-creates RaspberryPiSPI
```
