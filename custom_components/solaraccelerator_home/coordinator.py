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

from .api import (
    async_ack_command,
    async_execute_command,
    async_fetch_prices,
    async_fetch_profit,
    async_send_live_data,
)
from .const import DEFAULT_LIVE_INTERVAL, LIVE_AUTH_RETRY, LIVE_DISABLED_RETRY, METRICS_FETCH_INTERVAL

_LOGGER = logging.getLogger(__name__)


async def async_fetch_metrics_loop(
    hass: HomeAssistant,
    entry: ConfigEntry,
    coordinator_data: dict[str, Any],
) -> None:
    """Pętla odświeżająca ceny i zysk co ``METRICS_FETCH_INTERVAL`` sekund.

    W przeciwieństwie do kanału live (EV), metryki nie muszą być pushowane
    przez Home — backend liczy je niezależnie od tej integracji. Wystarczy
    je okresowo odpytać.
    """
    while True:
        try:
            await async_fetch_prices(hass, coordinator_data)
            await async_fetch_profit(hass, coordinator_data)
        except asyncio.CancelledError:
            _LOGGER.debug("Pętla metryk anulowana")
            break
        except Exception as e:
            _LOGGER.exception("Błąd w pętli metryk: %s", e)

        try:
            await asyncio.sleep(METRICS_FETCH_INTERVAL)
        except asyncio.CancelledError:
            break


async def async_send_live_data_loop(
    hass: HomeAssistant,
    entry: ConfigEntry,
    coordinator_data: dict[str, Any],
) -> None:
    interval = coordinator_data.get("live_interval_seconds", DEFAULT_LIVE_INTERVAL)

    while True:
        try:
            status, server_interval, retry_after, pending_commands = await async_send_live_data(
                hass, coordinator_data
            )

            if server_interval:
                interval = server_interval

            if status == "ok":
                # Komendy dla sterowalnych odbiorników (EV/CWU/inne) — wykonaj i ACK
                # od razu, bez kolejki/opóźnień jak przy falowniku (zwykły switch call).
                for cmd in pending_commands:
                    success, error = await async_execute_command(hass, cmd)
                    await async_ack_command(hass, coordinator_data, cmd["id"], success, error)
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
