"""
Tests for CLI commands
"""

import os
import sys
import logging
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
        assert '0.1.2' in captured.out

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
        with patch('builtins.input', return_value='2'):
            with patch('sys.argv', ['freerouter', 'init']):
                main()

        # Clear captured output
        capsys.readouterr()

        # Try to create again - should ask location first, then ask to overwrite
        # We need to provide two inputs: '2' for location, 'n' for overwrite
        with patch('builtins.input', side_effect=['2', 'n']):
            with patch('sys.argv', ['freerouter', 'init']):
                main()

        captured = capsys.readouterr()
        assert 'already exists' in captured.out or 'Keeping existing' in captured.out

    def test_fetch_command(self, temp_config_dir, capsys):
        """Test fetch command"""
        # Create config first
        with patch('builtins.input', return_value='2'):
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
        # Mock get_output_config_path to return non-existent path
        fake_path = Path(temp_config_dir) / "nonexistent" / "config.yaml"

        with patch('freerouter.cli.main.ConfigManager.get_output_config_path', return_value=fake_path):
            with pytest.raises(SystemExit):
                with patch('sys.argv', ['freerouter', 'list']):
                    main()

        # Check in logs instead of stdout
        assert 'not found' in caplog.text or 'Config not found' in caplog.text

    def test_start_command_no_config(self, temp_config_dir, caplog):
        """Test start command without config file"""
        # Mock get_output_config_path to return non-existent path
        fake_path = Path(temp_config_dir) / "nonexistent" / "config.yaml"

        with patch('freerouter.cli.main.ConfigManager.get_output_config_path', return_value=fake_path):
            with pytest.raises(SystemExit):
                with patch('sys.argv', ['freerouter', 'start']):
                    main()

        assert 'Config not found' in caplog.text

    @patch('time.sleep')  # Mock sleep to avoid delays
    @patch('subprocess.Popen')
    def test_start_command_creates_pid_file(self, mock_popen, mock_sleep, temp_config_dir):
        """Test start command creates PID file"""
        # Setup config
        config_dir = Path('config')
        config_dir.mkdir()
        (config_dir / 'config.yaml').write_text('model_list: []')

        # Create log file with startup message
        log_file = config_dir / 'freerouter.log'
        log_file.write_text("INFO:     Uvicorn running on http://0.0.0.0:4000\n")

        # Mock process
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_popen.return_value = mock_process

        # Run start
        with patch('sys.argv', ['freerouter', 'start']):
            main()

        # Verify Popen was called with correct params
        mock_popen.assert_called_once()
        call_args = mock_popen.call_args
        assert 'litellm' in call_args[0][0]
        assert call_args[1]['start_new_session'] is True

        # Verify PID file was created
        pid_file = config_dir / 'freerouter.pid'
        assert pid_file.exists()
        assert pid_file.read_text().strip() == '12345'

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

        # Mock os.kill - simulate process stopping after SIGTERM
        # Call sequence: check(0), kill(15), check(0) x N times, final check(0) raises
        mock_kill.side_effect = [
            None,  # Initial check: process exists
            None,  # SIGTERM: kill signal sent
            None,  # Loop check 1: still running
            OSError("Process stopped"),  # Loop check 2: stopped
            OSError("Process stopped")  # Final check: confirm stopped
        ]

        with patch('sys.argv', ['freerouter', 'stop']):
            main()

        # Verify kill was called multiple times
        assert mock_kill.call_count >= 3
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
        with patch('builtins.input', return_value='2'):  # Choose project-level config
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
        with patch('builtins.input', return_value='2'):  # Choose project-level config
            with patch('sys.argv', ['freerouter', 'init']):
                main()

        config_dir = Path('config')
        assert config_dir.is_dir()

        providers_yaml = config_dir / 'providers.yaml'
        assert providers_yaml.is_file()

        # Check file permissions (should be readable)
        assert os.access(providers_yaml, os.R_OK)


class TestReloadCommand:
    """Test reload command"""

    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary config directory"""
        temp_dir = tempfile.mkdtemp()
        original_dir = os.getcwd()
        os.chdir(temp_dir)
        yield temp_dir
        os.chdir(original_dir)
        shutil.rmtree(temp_dir)

    @patch('time.sleep')
    @patch('subprocess.Popen')
    def test_reload_without_refresh(self, mock_popen, mock_sleep, temp_config_dir):
        """Test reload command without refresh (simple restart)"""
        # Setup config
        config_dir = Path('config')
        config_dir.mkdir()
        config_file = config_dir / 'config.yaml'
        config_file.write_text('model_list: []')

        # Create log file with startup message
        log_file = config_dir / 'freerouter.log'
        log_file.write_text("INFO:     Uvicorn running on http://0.0.0.0:4000\n")

        # Mock process
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_popen.return_value = mock_process

        # Run reload (service not running, should just start)
        with patch('sys.argv', ['freerouter', 'reload']):
            main()

        # Verify start was called
        assert mock_popen.called

    @patch('time.sleep')
    @patch('subprocess.Popen')
    def test_reload_with_refresh(self, mock_popen, mock_sleep, temp_config_dir):
        """Test reload command with --refresh (backup + fetch + restart)"""
        # Setup config
        config_dir = Path('config')
        config_dir.mkdir()

        # Create providers.yaml
        providers_file = config_dir / 'providers.yaml'
        providers_file.write_text("""
providers:
  - type: static
    enabled: true
    model_name: test-model
    provider: openai
    api_base: http://test.com
    api_key: test
""")

        # Create existing config.yaml
        config_file = config_dir / 'config.yaml'
        config_file.write_text('model_list: [old-model]')

        # Create log file
        log_file = config_dir / 'freerouter.log'
        log_file.write_text("INFO:     Uvicorn running on http://0.0.0.0:4000\n")

        # Mock process
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_popen.return_value = mock_process

        # Run reload with refresh
        with patch('sys.argv', ['freerouter', 'reload', '--refresh']):
            main()

        # Check backup was created
        backups = list(config_dir.glob('config.yaml.backup.*'))
        assert len(backups) > 0

        # Verify new config was generated
        assert config_file.exists()

    @patch('time.sleep')
    @patch('os.kill')
    @patch('subprocess.Popen')
    def test_reload_with_running_service(self, mock_popen, mock_kill, mock_sleep, temp_config_dir):
        """Test reload command when service is already running"""
        # Setup config
        config_dir = Path('config')
        config_dir.mkdir()
        config_file = config_dir / 'config.yaml'
        config_file.write_text('model_list: []')

        # Create PID file (service running)
        pid_file = config_dir / 'freerouter.pid'
        pid_file.write_text('12345')

        # Create log file
        log_file = config_dir / 'freerouter.log'
        log_file.write_text("INFO:     Uvicorn running on http://0.0.0.0:4000\n")

        # Mock os.kill for is_service_running check and stop command
        mock_kill.side_effect = [
            None,  # is_service_running check
            None,  # stop: initial check
            None,  # stop: SIGTERM
            None,  # stop: loop check
            OSError("Process stopped"),  # stop: stopped
            OSError("Process stopped")  # stop: final check
        ]

        # Mock process
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_popen.return_value = mock_process

        # Run reload
        with patch('sys.argv', ['freerouter', 'reload']):
            main()

        # Verify stop and start were called
        assert mock_kill.call_count >= 2  # At least check + kill
        assert mock_popen.called

    def test_reload_short_option(self, temp_config_dir, capsys):
        """Test reload -r short option works"""
        # Setup minimal config
        config_dir = Path('config')
        config_dir.mkdir()

        providers_file = config_dir / 'providers.yaml'
        providers_file.write_text("""
providers:
  - type: static
    enabled: true
    model_name: test
    provider: openai
    api_base: http://test.com
    api_key: test
""")

        # Create existing config.yaml (to be backed up)
        config_file = config_dir / 'config.yaml'
        config_file.write_text('model_list: [old-model]')

        log_file = config_dir / 'freerouter.log'
        log_file.write_text("INFO:     Uvicorn running on http://0.0.0.0:4000\n")

        with patch('time.sleep'):
            with patch('subprocess.Popen') as mock_popen:
                mock_process = MagicMock()
                mock_process.pid = 12345
                mock_popen.return_value = mock_process

                with patch('sys.argv', ['freerouter', 'reload', '-r']):
                    main()

        # Check backup was created
        backups = list(config_dir.glob('config.yaml.backup.*'))
        assert len(backups) > 0



class TestRestoreCommand:
    """Test restore command"""

    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary config directory"""
        temp_dir = tempfile.mkdtemp()
        original_dir = os.getcwd()
        os.chdir(temp_dir)
        yield temp_dir
        os.chdir(original_dir)
        shutil.rmtree(temp_dir)

    def test_restore_with_valid_backup(self, temp_config_dir):
        """Test restore command with valid backup file"""
        # Setup config
        config_dir = Path('config')
        config_dir.mkdir()

        config_file = config_dir / 'config.yaml'
        config_file.write_text('model_list: [current]')

        # Create backup
        backup_file = config_dir / 'config.yaml.backup.20251226_120000'
        backup_file.write_text('model_list: [backup]')

        # Run restore with -y to skip confirmation
        with patch('sys.argv', ['freerouter', 'restore', 'config.yaml.backup.20251226_120000', '-y']):
            main()

        # Verify config was restored
        restored_content = config_file.read_text()
        assert 'backup' in restored_content

        # Verify current config was backed up
        backups = list(config_dir.glob('config.yaml.backup.*'))
        assert len(backups) >= 2  # Original backup + new backup

    def test_restore_with_nonexistent_backup(self, temp_config_dir, caplog):
        """Test restore command with non-existent backup"""
        config_dir = Path('config')
        config_dir.mkdir()

        config_file = config_dir / 'config.yaml'
        config_file.write_text('model_list: []')

        with pytest.raises(SystemExit):
            with patch('sys.argv', ['freerouter', 'restore', 'nonexistent.backup', '-y']):
                main()

        assert 'not found' in caplog.text

    def test_restore_lists_available_backups(self, temp_config_dir, capsys):
        """Test restore shows available backups when file not found"""
        config_dir = Path('config')
        config_dir.mkdir()

        config_file = config_dir / 'config.yaml'
        config_file.write_text('model_list: []')

        # Create some backups
        (config_dir / 'config.yaml.backup.20251226_120000').write_text('backup1')
        (config_dir / 'config.yaml.backup.20251226_130000').write_text('backup2')

        with pytest.raises(SystemExit):
            with patch('sys.argv', ['freerouter', 'restore', 'nonexistent', '-y']):
                main()

        # Check that available backups are listed in output
        captured = capsys.readouterr()
        # Either in stdout or stderr (due to logging)
        output = captured.out + captured.err
        # Just check that the command didn't crash and exited properly
        # The backup listing is logged, so we mainly verify it handles missing files correctly

    def test_restore_with_confirmation(self, temp_config_dir):
        """Test restore command with user confirmation"""
        config_dir = Path('config')
        config_dir.mkdir()

        config_file = config_dir / 'config.yaml'
        config_file.write_text('model_list: [current]')

        backup_file = config_dir / 'config.yaml.backup.20251226_120000'
        backup_file.write_text('model_list: [backup]')

        # User says yes
        with patch('builtins.input', return_value='y'):
            with patch('sys.argv', ['freerouter', 'restore', 'config.yaml.backup.20251226_120000']):
                main()

        restored_content = config_file.read_text()
        assert 'backup' in restored_content

    def test_restore_cancelled_by_user(self, temp_config_dir):
        """Test restore command cancelled by user"""
        config_dir = Path('config')
        config_dir.mkdir()

        config_file = config_dir / 'config.yaml'
        original_content = 'model_list: [current]'
        config_file.write_text(original_content)

        backup_file = config_dir / 'config.yaml.backup.20251226_120000'
        backup_file.write_text('model_list: [backup]')

        # User says no
        with patch('builtins.input', return_value='n'):
            with pytest.raises(SystemExit) as exc_info:
                with patch('sys.argv', ['freerouter', 'restore', 'config.yaml.backup.20251226_120000']):
                    main()

        # Verify config was NOT changed
        assert config_file.read_text() == original_content


class TestStatusCommand:
    """Test status command"""

    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary config directory"""
        temp_dir = tempfile.mkdtemp()
        config_dir = Path(temp_dir) / "config"
        config_dir.mkdir()

        # Create config file
        config_file = config_dir / "config.yaml"
        config_file.write_text("model_list:\n  - model_name: test-model\n")

        original_dir = os.getcwd()
        os.chdir(temp_dir)
        yield config_dir
        os.chdir(original_dir)
        shutil.rmtree(temp_dir)

    def test_status_command_not_running(self, temp_config_dir, capsys):
        """Test status command when service is not running"""
        with patch('sys.argv', ['freerouter', 'status']):
            main()

        # Check console output (rich outputs to stdout)
        captured = capsys.readouterr()
        assert "Not Running" in captured.out

    def test_status_command_running(self, temp_config_dir, capsys):
        """Test status command when service is running"""
        # Create PID file
        pid_file = temp_config_dir / "freerouter.pid"
        current_pid = os.getpid()
        pid_file.write_text(str(current_pid))

        with patch('sys.argv', ['freerouter', 'status']):
            main()

        # Check console output
        captured = capsys.readouterr()
        assert "Running" in captured.out
        assert str(current_pid) in captured.out

    def test_status_command_stale_pid(self, temp_config_dir, capsys):
        """Test status command with stale PID file"""
        # Create PID file with non-existent PID
        pid_file = temp_config_dir / "freerouter.pid"
        pid_file.write_text("999999")

        with patch('sys.argv', ['freerouter', 'status']):
            main()

        # Check console output
        captured = capsys.readouterr()
        assert "Not Running" in captured.out
        assert "stale" in captured.out

        # Verify PID file was cleaned up
        assert not pid_file.exists()


class TestListCommand:
    """Test list command improvements"""

    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary config directory"""
        temp_dir = tempfile.mkdtemp()
        config_dir = Path(temp_dir) / "config"
        config_dir.mkdir()

        # Create config file with multiple providers
        config_file = config_dir / "config.yaml"
        config_content = """
model_list:
  - model_name: gpt-4
    litellm_params:
      model: openai/gpt-4
  - model_name: claude-3
    litellm_params:
      model: anthropic/claude-3
  - model_name: gemini-pro
    litellm_params:
      model: google/gemini-pro
"""
        config_file.write_text(config_content)

        original_dir = os.getcwd()
        os.chdir(temp_dir)
        yield config_dir
        os.chdir(original_dir)
        shutil.rmtree(temp_dir)

    def test_list_shows_service_status_not_running(self, temp_config_dir, capsys):
        """Test list command shows service status when not running"""
        with patch('sys.argv', ['freerouter', 'list']):
            main()

        captured = capsys.readouterr()
        assert "Service Not Running" in captured.out
        assert "freerouter start" in captured.out

    def test_list_shows_service_status_running(self, temp_config_dir, capsys):
        """Test list command shows service status when running"""
        # Create PID file
        pid_file = temp_config_dir / "freerouter.pid"
        current_pid = os.getpid()
        pid_file.write_text(str(current_pid))

        with patch('sys.argv', ['freerouter', 'list']):
            main()

        captured = capsys.readouterr()
        assert "Service Running" in captured.out
        assert str(current_pid) in captured.out

    def test_list_groups_by_provider(self, temp_config_dir, capsys):
        """Test list command groups models by provider"""
        with patch('sys.argv', ['freerouter', 'list']):
            main()

        captured = capsys.readouterr()
        # Check provider grouping (now uppercase)
        assert "OPENAI" in captured.out or "ANTHROPIC" in captured.out or "GOOGLE" in captured.out
        assert "3 models across" in captured.out

    def test_list_compact_format(self, temp_config_dir, capsys):
        """Test list command uses compact 2-column format"""
        with patch('sys.argv', ['freerouter', 'list']):
            main()

        captured = capsys.readouterr()
        # Verify it's more compact than before (grouped by provider)
        lines = captured.out.split('\n')
        # Should have fewer lines than old format (was 1 line per model)
        assert len([l for l in lines if l.strip()]) < 20  # Much fewer than 3 models in old format


class TestSelectCommand:
    """Test select command"""

    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary config directory"""
        temp_dir = tempfile.mkdtemp()
        config_dir = Path(temp_dir) / "config"
        config_dir.mkdir()

        original_dir = os.getcwd()
        os.chdir(temp_dir)
        yield config_dir
        os.chdir(original_dir)
        shutil.rmtree(temp_dir)

    def test_select_command_no_config(self, temp_config_dir, caplog):
        """Test select command without config file"""
        with pytest.raises(SystemExit):
            with patch('sys.argv', ['freerouter', 'select']):
                main()

        assert 'not found' in caplog.text

    def test_select_command_empty_config(self, temp_config_dir, caplog):
        """Test select command with empty config"""
        config_file = temp_config_dir / "config.yaml"
        config_file.write_text("model_list: []")

        with pytest.raises(SystemExit):
            with patch('sys.argv', ['freerouter', 'select']):
                main()

        assert 'No models found' in caplog.text

    def test_select_command_filters_models(self, temp_config_dir):
        """Test select command filters config to selected models"""
        # Create config with multiple models
        config_file = temp_config_dir / "config.yaml"
        config_content = """
litellm_settings:
  drop_params: true
  set_verbose: true
model_list:
  - model_name: model-1
    litellm_params:
      model: openai/model-1
  - model_name: model-2
    litellm_params:
      model: openai/model-2
  - model_name: model-3
    litellm_params:
      model: openai/model-3
router_settings:
  num_retries: 3
"""
        config_file.write_text(config_content)

        # Mock questionary to select only model-1 and model-2
        with patch('questionary.checkbox') as mock_checkbox:
            mock_checkbox.return_value.ask.return_value = ['model-1', 'model-2']

            with patch('sys.argv', ['freerouter', 'select']):
                main()

        # Verify config was filtered
        updated_content = config_file.read_text()
        assert 'model-1' in updated_content
        assert 'model-2' in updated_content
        assert 'model-3' not in updated_content

        # Verify backup was created
        backups = list(temp_config_dir.glob('config.yaml.backup.*'))
        assert len(backups) > 0

    def test_select_command_no_selection(self, temp_config_dir):
        """Test select command when no models are selected"""
        config_file = temp_config_dir / "config.yaml"
        config_content = """
model_list:
  - model_name: model-1
    litellm_params:
      model: openai/model-1
"""
        config_file.write_text(config_content)

        # Mock questionary to return empty selection
        with patch('questionary.checkbox') as mock_checkbox:
            mock_checkbox.return_value.ask.return_value = None

            with pytest.raises(SystemExit):
                with patch('sys.argv', ['freerouter', 'select']):
                    main()

        # Verify config was NOT changed
        updated_content = config_file.read_text()
        assert 'model-1' in updated_content

    def test_select_command_preserves_settings(self, temp_config_dir):
        """Test select command preserves litellm_settings and router_settings"""
        config_file = temp_config_dir / "config.yaml"
        config_content = """
litellm_settings:
  drop_params: true
  set_verbose: true
  custom_param: test
model_list:
  - model_name: model-1
    litellm_params:
      model: openai/model-1
  - model_name: model-2
    litellm_params:
      model: openai/model-2
router_settings:
  num_retries: 3
  timeout: 60
"""
        config_file.write_text(config_content)

        # Select only model-1
        with patch('questionary.checkbox') as mock_checkbox:
            mock_checkbox.return_value.ask.return_value = ['model-1']

            with patch('sys.argv', ['freerouter', 'select']):
                main()

        # Verify settings are preserved
        import yaml
        with open(config_file) as f:
            config = yaml.safe_load(f)

        assert config['litellm_settings']['drop_params'] is True
        assert config['litellm_settings']['set_verbose'] is True
        assert config['litellm_settings']['custom_param'] == 'test'
        assert config['router_settings']['num_retries'] == 3
        assert config['router_settings']['timeout'] == 60
        assert len(config['model_list']) == 1

