"""Integracja Solar Accelerator Home dla Home Assistant."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import (
    CONF_API_KEY,
    CONF_CONTROLLABLE_DEVICES,
    CONF_ENTITY_MAPPING,
    CONF_EV_ENABLED,
    CONF_EV_PREFIX,
    CONF_SERVER_URL,
    DEFAULT_LIVE_INTERVAL,
    DOMAIN,
    PLATFORMS,
)

LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        CONF_API_KEY: entry.data.get(CONF_API_KEY),
        CONF_SERVER_URL: entry.data.get(CONF_SERVER_URL),
        # EV i mapowanie encji trafiają do entry.options (edytowalne z UI bez
        # ponownego dodawania integracji) — patrz config_flow.py OptionsFlow.
        CONF_EV_ENABLED: entry.options.get(CONF_EV_ENABLED, False),
        CONF_EV_PREFIX: entry.options.get(CONF_EV_PREFIX, ""),
        CONF_ENTITY_MAPPING: entry.options.get(CONF_ENTITY_MAPPING, {}),
        CONF_CONTROLLABLE_DEVICES: entry.options.get(CONF_CONTROLLABLE_DEVICES, []),
        # Stan kanału live (EV + sterowalne odbiorniki)
        "live_status": "inactive",
        "live_last_push": None,
        "live_interval_seconds": DEFAULT_LIVE_INTERVAL,
        "entities_sent": 0,
        # Bufor cen energii — uzupełnia async_fetch_prices, czytają sensory cen
        "prices": {},
        "prices_last_update": None,
        # Bufor zysku dziennego — uzupełnia async_fetch_profit
        "profit": {},
        "profit_last_update": None,
    }

    # Pętle w tle (live push, metryki) startują w sensor.py#async_setup_entry —
    # PLATFORMS zawiera "sensor", więc forward_entry_setups je uruchamia.
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(_async_options_updated))

    return True


async def _async_options_updated(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Przeładuj wpis po zapisaniu opcji (EV, sterowalne odbiorniki)."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
