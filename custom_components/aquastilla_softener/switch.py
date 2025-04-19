import logging
from abc import ABC, abstractmethod
from datetime import timedelta
from typing import Optional

from homeassistant.components.switch import (
    SwitchEntity,
    SwitchEntityDescription,
)
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
)

from homeassistant.core import callback
from homeassistant import config_entries, core

from .const import DOMAIN, CONF_USERNAME, CONF_PASSWORD, CONF_DEVICE
from .coordinator import AquastillaSoftenerCoordinator
from aquastilla_softener import AquastillaSoftener, AquastillaSoftenerData

_LOGGER = logging.getLogger(__name__)
UPDATE_INTERVAL = timedelta(minutes=1)


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
        AquastillaSoftener(config[CONF_USERNAME], config[CONF_PASSWORD]),
        device,
    )

    await coordinator.async_config_entry_first_refresh()

    switches = [
        AquastillaSoftenerVacationModeSwitch(
            coordinator,
            device,
            SwitchEntityDescription(
                key="VACATION_MODE",
                translation_key="vacation_mode",
                icon="mdi:beach",
            )
        )
    ]

    async_add_entities(switches)


class AquastillaSoftenerSwitch(SwitchEntity, CoordinatorEntity, ABC):
    def __init__(
        self,
        coordinator: AquastillaSoftenerCoordinator,
        device: dict,
        entity_description: SwitchEntityDescription,
    ):
        super().__init__(coordinator)
        self.entity_description = entity_description
        self._device = device
        self._attr_unique_id = f"{device['uuid']}_{entity_description.key}"
        self._attr_has_entity_name = True

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        self._handle_coordinator_update()

    @property
    def device_info(self) -> Optional[DeviceInfo]:
        device = self.coordinator._device
        if isinstance(device, dict):
            return DeviceInfo(
                identifiers={(DOMAIN, device["uuid"])},
                name=device["model"]["model"],
                serial_number=device["serial"],
                model=device["model"]["model"],
            )
        return None

    @callback
    def _handle_coordinator_update(self) -> None:
        self.update(self.coordinator.data)
        self.async_write_ha_state()

    @abstractmethod
    def update(self, data: AquastillaSoftenerData):
        ...


class AquastillaSoftenerVacationModeSwitch(AquastillaSoftenerSwitch):
    def update(self, data: AquastillaSoftenerData):
        self._attr_is_on = data.vacation_mode

    async def async_turn_on(self, **kwargs):
        await self.hass.async_add_executor_job(
            self.coordinator.api.set_vacation_mode,
            self._device,
            1
        )
        self._attr_is_on = True
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):
        await self.hass.async_add_executor_job(
            self.coordinator.api.set_vacation_mode,
            self._device,
            0
        )
        self._attr_is_on = False
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()

