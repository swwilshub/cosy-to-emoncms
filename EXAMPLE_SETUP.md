# Example Setup Guide

This guide shows you how to migrate from your current template-based setup to the new integration.

## Current Setup (to be replaced)

Your current `configuration.yaml` has:

```yaml
emoncms_history:
    api_key: xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    url: https://emoncms.org
    inputnode: 302
    whitelist:
        - sensor.hp_live_outdoor_temp
        - sensor.hp_mid_room_temperature
        - sensor.hot_water_hp_current_temperature
        - sensor.hot_water_hp_temperature
        - sensor.heating_hp_current_temperature
        - sensor.heating_hp_temperature
        - sensor.heating_hp_hvac_action_numeric
    scan_interval: 30

template:
  - sensor:
      - name: "Heating HP HVAC Action Numeric"
        state: >
          {% if state_attr('climate.octopus_energy_heat_pump_DEVICE_ID_zone_1', 'hvac_action') == 'heating' %}
            1
          {% else %}
            0
          {% endif %}
        unit_of_measurement: "bool"
      # ... more template sensors
```

## Migration Steps

### Step 1: Install the Integration

1. Copy `custom_components/octopus_cosy_emoncms` to your Home Assistant config directory
2. Restart Home Assistant
3. The integration will now be available

### Step 2: Keep Your Template Sensors (Important!)

**Do NOT remove** your template sensors from `configuration.yaml`. The integration will read their values.

Keep this template sensor:
```yaml
template:
  - sensor:
      - name: "Heating HP HVAC Action Numeric"
        state: >
          {% if state_attr('climate.octopus_energy_heat_pump_DEVICE_ID_zone_1', 'hvac_action') == 'heating' %}
            1
          {% else %}
            0
          {% endif %}
        unit_of_measurement: "bool"
```

### Step 3: Add the Integration

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for "Octopus Cosy to Emoncms"
4. Fill in the form:
   - **Emoncms URL**: `https://emoncms.org`
   - **API Key**: Your API key from Emoncms (the write key)
   - **Input Node Number**: `303` (or choose any available node number)
   - **Heat Pump Sensors**: Select these entities:
     - `sensor.hp_live_outdoor_temp`
     - `sensor.hp_mid_room_temperature`
     - `sensor.hot_water_hp_current_temperature`
     - `sensor.hot_water_hp_temperature`
     - `sensor.heating_hp_current_temperature`
     - `sensor.heating_hp_temperature`
     - `sensor.heating_hp_hvac_action_numeric`
   - **Update Interval**: `30` seconds

5. Click **Submit**

### Step 4: Remove Old Configuration (Optional)

Once you've verified the new integration is working:

1. **Remove** the `emoncms_history` section from `configuration.yaml`
2. **Keep** the template sensors (they're still needed!)
3. Restart Home Assistant

## Verifying It Works

### Check Home Assistant Logs

Enable debug logging:
```yaml
logger:
  default: info
  logs:
    custom_components.octopus_cosy_emoncms: debug
```

You should see messages like:
```
Successfully sent data to Emoncms: {'hp_live_outdoor_temp': 5.2, 'hp_mid_room_temperature': 20.4, ...}
```

### Check Emoncms

1. Log into your Emoncms instance
2. Go to **Inputs**
3. Look for node `303` (or whatever node number you configured)
4. You should see your sensor data updating every 30 seconds

## Adding More Sensors

You can add any sensor to send to Emoncms:

1. Go to **Settings** → **Devices & Services**
2. Find "Octopus Cosy to Emoncms"
3. Click **Configure**
4. Add or remove entities from the list
5. Click **Submit**

For example, if you have a local device monitoring SCOP:
- `sensor.electric_power`
- `sensor.heatmeter_power`
- `sensor.heatmeter_flow_rate`
- etc.

## Emoncms Input Node Structure

The integration sends data in this format to Emoncms:

```
/input/post?node=303&fulljson={"hp_live_outdoor_temp":5.2,"hp_mid_room_temperature":20.4,...}
```

In Emoncms, you'll see these fields under node 303 (or your configured node):
- `hp_live_outdoor_temp`
- `hp_mid_room_temperature`
- `hot_water_hp_current_temperature`
- `hot_water_hp_temperature`
- `heating_hp_current_temperature`
- `heating_hp_temperature`
- `heating_hp_hvac_action_numeric`

You can then configure these in Emoncms to:
- Log to feeds
- Apply processing (e.g., `log to feed`, `x + > 0 <max`, etc.)
- Display on [heatpumpmonitor.org](https://heatpumpmonitor.org)

> **⚠️ Important Node Naming**: When naming your node in Emoncms, **avoid using `heatpump` or `EmonPi2`**. These names are typically reserved for physical hardware devices sent by heatpumpmonitor.org (like the EmonPi monitoring equipment). Instead, use a descriptive name like:
> - `hp_api`
> - `octopus_hp`
> - `ha_heatpump`
> - `cosy_integration`
>
> This prevents conflicts if you also have physical monitoring hardware installed.

## Troubleshooting

**"Entity not found" warnings in logs**:
- Make sure the Octopus Energy integration is installed and configured
- Check that your template sensors are defined in `configuration.yaml`
- Verify entity IDs match exactly (check in Developer Tools → States)

**Data not appearing in Emoncms**:
- Verify API key is correct (use the **write** key, not read key)
- Check node number matches your Emoncms setup
- Look for error messages in Home Assistant logs

**Update interval too slow/fast**:
- Change the scan interval in the integration options
- Minimum is 10 seconds, maximum is 3600 seconds (1 hour)
