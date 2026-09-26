"""Security test suite for SSRF and unsafe link rejection (TASK-TEST-SEC-002)."""

import ipaddress
from pathlib import Path
from urllib.parse import urlparse
import pytest
import yaml

FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "ssrf.yaml"


def load_ssrf_config():
    with FIXTURE_PATH.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def is_url_safe(url: str, allowed_schemes: list[str]) -> tuple[bool, str]:
    parsed = urlparse(url)
    if parsed.scheme not in allowed_schemes:
        return False, f"Disallowed scheme: {parsed.scheme}"

    if parsed.scheme == "fixture":
        return True, "Safe internal fixture URI"

    hostname = parsed.hostname
    if not hostname:
        return False, "Missing hostname"

    if hostname.lower() == "localhost":
        return False, "Localhost target blocked"

    try:
        ip = ipaddress.ip_address(hostname)
        if ip.is_loopback:
            return False, "Loopback IP blocked"
        if ip.is_private:
            return False, "Private IP range blocked"
        if ip.is_link_local:
            return False, "Link-local/metadata IP blocked"
    except ValueError:
        # Domain name
        pass

    return True, "Safe outbound URL"


def test_ssrf_fixture_exists_and_valid():
    config = load_ssrf_config()
    assert "allowed_schemes" in config
    assert "blocked_payloads" in config
    assert "allowed_samples" in config


def test_all_blocked_ssrf_payloads_are_rejected():
    config = load_ssrf_config()
    allowed_schemes = config["allowed_schemes"]
    for item in config["blocked_payloads"]:
        url = item["url"]
        safe, reason = is_url_safe(url, allowed_schemes)
        assert safe is False, f"URL {url} should have been blocked (expected: {item['reason']})"


def test_all_allowed_samples_are_accepted():
    config = load_ssrf_config()
    allowed_schemes = config["allowed_schemes"]
    for item in config["allowed_samples"]:
        url = item["url"]
        safe, reason = is_url_safe(url, allowed_schemes)
        assert safe is True, f"URL {url} should have been accepted, but got: {reason}"


def test_negative_path_custom_link_local_metadata_blocked():
    config = load_ssrf_config()
    safe, reason = is_url_safe("https://169.254.169.254/latest/meta-data/", config["allowed_schemes"])
    assert safe is False
    assert "blocked" in reason.lower()
