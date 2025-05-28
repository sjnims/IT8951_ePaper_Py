<!-- markdownlint-disable MD013 MD036 -->
# IT8951 E-Paper Python Driver Roadmap

This roadmap outlines the phased implementation of missing features and improvements identified in the driver comparison and wiki analysis. Features are prioritized by impact on performance, usability, and hardware compatibility.

## Phase 1: Performance Optimizations (v0.2.0)

**High-impact features that significantly improve display performance and user experience**

### 1.1 Implement 4bpp Support (Wiki Recommended) ✅

1.1.1 ✅ Add 4bpp pixel packing functionality in `it8951.py`
1.1.2 ✅ Create `display_image_4bpp()` method in `display.py` (implemented as parameter)
1.1.3 ✅ Add pixel format conversion utilities (8bpp to 4bpp) (integrated in pack_pixels)
1.1.4 ✅ Update examples to demonstrate 4bpp usage (performance_4bpp.py)
1.1.5 ✅ Add performance comparison tests (4bpp vs 8bpp) (test_performance.py)

### 1.2 Dynamic SPI Speed Configuration ✅

1.2.1 ✅ Add Raspberry Pi version detection utility
1.2.2 ✅ Update `SPIConstants` with Pi-specific speeds
1.2.3 ✅ Modify `RaspberryPiSPI` to auto-select appropriate speed
1.2.4 ✅ Add manual speed override option
1.2.5 ✅ Document speed recommendations in README

### 1.3 A2 Mode Auto-Clear Protection

1.3.1 Add A2 refresh counter to `EPaperDisplay` class
1.3.2 Implement automatic INIT mode clearing after N refreshes
1.3.3 Make threshold configurable (default: 10)
1.3.4 Add warning when approaching clear threshold
1.3.5 Create example demonstrating safe A2 usage

## Phase 2: Display Quality Enhancements (v0.3.0)

**Features that improve display quality and handle edge cases**

### 2.1 Enhanced Driving Capability

2.1.1 Add `enhance_driving_capability()` method to `IT8951`
2.1.2 Add `enhance_driving` parameter to `EPaperDisplay.__init__()`
2.1.3 Document when to use enhanced driving (long cables, blur)
2.1.4 Add diagnostic method to check current driving mode

### 2.2 Improved 4-Byte Alignment for 1bpp

2.2.1 Create specialized alignment for 1bpp mode (32-bit boundaries)
2.2.2 Add model detection for alignment requirements
2.2.3 Update `_align_coordinate()` to handle different modes
2.2.4 Add alignment validation and warnings
2.2.5 Create tests for edge cases

### 2.3 VCOM Value Validation and Warnings

2.3.1 Add VCOM range validation with clear error messages
2.3.2 Create prominent VCOM warning in all examples
2.3.3 Add `get_vcom()` method using register read
2.3.4 Implement VCOM calibration helper
2.3.5 Add VCOM mismatch detection

## Phase 3: Additional Bit Depth Support (v0.4.0)

**Expand display capabilities for specialized use cases**

### 3.1 Implement 1bpp Support

3.1.1 Add 1bpp pixel packing (8 pixels per byte)
3.1.2 Create `display_image_1bpp()` method
3.1.3 Implement proper endian conversion
3.1.4 Add specialized A2 mode support for 1bpp
3.1.5 Create binary image examples

### 3.2 Implement 2bpp Support

3.2.1 Add 2bpp pixel packing (4 pixels per byte)
3.2.2 Create `display_image_2bpp()` method
3.2.3 Add 4-level grayscale conversion
3.2.4 Create examples for simple graphics

## Phase 4: Power Management (v0.5.0)

**Essential for battery-powered and embedded applications**

### 4.1 Basic Power Management Commands

4.1.1 Implement `standby()` method in `IT8951`
4.1.2 Implement `sleep()` method in `IT8951`
4.1.3 Add `wake()` method for recovery
4.1.4 Create power state tracking
4.1.5 Add auto-sleep timeout option

### 4.2 Power Management Integration

4.2.1 Add context manager support for auto-sleep
4.2.2 Create power usage examples
4.2.3 Document power consumption differences
4.2.4 Add power state to device info

## Phase 5: Debugging and Diagnostics (v0.6.0)

**Tools for troubleshooting and verification**

### 5.1 Register Read Capability

5.1.1 Implement `read_register()` in `IT8951`
5.1.2 Add register dump utility
5.1.3 Create register verification methods
5.1.4 Add register documentation

### 5.2 Extended Display Modes Testing

5.2.1 Test and document GLR16 mode
5.2.2 Test and document GLD16 mode
5.2.3 Test and document DU4 mode
5.2.4 Create mode comparison examples
5.2.5 Add mode selection guide

## Phase 6: Developer Experience (v0.7.0)

**Improvements to make the library easier to use**

### 6.1 Enhanced Examples

6.1.1 Create performance optimization example
6.1.2 Add battery-powered device example
6.1.3 Create mode selection guide example
6.1.4 Add troubleshooting example

### 6.2 Comprehensive Testing

6.2.1 Add performance benchmarks
6.2.2 Create bit depth conversion tests
6.2.3 Add power management tests
6.2.4 Create alignment edge case tests

### 6.3 Documentation Updates

6.3.1 Update README with new features
6.3.2 Create performance tuning guide
6.3.3 Add troubleshooting section
6.3.4 Document all new APIs

## Phase 7: CI/CD Optimizations (v0.8.0)

**Improve development workflow efficiency as the project scales**

### 7.1 Automated Test Selection (Codecov ATS)

7.1.1 Integrate Codecov CLI into CI workflow
7.1.2 Configure ATS for pytest test filtering
7.1.3 Set up test impact analysis
7.1.4 Add fallback for full test runs when needed
7.1.5 Monitor and tune ATS performance

## Implementation Notes

- Each phase builds upon previous phases
- Phase 1-2 provide the most immediate user value
- Phase 3-4 enable new use cases
- Phase 5-6 improve maintainability and developer experience
- All features should maintain backward compatibility
- Type hints and proper error handling required throughout
