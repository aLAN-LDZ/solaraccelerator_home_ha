"""Klient HTTP do komunikacji z backendem Solar Accelerator."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.util import dt as dt_util

from .const import (
    CONF_API_KEY,
    CONF_CONTROLLABLE_DEVICES,
    CONF_ENTITY_MAPPING,
    CONF_EV_ENABLED,
    CONF_EV_PREFIX,
    CONF_SERVER_URL,
    API_COMMAND_ACK_ENDPOINT,
    API_LIVE_ENDPOINT,
    API_PRICES_ENDPOINT,
    API_PROFIT_ENDPOINT,
    EV_ENTITY_KEYS,
)
from .helpers import convert_value

_LOGGER = logging.getLogger(__name__)


async def async_fetch_prices(hass: HomeAssistant, coordinator_data: dict[str, Any]) -> bool:
    """Pobierz aktualne ceny energii (zakup + sprzedaż) z backendu.

    Wynik trafia do ``coordinator_data["prices"]``. Status 404 (serwer nie ma
    jeszcze cen na dziś) jest tylko logowany — nie nullujemy starych wartości.
    """
    api_key = coordinator_data.get(CONF_API_KEY)
    server_url = coordinator_data.get(CONF_SERVER_URL)
    session = async_get_clientsession(hass)
    endpoint = f"{server_url}{API_PRICES_ENDPOINT}"

    try:
        async with session.get(
            endpoint,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=aiohttp.ClientTimeout(total=30),
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                coordinator_data["prices"] = {
                    "current_buy_price": data.get("current_buy_price"),
                    "min_buy_price": data.get("min_buy_price"),
                    "max_buy_price": data.get("max_buy_price"),
                    "average_buy_price": data.get("average_buy_price"),
                    "current_sell_price": data.get("current_sell_price"),
                    "min_sell_price": data.get("min_sell_price"),
                    "max_sell_price": data.get("max_sell_price"),
                    "average_sell_price": data.get("average_sell_price"),
                    "currency": data.get("currency"),
                    "unit": data.get("unit"),
                    "current_hour": data.get("current_hour"),
                    "is_cheap": data.get("is_cheap"),
                    "is_expensive": data.get("is_expensive"),
                    "provider": data.get("provider"),
                    "updated_at": data.get("updated_at"),
                }
                coordinator_data["prices_last_update"] = dt_util.now().strftime("%Y-%m-%d %H:%M:%S")
                return True
            elif resp.status == 404:
                _LOGGER.warning("Brak dostępnych cen energii: %s", await resp.text())
            else:
                _LOGGER.error("Nie udało się pobrać cen: %s", resp.status)
    except aiohttp.ClientError as e:
        _LOGGER.error("Błąd połączenia podczas pobierania cen: %s", e)
    except Exception as e:
        _LOGGER.exception("Błąd podczas pobierania cen: %s", e)

    return False


async def async_fetch_profit(hass: HomeAssistant, coordinator_data: dict[str, Any]) -> bool:
    """Pobierz dzienny bilans finansowy instalacji PV z backendu.

    Zapisuje do ``coordinator_data["profit"]`` — czytają sensory daily_profit,
    battery_value, battery_avg_price.
    """
    api_key = coordinator_data.get(CONF_API_KEY)
    server_url = coordinator_data.get(CONF_SERVER_URL)
    session = async_get_clientsession(hass)
    endpoint = f"{server_url}{API_PROFIT_ENDPOINT}"

    try:
        async with session.get(
            endpoint,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=aiohttp.ClientTimeout(total=30),
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                coordinator_data["profit"] = {
                    "date": data.get("date"),
                    "daily_profit_pln": data.get("daily_profit_pln"),
                    "battery_value_pln": data.get("battery_value_pln"),
                    "battery_avg_price_pln": data.get("battery_avg_price_pln"),
                    "currency": data.get("currency"),
                }
                coordinator_data["profit_last_update"] = dt_util.now().strftime("%Y-%m-%d %H:%M:%S")
                return True
            elif resp.status == 404:
                _LOGGER.warning("Brak danych o zysku: %s", await resp.text())
            else:
                _LOGGER.error("Nie udało się pobrać zysku: %s", resp.status)
    except aiohttp.ClientError as e:
        _LOGGER.error("Błąd połączenia podczas pobierania zysku: %s", e)
    except Exception as e:
        _LOGGER.exception("Błąd podczas pobierania zysku: %s", e)

    return False


def _build_ev_payload(hass: HomeAssistant, coordinator_data: dict[str, Any]) -> dict[str, Any]:
    """Zbierz stan encji ładowarki EV zmapowanych w OptionsFlow."""
    entity_mapping = coordinator_data.get(CONF_ENTITY_MAPPING, {})
    ev_data: dict[str, Any] = {}

    for entity_key in EV_ENTITY_KEYS:
        ha_entity_id = entity_mapping.get(entity_key)
        state = hass.states.get(ha_entity_id) if ha_entity_id else None
        ev_data[entity_key] = convert_value(state.state, entity_key) if state else 0

    return ev_data


def _build_controllable_payload(hass: HomeAssistant, coordinator_data: dict[str, Any]) -> list[dict[str, Any]]:
    """Zbierz definicje sterowalnych odbiorników + bieżący stan ich encji."""
    devices = coordinator_data.get(CONF_CONTROLLABLE_DEVICES) or []
    out: list[dict[str, Any]] = []

    for dev in devices:
        switch_entity = dev.get("switch_entity")
        switch_state = None
        if switch_entity and (st := hass.states.get(switch_entity)):
            switch_state = st.state

        entry: dict[str, Any] = {
            "key": dev.get("key"),
            "label": dev.get("label"),
            "device_type": dev.get("device_type", "other"),
            "switch_entity": switch_entity,
            "switch_state": switch_state,
            "power_sensor": dev.get("power_sensor"),
            "energy_sensor": dev.get("energy_sensor"),
            "status_entity": dev.get("status_entity"),
            "nominal_power_w": dev.get("nominal_power_w"),
        }

        for field, sensor_key in (("power_w", "power_sensor"), ("energy_kwh", "energy_sensor"), ("status", "status_entity")):
            sensor_id = dev.get(sensor_key)
            if sensor_id and (s := hass.states.get(sensor_id)):
                entry[field] = s.state

        out.append(entry)

    return out


def _build_live_payload(hass: HomeAssistant, coordinator_data: dict[str, Any]) -> tuple[dict[str, Any], int]:
    """Zbuduj payload live pushu. Zwraca (payload, entities_count)."""
    payload: dict[str, Any] = {"timestamp": dt_util.utcnow().isoformat(), "prefix": "home"}
    entities_count = 0

    ev_enabled = bool(coordinator_data.get(CONF_EV_ENABLED) and coordinator_data.get(CONF_EV_PREFIX))
    entities: dict[str, Any] = {}
    if ev_enabled:
        ev_data = _build_ev_payload(hass, coordinator_data)
        entities["ev_charger"] = ev_data
        entities_count += sum(1 for v in ev_data.values() if v != 0)
        payload["evPrefix"] = coordinator_data.get(CONF_EV_PREFIX, "")

    if entities:
        payload["entities"] = entities

    controllable = _build_controllable_payload(hass, coordinator_data)
    if controllable:
        payload["controllable_devices"] = controllable

    return payload, entities_count


async def async_send_live_data(
    hass: HomeAssistant,
    coordinator_data: dict[str, Any],
) -> tuple[str, int | None, int | None, list[dict[str, Any]]]:
    """Wyślij szybki push stanu na endpoint ``/api/homeassistant/live``.

    Zwraca ``(status, live_interval_seconds, retry_after_seconds, pending_commands)``,
    gdzie ``status`` to ``ok`` / ``disabled`` / ``rate_limited`` / ``auth_error`` / ``error``.
    """
    api_key = coordinator_data.get(CONF_API_KEY)
    server_url = coordinator_data.get(CONF_SERVER_URL)

    session = async_get_clientsession(hass)
    endpoint = f"{server_url}{API_LIVE_ENDPOINT}"

    payload, entities_count = _build_live_payload(hass, coordinator_data)
    # Push zawsze, nawet z pustym payloadem (heartbeat).

    try:
        async with session.post(
            endpoint,
            json=payload,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=aiohttp.ClientTimeout(total=15),
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                live_interval = data.get("live_interval_seconds")
                coordinator_data["live_status"] = "live"
                coordinator_data["live_last_push"] = dt_util.now().strftime("%Y-%m-%d %H:%M:%S")
                coordinator_data["entities_sent"] = entities_count
                if live_interval:
                    coordinator_data["live_interval_seconds"] = live_interval
                pending_commands = data.get("pending_commands", []) or []
                return ("ok", live_interval, None, pending_commands)

            elif resp.status == 503:
                coordinator_data["live_status"] = "disabled"
                return ("disabled", None, None, [])

            elif resp.status == 429:
                coordinator_data["live_status"] = "rate_limited"
                retry_after = int(resp.headers.get("Retry-After", "5"))
                live_interval = None
                try:
                    data = await resp.json()
                    if server_iv := data.get("live_interval_seconds"):
                        live_interval = server_iv
                        coordinator_data["live_interval_seconds"] = server_iv
                except Exception:
                    pass
                return ("rate_limited", live_interval, retry_after, [])

            elif resp.status == 401:
                coordinator_data["live_status"] = "auth_error"
                _LOGGER.error("Live push: nieprawidłowy klucz API (401)")
                return ("auth_error", None, None, [])

            else:
                coordinator_data["live_status"] = "error"
                text = await resp.text()
                _LOGGER.error("Live push nieudany: %s - %s", resp.status, text[:100])
                return ("error", None, None, [])

    except aiohttp.ClientError as e:
        coordinator_data["live_status"] = "error"
        _LOGGER.warning("Live push: błąd połączenia: %s", e)
        return ("error", None, None, [])
    except Exception as e:
        coordinator_data["live_status"] = "error"
        _LOGGER.exception("Live push: nieoczekiwany błąd: %s", e)
        return ("error", None, None, [])


async def async_execute_command(hass: HomeAssistant, command: dict[str, Any]) -> tuple[bool, str | None]:
    """Wykonaj jedną komendę switch na sterowalnym odbiorniku."""
    try:
        await hass.services.async_call(
            command["domain"],
            command["service"],
            {"entity_id": command["entity_id"], **command.get("service_data", {})},
            blocking=True,
        )
        return True, None
    except Exception as e:
        _LOGGER.error("Wykonanie komendy %s nieudane: %s", command.get("id"), e)
        return False, str(e)[:200]


async def async_ack_command(
    hass: HomeAssistant,
    coordinator_data: dict[str, Any],
    cmd_id: str,
    success: bool,
    error: str | None,
) -> None:
    """Potwierdź serwerowi wykonanie komendy — bez ACK backend poda ją znowu."""
    api_key = coordinator_data.get(CONF_API_KEY)
    server_url = coordinator_data.get(CONF_SERVER_URL)
    session = async_get_clientsession(hass)
    endpoint = f"{server_url}{API_COMMAND_ACK_ENDPOINT.replace('{id}', cmd_id)}"

    try:
        async with session.post(
            endpoint,
            json={"success": success, "error": error},
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=aiohttp.ClientTimeout(total=10),
        ) as resp:
            if resp.status != 200:
                text = await resp.text()
                _LOGGER.warning("ACK dla %s nieudany: %s - %s", cmd_id, resp.status, text[:100])
    except Exception as e:
        _LOGGER.warning("ACK dla %s: błąd połączenia: %s", cmd_id, e)
