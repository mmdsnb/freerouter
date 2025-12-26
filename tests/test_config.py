"""
Tests for configuration management
"""

import os
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch

from freerouter.cli.config import ConfigManager


class TestConfigManager:
    """Test ConfigManager functionality"""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory"""
        temp_dir = tempfile.mkdtemp()
        original_dir = os.getcwd()
        os.chdir(temp_dir)
        yield temp_dir
        os.chdir(original_dir)
        shutil.rmtree(temp_dir)

    def test_find_provider_config_current_dir(self, temp_dir):
        """Test finding provider config in current directory"""
        # Create config in current directory
        config_dir = Path('config')
        config_dir.mkdir()
        providers_file = config_dir / 'providers.yaml'
        providers_file.write_text('providers: []')

        manager = ConfigManager()
        found = manager.find_provider_config()

        assert found == providers_file.resolve()
        assert found.exists()

    def test_find_provider_config_user_home(self, temp_dir):
        """Test finding provider config in user home"""
        # Create config in user home
        user_config = Path.home() / '.config' / 'freerouter'
        user_config.mkdir(parents=True, exist_ok=True)
        providers_file = user_config / 'providers.yaml'
        providers_file.write_text('providers: []')

        try:
            manager = ConfigManager()
            found = manager.find_provider_config()

            # Should find the one in user home if current dir doesn't have one
            assert found == providers_file
        finally:
            # Cleanup
            if providers_file.exists():
                providers_file.unlink()

    def test_find_provider_config_not_found(self, temp_dir):
        """Test when provider config is not found"""
        manager = ConfigManager()
        found = manager.find_provider_config()

        assert found is None

    def test_get_output_config_path_current_dir(self, temp_dir):
        """Test getting output config path for current directory"""
        config_dir = Path('config')
        config_dir.mkdir()

        manager = ConfigManager()
        output_path = manager.get_output_config_path()

        expected = (config_dir / 'config.yaml').resolve()
        assert output_path == expected

    def test_get_output_config_path_user_home(self, temp_dir):
        """Test getting output config path for user home"""
        manager = ConfigManager()
        output_path = manager.get_output_config_path()

        # Should use user home if current dir doesn't have config
        expected = Path.home() / '.config' / 'freerouter' / 'config.yaml'
        assert output_path == expected

    def test_ensure_user_config_dir(self, temp_dir):
        """Test ensuring user config directory exists"""
        manager = ConfigManager()
        user_dir = manager.ensure_user_config_dir()

        expected = Path.home() / '.config' / 'freerouter'
        assert user_dir == expected
        assert user_dir.exists()
        assert user_dir.is_dir()

    def test_init_config_project_level(self, temp_dir):
        """Test initializing project-level config"""
        manager = ConfigManager()
        config_dir = manager.init_config(interactive=False, use_user_config=False)

        assert config_dir == Path.cwd() / 'config'
        assert config_dir.exists()

        providers_file = config_dir / 'providers.yaml'
        assert providers_file.exists()

        # Verify content
        content = providers_file.read_text()
        assert 'providers:' in content
        assert 'enabled: false' in content

    def test_init_config_user_level(self, temp_dir):
        """Test initializing user-level config"""
        manager = ConfigManager()
        config_dir = manager.init_config(interactive=False, use_user_config=True)

        expected = Path.home() / '.config' / 'freerouter'
        assert config_dir == expected
        assert config_dir.exists()

        providers_file = config_dir / 'providers.yaml'
        assert providers_file.exists()

    def test_disable_all_providers(self, temp_dir):
        """Test _disable_all_providers method"""
        manager = ConfigManager()

        config_dict = {
            'providers': [
                {'type': 'openrouter', 'enabled': True},
                {'type': 'ollama', 'enabled': True},
                {'type': 'modelscope', 'enabled': True}
            ]
        }

        result = manager._disable_all_providers(config_dict)

        # All should be disabled
        for provider in result['providers']:
            assert provider['enabled'] is False

    def test_init_config_replaces_enabled_true(self, temp_dir):
        """Test that init_config replaces all enabled: true with false"""
        manager = ConfigManager()
        config_dir = manager.init_config(interactive=False, use_user_config=False)

        providers_file = config_dir / 'providers.yaml'
        content = providers_file.read_text()

        # Should have no enabled: true
        assert 'enabled: true' not in content
        # Should have multiple enabled: false
        assert content.count('enabled: false') >= 3

    def test_init_config_overwrite_interactive(self, temp_dir):
        """Test init_config with overwrite in interactive mode"""
        manager = ConfigManager()

        # Create initial config
        config_dir = manager.init_config(interactive=False, use_user_config=False)
        providers_file = config_dir / 'providers.yaml'

        # Modify file
        providers_file.write_text("# Modified content")

        # Init again without overwrite (interactive=True requires user input)
        # This would normally prompt user, so we test non-interactive
        config_dir2 = manager.init_config(interactive=False, use_user_config=False)

        # File should be overwritten
        content = providers_file.read_text()
        assert content != "# Modified content"
        assert 'providers:' in content
