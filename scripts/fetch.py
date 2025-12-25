#!/usr/bin/env python3
"""
FreeRouter Fetch Script

Fetches models from configured providers and generates litellm config.
"""

import sys
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from freerouter.core.fetcher import FreeRouterFetcher
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main execution"""
    logger.info("=" * 60)
    logger.info("FreeRouter - Fetching models and generating config")
    logger.info("=" * 60)

    fetcher = FreeRouterFetcher(config_path="config/config.yaml")

    # Load providers from YAML config
    fetcher.load_providers_from_yaml("config/providers.yaml")

    # Generate litellm config
    if fetcher.generate_config():
        logger.info("=" * 60)
        logger.info("✓ Config generation successful!")
        logger.info("Run 'python scripts/start.py' to start the service")
        logger.info("=" * 60)
    else:
        logger.error("=" * 60)
        logger.error("✗ Config generation failed!")
        logger.error("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()
