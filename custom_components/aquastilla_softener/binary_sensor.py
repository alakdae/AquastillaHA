from abc import ABC, abstractmethod
from datetime import datetime, timedelta
import logging
from typing import Optional
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorEntityDescription,
    BinarySensorDeviceClass
)
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
    CoordinatorEntity,
)

from homeassistant.core import callback
from aquastilla_softener import (
    AquastillaSoftener,
    AquastillaSoftenerData,
    AquastillaSoftenerState,
)

from homeassistant import config_entries, core
from homeassistant.const import PERCENTAGE, UnitOfVolume

from .const import DOMAIN, CONF_USERNAME, CONF_PASSWORD, CONF_DEVICE
from .coordinator import AquastillaSoftenerCoordinator

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
        AquastillaSoftener(
            config[CONF_USERNAME], config[CONF_PASSWORD]
        ),
        device,
    )

    await coordinator.async_config_entry_first_refresh()
    
    binary_sensors = [
        clz(coordinator, device, entity_description)
        for clz, entity_description in (
            (AquastillaSoftenerIsOnlineBinarySensor, BinarySensorEntityDescription(
                key="IS_ONLINE", translation_key="is_online", device_class=BinarySensorDeviceClass.CONNECTIVITY)),
            (AquastillaSoftenerIsUpdateBinarySensor, BinarySensorEntityDescription(
                key="IS_UPDATE", translation_key="is_update", icon="mdi:water")),
        )
    ]

    async_add_entities(binary_sensors)


class AquastillaSoftenerBinarySensor(BinarySensorEntity, CoordinatorEntity, ABC):
    def __init__(
        self,
        coordinator: AquastillaSoftenerCoordinator,
        device: dict,
        entity_description: BinarySensorEntityDescription = None,
    ):
        super().__init__(coordinator)
        self.entity_description = entity_description
        self._device = device
        self._attr_unique_id = f"{device['uuid']}_{entity_description.key}"
        self._attr_has_entity_name = True

    async def async_added_to_hass(self) -> None:
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


class AquastillaSoftenerIsOnlineBinarySensor(AquastillaSoftenerBinarySensor):
    def update(self, data: AquastillaSoftenerData):
        self._attr_is_on = data.is_online


class AquastillaSoftenerIsUpdateBinarySensor(AquastillaSoftenerBinarySensor):
    def update(self, data: AquastillaSoftenerData):
        self._attr_is_on = data.is_update

