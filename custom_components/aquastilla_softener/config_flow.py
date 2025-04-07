import logging
from typing import Any, Dict, Optional
from .sensor import async_setup_entry

from homeassistant import config_entries
from homeassistant import core
import voluptuous as vol

from .const import DOMAIN, CONF_USERNAME, CONF_PASSWORD, CONF_DEVICE
from aquastilla_softener import AquastillaSoftener

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA_USER = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


class AquastillaSoftenerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for AquastillaSoftener integration."""

    def __init__(self):
        self.data: Optional[Dict[str, Any]] = None
        self.devices = []

    async def async_step_user(self, user_input: Optional[Dict[str, Any]] = None):
        """Handle user authentication step."""
        errors: Dict[str, str] = {}

        if user_input is not None:
            email = user_input[CONF_USERNAME]
            password = user_input[CONF_PASSWORD]

            # Validate credentials and fetch devices
            try:
                softener = AquastillaSoftener(email=email, password=password)
                self.devices = await self.hass.async_add_executor_job(softener.list_devices)

                if not self.devices:
                    errors["base"] = "no_devices"
                else:
                    self.data = user_input
                    return await self.async_step_select_device()

            except Exception as e:
                _LOGGER.error("Authentication failed: %s", e)
                errors["base"] = "auth_failed"

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA_USER, errors=errors
        )

    async def async_step_select_device(self, user_input: Optional[Dict[str, Any]] = None):
        """Handle device selection step."""
        errors: Dict[str, str] = {}

        if user_input is not None:
            selected_uuid = user_input[CONF_DEVICE]
            selected_device = next(
                (device for device in self.devices if device["uuid"] == selected_uuid), None
            )

            if selected_device:
                await self.async_set_unique_id(selected_uuid)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"{selected_device['model']['model']}",
                    data={**self.data, CONF_DEVICE: selected_device},
                )

            errors["base"] = "device_not_found"

        # Create selection list
        device_choices = {
            device["uuid"]: f"{device['model']['model']} ({device['uuid']})"
            for device in self.devices
        }

        return self.async_show_form(
            step_id="select_device",
            data_schema=vol.Schema({vol.Required(CONF_DEVICE): vol.In(device_choices)}),
            errors=errors,
        )

