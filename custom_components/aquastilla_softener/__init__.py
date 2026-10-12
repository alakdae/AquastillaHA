import logging
import asyncio
from homeassistant import config_entries, core
from aquastilla_softener import AquastillaSoftener
from .const import DOMAIN, CONF_USERNAME, CONF_PASSWORD, CONF_DEVICE
from .coordinator import AquastillaSoftenerCoordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: core.HomeAssistant, entry: config_entries.ConfigEntry
) -> bool:
    hass.data.setdefault(DOMAIN, {})
    hass_data = dict(entry.data)
    hass_data.update(entry.options)

    coordinator = AquastillaSoftenerCoordinator(
        hass,
        AquastillaSoftener(hass_data[CONF_USERNAME], hass_data[CONF_PASSWORD]),
        hass_data[CONF_DEVICE],
    )
    # Raises ConfigEntryNotReady on failure so HA retries (e.g. network not up after boot)
    await coordinator.async_config_entry_first_refresh()
    hass_data["coordinator"] = coordinator

    unsub_options_update_listener = entry.add_update_listener(options_update_listener)
    hass_data["unsub_options_update_listener"] = unsub_options_update_listener
    hass.data[DOMAIN][entry.entry_id] = hass_data

    await hass.config_entries.async_forward_entry_setups(entry, ["sensor", "binary_sensor", "switch", "button"])

    return True


async def options_update_listener(
    hass: core.HomeAssistant, config_entry: config_entries.ConfigEntry
):
    await hass.config_entries.async_reload(config_entry.entry_id)


async def async_unload_entry(
    hass: core.HomeAssistant, entry: config_entries.ConfigEntry
) -> bool:
    unload_ok = all(await asyncio.gather(
        hass.config_entries.async_forward_entry_unload(entry, "sensor"),
        hass.config_entries.async_forward_entry_unload(entry, "binary_sensor"),
        hass.config_entries.async_forward_entry_unload(entry, "switch"),
        hass.config_entries.async_forward_entry_unload(entry, "button"),
    ))

    hass.data[DOMAIN][entry.entry_id]["unsub_options_update_listener"]()

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
