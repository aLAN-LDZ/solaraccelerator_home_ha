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

# Pompy ciepła (krok „Pompa ciepła" w Konfiguruj). Lista słowników:
# {key, label, source, prefix, roles: {rola: encja | [encje]}}. Trzymane w entry.options.
CONF_HEAT_PUMPS = "heat_pumps"

HEAT_PUMP_SOURCE_HEISHAMON = "heishamon"
HEAT_PUMP_SOURCE_MANUAL = "manual"
HEISHAMON_DEFAULT_PREFIX = "panasonic_heat_pump"

# Typy ról: jak czytać stan encji i jakie domeny pokazać w wyborze.
ROLE_NUMBER = "number"   # liczba (moc, temperatura, licznik)
ROLE_BOOL = "bool"       # on/off (defrost, grzałka, sterylizacja)
ROLE_TEXT = "text"       # surowy stan tekstowy (tryb pracy, sezon)

# Rola → (typ, wiele encji sumowanych?, jednostka docelowa, sekcja formularza).
# Każda rola jest opcjonalna — nie każda pompa wystawia wszystko; brak roli = brak
# danej statystyki, nie błąd. Jednostka docelowa: moc w W, energia w kWh.
HEAT_PUMP_ROLES: dict[str, tuple[str, bool, str | None, str]] = {
    # Pomiar poboru całego urządzenia — licznik zewnętrzny (1–3 fazy) albo moc.
    "meter_energy_kwh": (ROLE_NUMBER, True, "kWh", "measurement"),
    "meter_power_w": (ROLE_NUMBER, True, "W", "measurement"),
    "power_w": (ROLE_NUMBER, False, "W", "measurement"),
    # Pobór wg trybu pracy — podział na CO i CWU.
    "co_power_w": (ROLE_NUMBER, False, "W", "modes"),
    "cwu_power_w": (ROLE_NUMBER, False, "W", "modes"),
    "mode": (ROLE_TEXT, False, None, "modes"),
    # Sezon grzewczy i odszranianie.
    "season": (ROLE_TEXT, False, None, "season_defrost"),
    "defrost": (ROLE_BOOL, False, None, "season_defrost"),
    # Ciepło oddane i obieg wody.
    "co_heat_w": (ROLE_NUMBER, False, "W", "heat"),
    "cwu_heat_w": (ROLE_NUMBER, False, "W", "heat"),
    "flow_lpm": (ROLE_NUMBER, False, None, "heat"),
    "supply_temp_c": (ROLE_NUMBER, False, None, "heat"),
    "return_temp_c": (ROLE_NUMBER, False, None, "heat"),
    # Ciepła woda użytkowa.
    "dhw_temp_c": (ROLE_NUMBER, False, None, "dhw"),
    "dhw_target_temp_c": (ROLE_NUMBER, False, None, "dhw"),
    "sterilization": (ROLE_BOOL, False, None, "dhw"),
    # Sprężarka, grzałka, czujnik zewnętrzny.
    "compressor_hz": (ROLE_NUMBER, False, None, "compressor"),
    "operations_counter": (ROLE_NUMBER, False, None, "compressor"),
    "operations_hours": (ROLE_NUMBER, False, None, "compressor"),
    "heater": (ROLE_BOOL, False, None, "compressor"),
    "outside_temp_c": (ROLE_NUMBER, False, None, "compressor"),
    # Ustawienia sterownika (krzywa grzewcza, progi).
    "heating_off_outdoor_temp_c": (ROLE_NUMBER, False, None, "settings"),
    "heater_on_outdoor_temp_c": (ROLE_NUMBER, False, None, "settings"),
    "curve_outside_high_c": (ROLE_NUMBER, False, None, "settings"),
    "curve_outside_low_c": (ROLE_NUMBER, False, None, "settings"),
    "curve_target_high_c": (ROLE_NUMBER, False, None, "settings"),
    "curve_target_low_c": (ROLE_NUMBER, False, None, "settings"),
}

HEAT_PUMP_SECTIONS = ["measurement", "modes", "season_defrost", "heat", "dhw", "compressor", "settings"]

# Preset HeishaMon: rola → kandydaci (pierwszy istniejący wygrywa). Ta sama wielkość
# bywa wystawiona w kilku domenach (np. defrost jako binary_sensor i switch).
# Uwaga na pułapki HeishaMona:
#  - *_room_heater_state / *_dhw_heater_state = grzałka DOZWOLONA, nie pracująca —
#    pracę pokazuje *_internal_heater_state;
#  - zawory 2-/3-drogowe nie mówią, co pompa robi (stoją też w postoju) — tryb
#    wynika z poboru CO/CWU.
HEISHAMON_CANDIDATES: dict[str, list[str]] = {
    "power_w": ["sensor.{p}_consumption"],
    "co_power_w": ["sensor.{p}_main_heat_power_consumption"],
    "cwu_power_w": ["sensor.{p}_main_dhw_power_consumption"],
    "season": ["select.{p}_main_operating_mode_state", "sensor.{p}_main_operating_mode_state"],
    "defrost": ["binary_sensor.{p}_main_defrosting_state", "switch.{p}_main_defrosting_state"],
    "co_heat_w": ["sensor.{p}_main_heat_power_production"],
    "cwu_heat_w": ["sensor.{p}_main_dhw_power_production"],
    "flow_lpm": ["sensor.{p}_main_pump_flow"],
    "supply_temp_c": ["sensor.{p}_main_main_outlet_temp"],
    "return_temp_c": ["sensor.{p}_main_main_inlet_temp"],
    "dhw_temp_c": ["sensor.{p}_main_dhw_temp"],
    "dhw_target_temp_c": ["number.{p}_main_dhw_target_temp", "sensor.{p}_main_dhw_target_temp"],
    "sterilization": ["switch.{p}_main_sterilization_state", "binary_sensor.{p}_main_sterilization_state"],
    "compressor_hz": ["sensor.{p}_main_compressor_freq"],
    "operations_counter": ["sensor.{p}_main_operations_counter"],
    "operations_hours": ["sensor.{p}_main_operations_hours"],
    "heater": ["binary_sensor.{p}_main_internal_heater_state"],
    "outside_temp_c": ["sensor.{p}_main_outside_temp"],
    "heating_off_outdoor_temp_c": ["number.{p}_main_heating_off_outdoor_temp", "sensor.{p}_main_heating_off_outdoor_temp"],
    "heater_on_outdoor_temp_c": ["sensor.{p}_main_heater_on_outdoor_temp", "number.{p}_main_heater_on_outdoor_temp"],
    "curve_outside_high_c": ["number.{p}_main_z1_heat_curve_outside_high_temp"],
    "curve_outside_low_c": ["number.{p}_main_z1_heat_curve_outside_low_temp"],
    "curve_target_high_c": ["number.{p}_main_z1_heat_curve_target_high_temp"],
    "curve_target_low_c": ["number.{p}_main_z1_heat_curve_target_low_temp"],
}

SUPPORTED_EV_CHARGERS = [
    {"value": "autel_maxicharger_ac_75kw", "label": "Autel - MaxiChargerAC 7.5KW"},
]

DEFAULT_SERVER_URL = "https://solaraccelerator.cloud"

API_TEST_CONNECTION_ENDPOINT = "/api/homeassistant/test-connection"
API_LIVE_ENDPOINT = "/api/homeassistant/live"
API_PRICES_ENDPOINT = "/api/homeassistant/prices"
API_PROFIT_ENDPOINT = "/api/homeassistant/profit"
API_COMMAND_ACK_ENDPOINT = "/api/homeassistant/commands/{id}/ack"

# Interwał startowy — serwer nadpisuje go w odpowiedzi na pierwszy push
DEFAULT_LIVE_INTERVAL = 15
LIVE_DISABLED_RETRY = 60
LIVE_AUTH_RETRY = 300

# Co ile sekund odświeżamy ceny i zysk (metryki nie potrzebują szybkiego pushu jak EV)
METRICS_FETCH_INTERVAL = 3600

PLATFORMS: list[str] = ["sensor"]

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
