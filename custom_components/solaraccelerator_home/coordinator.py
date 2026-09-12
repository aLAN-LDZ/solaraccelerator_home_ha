"""Pętla w tle: szybki push stanu EV/sterowalnych odbiorników.

Interwał jest sterowany przez serwer — startujemy z ``DEFAULT_LIVE_INTERVAL``
i nadpisujemy przy pierwszej odpowiedzi z poprawnym ``live_interval_seconds``.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .api import async_send_live_data
from .const import DEFAULT_LIVE_INTERVAL, LIVE_AUTH_RETRY, LIVE_DISABLED_RETRY

_LOGGER = logging.getLogger(__name__)


async def async_send_live_data_loop(
    hass: HomeAssistant,
    entry: ConfigEntry,
    coordinator_data: dict[str, Any],
) -> None:
    interval = coordinator_data.get("live_interval_seconds", DEFAULT_LIVE_INTERVAL)

    while True:
        try:
            status, server_interval, retry_after = await async_send_live_data(hass, coordinator_data)

            if server_interval:
                interval = server_interval

            if status in ("ok",):
                await asyncio.sleep(interval)
            elif status == "disabled":
                await asyncio.sleep(LIVE_DISABLED_RETRY)
            elif status == "rate_limited":
                wait = max(retry_after or 5, interval)
                await asyncio.sleep(wait)
            elif status == "auth_error":
                await asyncio.sleep(LIVE_AUTH_RETRY)
            else:
                await asyncio.sleep(interval)

        except asyncio.CancelledError:
            _LOGGER.debug("Pętla live anulowana")
            break
        except Exception as e:
            _LOGGER.exception("Nieoczekiwany błąd w pętli live: %s", e)
            await asyncio.sleep(interval)
