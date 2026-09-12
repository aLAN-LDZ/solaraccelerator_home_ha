"""Config flow integracji Solar Accelerator Home."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    EntitySelector,
    EntitySelectorConfig,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)
from homeassistant.util import slugify

from .const import (
    API_TEST_CONNECTION_ENDPOINT,
    CONF_API_KEY,
    CONF_CONTROLLABLE_DEVICES,
    CONF_ENTITY_MAPPING,
    CONF_EV_ENABLED,
    CONF_EV_PREFIX,
    CONF_SERVER_URL,
    CONTROLLABLE_DEVICE_TYPES,
    DEFAULT_SERVER_URL,
    DOMAIN,
    build_ocpp_entity_mapping,
)

_LOGGER = logging.getLogger(__name__)


async def async_validate_api_key(
    hass: HomeAssistant,
    api_key: str,
    server_url: str,
) -> dict[str, Any]:
    """Sprawdź klucz API wysyłając GET na endpoint test-connection."""
    try:
        session = async_get_clientsession(hass)
        server_url = server_url.rstrip("/")
        endpoint = f"{server_url}{API_TEST_CONNECTION_ENDPOINT}"

        _LOGGER.debug("Test połączenia: %s", endpoint)

        async with session.get(
            endpoint,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=aiohttp.ClientTimeout(total=30),
        ) as resp:
            text = await resp.text()
            _LOGGER.debug("Odpowiedź API: status=%s, body=%s", resp.status, text[:200])

            if resp.status == 200:
                return {"success": True}
            elif resp.status == 401:
                return {"success": False, "error": "invalid_api_key"}
            elif resp.status == 403:
                return {"success": False, "error": "integration_disabled"}
            else:
                _LOGGER.error("Walidacja API nieudana: %s - %s", resp.status, text)
                return {"success": False, "error": "cannot_connect"}
    except aiohttp.ClientConnectorError as e:
        _LOGGER.error("Błąd połączenia z %s: %s", server_url, e)
        return {"success": False, "error": "cannot_connect"}
    except aiohttp.ClientError as e:
        _LOGGER.error("Błąd klienta HTTP: %s", e)
        return {"success": False, "error": "cannot_connect"}
    except asyncio.TimeoutError:
        _LOGGER.error("Timeout połączenia z %s", server_url)
        return {"success": False, "error": "cannot_connect"}
    except Exception as e:
        _LOGGER.exception("Walidacja API nieudana: %s", e)
        return {"success": False, "error": "unknown"}


class SolarAcceleratorHomeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow Solar Accelerator Home — jeden krok (klucz API + URL).

    Ładowarka EV i sterowalne odbiorniki konfiguruje się później przyciskiem
    „Konfiguruj" na karcie integracji (OptionsFlow) — patrz klasa poniżej.
    """

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> "SolarAcceleratorHomeOptionsFlow":
        return SolarAcceleratorHomeOptionsFlow(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            api_key = user_input.get(CONF_API_KEY, "").strip()
            server_url = user_input.get(CONF_SERVER_URL, DEFAULT_SERVER_URL).strip()

            if not api_key.startswith("sa_haapi_"):
                errors[CONF_API_KEY] = "invalid_api_key_format"
            elif len(api_key) < 40:
                errors[CONF_API_KEY] = "invalid_api_key_format"

            if not server_url.startswith(("http://", "https://")):
                errors[CONF_SERVER_URL] = "invalid_url"

            if not errors:
                result = await async_validate_api_key(self.hass, api_key, server_url)

                if result["success"]:
                    return self.async_create_entry(
                        title="Solar Accelerator Home",
                        data={
                            CONF_API_KEY: api_key,
                            CONF_SERVER_URL: server_url.rstrip("/"),
                        },
                    )
                else:
                    errors["base"] = result.get("error", "cannot_connect")

        schema = vol.Schema({
            vol.Required(CONF_API_KEY): TextSelector(
                TextSelectorConfig(type=TextSelectorType.PASSWORD)
            ),
            vol.Required(CONF_SERVER_URL, default=DEFAULT_SERVER_URL): TextSelector(
                TextSelectorConfig(type=TextSelectorType.URL)
            ),
        })

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)


class SolarAcceleratorHomeOptionsFlow(config_entries.OptionsFlow):
    """Options flow — konfiguracja ładowarki EV i sterowalnych odbiorników.

    Dostępny przez przycisk „Konfiguruj" na karcie integracji. Każda akcja
    zapisuje od razu (jak config flow) — nic nie ginie po zamknięciu okna.
    Nie ustawiamy ``self.config_entry`` (deprecation w nowszych HA) — trzymamy
    własną referencję ``self._entry``.
    """

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._entry = config_entry
        self._devices: list[dict[str, Any]] = list(
            config_entry.options.get(CONF_CONTROLLABLE_DEVICES, [])
        )

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        menu_options = ["ev_charger", "add_device"]
        if self._devices:
            menu_options.append("remove_device")

        return self.async_show_menu(step_id="init", menu_options=menu_options)

    def _save(self, patch: dict[str, Any]) -> FlowResult:
        """Scal zmianę z bieżącymi ``entry.options`` i zakończ flow (wyzwala reload)."""
        data = dict(self._entry.options)
        data.update(patch)
        return self.async_create_entry(title="", data=data)

    async def async_step_ev_charger(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Włącz/wyłącz ładowarkę EV i ustaw prefix integracji OCPP."""
        errors: dict[str, str] = {}
        current_enabled = self._entry.options.get(CONF_EV_ENABLED, False)
        current_prefix = self._entry.options.get(CONF_EV_PREFIX, "")

        if user_input is not None:
            enabled = bool(user_input.get(CONF_EV_ENABLED, False))
            prefix = (user_input.get(CONF_EV_PREFIX) or "").strip().lower()

            if enabled:
                if not prefix:
                    errors[CONF_EV_PREFIX] = "prefix_required"
                elif " " in prefix or not prefix.replace("_", "").isalnum():
                    errors[CONF_EV_PREFIX] = "invalid_prefix"

            if not errors:
                entity_mapping = dict(self._entry.options.get(CONF_ENTITY_MAPPING, {}))
                if enabled:
                    entity_mapping.update(build_ocpp_entity_mapping(prefix))
                return self._save({
                    CONF_EV_ENABLED: enabled,
                    CONF_EV_PREFIX: prefix,
                    CONF_ENTITY_MAPPING: entity_mapping,
                })

        schema = vol.Schema({
            vol.Required(CONF_EV_ENABLED, default=current_enabled): bool,
            vol.Optional(CONF_EV_PREFIX, default=current_prefix): TextSelector(
                TextSelectorConfig(type=TextSelectorType.TEXT)
            ),
        })

        return self.async_show_form(step_id="ev_charger", data_schema=schema, errors=errors)

    async def async_step_add_device(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Formularz dodania jednego sterowalnego odbiornika (encja switch + opcjonalne sensory)."""
        errors: dict[str, str] = {}

        if user_input is not None:
            label = (user_input.get("label") or "").strip()
            switch_entity = user_input.get("switch_entity") or ""
            if not label:
                errors["label"] = "label_required"
            elif not switch_entity:
                errors["switch_entity"] = "entity_required"

            if not errors:
                key = slugify(label) or slugify(switch_entity)
                device = {
                    "key": key,
                    "label": label,
                    "device_type": user_input.get("device_type", "other"),
                    "switch_entity": switch_entity,
                    "power_sensor": user_input.get("power_sensor") or None,
                    "energy_sensor": user_input.get("energy_sensor") or None,
                    "status_entity": user_input.get("status_entity") or None,
                    "nominal_power_w": user_input.get("nominal_power_w"),
                }
                self._devices = [d for d in self._devices if d.get("key") != key]
                self._devices.append(device)
                return self._save({CONF_CONTROLLABLE_DEVICES: self._devices})

        schema = vol.Schema({
            vol.Required("label"): TextSelector(TextSelectorConfig(type=TextSelectorType.TEXT)),
            vol.Required("device_type", default="other"): SelectSelector(
                SelectSelectorConfig(options=CONTROLLABLE_DEVICE_TYPES, mode=SelectSelectorMode.DROPDOWN)
            ),
            vol.Required("switch_entity"): EntitySelector(
                EntitySelectorConfig(domain=["switch", "input_boolean"])
            ),
            vol.Optional("power_sensor"): EntitySelector(
                EntitySelectorConfig(domain=["sensor"])
            ),
            vol.Optional("energy_sensor"): EntitySelector(
                EntitySelectorConfig(domain=["sensor"])
            ),
            vol.Optional("status_entity"): EntitySelector(
                EntitySelectorConfig(domain=["sensor", "binary_sensor"])
            ),
            vol.Optional("nominal_power_w"): NumberSelector(
                NumberSelectorConfig(min=0, max=50000, step=10, mode=NumberSelectorMode.BOX)
            ),
        })

        return self.async_show_form(step_id="add_device", data_schema=schema, errors=errors)

    async def async_step_remove_device(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Usuń zaznaczone urządzenia z listy."""
        if user_input is not None:
            to_remove = set(user_input.get("remove", []))
            self._devices = [d for d in self._devices if d.get("key") not in to_remove]
            return self._save({CONF_CONTROLLABLE_DEVICES: self._devices})

        options = [
            {"value": d.get("key"), "label": f'{d.get("label")} ({d.get("switch_entity")})'}
            for d in self._devices
        ]
        schema = vol.Schema({
            vol.Required("remove", default=[]): SelectSelector(
                SelectSelectorConfig(options=options, multiple=True, mode=SelectSelectorMode.LIST)
            ),
        })

        return self.async_show_form(step_id="remove_device", data_schema=schema)
