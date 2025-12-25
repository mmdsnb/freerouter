"""
Tests for CLI commands
"""

import os
import sys
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
from io import StringIO

from freerouter.cli.main import main


class TestCLI:
    """Test CLI commands"""

    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary config directory"""
        temp_dir = tempfile.mkdtemp()
        original_dir = os.getcwd()
        os.chdir(temp_dir)
        yield temp_dir
        os.chdir(original_dir)
        shutil.rmtree(temp_dir)

    def test_version(self, capsys):
        """Test --version flag"""
        with pytest.raises(SystemExit) as exc_info:
            with patch('sys.argv', ['freerouter', '--version']):
                main()

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert 'FreeRouter' in captured.out
        assert '0.1.0' in captured.out

    def test_help(self, capsys):
        """Test --help flag"""
        with pytest.raises(SystemExit) as exc_info:
            with patch('sys.argv', ['freerouter', '--help']):
                main()

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert 'FreeRouter' in captured.out
        assert 'init' in captured.out
        assert 'fetch' in captured.out
        assert 'start' in captured.out
        assert 'list' in captured.out

    def test_init_command(self, temp_config_dir):
        """Test init command"""
        with patch('sys.argv', ['freerouter', 'init']):
            main()

        # Check config directory was created
        config_dir = Path('config')
        assert config_dir.exists()
        assert config_dir.is_dir()

        # Check providers.yaml was created
        providers_file = config_dir / 'providers.yaml'
        assert providers_file.exists()

        # Check content
        content = providers_file.read_text()
        assert 'openrouter' in content
        assert 'iflow' in content
        assert 'modelscope' in content

    def test_init_command_already_exists(self, temp_config_dir, capsys):
        """Test init command when config already exists"""
        # Create config first time
        with patch('sys.argv', ['freerouter', 'init']):
            main()

        # Clear captured output
        capsys.readouterr()

        # Try to create again
        with patch('sys.argv', ['freerouter', 'init']):
            main()

        captured = capsys.readouterr()
        assert 'already exists' in captured.out or 'Initialized' in captured.out

    def test_fetch_command(self, temp_config_dir, capsys):
        """Test fetch command"""
        # Create config first
        with patch('sys.argv', ['freerouter', 'init']):
            main()

        # Create a simple provider config
        providers_yaml = Path('config/providers.yaml')
        providers_yaml.write_text("""
providers:
  - type: static
    enabled: true
    model_name: test-model
    provider: openai
    api_base: http://test.com
    api_key: test
""")

        # Run fetch - should complete without error
        with patch('sys.argv', ['freerouter', 'fetch']):
            main()

        # Check config.yaml was created
        assert Path('config/config.yaml').exists()

    def test_list_command(self, temp_config_dir, capsys):
        """Test list command"""
        # Create config directory and config.yaml
        config_dir = Path('config')
        config_dir.mkdir()

        config_yaml = config_dir / 'config.yaml'
        config_yaml.write_text("""
model_list:
  - model_name: test-model-1
    litellm_params:
      model: openai/test-model-1
      api_key: test
  - model_name: test-model-2
    litellm_params:
      model: openai/test-model-2
      api_key: test
""")

        # Run list
        with patch('sys.argv', ['freerouter', 'list']):
            main()

        captured = capsys.readouterr()
        assert 'test-model-1' in captured.out
        assert 'test-model-2' in captured.out
        assert 'Total: 2 models' in captured.out

    def test_list_command_no_config(self, temp_config_dir, caplog):
        """Test list command without config file"""
        with pytest.raises(SystemExit):
            with patch('sys.argv', ['freerouter', 'list']):
                main()

        # Check in logs instead of stdout
        assert 'not found' in caplog.text or 'Config not found' in caplog.text

    def test_start_command_help(self, capsys):
        """Test start command help"""
        with pytest.raises(SystemExit):
            with patch('sys.argv', ['freerouter', 'start', '--help']):
                main()

        captured = capsys.readouterr()
        # Should show help info
        assert captured.out != '' or captured.err != ''


class TestCLIIntegration:
    """Integration tests for CLI with real file system"""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for integration tests"""
        temp_dir = tempfile.mkdtemp()
        original_dir = os.getcwd()
        os.chdir(temp_dir)
        yield temp_dir
        os.chdir(original_dir)
        shutil.rmtree(temp_dir)

    def test_init_and_check_files(self, temp_dir):
        """Test init creates proper file structure"""
        with patch('sys.argv', ['freerouter', 'init']):
            main()

        assert Path('config').exists()
        assert Path('config/providers.yaml').exists()

        # Verify content
        content = Path('config/providers.yaml').read_text()
        assert 'providers:' in content
        assert 'openrouter' in content
        assert 'OPENROUTER_API_KEY' in content
        assert 'iflow' in content
        assert 'IFLOW_API_KEY' in content
        assert 'modelscope' in content
        assert 'MODELSCOPE_API_KEY' in content

    def test_init_creates_correct_structure(self, temp_dir):
        """Test init creates correct directory structure"""
        with patch('sys.argv', ['freerouter', 'init']):
            main()

        config_dir = Path('config')
        assert config_dir.is_dir()

        providers_yaml = config_dir / 'providers.yaml'
        assert providers_yaml.is_file()

        # Check file permissions (should be readable)
        assert os.access(providers_yaml, os.R_OK)
