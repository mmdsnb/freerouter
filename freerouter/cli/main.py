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
    """Initialize configuration"""
    config_mgr = ConfigManager()
    config_dir = config_mgr.init_config()

    print(f"✓ Initialized FreeRouter configuration at: {config_dir}")
    print(f"\nNext steps:")
    print(f"1. Edit {config_dir}/providers.yaml to configure your providers")
    print(f"2. Run 'freerouter fetch' to fetch models")
    print(f"3. Run 'freerouter start' to start the service")


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

    config_mgr = ConfigManager()

    # Find config
    output_config = config_mgr.get_output_config_path()
    if not output_config.exists():
        logger.error(f"Config not found: {output_config}")
        logger.info("Run 'freerouter fetch' first to generate config")
        sys.exit(1)

    port = os.getenv("LITELLM_PORT", "4000")
    host = os.getenv("LITELLM_HOST", "0.0.0.0")

    logger.info("=" * 60)
    logger.info("Starting FreeRouter Service")
    logger.info("=" * 60)
    logger.info(f"Host: {host}")
    logger.info(f"Port: {port}")
    logger.info(f"Config: {output_config}")
    logger.info("=" * 60)

    try:
        cmd = [
            "litellm",
            "--config", str(output_config),
            "--port", str(port),
            "--host", host
        ]

        subprocess.run(cmd, check=True)

    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to start litellm: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("\nShutting down FreeRouter service...")
        sys.exit(0)
    except FileNotFoundError:
        logger.error("litellm not found! Please install: pip install litellm")
        sys.exit(1)


def cmd_list(args):
    """List available models"""
    import yaml

    config_mgr = ConfigManager()
    output_config = config_mgr.get_output_config_path()

    if not output_config.exists():
        logger.error(f"Config not found: {output_config}")
        logger.info("Run 'freerouter fetch' first to generate config")
        sys.exit(1)

    with open(output_config) as f:
        config = yaml.safe_load(f)

    models = config.get("model_list", [])

    if not models:
        print("No models configured.")
        return

    print(f"\n{'Model Name':<40} {'Provider':<20}")
    print("=" * 60)

    for model in models:
        model_name = model.get("model_name", "")
        litellm_model = model.get("litellm_params", {}).get("model", "")
        provider = litellm_model.split("/")[0] if "/" in litellm_model else "unknown"

        print(f"{model_name:<40} {provider:<20}")

    print(f"\nTotal: {len(models)} models")


def cmd_logs(args):
    """Show service logs (placeholder)"""
    print("Log viewing coming soon!")
    print("For now, run 'freerouter start' in foreground to see logs")


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

    # logs command
    parser_logs = subparsers.add_parser("logs", help="Show service logs")
    parser_logs.set_defaults(func=cmd_logs)

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
