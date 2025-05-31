# Power Management Guide

This guide explains the power management features of the IT8951 e-paper controller and how to use them effectively in battery-powered applications.

## Power States

The IT8951 controller supports three power states:

### 1. ACTIVE State

- **Description**: Normal operating mode with full functionality
- **Power Consumption**: ~200-250mW (typical)
- **Wake Time**: Immediate (already active)
- **Use Case**: Active display updates and normal operation

### 2. STANDBY State

- **Description**: Low-power mode with quick wake capability
- **Power Consumption**: ~5-10mW (typical)
- **Wake Time**: <100ms
- **Use Case**: Short idle periods between updates
- **Note**: Display retains image content

### 3. SLEEP State

- **Description**: Ultra-low power mode for extended idle periods
- **Power Consumption**: <1mW (typical)
- **Wake Time**: ~500ms
- **Use Case**: Long idle periods (hours/days)
- **Note**: Display may need refresh after wake

## Power Consumption Comparison

| Mode | Typical Power | Relative to Active | Battery Life Impact |
|------|---------------|-------------------|-------------------|
| Active | 200-250mW | 100% | Hours |
| Standby | 5-10mW | 2-5% | Days to weeks |
| Sleep | <1mW | <0.5% | Months |

*Note: Actual power consumption depends on display size, temperature, and usage patterns.*

## Transition Times

| From → To | Typical Time | Notes |
|-----------|--------------|-------|
| Active → Standby | <10ms | Instant transition |
| Active → Sleep | <50ms | Quick transition |
| Standby → Active | <100ms | Fast wake |
| Sleep → Active | ~500ms | Requires initialization |

## Best Practices

### 1. Auto-Sleep Configuration

```python
# Set auto-sleep for battery applications
display.set_auto_sleep_timeout(30.0)  # Sleep after 30 seconds

# For interactive applications
display.set_auto_sleep_timeout(300.0)  # 5 minutes

# For always-on displays
display.set_auto_sleep_timeout(None)  # Disable auto-sleep
```

### 2. Power State Selection

**Use STANDBY when:**

- Updates occur every few minutes
- Quick response time is needed
- Display content should be retained

**Use SLEEP when:**

- Updates occur hourly or less frequently
- Maximum battery life is critical
- Wake time of ~500ms is acceptable

### 3. Context Manager for Automatic Power Management

```python
# Automatically sleeps on exit
with EPaperDisplay(vcom=-2.0) as display:
    display.set_auto_sleep_timeout(30.0)
    display.init()
    # ... do work ...
# Display automatically enters sleep mode here
```

### 4. Manual Power Management

```python
# For predictable update patterns
display.sleep()  # Enter sleep mode
# ... wait for next update time ...
display.wake()   # Wake when needed
display.clear()  # Refresh after sleep
```

## Power Optimization Strategies

### 1. Batch Updates

Combine multiple updates into a single active period:

```python
display.wake()
for image in images_to_display:
    display.display_image(image)
    time.sleep(5)
display.sleep()
```

### 2. Progressive Loading for Large Images

Reduces peak power consumption:

```python
# Uses less memory and power
display.display_image_progressive(large_image, chunk_height=256)
```

### 3. Appropriate Display Modes

- Use A2 mode for frequent updates (lowest power per update)
- Use GC16 for best quality (higher power but less frequent)
- Avoid INIT mode unless necessary (highest power consumption)

### 4. VCOM Optimization

Proper VCOM calibration reduces power consumption:

```python
# Find optimal VCOM for your display
optimal_vcom = display.find_optimal_vcom()
display.set_vcom(optimal_vcom)
```

## Battery Life Calculations

### Example: Weather Station

- Update frequency: Every 30 minutes
- Active time per update: 5 seconds
- Display size: 10.3" (typical 250mW active)

**Without Power Management:**

- Daily consumption: 24h × 250mW = 6000mWh
- 3000mAh battery at 3.7V: ~2 days

**With Auto-Sleep (30s timeout):**

- Active time: 48 updates × 35s = 28 minutes
- Sleep time: 23.5 hours
- Daily consumption: (0.47h × 250mW) + (23.5h × 1mW) ≈ 141mWh
- Same battery: ~79 days

**With Aggressive Sleep:**

- Active time: 48 updates × 5s = 4 minutes
- Sleep time: 23.93 hours
- Daily consumption: (0.067h × 250mW) + (23.93h × 1mW) ≈ 41mWh
- Same battery: ~270 days

## Temperature Considerations

Power consumption varies with temperature:

- **Cold (<0°C)**: +20-30% power consumption
- **Normal (20°C)**: Baseline consumption
- **Hot (>40°C)**: +10-15% power consumption

Consider more aggressive power management in extreme temperatures.

## Troubleshooting

### Display Not Waking

- Ensure proper wake sequence: `wake()` → `clear()` → `display_image()`
- Check power supply stability
- Verify SPI connection integrity

### Unexpected Power Consumption

- Check for wake events (button presses, sensors)
- Verify auto-sleep timeout is set correctly
- Monitor actual state transitions with `display.power_state`

### Image Ghosting After Wake

- Always perform `clear()` after waking from sleep
- Use INIT mode periodically for deep refresh
- Consider environmental factors (temperature, humidity)

## Example Implementation

See `examples/power_management_demo.py` for a complete demonstration of all power management features.
