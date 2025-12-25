#!/usr/bin/env python3
"""
FreeRouter Test Runner

Run all tests with coverage report
"""

import sys
import subprocess
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)


def print_header(text):
    """Print a formatted header"""
    logger.info("")
    logger.info("=" * 60)
    logger.info(f"  {text}")
    logger.info("=" * 60)


def run_tests():
    """Run all tests with coverage"""
    print_header("Running FreeRouter Tests")

    try:
        # Run pytest with coverage
        cmd = [
            "pytest",
            "tests/",
            "-v",
            "--cov=freerouter",
            "--cov-report=term-missing",
            "--cov-report=html",
            "--tb=short"
        ]

        logger.info("")
        logger.info(f"Command: {' '.join(cmd)}")
        logger.info("")

        result = subprocess.run(cmd, check=True)

        print_header("✅ All Tests Passed!")
        logger.info("")
        logger.info("Coverage report generated:")
        logger.info("  - Terminal output above")
        logger.info("  - HTML report: htmlcov/index.html")
        logger.info("")

        return 0

    except subprocess.CalledProcessError as e:
        print_header("❌ Tests Failed!")
        logger.error("")
        logger.error(f"Exit code: {e.returncode}")
        logger.error("")
        return e.returncode

    except FileNotFoundError:
        print_header("❌ Error: pytest not found")
        logger.error("")
        logger.error("Please install test dependencies:")
        logger.error("  pip install pytest pytest-cov")
        logger.error("")
        return 1

    except KeyboardInterrupt:
        logger.info("")
        logger.info("Tests interrupted by user")
        return 130


def run_quick_tests():
    """Run only unit and integration tests (skip E2E)"""
    print_header("Running Quick Tests (Skip E2E)")

    try:
        cmd = [
            "pytest",
            "tests/test_providers.py",
            "tests/test_fetcher.py",
            "tests/test_integration.py",
            "-v",
            "--tb=short"
        ]

        logger.info("")
        logger.info(f"Command: {' '.join(cmd)}")
        logger.info("")

        result = subprocess.run(cmd, check=True)

        print_header("✅ Quick Tests Passed!")
        logger.info("")
        logger.info("Note: E2E tests were skipped (use --all to run all tests)")
        logger.info("")

        return 0

    except subprocess.CalledProcessError as e:
        print_header("❌ Tests Failed!")
        return e.returncode


def main():
    """Main execution"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Run FreeRouter tests",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/test.py              # Run all tests with coverage
  python scripts/test.py --quick      # Run only unit/integration tests (fast)
  python scripts/test.py --e2e        # Run only E2E tests

Test Types:
  - Unit tests: Test individual components (fast)
  - Integration tests: Test config generation (fast)
  - E2E tests: Test complete workflow with real service (~10s)
        """
    )

    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run only quick tests (skip E2E)"
    )

    parser.add_argument(
        "--e2e",
        action="store_true",
        help="Run only E2E tests"
    )

    args = parser.parse_args()

    # Check we're in the right directory
    if not Path("tests").exists():
        logger.error("Error: tests/ directory not found")
        logger.error("Please run this script from the project root directory")
        return 1

    if args.e2e:
        print_header("Running E2E Tests Only")
        try:
            cmd = ["pytest", "tests/test_e2e.py", "-v", "--tb=short"]
            subprocess.run(cmd, check=True)
            print_header("✅ E2E Tests Passed!")
            return 0
        except subprocess.CalledProcessError as e:
            print_header("❌ E2E Tests Failed!")
            return e.returncode

    elif args.quick:
        return run_quick_tests()

    else:
        return run_tests()


if __name__ == "__main__":
    sys.exit(main())
