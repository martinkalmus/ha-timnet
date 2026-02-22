"""Config flow for TimNet Heating Controller integration."""
import logging
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback

_LOGGER = logging.getLogger(__name__)

DOMAIN = "timnet"

CONF_HOST = "host"
CONF_PORT = "port"
CONF_UNIT = "unit"
CONF_SCAN_INTERVAL = "scan_interval"


class TimNetConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for TimNet Heating Controller."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            host = user_input[CONF_HOST]
            port = user_input[CONF_PORT]
            
            try:
                # Test connection
                await self.hass.async_add_executor_job(
                    self._test_connection, host, port, user_input.get(CONF_UNIT, 1)
                )
                
                # Create unique ID based on host
                await self.async_set_unique_id(f"{host}_{port}")
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=f"TimNet ({host})",
                    data=user_input,
                )
            except Exception as err:
                _LOGGER.error("Error connecting to TimNet device: %s", err)
                errors["base"] = "cannot_connect"

        data_schema = vol.Schema(
            {
                vol.Required(CONF_HOST, default="10.0.0.11"): str,
                vol.Required(CONF_PORT, default=502): int,
                vol.Optional(CONF_UNIT, default=1): int,
                vol.Optional(CONF_SCAN_INTERVAL, default=8): int,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )

    def _test_connection(self, host: str, port: int, unit: int):
        """Test connection to the TimNet device."""
        import socket
        import struct
        
        try:
            with socket.create_connection((host, port), timeout=3) as s:
                s.settimeout(3)
                # Try to read 1 holding register at address 0
                pdu = struct.pack(">BHH", 3, 0, 1)
                mbap = struct.pack(">HHHB", 1, 0, len(pdu) + 1, unit)
                s.sendall(mbap + pdu)
                # Read response
                resp = s.recv(4096)
                if len(resp) < 9:
                    raise ConnectionError("Invalid response")
                return True
        except Exception as err:
            _LOGGER.error("Connection test failed: %s", err)
            raise
