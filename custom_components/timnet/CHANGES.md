# TimNet Home Assistant Integration - Rewritten Version

## 📋 Summary of Changes

This is a complete rewrite of the TimNet integration with **corrected register addresses** that match the device manual. Your device has been repaired by the manufacturer and now returns the correct values at the documented register addresses.

## 🔧 Key Changes from Old Version

### 1. **Domain Name Changed**
- **Old:** `modbus_device`
- **New:** `timnet`
- This forces Home Assistant to treat it as a completely new integration

### 2. **Register Addresses Fixed**
All register addresses now match the manual (REGISTERS.md):

| Register | Old Address | New Address | Description |
|----------|-------------|-------------|-------------|
| Door Switch (INP) | 0x0007 | **0x0004** | Door open/closed |
| Status Color (BARVA) | 0x0008 | **0x0009** | LED color indicator |
| Temperature T1 (TT) | 0x0018 | **0x0000** | Main temperature sensor |
| Combustion Time (CAS) | 0x0002 | **0x0002** | ✅ Same (now working) |
| Flap Position (SER1) | 0x0003 | **0x0003** | ✅ Same (now working) |

### 3. **Simplified Data Handling**
- Removed complex little-endian conversions (device was broken, now fixed)
- Temperature at 0x0000 is now standard big-endian ÷10
- Combustion time at 0x0002 is now standard ÷60 for minutes
- Flap position at 0x0003 is now direct 0-100% value (no weird divider)

### 4. **Cleaner Architecture**
- All sensors (including binary sensors) in one `sensor.py` file
- Clearer coordinator with connection status tracking
- Better error handling with last-known-value strategy
- Removed all workarounds for device firmware bugs

## 📦 Files Created

```
ha_modbus_device_new/
├── __init__.py          # Integration setup
├── manifest.json        # Integration metadata (domain: "timnet")
├── config_flow.py       # Configuration UI
├── sensor.py            # All sensors + binary sensors
├── modbus_client.py     # Modbus TCP client
├── strings.json         # UI text translations
├── icon.png             # Timpex flame logo
└── logo.png             # Timpex flame logo
```

## 📊 Entities Created

### Temperature Sensors
- **TimNet Temperature T1** - Main temperature (°C) at 0x0000
- **TimNet Temperature T2** - Secondary temp (°C) at 0x0001 (TimNet 200 only)

### Timing & Control
- **TimNet Combustion Time** - Duration in minutes (÷60) at 0x0002
- **TimNet Flap Position** - EPV flap 0-100% at 0x0003

### Operation Status
- **TimNet Unit Status** - Current state (text) at 0x0014
- **TimNet Combustion Mode** - Eco/Standard/Turbo at 0x0005
- **TimNet Fuel Type** - Wood/Briquettes at 0x0006
- **TimNet Refuel Offset** - -2 to +2 at 0x0007

### Diagnostic Sensors
- **TimNet Status Color** - LED color at 0x0009
- **TimNet Sound Signalization** - Beep on/off at 0x0010
- **TimNet Relay 1** - Relay state at 0x0011 (TimNet 200)
- **TimNet Relay 2** - Relay state at 0x0012 (TimNet 200)
- **TimNet Sensor Fault** - Fault detection at 0x0013
- **TimNet SDS Sensitivity** - SDS settings at 0x0008

### Binary Sensors
- **TimNet Door Switch** - Door open/closed at 0x0004
- **TimNet Connection Status** - Communication health

### Counters
- **TimNet Total Refuel Count** - Lifetime refuels at 0x0015

## 🎨 Special Features

### Temperature Special Values
- **HI** = 20000 (sensor disconnected)
- **LO** = -20000 (out of range)
- **---** = 20001 (unmeasured)
- **Neaktivní** = 20002 (inactive)

### Flap Position
- **0-100%** = Normal operation
- **Inicializace** = 255 (initializing)

### SDS Sensitivity Format
- **-2 to +2** with **(Aktivní)** or **(Neaktivní)** suffix
- **Vypnuto** = 255 (disabled)

### Status Text (Czech)
All 15+ status codes mapped to Czech text:
- "Start napájení", "Zatápění", "Hoření", "Přiložit", etc.

## ⚙️ Configuration

Default settings:
- **Host:** 10.0.0.11
- **Port:** 502
- **Unit ID:** 1
- **Scan Interval:** 8 seconds (safe for 10s device timeout)

## 🚀 Installation Steps

**BEFORE copying to Home Assistant:**

1. **Remove old integration:**
   - Go to Settings → Devices & Services
   - Find "Modbus Device" integration
   - Click the 3 dots → Delete
   - Restart Home Assistant

2. **Copy new integration:**
   ```powershell
   # Delete old integration
   Remove-Item \\10.0.0.22\config\custom_components\ha_modbus_device -Recurse -Force

   # Copy new integration
   Copy-Item c:\Users\marti\python\a\modbus_client\ha_modbus_device_new\* `
             \\10.0.0.22\config\custom_components\timnet\ -Recurse -Force
   ```

3. **Restart Home Assistant**

4. **Add new integration:**
   - Go to Settings → Devices & Services
   - Click "+ Add Integration"
   - Search for "TimNet"
   - Enter device IP: 10.0.0.11

## 🧪 Testing Checklist

After installation, verify these work correctly:

### Basic Functionality
- [ ] Temperature T1 shows real temperature (not stuck at one value)
- [ ] Combustion Time increases during operation (in minutes)
- [ ] Flap Position shows 0-100% or "Inicializace"
- [ ] Door Switch changes when opening/closing door

### Status & Mode
- [ ] Unit Status shows Czech text (not just numbers)
- [ ] Combustion Mode shows "Eco", "Standard", or "Turbo"
- [ ] Fuel Type shows "Dřevo" or "Brikety"
- [ ] Status Color shows "Žlutá", "Zelená", or "Červená"

### Diagnostics
- [ ] Connection Status turns OFF when device unplugged
- [ ] Sensor Fault shows "Bez poruchy" when no issues
- [ ] All entities maintain last value during brief disconnections

### Device Grouping
- [ ] All entities grouped under one "TimNet Heating Controller" device
- [ ] Device shows manufacturer "TimNet" and model "TimNet 100/200"

## 🐛 Known Issues / Notes

1. **Temperature T2, Relay 1, Relay 2** - Only available on TimNet 200 model
2. **SDS Register** - Complex format (tens digit = level, ones digit = active state)
3. **Read Limit** - Reading 22 registers (0-21) to cover all sensors
4. **Scan Interval** - Set to 8 seconds (device has 10s TCP timeout)

## 📝 Debug Information

All entities include these attributes for troubleshooting:
- `address` - Hex register address (e.g., "0x0000")
- `register_key` - Manual key name (e.g., "TT")
- `raw_value` - Unprocessed register value
- `host` - Device IP address
- `port` - Modbus TCP port

## ✅ What to Verify

Before I copy this to your Home Assistant, please verify:

1. **Are these the correct register addresses from your manual?**
   - Temperature at 0x0000 (not 0x0018)
   - Door at 0x0004 (not 0x0007)
   - Status Color at 0x0009 (not 0x0008)

2. **Is your device model TimNet 100 or TimNet 200?**
   - TimNet 100: Only T1 temperature, no relays
   - TimNet 200: Has T2 temperature + 2 relays

3. **Do you want to test this first, or copy directly to Home Assistant?**

Let me know if you want me to:
- **A)** Copy this to your Home Assistant now
- **B)** Make any changes first
- **C)** Create a test script to verify registers work correctly
