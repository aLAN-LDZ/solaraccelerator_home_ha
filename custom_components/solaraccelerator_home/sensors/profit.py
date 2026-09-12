"""Sensory zysku dziennego i wyceny energii w baterii.

Wartości liczy backend; dane pochodzą z ``coordinator_data["profit"]``
uzupełnianej przez ``async_fetch_profit`` (pętla metryk).
"""
from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from ._base import SolarAcceleratorHomeSensorBase


class SolarAcceleratorHomeDailyProfitSensor(SolarAcceleratorHomeSensorBase):
    _attr_icon = "mdi:cash-multiple"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "PLN"
    _attr_translation_key = "daily_profit"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, coordinator_data: dict[str, Any]) -> None:
        super().__init__(hass, entry, coordinator_data, "daily_profit")
        self._attr_name = "Dzienny zysk"

    @property
    def native_value(self) -> float | None:
        return self.coordinator_data.get("profit", {}).get("daily_profit_pln")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        profit = self.coordinator_data.get("profit", {})
        return {
            "date": profit.get("date"),
            "battery_value_pln": profit.get("battery_value_pln"),
            "battery_avg_price_pln": profit.get("battery_avg_price_pln"),
            "currency": profit.get("currency"),
        }


class SolarAcceleratorHomeBatteryValueSensor(SolarAcceleratorHomeSensorBase):
    _attr_icon = "mdi:battery-charging"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "PLN"
    _attr_translation_key = "battery_value"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, coordinator_data: dict[str, Any]) -> None:
        super().__init__(hass, entry, coordinator_data, "battery_value")
        self._attr_name = "Wartość baterii"

    @property
    def native_value(self) -> float | None:
        return self.coordinator_data.get("profit", {}).get("battery_value_pln")


class SolarAcceleratorHomeBatteryAvgPriceSensor(SolarAcceleratorHomeSensorBase):
    _attr_icon = "mdi:battery-clock"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "PLN/kWh"
    _attr_translation_key = "battery_avg_price"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, coordinator_data: dict[str, Any]) -> None:
        super().__init__(hass, entry, coordinator_data, "battery_avg_price")
        self._attr_name = "Średnia cena baterii"

    @property
    def native_value(self) -> float | None:
        return self.coordinator_data.get("profit", {}).get("battery_avg_price_pln")
