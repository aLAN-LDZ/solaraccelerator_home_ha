"""Platforma sensor — punkt wejścia HA dla wszystkich encji Solar Accelerator Home."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import async_fetch_prices, async_fetch_profit
from .const import DOMAIN
from .coordinator import async_fetch_metrics_loop, async_send_live_data_loop
from .sensors import (
    SolarAcceleratorHomeAverageBuyPriceSensor,
    SolarAcceleratorHomeAverageSellPriceSensor,
    SolarAcceleratorHomeBatteryAvgPriceSensor,
    SolarAcceleratorHomeBatteryValueSensor,
    SolarAcceleratorHomeCurrentBuyPriceSensor,
    SolarAcceleratorHomeCurrentSellPriceSensor,
    SolarAcceleratorHomeDailyProfitSensor,
    SolarAcceleratorHomeEntitiesCountSensor,
    SolarAcceleratorHomeIsCheapSensor,
    SolarAcceleratorHomeIsExpensiveSensor,
    SolarAcceleratorHomeLiveIntervalSensor,
    SolarAcceleratorHomeLiveLastPushSensor,
    SolarAcceleratorHomeLiveStatusSensor,
    SolarAcceleratorHomeMaxBuyPriceSensor,
    SolarAcceleratorHomeMaxSellPriceSensor,
    SolarAcceleratorHomeMinBuyPriceSensor,
    SolarAcceleratorHomeMinSellPriceSensor,
    SolarAcceleratorHomePriceProviderSensor,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator_data = hass.data[DOMAIN][entry.entry_id]

    async_add_entities([
        # Ceny zakupu energii
        SolarAcceleratorHomeCurrentBuyPriceSensor(hass, entry, coordinator_data),
        SolarAcceleratorHomeMinBuyPriceSensor(hass, entry, coordinator_data),
        SolarAcceleratorHomeMaxBuyPriceSensor(hass, entry, coordinator_data),
        SolarAcceleratorHomeAverageBuyPriceSensor(hass, entry, coordinator_data),
        # Ceny sprzedaży energii
        SolarAcceleratorHomeCurrentSellPriceSensor(hass, entry, coordinator_data),
        SolarAcceleratorHomeMinSellPriceSensor(hass, entry, coordinator_data),
        SolarAcceleratorHomeMaxSellPriceSensor(hass, entry, coordinator_data),
        SolarAcceleratorHomeAverageSellPriceSensor(hass, entry, coordinator_data),
        # Flagi i metadane cen
        SolarAcceleratorHomeIsCheapSensor(hass, entry, coordinator_data),
        SolarAcceleratorHomeIsExpensiveSensor(hass, entry, coordinator_data),
        SolarAcceleratorHomePriceProviderSensor(hass, entry, coordinator_data),
        # Zysk i bateria
        SolarAcceleratorHomeDailyProfitSensor(hass, entry, coordinator_data),
        SolarAcceleratorHomeBatteryValueSensor(hass, entry, coordinator_data),
        SolarAcceleratorHomeBatteryAvgPriceSensor(hass, entry, coordinator_data),
        # Diagnostyka kanału live
        SolarAcceleratorHomeLiveStatusSensor(hass, entry, coordinator_data),
        SolarAcceleratorHomeLiveLastPushSensor(hass, entry, coordinator_data),
        SolarAcceleratorHomeLiveIntervalSensor(hass, entry, coordinator_data),
        SolarAcceleratorHomeEntitiesCountSensor(hass, entry, coordinator_data),
    ])

    # Pobierz ceny i zysk od razu na starcie — żeby sensory nie świeciły "unknown"
    # przed pierwszym cyklem pętli metryk.
    entry.async_create_background_task(
        hass, async_fetch_prices(hass, coordinator_data), "sa_home_fetch_prices_init"
    )
    entry.async_create_background_task(
        hass, async_fetch_profit(hass, coordinator_data), "sa_home_fetch_profit_init"
    )

    # Pętla metryk — ceny i zysk co godzinę.
    entry.async_create_background_task(
        hass,
        async_fetch_metrics_loop(hass, entry, coordinator_data),
        "sa_home_fetch_metrics_loop",
    )

    # Pętla live — EV + sterowalne odbiorniki. Startowana tutaj (nie w __init__.py),
    # żeby nie dublować jej gdy PLATFORMS puste na wcześniejszych wersjach configu.
    entry.async_create_background_task(
        hass,
        async_send_live_data_loop(hass, entry, coordinator_data),
        "sa_home_send_live_data_loop",
    )
