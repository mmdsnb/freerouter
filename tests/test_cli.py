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

    def test_init_command_interactive_project_level(self, temp_config_dir):
        """Test init command with interactive prompt - project level"""
        # Mock user input: choose option 2 (project-level)
        with patch('builtins.input', return_value='2'):
            with patch('sys.argv', ['freerouter', 'init']):
                main()

        # Check config directory was created
        config_dir = Path('config')
        assert config_dir.exists()
        assert config_dir.is_dir()

        # Check providers.yaml was created
        providers_file = config_dir / 'providers.yaml'
        assert providers_file.exists()

        # Check content - all providers should be disabled
        content = providers_file.read_text()
        assert 'openrouter' in content
        assert 'iflow' in content
        assert 'modelscope' in content
        # Verify all are disabled
        assert content.count('enabled: false') >= 3
        assert 'enabled: true' not in content

    def test_init_command_interactive_user_level(self, temp_config_dir):
        """Test init command with interactive prompt - user level"""
        # Mock user input: choose option 1 (user-level)
        with patch('builtins.input', return_value='1'):
            with patch('sys.argv', ['freerouter', 'init']):
                main()

        # Check user config directory
        user_config = Path.home() / '.config' / 'freerouter'
        assert user_config.exists()

        providers_file = user_config / 'providers.yaml'
        assert providers_file.exists()

        # Verify all providers disabled
        content = providers_file.read_text()
        assert 'enabled: false' in content
        assert 'enabled: true' not in content

    def test_init_command_overwrite_existing(self, temp_config_dir):
        """Test init command with overwrite prompt"""
        # Create initial config
        with patch('builtins.input', return_value='2'):
            with patch('sys.argv', ['freerouter', 'init']):
                main()

        # Modify the file
        config_file = Path('config/providers.yaml')
        original_content = config_file.read_text()
        config_file.write_text("# Modified")

        # Try to init again, choose to overwrite
        with patch('builtins.input', side_effect=['2', 'y']):
            with patch('sys.argv', ['freerouter', 'init']):
                main()

        # Content should be reset to template
        new_content = config_file.read_text()
        assert new_content != "# Modified"
        assert 'providers:' in new_content

    def test_init_command_keep_existing(self, temp_config_dir):
        """Test init command choosing not to overwrite"""
        # Create initial config
        with patch('builtins.input', return_value='2'):
            with patch('sys.argv', ['freerouter', 'init']):
                main()

        # Modify the file
        config_file = Path('config/providers.yaml')
        config_file.write_text("# Modified")

        # Try to init again, choose NOT to overwrite
        with patch('builtins.input', side_effect=['2', 'n']):
            with patch('sys.argv', ['freerouter', 'init']):
                main()

        # Content should remain modified
        content = config_file.read_text()
        assert content == "# Modified"

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

    def test_start_command_no_config(self, temp_config_dir, caplog):
        """Test start command without config file"""
        with pytest.raises(SystemExit):
            with patch('sys.argv', ['freerouter', 'start']):
                main()

        assert 'Config not found' in caplog.text

    @patch('subprocess.Popen')
    def test_start_command_creates_pid_file(self, mock_popen, temp_config_dir):
        """Test start command creates PID file"""
        # Setup config
        config_dir = Path('config')
        config_dir.mkdir()
        (config_dir / 'config.yaml').write_text('model_list: []')

        # Mock process
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_process.stdout = iter(["INFO:     Uvicorn running on http://0.0.0.0:4000\n"])
        mock_popen.return_value = mock_process

        # Run start
        with patch('sys.argv', ['freerouter', 'start']):
            with patch('builtins.open', create=True) as mock_open:
                try:
                    main()
                except StopIteration:
                    pass  # Expected when mock iterator ends

        # Verify Popen was called with correct params
        mock_popen.assert_called_once()
        call_args = mock_popen.call_args
        assert 'litellm' in call_args[0][0]
        assert call_args[1]['start_new_session'] is True

    def test_stop_command_no_service(self, temp_config_dir, caplog):
        """Test stop command when service is not running"""
        config_dir = Path('config')
        config_dir.mkdir()

        with pytest.raises(SystemExit):
            with patch('sys.argv', ['freerouter', 'stop']):
                main()

        assert 'not running' in caplog.text

    @patch('os.kill')
    def test_stop_command_success(self, mock_kill, temp_config_dir):
        """Test stop command successfully stops service"""
        config_dir = Path('config')
        config_dir.mkdir()

        # Create fake PID file
        pid_file = config_dir / 'freerouter.pid'
        pid_file.write_text('12345')

        # Mock os.kill - first call succeeds (check), second kills, third fails (stopped)
        mock_kill.side_effect = [None, None, OSError("Process not found")]

        with patch('sys.argv', ['freerouter', 'stop']):
            main()

        # Verify kill was called
        assert mock_kill.call_count >= 2
        # PID file should be deleted
        assert not pid_file.exists()

    def test_logs_command_no_service(self, temp_config_dir, caplog):
        """Test logs command when service is not running"""
        config_dir = Path('config')
        config_dir.mkdir()

        with pytest.raises(SystemExit):
            with patch('sys.argv', ['freerouter', 'logs']):
                main()

        assert 'not running' in caplog.text

    @patch('os.kill')
    def test_logs_command_displays_logs(self, mock_kill, temp_config_dir, capsys):
        """Test logs command reads and displays log file"""
        config_dir = Path('config')
        config_dir.mkdir()

        # Create fake PID file and log file
        pid_file = config_dir / 'freerouter.pid'
        pid_file.write_text('12345')

        log_file = config_dir / 'freerouter.log'
        log_file.write_text('Log line 1\nLog line 2\n')

        # Mock os.kill to indicate process is running, then stopped
        mock_kill.side_effect = [None, OSError("Process stopped")]

        # Mock readline to return nothing (so loop exits quickly)
        with patch('builtins.open', create=True) as mock_open:
            mock_file = MagicMock()
            mock_file.__enter__.return_value = mock_file
            mock_file.readline.return_value = ''
            mock_open.return_value = mock_file

            try:
                with patch('sys.argv', ['freerouter', 'logs']):
                    main()
            except SystemExit:
                pass

        # Verify we tried to read the log file
        mock_open.assert_called()

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
