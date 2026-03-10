"""Tests for configuration management."""

import os

import pytest

from sniff.config import ConfigManager


def test_config_manager_get_set():
    """Test basic get/set operations."""
    config = ConfigManager("test", defaults={"database": {"path": "/tmp/db"}})

    assert config.get("database.path") == "/tmp/db"
    assert config.get("nonexistent.key", default="fallback") == "fallback"

    config.set("custom.value", "test")
    assert config.get("custom.value") == "test"


def test_config_manager_env_override(monkeypatch):
    """Test environment variable override."""
    config = ConfigManager("testapp", env_prefix="TESTAPP", defaults={"key": "default"})

    # Set env var
    monkeypatch.setenv("TESTAPP_KEY", "from_env")

    # Reload to pick up env var
    config._load()

    assert config.get("key") == "from_env"


def test_config_manager_to_dict():
    """Test converting config to dict."""
    config = ConfigManager("test", defaults={"a": 1, "b": {"c": 2}})

    result = config.to_dict()
    assert result == {"a": 1, "b": {"c": 2}}
