"""Type stubs for spidev module."""

from collections.abc import Sequence

class SpiDev:
    """SPI device interface."""

    mode: int
    bits_per_word: int
    max_speed_hz: int

    def open(self, bus: int, device: int) -> None:
        """Open SPI device."""
        ...
    def close(self) -> None:
        """Close SPI device."""
        ...
    def xfer2(
        self, values: Sequence[int], speed_hz: int = 0, delay_usecs: int = 0, bits_per_word: int = 0
    ) -> list[int]:
        """Transfer data to/from SPI device."""
        ...
    def xfer3(
        self, values: Sequence[int], speed_hz: int = 0, delay_usecs: int = 0, bits_per_word: int = 0
    ) -> list[int]:
        """Transfer data to/from SPI device (alternative method)."""
        ...
    def writebytes(self, values: Sequence[int]) -> None:
        """Write bytes to SPI device."""
        ...
    def readbytes(self, length: int) -> list[int]:
        """Read bytes from SPI device."""
        ...
    def writebytes2(self, values: Sequence[int]) -> None:
        """Write bytes to SPI device (alternative method)."""
        ...
