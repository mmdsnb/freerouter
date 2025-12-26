#!/usr/bin/env python3
"""
FreeRouter CLI - Command Line Interface

Usage:
    freerouter                  # Start service (interactive)
    freerouter start            # Start service
    freerouter fetch            # Fetch models and generate config
    freerouter list             # List available models
    freerouter logs             # Show service logs (if running in background)
    freerouter init             # Initialize config directory
    freerouter --version        # Show version
"""

import sys
import argparse
import logging
from pathlib import Path

from freerouter.__version__ import __version__
from freerouter.cli.config import ConfigManager
from freerouter.core.fetcher import FreeRouterFetcher
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def cmd_init(args):
    """Initialize configuration (interactive)"""
    config_mgr = ConfigManager()

    # Interactive prompts
    print("=" * 60)
    print("FreeRouter Configuration Initialization")
    print("=" * 60)
    print("\nChoose configuration file location:")
    print("1. ~/.config/freerouter/providers.yaml (Recommended, user-level)")
    print("2. ./config/providers.yaml (Current directory, project-level)")

    while True:
        choice = input("\nEnter your choice [1/2] (default: 1): ").strip() or "1"
        if choice in ["1", "2"]:
            break
        print("Invalid option. Please enter 1 or 2")

    use_user_config = (choice == "1")
    config_dir = config_mgr.init_config(interactive=True, use_user_config=use_user_config)

    print(f"\n✓ Configuration initialized: {config_dir / 'providers.yaml'}")
    print(f"✓ All providers are disabled by default (enabled: false)")
    print(f"\nNext steps:")
    print(f"1. Edit {config_dir / 'providers.yaml'} to configure your providers")
    print(f"2. Set enabled: true for the providers you want to use")
    print(f"3. Run 'freerouter fetch' to fetch model list")
    print(f"4. Run 'freerouter start' to start the service")
    print("=" * 60)


def cmd_fetch(args):
    """Fetch models and generate config"""
    config_mgr = ConfigManager()

    # Find provider config
    provider_config = config_mgr.find_provider_config()
    if not provider_config:
        logger.error("No providers.yaml found!")
        logger.info("Run 'freerouter init' to create configuration")
        sys.exit(1)

    # Get output path
    output_config = config_mgr.get_output_config_path()

    logger.info("=" * 60)
    logger.info("FreeRouter - Fetching models and generating config")
    logger.info("=" * 60)
    logger.info(f"Provider config: {provider_config}")
    logger.info(f"Output config: {output_config}")

    # Fetch models
    fetcher = FreeRouterFetcher(config_path=str(output_config))
    fetcher.load_providers_from_yaml(str(provider_config))

    if fetcher.generate_config():
        logger.info("=" * 60)
        logger.info("✓ Config generation successful!")
        logger.info(f"Generated: {output_config}")
        logger.info("=" * 60)
    else:
        logger.error("✗ Config generation failed!")
        sys.exit(1)


def cmd_start(args):
    """Start FreeRouter service"""
    import os
    import subprocess
    import time

    config_mgr = ConfigManager()

    # Find config
    output_config = config_mgr.get_output_config_path()
    if not output_config.exists():
        logger.error(f"Config not found: {output_config}")
        logger.info("Run 'freerouter fetch' first to generate config")
        sys.exit(1)

    # IMPORTANT: Remove CONFIG_FILE_PATH env var if exists
    # LiteLLM prioritizes env var over --config flag, which causes confusion
    if 'CONFIG_FILE_PATH' in os.environ:
        logger.warning(f"Removing CONFIG_FILE_PATH env var (was: {os.environ['CONFIG_FILE_PATH']})")
        logger.warning(f"Using freerouter config instead: {output_config}")
        del os.environ['CONFIG_FILE_PATH']

    # Log file path
    log_dir = output_config.parent
    log_file = log_dir / "freerouter.log"
    pid_file = log_dir / "freerouter.pid"

    # Check if already running
    if pid_file.exists():
        with open(pid_file) as f:
            old_pid = f.read().strip()
        try:
            # Check if process is still running
            os.kill(int(old_pid), 0)
            logger.error(f"FreeRouter is already running (PID: {old_pid})")
            logger.info("Use 'freerouter logs' to view logs or kill the process first")
            sys.exit(1)
        except (OSError, ValueError):
            # Process not running, remove stale pid file
            pid_file.unlink()

    port = os.getenv("LITELLM_PORT", "4000")
    host = os.getenv("LITELLM_HOST", "0.0.0.0")

    logger.info("=" * 60)
    logger.info("Starting FreeRouter Service")
    logger.info("=" * 60)
    logger.info(f"Host: {host}")
    logger.info(f"Port: {port}")
    logger.info(f"Config: {output_config}")
    logger.info(f"Log file: {log_file}")
    logger.info("=" * 60)

    try:
        cmd = [
            "litellm",
            "--config", str(output_config),
            "--port", str(port),
            "--host", host
        ]

        # Open log file
        log_handle = open(log_file, "a")

        # Start process as daemon (detached from parent)
        process = subprocess.Popen(
            cmd,
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            start_new_session=True,  # Detach from parent process
            bufsize=1
        )

        # Write PID file
        with open(pid_file, "w") as f:
            f.write(str(process.pid))

        # Wait and monitor log file for startup success
        startup_success = False
        startup_timeout = 30
        start_time = time.time()

        print("\nWaiting for service to start...")
        time.sleep(2)  # Give it a moment to start writing logs

        # Tail the log file to check for startup
        last_pos = 0
        while time.time() - start_time < startup_timeout:
            try:
                with open(log_file, "r") as f:
                    f.seek(last_pos)
                    new_lines = f.readlines()
                    last_pos = f.tell()

                    for line in new_lines:
                        print(line, end="")

                        if "Uvicorn running on" in line:
                            startup_success = True
                            break

                        if "error" in line.lower() and "failed" in line.lower():
                            logger.error("\nStartup failed! Check logs for details.")
                            process.terminate()
                            pid_file.unlink()
                            sys.exit(1)

                if startup_success:
                    break

                time.sleep(0.5)

            except FileNotFoundError:
                time.sleep(0.5)
                continue

        if startup_success:
            logger.info("\n" + "=" * 60)
            logger.info("✓ FreeRouter started successfully!")
            logger.info(f"  PID: {process.pid}")
            logger.info(f"  URL: http://{host}:{port}")
            logger.info(f"  Logs: {log_file}")
            logger.info("")
            logger.info("Commands:")
            logger.info("  freerouter logs      - View real-time logs")
            logger.info("  freerouter stop      - Stop the service")
            logger.info("=" * 60)
        else:
            logger.error("\nStartup timeout! The service may still be starting.")
            logger.info(f"Check logs: tail -f {log_file}")
            logger.info(f"If failed, kill process: kill {process.pid}")

    except FileNotFoundError:
        logger.error("litellm not found! Please install: pip install litellm")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to start: {e}")
        if pid_file.exists():
            pid_file.unlink()
        sys.exit(1)


def cmd_list(args):
    """List available models"""
    import os
    import yaml

    config_mgr = ConfigManager()
    output_config = config_mgr.get_output_config_path()

    if not output_config.exists():
        logger.error(f"Config not found: {output_config}")
        logger.info("Run 'freerouter fetch' first to generate config")
        sys.exit(1)

    # Show service status
    if is_service_running():
        log_dir = output_config.parent
        pid_file = log_dir / "freerouter.pid"
        with open(pid_file) as f:
            pid = f.read().strip()

        port = os.getenv("LITELLM_PORT", "4000")
        host = os.getenv("LITELLM_HOST", "0.0.0.0")
        url = f"http://localhost:{port}" if host == "0.0.0.0" else f"http://{host}:{port}"

        print(f"\n● Service Running (PID: {pid}, {url})")
    else:
        print(f"\n○ Service Not Running (start with: freerouter start)")

    print("=" * 60)

    with open(output_config) as f:
        config = yaml.safe_load(f)

    models = config.get("model_list", [])

    if not models:
        print("No models configured.")
        return

    # Group models by provider for better readability
    from collections import defaultdict
    providers_models = defaultdict(list)

    for model in models:
        model_name = model.get("model_name", "")
        litellm_model = model.get("litellm_params", {}).get("model", "")
        provider = litellm_model.split("/")[0] if "/" in litellm_model else "unknown"
        providers_models[provider].append(model_name)

    # Print models grouped by provider in compact format
    for provider in sorted(providers_models.keys()):
        models_list = providers_models[provider]
        print(f"\n[{provider}] ({len(models_list)} models)")

        # Print in 2 columns for compact display
        for i in range(0, len(models_list), 2):
            left = models_list[i]
            right = models_list[i + 1] if i + 1 < len(models_list) else ""
            print(f"  {left:<50} {right}")

    print(f"\n{'=' * 60}")
    print(f"Total: {len(models)} models across {len(providers_models)} providers")


def cmd_stop(args):
    """Stop FreeRouter service"""
    import os
    import time

    config_mgr = ConfigManager()
    output_config = config_mgr.get_output_config_path()
    log_dir = output_config.parent
    pid_file = log_dir / "freerouter.pid"

    # Check if service is running
    if not pid_file.exists():
        logger.error("FreeRouter is not running")
        sys.exit(1)

    with open(pid_file) as f:
        pid = f.read().strip()

    try:
        pid_int = int(pid)
        os.kill(pid_int, 0)  # Check if running
    except (OSError, ValueError):
        logger.error(f"FreeRouter process (PID: {pid}) is not running")
        pid_file.unlink()
        sys.exit(1)

    logger.info(f"Stopping FreeRouter service (PID: {pid})...")

    try:
        # Send SIGTERM
        os.kill(pid_int, 15)

        # Wait for process to stop
        for i in range(10):
            try:
                os.kill(pid_int, 0)
                time.sleep(0.5)
            except OSError:
                break

        # Check if stopped
        try:
            os.kill(pid_int, 0)
            logger.error("Failed to stop service gracefully, use: kill -9 {pid}")
            sys.exit(1)
        except OSError:
            pid_file.unlink()
            logger.info("✓ FreeRouter stopped successfully")

    except Exception as e:
        logger.error(f"Failed to stop service: {e}")
        sys.exit(1)


def cmd_logs(args):
    """Show service logs in real-time"""
    import os
    import time

    config_mgr = ConfigManager()
    output_config = config_mgr.get_output_config_path()
    log_dir = output_config.parent
    log_file = log_dir / "freerouter.log"
    pid_file = log_dir / "freerouter.pid"

    # Check if service is running
    if not pid_file.exists():
        logger.error("FreeRouter is not running")
        logger.info("Start it with: freerouter start")
        sys.exit(1)

    with open(pid_file) as f:
        pid = f.read().strip()

    try:
        os.kill(int(pid), 0)
    except (OSError, ValueError):
        logger.error(f"FreeRouter process (PID: {pid}) is not running")
        logger.info("Start it with: freerouter start")
        pid_file.unlink()
        sys.exit(1)

    # Check if log file exists
    if not log_file.exists():
        logger.error(f"Log file not found: {log_file}")
        sys.exit(1)

    logger.info(f"Showing logs from: {log_file}")
    logger.info(f"Service PID: {pid}")
    logger.info("Press Ctrl+C to exit\n")
    logger.info("=" * 60)

    # Tail the log file
    try:
        with open(log_file, "r") as f:
            # Go to end of file
            f.seek(0, 2)

            while True:
                line = f.readline()
                if line:
                    print(line, end="")
                else:
                    time.sleep(0.1)

                    # Check if process is still running
                    try:
                        os.kill(int(pid), 0)
                    except (OSError, ValueError):
                        logger.info("\n" + "=" * 60)
                        logger.info("Service stopped")
                        break

    except KeyboardInterrupt:
        logger.info("\n" + "=" * 60)
        logger.info("Stopped viewing logs")
    except Exception as e:
        logger.error(f"Error reading logs: {e}")


def cmd_status(args):
    """Show FreeRouter service status"""
    import os
    import time
    import datetime

    config_mgr = ConfigManager()
    output_config = config_mgr.get_output_config_path()
    log_dir = output_config.parent
    pid_file = log_dir / "freerouter.pid"
    log_file = log_dir / "freerouter.log"

    logger.info("=" * 60)
    logger.info("FreeRouter Service Status")
    logger.info("=" * 60)

    # Check if service is running
    if not pid_file.exists():
        logger.info("Status: ○ Not Running")
        logger.info("\nStart service with: freerouter start")
        logger.info("=" * 60)
        return

    try:
        with open(pid_file) as f:
            pid = int(f.read().strip())

        # Check if process is running
        os.kill(pid, 0)

        # Service is running
        logger.info("Status: ● Running")
        logger.info(f"PID: {pid}")

        # Get service URL
        port = os.getenv("LITELLM_PORT", "4000")
        host = os.getenv("LITELLM_HOST", "0.0.0.0")
        url = f"http://localhost:{port}" if host == "0.0.0.0" else f"http://{host}:{port}"
        logger.info(f"URL: {url}")

        # Config file
        logger.info(f"Config: {output_config}")

        # Calculate uptime from PID file creation time
        if pid_file.exists():
            start_time = pid_file.stat().st_mtime
            uptime_seconds = time.time() - start_time
            uptime_str = format_uptime(uptime_seconds)
            logger.info(f"Uptime: {uptime_str}")

        # Count models
        if output_config.exists():
            import yaml
            with open(output_config) as f:
                config = yaml.safe_load(f)
            model_count = len(config.get("model_list", []))
            logger.info(f"Models: {model_count} configured")

        # Log file
        if log_file.exists():
            log_size = log_file.stat().st_size / 1024  # KB
            logger.info(f"Log: {log_file} ({log_size:.1f} KB)")

    except (OSError, ValueError):
        # Process not running, but PID file exists (stale)
        logger.info("Status: ○ Not Running (stale PID file)")
        logger.info(f"PID: {pid} (not found)")
        logger.info("\nClean up and start: freerouter start")
        pid_file.unlink()

    logger.info("=" * 60)


def format_uptime(seconds):
    """Format uptime in human readable format"""
    if seconds < 60:
        return f"{int(seconds)} seconds"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''}"
    elif seconds < 86400:
        hours = int(seconds / 3600)
        minutes = int((seconds % 3600) / 60)
        return f"{hours} hour{'s' if hours != 1 else ''} {minutes} minute{'s' if minutes != 1 else ''}"
    else:
        days = int(seconds / 86400)
        hours = int((seconds % 86400) / 3600)
        return f"{days} day{'s' if days != 1 else ''} {hours} hour{'s' if hours != 1 else ''}"


def backup_config(config_path: Path):
    """
    Backup configuration file with timestamp

    Args:
        config_path: Path to config file to backup
    """
    import datetime
    import shutil

    if not config_path.exists():
        return

    # Create backup with timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = config_path.parent / f"{config_path.name}.backup.{timestamp}"

    shutil.copy2(config_path, backup_path)

    # Show prominent backup message
    logger.info("=" * 60)
    logger.info(f"✓ Backup created: {backup_path.name}")
    logger.info(f"  Location: {backup_path}")
    logger.info(f"  Restore: freerouter restore {backup_path.name}")
    logger.info("=" * 60)

    # Cleanup old backups (keep only 5 most recent)
    cleanup_old_backups(config_path, keep=5)


def cleanup_old_backups(config_path: Path, keep: int = 5):
    """
    Remove old backup files, keeping only the most recent ones

    Args:
        config_path: Path to config file
        keep: Number of backups to keep
    """
    backup_pattern = f"{config_path.name}.backup.*"
    backup_files = sorted(
        config_path.parent.glob(backup_pattern),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )

    # Remove old backups
    for old_backup in backup_files[keep:]:
        try:
            old_backup.unlink()
            logger.debug(f"Removed old backup: {old_backup.name}")
        except Exception as e:
            logger.warning(f"Failed to remove old backup {old_backup.name}: {e}")


def is_service_running() -> bool:
    """
    Check if FreeRouter service is currently running

    Returns:
        True if service is running, False otherwise
    """
    import os

    config_mgr = ConfigManager()
    output_config = config_mgr.get_output_config_path()
    log_dir = output_config.parent
    pid_file = log_dir / "freerouter.pid"

    if not pid_file.exists():
        return False

    try:
        with open(pid_file) as f:
            pid = int(f.read().strip())

        # Check if process is running
        os.kill(pid, 0)
        return True
    except (OSError, ValueError):
        return False


def cmd_reload(args):
    """
    Reload FreeRouter service

    Two modes:
    - Normal: stop + start (restart service with existing config)
    - Refresh (-r): fetch + stop + start (refresh config from providers)
    """
    import time

    config_mgr = ConfigManager()
    output_config = config_mgr.get_output_config_path()

    logger.info("=" * 60)
    logger.info("Reloading FreeRouter Service")
    logger.info("=" * 60)

    # 1. If --refresh, backup and regenerate config
    if args.refresh:
        logger.info("Refreshing configuration from providers...")

        # Backup existing config
        if output_config.exists():
            backup_config(output_config)

        # Regenerate config
        cmd_fetch(args)
        logger.info("✓ Configuration refreshed")

    # 2. Stop service if running
    if is_service_running():
        logger.info("Stopping service...")
        cmd_stop(args)
        time.sleep(1)  # Wait for clean shutdown
    else:
        logger.info("Service is not running")

    # 3. Start service
    logger.info("Starting service...")
    cmd_start(args)

    logger.info("=" * 60)
    logger.info("✓ Service reloaded successfully")
    logger.info("=" * 60)


def cmd_restore(args):
    """
    Restore configuration from backup

    Args:
        args.backup_file: Backup file name or full path
    """
    import shutil

    config_mgr = ConfigManager()
    output_config = config_mgr.get_output_config_path()
    config_dir = output_config.parent

    backup_file = args.backup_file

    # If just a filename, look in config directory
    if not Path(backup_file).is_absolute():
        backup_path = config_dir / backup_file
    else:
        backup_path = Path(backup_file)

    # Check if backup exists
    if not backup_path.exists():
        logger.error(f"Backup file not found: {backup_path}")

        # List available backups
        available_backups = sorted(
            config_dir.glob(f"{output_config.name}.backup.*"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )

        if available_backups:
            logger.info("\nAvailable backups:")
            for backup in available_backups:
                mtime = backup.stat().st_mtime
                import datetime
                timestamp = datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
                logger.info(f"  - {backup.name} ({timestamp})")
            logger.info(f"\nUsage: freerouter restore <backup-file>")
        else:
            logger.info("No backups found")

        sys.exit(1)

    # Confirm restore
    logger.info("=" * 60)
    logger.info("Restore Configuration")
    logger.info("=" * 60)
    logger.info(f"From: {backup_path.name}")
    logger.info(f"To:   {output_config}")

    if not args.yes:
        response = input("\nContinue? [y/N]: ").strip().lower()
        if response != 'y':
            logger.info("Restore cancelled")
            sys.exit(0)

    # Backup current config before restoring
    if output_config.exists():
        logger.info("Creating backup of current config...")
        backup_config(output_config)

    # Restore
    try:
        shutil.copy2(backup_path, output_config)
        logger.info("=" * 60)
        logger.info("✓ Configuration restored successfully")
        logger.info("=" * 60)
        logger.info(f"Restored from: {backup_path.name}")
        logger.info("\nTo apply changes, run: freerouter reload")

    except Exception as e:
        logger.error(f"Failed to restore configuration: {e}")
        sys.exit(1)


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        prog="freerouter",
        description="FreeRouter - Free LLM Router Service",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"FreeRouter {__version__}"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # init command
    parser_init = subparsers.add_parser("init", help="Initialize configuration")
    parser_init.set_defaults(func=cmd_init)

    # fetch command
    parser_fetch = subparsers.add_parser("fetch", help="Fetch models and generate config")
    parser_fetch.set_defaults(func=cmd_fetch)

    # start command
    parser_start = subparsers.add_parser("start", help="Start FreeRouter service")
    parser_start.set_defaults(func=cmd_start)

    # list command
    parser_list = subparsers.add_parser("list", help="List available models")
    parser_list.set_defaults(func=cmd_list)

    # stop command
    parser_stop = subparsers.add_parser("stop", help="Stop FreeRouter service")
    parser_stop.set_defaults(func=cmd_stop)

    # logs command
    parser_logs = subparsers.add_parser("logs", help="Show service logs")
    parser_logs.set_defaults(func=cmd_logs)

    # status command
    parser_status = subparsers.add_parser("status", help="Show service status")
    parser_status.set_defaults(func=cmd_status)

    # reload command
    parser_reload = subparsers.add_parser(
        "reload",
        help="Reload service (restart or refresh config)"
    )
    parser_reload.add_argument(
        "-r", "--refresh",
        action="store_true",
        help="Refresh configuration from providers before reloading"
    )
    parser_reload.set_defaults(func=cmd_reload)

    # restore command
    parser_restore = subparsers.add_parser(
        "restore",
        help="Restore configuration from backup"
    )
    parser_restore.add_argument(
        "backup_file",
        help="Backup file name (e.g., config.yaml.backup.20251226_120530)"
    )
    parser_restore.add_argument(
        "-y", "--yes",
        action="store_true",
        help="Skip confirmation prompt"
    )
    parser_restore.set_defaults(func=cmd_restore)

    # Parse arguments
    args = parser.parse_args()

    # If no command, default to start
    if not args.command:
        args.command = "start"
        args.func = cmd_start

    # Execute command
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
