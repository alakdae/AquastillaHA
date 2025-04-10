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

from homeassistant.core import callback
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
    CoordinatorEntity,
)

from aquastilla_softener import (
    AquastillaSoftener,
    AquastillaSoftenerData,
    AquastillaSoftenerState,
)

from homeassistant import config_entries, core
from homeassistant.const import PERCENTAGE, UnitOfVolume

from .const import DOMAIN, CONF_USERNAME, CONF_PASSWORD, CONF_DEVICE

_LOGGER = logging.getLogger(__name__)

UPDATE_INTERVAL = timedelta(minutes=1)


class AquastillaSoftenerCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: core.HomeAssistant, softener: AquastillaSoftener, device: dict):
        super().__init__(
            hass,
            _LOGGER,
            name="Aquastilla Softener",
            update_interval=UPDATE_INTERVAL,
        )
        self._softener = softener
        self._device = device
        self.device_data: Optional[AquastillaSoftenerData] = None  # type hint

    async def _async_update_data(self) -> AquastillaSoftenerData:
        try:
            data = await self.hass.async_add_executor_job(
                self._softener.get_device_data, self._device
            )
            self.device_data = data
            _LOGGER.debug("Fetched data: %s", data)
            return data
        except Exception as err:
            raise UpdateFailed(f"Get data failed: {err}")


