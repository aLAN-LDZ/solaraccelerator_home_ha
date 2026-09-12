"""Stałe integracji SolarAccelerator Home."""
from __future__ import annotations

DOMAIN = "solaraccelerator_home"

CONF_API_KEY = "api_key"
CONF_SERVER_URL = "server_url"

DEFAULT_SERVER_URL = "https://solaraccelerator.cloud"
API_TEST_CONNECTION_ENDPOINT = "/api/homeassistant/test-connection"

PLATFORMS: list[str] = []
