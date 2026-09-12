"""Stałe integracji Solar Accelerator Home."""
from __future__ import annotations

DOMAIN = "solaraccelerator_home"

CONF_API_KEY = "api_key"
CONF_SERVER_URL = "server_url"
CONF_ENTITY_MAPPING = "entity_mapping"
CONF_EV_ENABLED = "ev_enabled"
CONF_EV_PREFIX = "ev_prefix"
CONF_EV_MODEL = "ev_model"

# Custom sterowalne odbiorniki (przycisk „Konfiguruj" na karcie integracji).
# Lista słowników: {key, label, device_type, switch_entity, power_sensor,
# energy_sensor, status_entity, nominal_power_w}. Trzymane w entry.options.
CONF_CONTROLLABLE_DEVICES = "controllable_devices"

CONTROLLABLE_DEVICE_TYPES = [
    {"value": "ev", "label": "Ładowarka EV"},
    {"value": "cwu", "label": "CWU / bojler"},
    {"value": "hvac", "label": "Klimatyzacja / pompa ciepła"},
    {"value": "other", "label": "Inne"},
]

SUPPORTED_EV_CHARGERS = [
    {"value": "autel_maxicharger_ac_75kw", "label": "Autel - MaxiChargerAC 7.5KW"},
]

DEFAULT_SERVER_URL = "https://solaraccelerator.cloud"

API_TEST_CONNECTION_ENDPOINT = "/api/homeassistant/test-connection"
API_LIVE_ENDPOINT = "/api/homeassistant/live"

# Interwał startowy — serwer nadpisuje go w odpowiedzi na pierwszy push
DEFAULT_LIVE_INTERVAL = 15
LIVE_DISABLED_RETRY = 60
LIVE_AUTH_RETRY = 300

PLATFORMS: list[str] = []

# Encje ładowarki EV (OCPP) — klucze BEZ prefiksu ev_
EV_ENTITIES = [
    ("status", "Status ładowarki", "-"),
    ("status_connector", "Status połączenia", "-"),
    ("vendor", "Producent ładowarki", "-"),
    ("power_active_import", "Moc ładowania", "kW"),
    ("energy_session", "Energia sesji", "kWh"),
    ("energy_active_import_register", "Licznik energii", "kWh"),
    ("current_import", "Prąd ładowania", "A"),
    ("voltage", "Napięcie", "V"),
    ("time_session", "Czas sesji", "min"),
    ("error_code", "Kod błędu", "-"),
    ("transaction_id", "ID transakcji", "-"),
]
EV_ENTITY_KEYS = [e[0] for e in EV_ENTITIES]


def build_ocpp_entity_mapping(prefix: str) -> dict[str, str]:
    """Zbuduj mapowanie encji ładowarki EV dla integracji OCPP na podstawie prefixu.

    Integracja OCPP (HACS) tworzy encje w schemacie ``sensor.{prefix}_{field}``,
    gdzie ``{prefix}`` to Charge Point ID.
    """
    return {
        "status": f"sensor.{prefix}_status",
        "status_connector": f"sensor.{prefix}_status_connector",
        "vendor": f"sensor.{prefix}_vendor",
        "power_active_import": f"sensor.{prefix}_power_active_import",
        "energy_session": f"sensor.{prefix}_energy_session",
        "energy_active_import_register": f"sensor.{prefix}_energy_active_import_register",
        "current_import": f"sensor.{prefix}_current_import",
        "voltage": f"sensor.{prefix}_voltage",
        "time_session": f"sensor.{prefix}_time_session",
        "error_code": f"sensor.{prefix}_error_code",
        "transaction_id": f"sensor.{prefix}_transaction_id",
    }
