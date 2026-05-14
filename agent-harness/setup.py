#!/usr/bin/env python3
"""setup.py for cli-anything-minecontext."""

from setuptools import find_namespace_packages, setup

with open("cli_anything/minecontext/README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="cli-anything-minecontext",
    version="1.0.0",
    description="CLI-Anything harness for MineContext local services",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/volcengine/MineContext",
    packages=find_namespace_packages(include=["cli_anything.*"]),
    python_requires=">=3.10",
    install_requires=["click>=8.0.0"],
    extras_require={"dev": ["pytest>=8.0.0"]},
    entry_points={
        "console_scripts": [
            "cli-anything-minecontext=cli_anything.minecontext.minecontext_cli:main",
        ],
    },
    package_data={"cli_anything.minecontext": ["skills/*.md"]},
    include_package_data=True,
    zip_safe=False,
)
