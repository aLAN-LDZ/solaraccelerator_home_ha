"""Sensory diagnostyczne kanału live (EV + sterowalne odbiorniki).

Kategoria DIAGNOSTIC — w UI HA pojawiają się w sekcji "Diagnostyka".
"""
from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant

from ..const import DEFAULT_LIVE_INTERVAL
from ._base import SolarAcceleratorHomeSensorBase


class SolarAcceleratorHomeLiveStatusSensor(SolarAcceleratorHomeSensorBase):
    _attr_icon = "mdi:broadcast"
    _attr_translation_key = "live_status"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, coordinator_data: dict[str, Any]) -> None:
        super().__init__(hass, entry, coordinator_data, "live_status")
        self._attr_name = "Status LIVE"

    @property
    def native_value(self) -> str:
        return self.coordinator_data.get("live_status", "inactive")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "live_interval_seconds": self.coordinator_data.get("live_interval_seconds"),
            "live_last_push": self.coordinator_data.get("live_last_push"),
        }


class SolarAcceleratorHomeLiveLastPushSensor(SolarAcceleratorHomeSensorBase):
    _attr_icon = "mdi:clock-fast"
    _attr_translation_key = "live_last_push"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, coordinator_data: dict[str, Any]) -> None:
        super().__init__(hass, entry, coordinator_data, "live_last_push")
        self._attr_name = "Ostatni push LIVE"

    @property
    def native_value(self) -> str | None:
        return self.coordinator_data.get("live_last_push")


class SolarAcceleratorHomeLiveIntervalSensor(SolarAcceleratorHomeSensorBase):
    _attr_icon = "mdi:timer-outline"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "s"
    _attr_translation_key = "live_interval"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, coordinator_data: dict[str, Any]) -> None:
        super().__init__(hass, entry, coordinator_data, "live_interval")
        self._attr_name = "Interwał LIVE"

    @property
    def native_value(self) -> int:
        return self.coordinator_data.get("live_interval_seconds", DEFAULT_LIVE_INTERVAL)


class SolarAcceleratorHomeEntitiesCountSensor(SolarAcceleratorHomeSensorBase):
    """Liczba encji EV ze stanem przy ostatniej wysyłce."""

    _attr_icon = "mdi:counter"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_translation_key = "entities_sent"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, coordinator_data: dict[str, Any]) -> None:
        super().__init__(hass, entry, coordinator_data, "entities_sent")
        self._attr_name = "Wysłane encje EV"

    @property
    def native_value(self) -> int:
        return self.coordinator_data.get("entities_sent", 0)
