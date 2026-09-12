"""Sensory cen energii — zakup, sprzedaż i flagi tania/droga energia.

Dane pochodzą z ``coordinator_data["prices"]``, uzupełnianej przez
``async_fetch_prices`` (pętla metryk, co godzinę + na starcie).
"""
from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from ._base import SolarAcceleratorHomeSensorBase


class SolarAcceleratorHomeCurrentBuyPriceSensor(SolarAcceleratorHomeSensorBase):
    _attr_icon = "mdi:cash-minus"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "zł/kWh"
    _attr_translation_key = "current_buy_price"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, coordinator_data: dict[str, Any]) -> None:
        super().__init__(hass, entry, coordinator_data, "current_buy_price")
        self._attr_name = "Cena zakupu energii"

    @property
    def native_value(self) -> float | None:
        return self.coordinator_data.get("prices", {}).get("current_buy_price")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        prices = self.coordinator_data.get("prices", {})
        return {
            "is_cheap": prices.get("is_cheap"),
            "is_expensive": prices.get("is_expensive"),
            "current_hour": prices.get("current_hour"),
            "currency": prices.get("currency"),
            "updated_at": prices.get("updated_at"),
        }


class SolarAcceleratorHomeMinBuyPriceSensor(SolarAcceleratorHomeSensorBase):
    _attr_icon = "mdi:arrow-down-bold"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "zł/kWh"
    _attr_translation_key = "min_buy_price"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, coordinator_data: dict[str, Any]) -> None:
        super().__init__(hass, entry, coordinator_data, "min_buy_price")
        self._attr_name = "Min cena zakupu dziś"

    @property
    def native_value(self) -> float | None:
        return self.coordinator_data.get("prices", {}).get("min_buy_price")


class SolarAcceleratorHomeMaxBuyPriceSensor(SolarAcceleratorHomeSensorBase):
    _attr_icon = "mdi:arrow-up-bold"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "zł/kWh"
    _attr_translation_key = "max_buy_price"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, coordinator_data: dict[str, Any]) -> None:
        super().__init__(hass, entry, coordinator_data, "max_buy_price")
        self._attr_name = "Max cena zakupu dziś"

    @property
    def native_value(self) -> float | None:
        return self.coordinator_data.get("prices", {}).get("max_buy_price")


class SolarAcceleratorHomeAverageBuyPriceSensor(SolarAcceleratorHomeSensorBase):
    _attr_icon = "mdi:chart-line"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "zł/kWh"
    _attr_translation_key = "average_buy_price"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, coordinator_data: dict[str, Any]) -> None:
        super().__init__(hass, entry, coordinator_data, "average_buy_price")
        self._attr_name = "Średnia cena zakupu dziś"

    @property
    def native_value(self) -> float | None:
        return self.coordinator_data.get("prices", {}).get("average_buy_price")


class SolarAcceleratorHomeCurrentSellPriceSensor(SolarAcceleratorHomeSensorBase):
    _attr_icon = "mdi:cash-plus"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "zł/kWh"
    _attr_translation_key = "current_sell_price"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, coordinator_data: dict[str, Any]) -> None:
        super().__init__(hass, entry, coordinator_data, "current_sell_price")
        self._attr_name = "Cena sprzedaży energii"

    @property
    def native_value(self) -> float | None:
        return self.coordinator_data.get("prices", {}).get("current_sell_price")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        prices = self.coordinator_data.get("prices", {})
        return {
            "current_hour": prices.get("current_hour"),
            "currency": prices.get("currency"),
            "updated_at": prices.get("updated_at"),
        }


class SolarAcceleratorHomeMinSellPriceSensor(SolarAcceleratorHomeSensorBase):
    _attr_icon = "mdi:arrow-down-bold"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "zł/kWh"
    _attr_translation_key = "min_sell_price"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, coordinator_data: dict[str, Any]) -> None:
        super().__init__(hass, entry, coordinator_data, "min_sell_price")
        self._attr_name = "Min cena sprzedaży dziś"

    @property
    def native_value(self) -> float | None:
        return self.coordinator_data.get("prices", {}).get("min_sell_price")


class SolarAcceleratorHomeMaxSellPriceSensor(SolarAcceleratorHomeSensorBase):
    _attr_icon = "mdi:arrow-up-bold"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "zł/kWh"
    _attr_translation_key = "max_sell_price"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, coordinator_data: dict[str, Any]) -> None:
        super().__init__(hass, entry, coordinator_data, "max_sell_price")
        self._attr_name = "Max cena sprzedaży dziś"

    @property
    def native_value(self) -> float | None:
        return self.coordinator_data.get("prices", {}).get("max_sell_price")


class SolarAcceleratorHomeAverageSellPriceSensor(SolarAcceleratorHomeSensorBase):
    _attr_icon = "mdi:chart-line"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "zł/kWh"
    _attr_translation_key = "average_sell_price"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, coordinator_data: dict[str, Any]) -> None:
        super().__init__(hass, entry, coordinator_data, "average_sell_price")
        self._attr_name = "Średnia cena sprzedaży dziś"

    @property
    def native_value(self) -> float | None:
        return self.coordinator_data.get("prices", {}).get("average_sell_price")


class SolarAcceleratorHomeIsCheapSensor(SolarAcceleratorHomeSensorBase):
    _attr_icon = "mdi:cash-check"
    _attr_translation_key = "is_cheap"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, coordinator_data: dict[str, Any]) -> None:
        super().__init__(hass, entry, coordinator_data, "is_cheap")
        self._attr_name = "Tania energia"

    @property
    def native_value(self) -> bool | None:
        return self.coordinator_data.get("prices", {}).get("is_cheap")


class SolarAcceleratorHomeIsExpensiveSensor(SolarAcceleratorHomeSensorBase):
    _attr_icon = "mdi:cash-remove"
    _attr_translation_key = "is_expensive"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, coordinator_data: dict[str, Any]) -> None:
        super().__init__(hass, entry, coordinator_data, "is_expensive")
        self._attr_name = "Droga energia"

    @property
    def native_value(self) -> bool | None:
        return self.coordinator_data.get("prices", {}).get("is_expensive")


class SolarAcceleratorHomePriceProviderSensor(SolarAcceleratorHomeSensorBase):
    _attr_icon = "mdi:domain"
    _attr_translation_key = "price_provider"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, coordinator_data: dict[str, Any]) -> None:
        super().__init__(hass, entry, coordinator_data, "price_provider")
        self._attr_name = "Dostawca cen"

    @property
    def native_value(self) -> str | None:
        return self.coordinator_data.get("prices", {}).get("provider")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {"prices_last_update": self.coordinator_data.get("prices_last_update")}
