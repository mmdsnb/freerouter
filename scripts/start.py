#!/usr/bin/env python3
"""
FreeRouter Service Starter

Starts the litellm service with the generated config
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_config_exists():
    """Check if config.yaml exists"""
    if not Path("config/config.yaml").exists():
        logger.error("config/config.yaml not found!")
        logger.info("Please run 'python scripts/fetch.py' first to generate config")
        return False
    return True


def start_litellm():
    """Start litellm service"""
    port = os.getenv("LITELLM_PORT", "4000")
    host = os.getenv("LITELLM_HOST", "0.0.0.0")

    # Clear CONFIG_FILE_PATH to ensure our config is used
    if "CONFIG_FILE_PATH" in os.environ:
        logger.info(f"Removing CONFIG_FILE_PATH environment variable: {os.environ['CONFIG_FILE_PATH']}")
        del os.environ["CONFIG_FILE_PATH"]

    logger.info("=" * 60)
    logger.info("Starting FreeRouter Service")
    logger.info("=" * 60)
    logger.info(f"Host: {host}")
    logger.info(f"Port: {port}")
    logger.info(f"Config: config/config.yaml")
    logger.info("=" * 60)

    try:
        cmd = [
            "litellm",
            "--config", "config/config.yaml",
            "--port", str(port),
            "--host", host,
            "--detailed_debug"
        ]

        logger.info(f"Executing: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)

    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to start litellm: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("\nShutting down FreeRouter service...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


def main():
    """Main execution"""
    if not check_config_exists():
        sys.exit(1)

    start_litellm()


if __name__ == "__main__":
    main()
