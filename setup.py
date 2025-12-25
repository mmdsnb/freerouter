"""
FreeRouter Setup Configuration
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# Read version
version_file = Path(__file__).parent / "freerouter" / "__version__.py"
version_dict = {}
if version_file.exists():
    exec(version_file.read_text(), version_dict)
    version = version_dict.get("__version__", "0.1.0")
else:
    version = "0.1.0"

setup(
    name="freerouter",
    version=version,
    author="FreeRouter Contributors",
    author_email="",
    description="Free LLM Router Service based on LiteLLM",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mmdsnb/freerouter",
    packages=find_packages(exclude=["tests", "tests.*", "scripts", "docs"]),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "litellm[proxy]>=1.0.0",
        "pyyaml>=6.0",
        "requests>=2.31.0",
        "python-dotenv>=1.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "freerouter=freerouter.cli.main:main",
        ],
    },
)
