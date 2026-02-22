# TimNet Home Assistant Integration

Custom Home Assistant integration for TimNet kamna over Modbus TCP.

## Features

- Config Flow setup from Home Assistant UI
- Temperature, status, flap, counters, diagnostic sensors
- Connection status tracking
- Supports TimNet 100 and TimNet 200 variants

## Repository structure

- `custom_components/timnet/` – integration code
- `custom_components/timnet/manifest.json` – metadata and version
- `custom_components/timnet/config_flow.py` – UI setup flow
- `custom_components/timnet/sensor.py` – entities and coordinator

## Install (manual)

1. Copy `custom_components/timnet` to your HA config directory:
   - `<config>/custom_components/timnet`
2. Restart Home Assistant.
3. Go to **Settings → Devices & Services → Add Integration**.
4. Search for **TimNet Heating Controller** and configure host/port/unit id.

## Install from GitHub (HACS custom repository)

1. Open HACS → Integrations → menu → **Custom repositories**.
2. Add this repo URL and category **Integration**.
3. Search and install **TimNet Home Assistant Integration**.
4. Restart Home Assistant and add integration from UI.

## Development

- Domain: `timnet`
- Current version: see `custom_components/timnet/manifest.json`

## License

Use your preferred license before publishing (e.g., MIT).
