# Octopus Cosy to Emoncms Integration

A Home Assistant custom integration that sends Octopus Cosy Heat Pump data to Emoncms (heatpumpmonitor.org) in a clean, configurable way.

## Features

- **UI Configuration**: Easy setup through Home Assistant's UI with a config flow
- **Entity Selection**: Choose which heat pump sensors to send to Emoncms
- **Configurable Update Interval**: Set how often data is sent (default: 30 seconds)
- **Automatic Data Collection**: Periodically reads sensor states and sends them to Emoncms
- **Options Flow**: Update settings without recreating the integration

## Installation

### Method 1: Manual Installation

1. Copy the `custom_components/octopus_cosy_emoncms` folder to your Home Assistant `custom_components` directory:
   ```
   <config_dir>/custom_components/octopus_cosy_emoncms/
   ```

2. Restart Home Assistant

3. Add the integration through the UI:
   - Go to **Settings** → **Devices & Services**
   - Click **+ Add Integration**
   - Search for "Octopus Cosy to Emoncms"

### Method 2: HACS (when published)

1. Open HACS
2. Go to Integrations
3. Click the three dots in the top right
4. Select "Custom repositories"
5. Add this repository URL
6. Install "Octopus Cosy to Emoncms"
7. Restart Home Assistant

## Configuration

### Initial Setup

1. **Emoncms URL**: The URL of your Emoncms instance (default: `https://emoncms.org`)
2. **API Key**: Your Emoncms API write key (found in Emoncms under "Input API Help")
3. **Input Node Number**: The node number in Emoncms (default: 303)
4. **Heat Pump Sensors**: Select the sensors you want to send to Emoncms
5. **Update Interval**: How often to send data in seconds (default: 30, min: 10, max: 3600)

> **⚠️ Important**: When naming your node in Emoncms, avoid using `heatpump` or `EmonPi2` as these names are typically reserved for physical hardware sent by heatpumpmonitor.org. Choose a different name like `hp_api`, `octopus_hp`, or similar.

### Recommended Sensors

For Octopus Cosy Heat Pump monitoring, select these types of entities from the [Octopus Energy integration](https://github.com/BottlecapDave/HomeAssistant-OctopusEnergy):

- `sensor.hp_live_outdoor_temp` - Outdoor temperature
- `sensor.hp_mid_room_temperature` - Room temperature
- `sensor.hot_water_hp_current_temperature` - Hot water current temp
- `sensor.hot_water_hp_temperature` - Hot water target temp
- `sensor.heating_hp_current_temperature` - Heating current temp
- `sensor.heating_hp_temperature` - Heating target temp
- `sensor.heating_hp_hvac_action_numeric` - HVAC action (0=off, 1=heating)

You can also include any local sensors that monitor SCOP or other heat pump metrics.

### Updating Configuration

To change which sensors are sent or update the interval:

1. Go to **Settings** → **Devices & Services**
2. Find "Octopus Cosy to Emoncms"
3. Click **Configure**
4. Update your settings
5. Click **Submit**

## How It Works

This integration:

1. Periodically reads the state of your selected sensors
2. Formats the data for Emoncms (numeric values and text states)
3. Sends data to Emoncms using the Input API: `/input/post?node=X&fulljson={data}`
4. Logs success/failure for monitoring

### Data Format

The integration uses your sensor's **friendly name** (the name you see in Home Assistant) and automatically cleans it for Emoncms compatibility:

**Emoncms Restrictions:**
- Reserved characters: `! # $ & ' ( ) * + , / : ; = ? @ [ ]` are removed
- Recommended length: ~10 characters (names are automatically shortened)

**Name Transformations:**
The integration uses the friendly name you set in Home Assistant:
- Friendly name: `"Temperature (middle landing)"` → Emoncms field: `temp_middle_land`
- Friendly name: `"Heat Pump Outdoor Temperature"` → Emoncms field: `hp_out_temp`
- Friendly name: `"Hot Water Current Temperature"` → Emoncms field: `hw_cur_temp`
- Friendly name: `"Heating HVAC Action"` → Emoncms field: `heat_hvac`

The integration automatically:
- Uses your sensor's friendly name (not the cryptic entity ID)
- Converts to lowercase
- Replaces spaces with underscores
- Removes MAC addresses
- Shortens common patterns (`temperature` → `temp`, `current` → `cur`, etc.)
- Strips reserved characters (including parentheses)
- Keeps names Emoncms-friendly

**Tip:** Give your sensors meaningful names in Home Assistant - those names will appear in Emoncms!

### Climate & Water Heater Entities

The integration automatically **expands climate and water_heater entities** into multiple fields:

**Climate entities** (like `climate.octopus_energy_heat_pump_zone_1`):
- Friendly name: `"Heating Zone 1"`
- Sends to Emoncms:
  - `heating_zone_1` → Main state (heat/cool/off)
  - `heating_zone_1_cur_t` → Current temperature
  - `heating_zone_1_target_t` → Target temperature
  - `heating_zone_1_hvac_act` → HVAC action (heating/idle)
  - `heating_zone_1_hvac_mode` → HVAC mode
  - `heating_zone_1_humid` → Current humidity (if available)

**Water heater entities** (like `water_heater.octopus_energy_heat_pump`):
- Friendly name: `"Hot Water"`
- Sends to Emoncms:
  - `hot_water` → Main state
  - `hot_water_cur_t` → Current temperature
  - `hot_water_target_t` → Target temperature
  - `hot_water_mode` → Operation mode

**This eliminates the need for template sensors!** Just add the climate/water_heater entity directly.

Check your Home Assistant logs (debug mode) to see the exact name mappings.

## Comparison with Old Setup

### Old Way (Template + emoncms_history)
```yaml
emoncms_history:
    api_key: xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    url: https://emoncms.org
    inputnode: 302
    whitelist:
        - sensor.hp_live_outdoor_temp
        - sensor.hp_mid_room_temperature
    scan_interval: 30

template:
  - sensor:
      - name: "Heating HP HVAC Action Numeric"
        state: >
          {% if state_attr('climate.octopus_energy_heat_pump_...', 'hvac_action') == 'heating' %}
            1
          {% else %}
            0
          {% endif %}
```

### New Way (This Integration)
1. Add integration via UI
2. Enter Emoncms URL and API key
3. Select sensors from dropdown
4. Done!

No YAML configuration needed, and you can easily modify settings through the UI.

## Troubleshooting

### Check Logs

Enable debug logging by adding to `configuration.yaml`:
```yaml
logger:
  default: info
  logs:
    custom_components.octopus_cosy_emoncms: debug
```

### Common Issues

**Integration not appearing**:
- Make sure you've restarted Home Assistant after copying the files
- Check the logs for errors

**Data not appearing in Emoncms**:
- Verify your API key is correct (it should be the write key, not read key)
- Check that your node number matches what you expect in Emoncms
- Look at Home Assistant logs for API errors

**Sensors not updating**:
- Make sure the Octopus Energy integration is working and providing data
- Check that your selected entities exist and have valid states

## Development

### Project Structure
```
custom_components/octopus_cosy_emoncms/
├── __init__.py           # Integration setup
├── config_flow.py        # UI configuration
├── const.py              # Constants
├── coordinator.py        # Data fetching and API calls
├── manifest.json         # Integration metadata
├── strings.json          # UI strings
└── translations/
    └── en.json           # English translations
```

## Credits

- Built for use with [Octopus Energy Heat Pump Integration](https://github.com/BottlecapDave/HomeAssistant-OctopusEnergy)
- Sends data to [Emoncms](https://emoncms.org) for display on [heatpumpmonitor.org](https://heatpumpmonitor.org)

## License

MIT License - feel free to use and modify as needed.

## Support

For issues, questions, or feature requests, please open an issue on GitHub.
