# SolarAccelerator Home — integracja Home Assistant

Zero związku z falownikiem — do tego służą `solaraccelerator_connect` (bramka
SA Connect) i `SolarAccelerator Bridge` (falownik przez istniejące encje HA,
np. Solarman).

Ta integracja robi wyłącznie dwie rzeczy:

- **Odpytuje SolarAccelerator o metryki** — ceny energii i dzienny zysk, jako
  sensory Home Assistanta (ten sam mechanizm co dziś w `solaraccelerator`).
- **Rejestruje w SolarAcceleratorze akcesoria** — ładowarki EV i sterowalne
  odbiorniki, żeby optymalizator wiedział o nich i mógł nimi zarządzać.

Jeśli sterujesz falownikiem przez Solarman (albo inną istniejącą integrację
w HA), zainstaluj obok `SolarAccelerator Bridge`. Jeśli masz bramkę SA Connect,
zainstaluj obok `solaraccelerator_connect`. Te trzy integracje nie wchodzą
sobie w drogę — każda ma jedną, wąską odpowiedzialność.

## Wymagania

- Home Assistant 2024.11.0+
- Klucz API SolarAccelerator (`sa_haapi_...`) z panelu SolarAccelerator,
  sekcja Integracje → SolarAccelerator Home

## Status

Wczesna wersja — config flow i walidacja klucza działają, sensory metryk i
rejestracja akcesoriów w budowie.
