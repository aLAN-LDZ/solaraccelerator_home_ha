"""Funkcje pomocnicze."""
from __future__ import annotations


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
