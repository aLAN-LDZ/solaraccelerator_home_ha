"""Funkcje pomocnicze."""
from __future__ import annotations

from typing import Any


def convert_value(value: str | None, entity_key: str) -> float | int | str | None:
    """Zamień wartość encji HA na typ akceptowany przez backend.

    HA przechowuje stany jako stringi. Pola tekstowe ładowarki EV zostają
    stringiem, resztę próbujemy sparsować jako liczbę. Stan ``unknown``/
    ``unavailable``/pusty/brak → 0, żeby payload miał spójny kształt.
    """
    if value is None or value in ("unknown", "unavailable", ""):
        return 0

    if entity_key in ("status", "status_connector", "vendor", "error_code", "transaction_id"):
        return value

    try:
        float_val = float(value)
        if float_val.is_integer():
            return int(float_val)
        return round(float_val, 2)
    except (ValueError, TypeError):
        return 0


# ── Pompa ciepła ──────────────────────────────────────────────────────────────
# W przeciwieństwie do EV brak odczytu to None, nie 0: pompa, która nie grzeje
# (0 W), i pompa, której odczyt zniknął (unavailable), to dwie różne sytuacje.

_UNAVAILABLE = ("unknown", "unavailable", "", "none")

# Mnożnik do jednostki docelowej roli (moc → W, energia → kWh).
_UNIT_FACTORS: dict[str, dict[str, float]] = {
    "W": {"w": 1.0, "kw": 1000.0, "mw": 1_000_000.0},
    "kWh": {"wh": 0.001, "kwh": 1.0, "mwh": 1000.0},
}


def read_number(state: Any, target_unit: str | None) -> float | None:
    """Stan encji jako liczba w jednostce docelowej roli (W / kWh) albo None."""
    if state is None or str(state.state).lower() in _UNAVAILABLE:
        return None
    try:
        value = float(state.state)
    except (ValueError, TypeError):
        return None
    if target_unit:
        unit = str(state.attributes.get("unit_of_measurement") or "").strip().lower()
        factor = _UNIT_FACTORS.get(target_unit, {}).get(unit)
        if factor is not None:
            value *= factor
    return round(value, 4)


def read_bool(state: Any) -> bool | None:
    """on/off (binary_sensor, switch, input_boolean) → True/False albo None."""
    if state is None:
        return None
    raw = str(state.state).lower()
    if raw in ("on", "true", "1", "yes"):
        return True
    if raw in ("off", "false", "0", "no"):
        return False
    return None


def read_text(state: Any) -> str | None:
    """Surowy stan tekstowy (tryb pracy, sezon) albo None."""
    if state is None or str(state.state).lower() in _UNAVAILABLE:
        return None
    return str(state.state)
