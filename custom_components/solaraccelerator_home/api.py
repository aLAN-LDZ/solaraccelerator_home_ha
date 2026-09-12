"""Klient HTTP do komunikacji z backendem Solar Accelerator.

Integracja Home nie ma nic wspólnego z falownikiem — wysyła tylko stan
ładowarki EV i sterowalnych odbiorników kanałem live. Backend rozróżnia
klienta po kluczu API (provider), nie po zawartości payloadu.
"""
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
    API_LIVE_ENDPOINT,
    EV_ENTITY_KEYS,
)
from .helpers import convert_value

_LOGGER = logging.getLogger(__name__)


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
    """Zbuduj payload live pushu. Zwraca (payload, entities_count).

    Brak sekcji ``inverter`` i pola ``inverterOnline`` — Home nigdy nie
    raportuje falownika, więc backend traktuje to tak, jakby był online
    (domyślne zachowanie starszego klienta), bez wpływu na status komunikacji
    falownika utrzymywany przez inną integrację na tym samym site.
    """
    payload: dict[str, Any] = {"timestamp": dt_util.utcnow().isoformat()}
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
) -> tuple[str, int | None, int | None]:
    """Wyślij szybki push stanu na endpoint ``/api/homeassistant/live``.

    Zwraca ``(status, live_interval_seconds, retry_after_seconds)``, gdzie
    ``status`` to ``ok`` / ``disabled`` / ``rate_limited`` / ``auth_error`` / ``error``.
    Home nigdy nie wykonuje komend zwrotnych — ``pending_commands`` w
    odpowiedzi jest ignorowane (backend go i tak nie wysyła dla tego providera).
    """
    api_key = coordinator_data.get(CONF_API_KEY)
    server_url = coordinator_data.get(CONF_SERVER_URL)

    session = async_get_clientsession(hass)
    endpoint = f"{server_url}{API_LIVE_ENDPOINT}"

    payload, entities_count = _build_live_payload(hass, coordinator_data)
    if "entities" not in payload and "controllable_devices" not in payload:
        # Nic do wysłania (EV niewłączone i brak sterowalnych odbiorników)
        return ("ok", None, None)

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
                return ("ok", live_interval, None)

            elif resp.status == 503:
                coordinator_data["live_status"] = "disabled"
                return ("disabled", None, None)

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
                return ("rate_limited", live_interval, retry_after)

            elif resp.status == 401:
                coordinator_data["live_status"] = "auth_error"
                _LOGGER.error("Live push: nieprawidłowy klucz API (401)")
                return ("auth_error", None, None)

            else:
                coordinator_data["live_status"] = "error"
                text = await resp.text()
                _LOGGER.error("Live push nieudany: %s - %s", resp.status, text[:100])
                return ("error", None, None)

    except aiohttp.ClientError as e:
        coordinator_data["live_status"] = "error"
        _LOGGER.warning("Live push: błąd połączenia: %s", e)
        return ("error", None, None)
    except Exception as e:
        coordinator_data["live_status"] = "error"
        _LOGGER.exception("Live push: nieoczekiwany błąd: %s", e)
        return ("error", None, None)
