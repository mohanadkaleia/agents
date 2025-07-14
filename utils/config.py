import os
from typing import Any, Dict

import yaml


class ConfigurationError(Exception):
    pass


class Config:
    def __init__(self):
        self._config = {}
        self.load_config()

    def load_config(self) -> None:
        env = os.getenv("ENV", "local")

        # Load environment specific config
        env_path = os.path.join(os.path.dirname(__file__), f"../configs/{env}.yml")
        if os.path.exists(env_path):
            env_config = self._load_yaml(env_path)
            self._config = self._deep_merge(self._config, env_config)

        # Override with environment variables
        self._override_from_env()

    def _load_yaml(self, path: str) -> Dict[str, Any]:
        try:
            with open(path, "r") as f:
                return yaml.safe_load(f)
        except Exception as e:
            raise ConfigurationError(f"Error loading config from {path}: {str(e)}")

    def _deep_merge(self, base: dict, override: dict) -> dict:
        """Recursively merge two dictionaries."""
        result = base.copy()
        for key, value in override.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    def _override_from_env(self) -> None:
        """Override config values from environment variables."""
        for key in os.environ:
            if key.startswith("APP_"):
                path = key[4:].lower().split("_")
                self._set_nested_value(self._config, path, os.environ[key])

    def _set_nested_value(self, d: dict, path: list, value: Any) -> None:
        """Set value in nested dictionary using path list."""
        for key in path[:-1]:
            d = d.setdefault(key, {})
        d[path[-1]] = value

    def get(self, path: str, default: Any = None) -> Any:
        """Get config value using dot notation."""
        keys = path.split(".")
        value = self._config
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default


# Create a singleton instance
config = Config()