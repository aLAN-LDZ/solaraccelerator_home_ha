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
from .coordinator import async_send_live_data_loop

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
        "live_status": "inactive",
        "live_last_push": None,
        "live_interval_seconds": DEFAULT_LIVE_INTERVAL,
        "entities_sent": 0,
    }

    if PLATFORMS:
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_create_background_task(
        hass,
        async_send_live_data_loop(hass, entry, hass.data[DOMAIN][entry.entry_id]),
        f"solaraccelerator_home_live_{entry.entry_id}",
    )

    entry.async_on_unload(entry.add_update_listener(_async_options_updated))

    return True


async def _async_options_updated(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Przeładuj wpis po zapisaniu opcji (EV, sterowalne odbiorniki)."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    if PLATFORMS:
        unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    else:
        unload_ok = True

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)

    return unload_ok
