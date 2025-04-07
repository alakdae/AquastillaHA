from abc import ABC, abstractmethod
from datetime import datetime, timedelta
import logging
from typing import Optional
from homeassistant.helpers.device_registry import DeviceInfo

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
from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
    SensorEntityDescription,
)
from homeassistant.const import PERCENTAGE, UnitOfVolume

from .const import DOMAIN, CONF_USERNAME, CONF_PASSWORD, CONF_DEVICE

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
    
    sensors = [
        clz(coordinator, device, entity_description)
        for clz, entity_description in (
            (AquastillaSoftenerStateSensor, SensorEntityDescription(key="State", name="State")),
            (AquastillaSoftenerSaltLevelSensor, SensorEntityDescription(
                key="SALT_LEVEL", name="Salt level", state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=PERCENTAGE)),
            (AquastillaSoftenerAvailableWaterSensor, SensorEntityDescription(
                key="AVAILABLE_WATER", name="Available water", state_class=SensorStateClass.TOTAL, device_class=SensorDeviceClass.WATER, icon="mdi:water")),
            (AquastillaSoftenerWaterUsageTodaySensor, SensorEntityDescription(
                key="WATER_USAGE_TODAY", name="Today water usage", state_class=SensorStateClass.TOTAL_INCREASING, device_class=SensorDeviceClass.WATER, icon="mdi:water-minus")),
            (AquastillaSoftenerExpectedRegenerationSensor, SensorEntityDescription(
                key="EXPECTED_REGENERATION_DATE", name="Expected Regeneration Date", device_class=SensorDeviceClass.TIMESTAMP)),
            (AquastillaSoftenerLastRegenerationSensor, SensorEntityDescription(
                key="LAST_REGENERATION", name="Last Regeneration", device_class=SensorDeviceClass.TIMESTAMP)),
        )
    ]

    async_add_entities(sensors)

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


class AquastillaSoftenerSensor(SensorEntity, CoordinatorEntity, ABC):
    def __init__(
        self,
        coordinator: AquastillaSoftenerCoordinator,
        device: dict,
        entity_description: SensorEntityDescription = None,
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


class AquastillaSoftenerStateSensor(AquastillaSoftenerSensor):
    def update(self, data: AquastillaSoftenerData):
        state_map = {
            "deviceStateRegenBrineRefill": "brineRefill",
            "deviceStateRegenSaltDissolve": "saltDissolve",
            "deviceStateRegenBackwash": "backwash",
            "deviceStateRegenBrineCollect": "brineCollect",
            "deviceStateRegenFastwash": "fastWash",
            "deviceStateSoftening": "softening"
        }
        raw_state = data.state.value
        self._attr_native_value = state_map.get(raw_state, raw_state)

class AquastillaSoftenerSaltLevelSensor(AquastillaSoftenerSensor):
    def update(self, data: AquastillaSoftenerData):
        self._attr_native_value = data.salt_level_percent

    @property
    def icon(self) -> Optional[str]:
        if self._attr_native_value is not None:
            if self._attr_native_value > 75:
                return "mdi:signal-cellular-3"
            elif self._attr_native_value > 50:
                return "mdi:signal-cellular-2"
            elif self._attr_native_value > 25:
                return "mdi:signal-cellular-1"
            elif self._attr_native_value > 5:
                return "mdi:signal-cellular-outline"
            return "mdi:signal-off"
        else:
            return "mdi:signal"


class AquastillaSoftenerAvailableWaterSensor(AquastillaSoftenerSensor):
    def update(self, data: AquastillaSoftenerData):
        self._attr_native_value = data.water_available_liters
        self._attr_native_unit_of_measurement = UnitOfVolume.LITERS


class AquastillaSoftenerWaterUsageTodaySensor(AquastillaSoftenerSensor):
    def update(self, data: AquastillaSoftenerData):
        self._attr_native_value = data.today_water_usage_liters
        self._attr_native_unit_of_measurement = UnitOfVolume.LITERS


class AquastillaSoftenerExpectedRegenerationSensor(AquastillaSoftenerSensor):
    def update(self, data: AquastillaSoftenerData):
        self._attr_native_value = data.expected_regeneration_date


class AquastillaSoftenerLastRegenerationSensor(AquastillaSoftenerSensor):
    def update(self, data: AquastillaSoftenerData):
        self._attr_native_value = data.last_regeneration
