"""
Configuration file discovery and management
"""

import os
from pathlib import Path
from typing import Optional


class ConfigManager:
    """
    Manages configuration file locations with priority order:
    1. Current directory: ./config/providers.yaml
    2. User home: ~/.config/freerouter/providers.yaml
    3. System default: Use example
    """

    DEFAULT_PROVIDER_CONFIG = "providers.yaml"
    DEFAULT_OUTPUT_CONFIG = "config.yaml"

    def __init__(self):
        self.config_locations = [
            Path.cwd() / "config",
            Path.home() / ".config" / "freerouter",
        ]

    def find_provider_config(self) -> Optional[Path]:
        """
        Find providers.yaml with priority order

        Returns:
            Path to providers.yaml or None if not found
        """
        for location in self.config_locations:
            config_file = location / self.DEFAULT_PROVIDER_CONFIG
            if config_file.exists():
                return config_file
        return None

    def get_output_config_path(self) -> Path:
        """
        Get path for output config.yaml

        Returns:
            Path where config.yaml should be written
        """
        # Try current directory first
        local_config = Path.cwd() / "config"
        if local_config.exists():
            return local_config / self.DEFAULT_OUTPUT_CONFIG

        # Use user home
        user_config = Path.home() / ".config" / "freerouter"
        user_config.mkdir(parents=True, exist_ok=True)
        return user_config / self.DEFAULT_OUTPUT_CONFIG

    def ensure_user_config_dir(self) -> Path:
        """
        Ensure user config directory exists

        Returns:
            Path to user config directory
        """
        user_config = Path.home() / ".config" / "freerouter"
        user_config.mkdir(parents=True, exist_ok=True)
        return user_config

    def init_config(self) -> Path:
        """
        Initialize config directory with example

        Returns:
            Path to created config directory
        """
        # Check if already exists in current directory
        local_config = Path.cwd() / "config"
        if local_config.exists():
            return local_config

        # Create in current directory
        local_config.mkdir(exist_ok=True)

        # Copy example if available
        example_file = Path(__file__).parent.parent.parent / "examples" / "providers.yaml.example"
        target_file = local_config / "providers.yaml"

        if example_file.exists() and not target_file.exists():
            import shutil
            shutil.copy(example_file, target_file)

        return local_config
