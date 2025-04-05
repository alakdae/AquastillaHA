import logging
from typing import Any, Dict, Optional

from homeassistant import config_entries, core
import voluptuous as vol

from .const import DOMAIN, CONF_USERNAME, CONF_PASSWORD
from .aquastilla import AquastillaSoftener

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA_USER = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


class AquastillaSoftenerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for AquastillaSoftener integration."""

    async def async_step_user(self, user_input: Optional[Dict[str, Any]] = None):
        """Handle user step."""
        errors: Dict[str, str] = {}

        if user_input is not None:
            email = user_input[CONF_USERNAME]
            password = user_input[CONF_PASSWORD]

            # Validate credentials
            try:
                softener = AquastillaSoftener(email=email, password=password)
                softener.list_devices()  # Try fetching devices to verify login

                return self.async_create_entry(
                    title="AQUASTILLA DUO SMART", data=user_input
                )

            except Exception as e:
                _LOGGER.error("Authentication failed: %s", e)
                errors["base"] = "auth_failed"

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA_USER, errors=errors
        )

