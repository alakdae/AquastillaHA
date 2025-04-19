import logging
from datetime import timedelta
from typing import Optional

from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from aquastilla_softener import AquastillaSoftener
from homeassistant import config_entries, core

from .const import DOMAIN, CONF_USERNAME, CONF_PASSWORD, CONF_DEVICE
from .coordinator import AquastillaSoftenerCoordinator

_LOGGER = logging.getLogger(__name__)

BUTTON_DESCRIPTIONS = [
    ButtonEntityDescription(
        key="force_regen",
        translation_key="force_regen",
        name="Force Regeneration",
        icon="mdi:refresh",
    ),
    ButtonEntityDescription(
        key="close_valve",
        translation_key="close_valve",
        name="Close valve",
        icon="mdi:valve-closed",
    ),
    ButtonEntityDescription(
        key="postpone_regen",
        translation_key="postpone_regeneration",
        name="Postpone regeneration",
        icon="mdi:clock-plus",
    ),
]


async def async_setup_entry(
    hass: core.HomeAssistant,
    config_entry: config_entries.ConfigEntry,
    async_add_entities,
):
    config = hass.data[DOMAIN][config_entry.entry_id]
    if config_entry.options:
        config.update(config_entry.options)

    device = config[CONF_DEVICE]

    coordinator = AquastillaSoftenerCoordinator(
        hass,
        AquastillaSoftener(
            config[CONF_USERNAME], config[CONF_PASSWORD]
        ),
        device,
    )

    await coordinator.async_config_entry_first_refresh()

    buttons = [
        AquastillaSoftenerButton(coordinator, description)
        for description in BUTTON_DESCRIPTIONS
    ]

    async_add_entities(buttons)


class AquastillaSoftenerButton(CoordinatorEntity, ButtonEntity):
    def __init__(
        self,
        coordinator: AquastillaSoftenerCoordinator,
        description: ButtonEntityDescription,
    ):
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{DOMAIN}_{description.key}_{coordinator._device['uuid']}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator._device["uuid"])},
            "name": coordinator._device["name"],
        }
        self._attr_has_entity_name = True

    async def async_press(self) -> None:
        softener = self.coordinator.api
        device = self.coordinator._device

        try:
            if self.entity_description.key == "force_regen":
                await self.hass.async_add_executor_job(softener.force_regeneration, device)
                _LOGGER.info("Triggered regeneration")
            elif self.entity_description.key == "close_valve":
                await self.hass.async_add_executor_job(softener.close_water_valve, device)
                _LOGGER.info("Closed valve")
            elif self.entity_description.key == "postpone_regen":
                await self.hass.async_add_executor_job(softener.postpone_regeneration, device)
                _LOGGER.info("Postponed regeneration")
        except Exception as e:
            _LOGGER.error("Error handling button press %s: %s", self.entity_description.key, e)

