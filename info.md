# Octopus Cosy to Emoncms

Send your Octopus Cosy Heat Pump data to Emoncms for monitoring on heatpumpmonitor.org

## Features

- **UI Configuration** - Easy setup through Home Assistant UI
- **Entity Selection** - Choose which sensors to send
- **Configurable Interval** - Update frequency from 10-3600 seconds
- **Automatic Sync** - Periodic data transmission to Emoncms

## Installation

### Via HACS (Recommended)

1. Open HACS
2. Go to **Integrations**
3. Click the **three dots** (⋮) in the top right
4. Select **Custom repositories**
5. Add this repository: `https://github.com/swwilshub/cosy-to-emoncms`
6. Category: **Integration**
7. Click **Add**
8. Find "Octopus Cosy to Emoncms" in the integration list
9. Click **Download**
10. Restart Home Assistant

### Manual Installation

Copy the `custom_components/octopus_cosy_emoncms` folder to your Home Assistant config directory.

## Configuration

After installation:

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for "Octopus Cosy to Emoncms"
4. Enter:
   - Emoncms URL (default: `https://emoncms.org`)
   - API Key (your Emoncms write key)
   - Input Node Number (default: 303)
   - Select sensors to send
   - Update interval (default: 30 seconds)

## Requirements

- [Octopus Energy Integration](https://github.com/BottlecapDave/HomeAssistant-OctopusEnergy) providing heat pump sensors
- Emoncms account with API access
