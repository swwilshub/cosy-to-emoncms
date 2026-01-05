"""Constants for the Octopus Cosy to Emoncms integration."""
from datetime import timedelta

DOMAIN = "octopus_cosy_emoncms"

# Configuration keys
CONF_EMONCMS_URL = "emoncms_url"
CONF_API_KEY = "api_key"
CONF_NODE_NAME = "node_name"
CONF_ENTITIES = "entities"
CONF_SCAN_INTERVAL = "scan_interval"

# Defaults
DEFAULT_EMONCMS_URL = "https://emoncms.org"
DEFAULT_NODE_NAME = "octopus_hp"
DEFAULT_SCAN_INTERVAL = 30

# Update interval
UPDATE_INTERVAL = timedelta(seconds=DEFAULT_SCAN_INTERVAL)

# Emoncms API endpoint
EMONCMS_INPUT_POST_ENDPOINT = "/input/post"
