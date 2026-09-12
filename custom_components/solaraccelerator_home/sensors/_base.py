"""Klasa bazowa dla wszystkich sensorów Solar Accelerator Home."""
from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo

from ..const import DOMAIN


class SolarAcceleratorHomeSensorBase(SensorEntity):
    """Bazowa klasa sensora — wspólne unique_id i device_info."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        coordinator_data: dict[str, Any],
        sensor_type: str,
    ) -> None:
        self.hass = hass
        self.entry = entry
        self.coordinator_data = coordinator_data
        self.sensor_type = sensor_type
        self._attr_unique_id = f"{entry.entry_id}_{sensor_type}"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self.entry.entry_id)},
            name="Solar Accelerator Home",
            manufacturer="Solar Accelerator",
            model="Home Assistant Integration",
            entry_type=DeviceEntryType.SERVICE,
        )
