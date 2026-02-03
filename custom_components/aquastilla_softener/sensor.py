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
    
    sensors = [
        clz(coordinator, device, entity_description)
        for clz, entity_description in (
            (AquastillaSoftenerStateSensor, SensorEntityDescription(
                key="State", translation_key="state")),
            (AquastillaSoftenerSaltLevelSensor, SensorEntityDescription(
                key="SALT_LEVEL", translation_key="salt_level", state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=PERCENTAGE)),
            (AquastillaSoftenerAvailableWaterSensor, SensorEntityDescription(
                key="AVAILABLE_WATER", translation_key="available_water", state_class=SensorStateClass.TOTAL, device_class=SensorDeviceClass.WATER, icon="mdi:water")),
            (AquastillaSoftenerWaterUsageTodaySensor, SensorEntityDescription(
                key="WATER_USAGE_TODAY", translation_key="water_usage_today", state_class=SensorStateClass.TOTAL_INCREASING, device_class=SensorDeviceClass.WATER, icon="mdi:water-minus")),
            (AquastillaSoftenerExpectedRegenerationSensor, SensorEntityDescription(
                key="EXPECTED_REGENERATION_DATE", translation_key="expected_regeneration_date", device_class=SensorDeviceClass.TIMESTAMP)),
            (AquastillaSoftenerLastRegenerationSensor, SensorEntityDescription(
                key="LAST_REGENERATION", translation_key="last_regeneration", device_class=SensorDeviceClass.TIMESTAMP)),
            (AquastillaSoftenerSaltDaysRemainingSensor, SensorEntityDescription(
                key="SALT_DAYS_REMAINING", translation_key="salt_days_remaining", state_class=SensorStateClass.MEASUREMENT, icon="mdi:calendar-clock")),
            (AquastillaSoftenerSaltDaysMaxSensor, SensorEntityDescription(
                key="SALT_DAYS_MAX", translation_key="salt_days_max", state_class=SensorStateClass.MEASUREMENT, icon="mdi:calendar-range")),
            (AquastillaSoftenerRegenPercentageSensor, SensorEntityDescription(
                key="REGEN_PERCENTAGE", translation_key="regen_percentage", state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=PERCENTAGE, icon="mdi:restore")),
            (AquastillaSoftenerFirmwareUpgradePercentageSensor, SensorEntityDescription(
                key="FIRMWARE_UPGRADE_PERCENTAGE", translation_key="firmware_upgrade_percentage", state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=PERCENTAGE, icon="mdi:download"))
        )
    ]

    async_add_entities(sensors)

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
            "deviceStateRegenBrineRefill": "brine_refill",
            "deviceStateRegenSaltDissolve": "salt_dissolve",
            "deviceStateRegenBackwash": "backwash",
            "deviceStateRegenBrineCollect": "brine_collect",
            "deviceStateRegenFastwash": "fast_wash",
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


class AquastillaSoftenerSaltDaysRemainingSensor(AquastillaSoftenerSensor):
    def update(self, data: AquastillaSoftenerData):
        self._attr_native_value = data.salt_days_remaining


class AquastillaSoftenerSaltDaysMaxSensor(AquastillaSoftenerSensor):
    def update(self, data: AquastillaSoftenerData):
        self._attr_native_value = data.salt_days_max


class AquastillaSoftenerRegenPercentageSensor(AquastillaSoftenerSensor):
    def update(self, data: AquastillaSoftenerData):
        self._attr_native_value = data.regen_percentage


class AquastillaSoftenerFirmwareUpgradePercentageSensor(AquastillaSoftenerSensor):
    def update(self, data: AquastillaSoftenerData):
        self._attr_native_value = data.firmware_upgrade_percentage

